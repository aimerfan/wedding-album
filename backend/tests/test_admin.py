import os

import pytest

from app.db import db
from app.models import Blessing, Favorite, Like
from tests.conftest import auth


def _make_admin(client, token, code="admin"):
    return client.post("/api/me/admin", headers=auth(token), json={"adminCode": code})


@pytest.fixture
def people(join, add_photo):
    """小慧上傳了一張照片；阿凱是一般賓客；婷婷之後會變成管理員。"""
    hui, hui_guest = join("小慧")
    kai, _ = join("阿凱")
    admin, _ = join("婷婷")
    return {"hui": hui, "kai": kai, "admin": admin, "photo": add_photo(hui_guest["id"])}


# --- 開通管理員 -----------------------------------------------------------


def test_become_admin(client, people):
    res = _make_admin(client, people["admin"])

    assert res.status_code == 200
    assert res.get_json()["isAdmin"] is True
    assert client.get("/api/me", headers=auth(people["admin"])).get_json()["isAdmin"] is True
    assert client.get("/api/me", headers=auth(people["kai"])).get_json()["isAdmin"] is False


def test_wrong_admin_code(client, people):
    res = _make_admin(client, people["kai"], code="guess")

    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "invalid_admin_code"


def test_chinese_admin_code_is_rejected_not_500(client, people):
    res = _make_admin(client, people["kai"], code="管理員")

    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "invalid_admin_code"


def test_admin_is_not_exposed_publicly(client, people):
    _make_admin(client, people["admin"])
    blessing = client.post(
        "/api/blessings", headers=auth(people["admin"]), json={"text": "管理員也會留言"}
    ).get_json()
    # 別人看到的作者資料裡不會透露誰是管理員
    assert "isAdmin" not in blessing["guest"] and "is_admin" not in blessing["guest"]


def test_admin_disabled_when_no_code(app, client, people):
    app.config["ADMIN_CODE"] = ""

    res = _make_admin(client, people["admin"], code="")

    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "admin_disabled"


def test_production_without_admin_code_still_starts(monkeypatch):
    # 跟活動碼不同：沒有管理員不影響賓客使用，所以不擋啟動，只是關閉管理員功能
    from app import create_app

    monkeypatch.delenv("ADMIN_CODE", raising=False)
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "EVENT_CODE": "real"})
    assert app.config["ADMIN_CODE"] == ""


# --- 刪照片 ---------------------------------------------------------------


def test_uploader_can_delete_own_photo(client, people):
    res = client.delete(f"/api/photos/{people['photo']}", headers=auth(people["hui"]))

    assert res.status_code == 204
    assert client.get(f"/api/photos/{people['photo']}", headers=auth(people["hui"])).status_code == 404


def test_others_cannot_delete(client, people):
    res = client.delete(f"/api/photos/{people['photo']}", headers=auth(people["kai"]))

    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "not_your_photo"


def test_admin_can_delete_any_photo(client, people):
    _make_admin(client, people["admin"])

    res = client.delete(f"/api/photos/{people['photo']}", headers=auth(people["admin"]))

    assert res.status_code == 204


def test_delete_removes_likes_favorites_and_keeps_blessing(app, client, people):
    photo = people["photo"]
    client.put(f"/api/photos/{photo}/like", headers=auth(people["kai"]))
    client.put(f"/api/photos/{photo}/favorite", headers=auth(people["kai"]))
    client.post("/api/blessings", headers=auth(people["hui"]), json={"text": "祝福", "photoId": photo})

    client.delete(f"/api/photos/{photo}", headers=auth(people["hui"]))

    with app.app_context():
        assert db.session.query(Like).count() == 0
        assert db.session.query(Favorite).count() == 0
        # 祝福留在留言牆，只是不再掛在照片上
        blessing = db.session.query(Blessing).one()
        assert blessing.photo_id is None
    assert client.get("/api/me", headers=auth(people["kai"])).get_json()["stats"]["favorited"] == 0


def test_delete_removes_files(app, client, join):
    import io

    from PIL import Image

    token, _ = join("小慧")
    buf = io.BytesIO()
    Image.new("RGB", (40, 30)).save(buf, "JPEG")
    photo = client.post(
        "/api/photos",
        headers=auth(token),
        data={"file": (io.BytesIO(buf.getvalue()), "a.jpg", "image/jpeg")},
        content_type="multipart/form-data",
    ).get_json()
    paths = [
        os.path.join(app.config["MEDIA_DIR"], *photo[k].removeprefix("/media/").split("/"))
        for k in ("url", "displayUrl", "thumbnailUrl")
    ]
    assert all(os.path.exists(p) for p in paths)

    client.delete(f"/api/photos/{photo['id']}", headers=auth(token))

    assert not any(os.path.exists(p) for p in paths)


def test_delete_missing_photo_is_404(client, people):
    assert client.delete("/api/photos/p_nope", headers=auth(people["hui"])).status_code == 404


# --- 刪祝福 ---------------------------------------------------------------


def test_admin_can_delete_others_blessing_but_not_edit(client, people):
    _make_admin(client, people["admin"])
    blessing_id = client.post(
        "/api/blessings", headers=auth(people["kai"]), json={"text": "阿凱的祝福"}
    ).get_json()["id"]

    edit = client.patch(
        f"/api/blessings/{blessing_id}", headers=auth(people["admin"]), json={"text": "改掉"}
    )
    delete = client.delete(f"/api/blessings/{blessing_id}", headers=auth(people["admin"]))

    # 管理員只能刪，不能替別人改內容
    assert edit.status_code == 403
    assert delete.status_code == 204


def test_admin_can_delete_imported_blessing(app, client, people, tmp_path):
    path = tmp_path / "b.csv"
    path.write_text("名字,祝福\n路人,不該出現的內容\n", encoding="utf-8")
    app.test_cli_runner().invoke(args=["import-blessings", str(path)])
    _make_admin(client, people["admin"])
    blessing_id = client.get("/api/blessings", headers=auth(people["admin"])).get_json()["items"][0]["id"]

    res = client.delete(f"/api/blessings/{blessing_id}", headers=auth(people["admin"]))

    assert res.status_code == 204
