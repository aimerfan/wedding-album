from app.db import db
from app.models import Blessing, Guest
from tests.conftest import auth


def _run(app, tmp_path, content: str, *args, encoding="utf-8"):
    path = tmp_path / "blessings.csv"
    path.write_text(content, encoding=encoding)
    return app.test_cli_runner().invoke(args=["import-blessings", str(path), *args])


def _wall(client, join):
    token, _ = join("看留言的人")
    return client.get("/api/blessings", headers=auth(token)).get_json()["items"]


def test_import_shows_on_wall_in_file_order(app, client, join, tmp_path):
    result = _run(
        app,
        tmp_path,
        "名字,祝福,關係\n阿凱,祝你們白頭偕老！,新郎的大學室友\n美玲阿姨,新婚快樂,\n",
    )

    assert result.exit_code == 0, result.output
    wall = _wall(client, join)
    # 第一列在最上面
    assert [(b["guest"]["nickname"], b["text"]) for b in wall] == [
        ("阿凱", "祝你們白頭偕老！"),
        ("美玲阿姨", "新婚快樂"),
    ]
    assert wall[0]["guest"]["relation"] == "新郎的大學室友"
    assert "relation" not in wall[1]["guest"]


def test_excel_utf8_bom_and_english_headers(app, client, join, tmp_path):
    # Excel 存「CSV UTF-8」會在開頭加 BOM
    result = _run(app, tmp_path, "name,text\n阿凱,恭喜\n", encoding="utf-8-sig")

    assert result.exit_code == 0, result.output
    assert _wall(client, join)[0]["text"] == "恭喜"


def test_rerun_does_not_duplicate(app, tmp_path):
    content = "名字,祝福\n阿凱,恭喜\n阿凱,再恭喜一次\n"
    _run(app, tmp_path, content)

    result = _run(app, tmp_path, content)

    assert "跳過 2 則" in result.output
    with app.app_context():
        assert db.session.query(Blessing).count() == 2
        # 同名的匯入作者共用一筆
        assert db.session.query(Guest).count() == 1


def test_imported_authors_cannot_log_in_and_are_not_counted_as_guests(app, client, join, tmp_path):
    _run(app, tmp_path, "名字,祝福\n阿凱,恭喜\n")
    token, _ = join("小慧")

    stats = client.get("/api/stats", headers=auth(token)).get_json()

    assert stats["guestCount"] == 1  # 只有小慧
    assert stats["blessingGuestCount"] == 1  # 阿凱留了祝福
    with app.app_context():
        author = db.session.scalar(db.select(Guest).where(Guest.nickname == "阿凱"))
        assert author.token_hash is None


def test_same_name_joining_later_is_a_different_guest(app, client, join, tmp_path):
    _run(app, tmp_path, "名字,祝福\n阿凱,恭喜\n")

    token, kai = join("阿凱")
    mine = client.get("/api/blessings", headers=auth(token), query_string={"guest": "me"})

    # 用手機加入的阿凱看不到匯入的那則（刻意的取捨，見 docs/api.md）
    assert mine.get_json()["items"] == []


def test_dry_run_writes_nothing(app, tmp_path):
    result = _run(app, tmp_path, "名字,祝福\n阿凱,恭喜\n", "--dry-run")

    assert result.exit_code == 0
    assert "預覽" in result.output
    with app.app_context():
        assert db.session.query(Blessing).count() == 0


def test_bad_rows_abort_whole_import(app, tmp_path):
    result = _run(app, tmp_path, "名字,祝福\n阿凱,恭喜\n,沒有名字\n小慧,\n")

    assert result.exit_code != 0
    assert "第 3 列" in result.output and "第 4 列" in result.output
    # 有錯就整批不匯入，不會只匯一半
    with app.app_context():
        assert db.session.query(Blessing).count() == 0


def test_missing_columns(app, tmp_path):
    result = _run(app, tmp_path, "誰,說了什麼\n阿凱,恭喜\n")

    assert result.exit_code != 0
    assert "找不到欄位" in result.output


def test_blank_lines_are_ignored(app, tmp_path):
    result = _run(app, tmp_path, "名字,祝福\n\n阿凱,恭喜\n,\n")

    assert result.exit_code == 0, result.output
    with app.app_context():
        assert db.session.query(Blessing).count() == 1


def test_imported_blessings_cannot_be_edited_from_app(app, client, join, tmp_path):
    _run(app, tmp_path, "名字,祝福\n阿凱,恭喜\n")
    # 同名的人用手機加入，也改不了匯入的那則
    token, _ = join("阿凱")
    imported = client.get("/api/blessings", headers=auth(token)).get_json()["items"][0]

    res = client.patch(f"/api/blessings/{imported['id']}", headers=auth(token), json={"text": "改掉"})

    assert res.status_code == 403
