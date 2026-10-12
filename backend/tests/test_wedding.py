import io

from PIL import Image

from app.db import db
from app.import_wedding import natural_key
from app.models import WeddingPhoto
from tests.conftest import auth


def _save_image(path, size=(300, 200), fmt="JPEG"):
    Image.new("RGB", size, "#C9A48E").save(path, fmt)


def _run(app, folder, *args):
    return app.test_cli_runner().invoke(args=["import-wedding", str(folder), *args])


def _list(client, join):
    token, _ = join("看婚紗的人")
    return client.get("/api/wedding-photos", headers=auth(token)).get_json()["items"]


def test_natural_order():
    names = ["10.jpg", "2.jpg", "01.jpg", "IMG_9.jpg", "img_10.jpg"]
    assert sorted(names, key=natural_key) == ["01.jpg", "2.jpg", "10.jpg", "IMG_9.jpg", "img_10.jpg"]


def test_import_and_list_in_filename_order(app, client, join, tmp_path):
    for name in ["10.jpg", "2.jpg", "1.jpg"]:
        _save_image(tmp_path / name)

    result = _run(app, tmp_path)

    assert result.exit_code == 0, result.output
    items = _list(client, join)
    assert len(items) == 3
    with app.app_context():
        order = [
            db.session.get(WeddingPhoto, i["id"]).filename for i in items
        ]
    assert order == ["1.jpg", "2.jpg", "10.jpg"]


def test_wedding_photo_shape_has_no_original(app, client, join, tmp_path):
    _save_image(tmp_path / "01.jpg", size=(4000, 3000))

    _run(app, tmp_path)
    photo = _list(client, join)[0]

    # 僅供觀賞：只有顯示用與縮圖，沒有原檔
    assert set(photo) == {"id", "displayUrl", "thumbnailUrl", "width", "height"}
    assert (photo["width"], photo["height"]) == (4000, 3000)
    assert client.get(photo["thumbnailUrl"]).status_code == 200


def test_rerun_skips_existing_and_adds_new(app, client, join, tmp_path):
    _save_image(tmp_path / "02.jpg")
    _run(app, tmp_path)
    _save_image(tmp_path / "01.jpg")

    result = _run(app, tmp_path)

    assert "匯入了 1 張，跳過 1 張" in result.output
    with app.app_context():
        ordered = db.session.scalars(db.select(WeddingPhoto).order_by(WeddingPhoto.position))
        assert [p.filename for p in ordered] == ["01.jpg", "02.jpg"]


def test_replace(app, tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    _save_image(first / "a.jpg")
    _save_image(first / "b.jpg")
    _save_image(second / "c.jpg")
    _run(app, first)

    result = _run(app, second, "--replace")

    assert result.exit_code == 0, result.output
    with app.app_context():
        assert [p.filename for p in db.session.scalars(db.select(WeddingPhoto))] == ["c.jpg"]


def test_ignores_other_files_and_subfolders(app, tmp_path):
    _save_image(tmp_path / "01.jpg")
    (tmp_path / "notes.txt").write_text("hi")
    (tmp_path / "sub").mkdir()
    _save_image(tmp_path / "sub" / "02.jpg")

    _run(app, tmp_path)

    with app.app_context():
        assert db.session.query(WeddingPhoto).count() == 1


def test_broken_file_aborts_whole_import(app, tmp_path):
    _save_image(tmp_path / "01.jpg")
    (tmp_path / "02.jpg").write_bytes(b"not an image")

    result = _run(app, tmp_path)

    assert result.exit_code != 0
    assert "02.jpg" in result.output
    with app.app_context():
        assert db.session.query(WeddingPhoto).count() == 0


def test_empty_folder(app, tmp_path):
    result = _run(app, tmp_path)
    assert result.exit_code != 0


def test_dry_run(app, tmp_path):
    _save_image(tmp_path / "01.jpg")

    result = _run(app, tmp_path, "--dry-run")

    assert "預覽" in result.output
    with app.app_context():
        assert db.session.query(WeddingPhoto).count() == 0


def test_heic_is_accepted(app, tmp_path):
    buf = io.BytesIO()
    Image.new("RGB", (300, 200), "#C9A48E").save(buf, "HEIF")
    (tmp_path / "01.heic").write_bytes(buf.getvalue())

    result = _run(app, tmp_path)

    assert result.exit_code == 0, result.output


def test_requires_token(client):
    assert client.get("/api/wedding-photos").status_code == 401
