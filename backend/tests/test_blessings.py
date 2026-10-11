from datetime import timedelta

import pytest

from app.models import now
from tests.conftest import auth


def _post(client, token, **body):
    return client.post("/api/blessings", headers=auth(token), json=body)


def _wall(client, token, **params):
    return client.get("/api/blessings", headers=auth(token), query_string=params).get_json()


def test_post_blessing_to_wall(client, join):
    token, me = join("阿凱")

    res = _post(client, token, text="  新婚快樂！  ")

    assert res.status_code == 201
    blessing = res.get_json()
    assert blessing["text"] == "新婚快樂！"  # 前後空白去掉
    assert blessing["guest"] == me
    assert blessing["photoId"] is None
    assert blessing["createdAt"].endswith("+08:00")


def test_wall_newest_first(client, join):
    token, _ = join("阿凱")
    _post(client, token, text="第一則")
    _post(client, token, text="第二則")

    texts = [b["text"] for b in _wall(client, token)["items"]]

    assert texts == ["第二則", "第一則"]


def test_wall_pagination(client, join):
    token, _ = join("阿凱")
    for i in range(5):
        _post(client, token, text=f"祝福 {i}")

    first = _wall(client, token, limit=3)
    second = _wall(client, token, limit=3, cursor=first["nextCursor"])

    assert len(first["items"]) == 3
    assert len(second["items"]) == 2 and second["nextCursor"] is None


def test_only_mine(client, join):
    kai, _ = join("阿凱")
    hui, _ = join("小慧")
    _post(client, kai, text="阿凱的")
    _post(client, hui, text="小慧的")

    assert [b["text"] for b in _wall(client, kai, guest="me")["items"]] == ["阿凱的"]


@pytest.mark.parametrize("text, code", [("", "text_required"), ("   ", "text_required")])
def test_empty_text_is_400(client, join, text, code):
    token, _ = join("阿凱")
    res = _post(client, token, text=text)
    assert res.status_code == 400 and res.get_json()["error"]["code"] == code


def test_text_too_long(app, client, join):
    token, _ = join("阿凱")
    limit = app.config["MAX_BLESSING_LENGTH"]

    assert _post(client, token, text="字" * limit).status_code == 201
    res = _post(client, token, text="字" * (limit + 1))
    assert res.get_json()["error"]["code"] == "text_too_long"


def test_requires_token(client):
    assert client.post("/api/blessings", json={"text": "嗨"}).status_code == 401
    assert client.get("/api/blessings").status_code == 401


# --- 掛在照片上的祝福 -----------------------------------------------------


def test_blessing_on_my_photo_shows_on_photo(client, join, add_photo):
    token, me = join("小慧")
    photo_id = add_photo(me["id"])

    res = _post(client, token, text="祝你們白頭偕老", photoId=photo_id)

    assert res.status_code == 201
    photo = client.get(f"/api/photos/{photo_id}", headers=auth(token)).get_json()
    assert photo["blessing"] == "祝你們白頭偕老"
    # 也會出現在留言牆
    assert _wall(client, token)["items"][0]["photoId"] == photo_id


def test_cannot_attach_to_someone_elses_photo(client, join, add_photo):
    _, hui = join("小慧")
    kai, _ = join("阿凱")
    photo_id = add_photo(hui["id"])

    res = _post(client, kai, text="借放一下", photoId=photo_id)

    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "not_your_photo"


def test_attach_to_missing_photo_is_404(client, join):
    token, _ = join("小慧")
    assert _post(client, token, text="嗨", photoId="p_nope").status_code == 404


def test_photo_without_blessing_is_null(client, join, add_photo):
    token, me = join("小慧")
    photo_id = add_photo(me["id"])
    assert client.get(f"/api/photos/{photo_id}", headers=auth(token)).get_json()["blessing"] is None


# --- 統計 -----------------------------------------------------------------


def test_stats_count_blessings_and_their_authors(client, join):
    kai, _ = join("阿凱")
    hui, _ = join("小慧")
    join("婷婷")  # 加入了但沒留祝福
    _post(client, kai, text="一")
    _post(client, kai, text="二")
    _post(client, hui, text="三")

    stats = client.get("/api/stats", headers=auth(kai)).get_json()
    me = client.get("/api/me", headers=auth(kai)).get_json()["stats"]

    assert stats["blessingCount"] == 3
    assert stats["blessingGuestCount"] == 2
    assert stats["guestCount"] == 3
    assert me["blessings"] == 2


def test_same_second_blessings_are_not_lost(app, client, join):
    # 同一秒的祝福在分頁時不能漏掉
    from app.db import db
    from app.models import Blessing

    token, me = join("阿凱")
    t = now() - timedelta(minutes=1)
    with app.app_context():
        for i in range(4):
            db.session.add(Blessing(guest_id=me["id"], text=str(i), created_at=t))
        db.session.commit()

    first = _wall(client, token, limit=2)
    second = _wall(client, token, limit=2, cursor=first["nextCursor"])

    texts = [b["text"] for b in first["items"] + second["items"]]
    assert sorted(texts) == ["0", "1", "2", "3"]


# --- 修改、刪除 -----------------------------------------------------------


def test_edit_my_blessing(client, join):
    token, _ = join("阿凱")
    blessing = _post(client, token, text="新婚快落").get_json()
    assert blessing["editedAt"] is None

    res = client.patch(f"/api/blessings/{blessing['id']}", headers=auth(token), json={"text": " 新婚快樂 "})

    assert res.status_code == 200
    edited = res.get_json()
    assert edited["text"] == "新婚快樂"
    assert edited["editedAt"] is not None
    assert edited["createdAt"] == blessing["createdAt"]  # 原本的時間不變，留言牆順序不會跳
    assert _wall(client, token)["items"][0]["text"] == "新婚快樂"


def test_edit_with_same_text_is_not_marked_edited(client, join):
    token, _ = join("阿凱")
    blessing = _post(client, token, text="恭喜").get_json()

    res = client.patch(f"/api/blessings/{blessing['id']}", headers=auth(token), json={"text": "恭喜"})

    assert res.get_json()["editedAt"] is None


def test_edit_validates_text(client, join):
    token, _ = join("阿凱")
    blessing_id = _post(client, token, text="恭喜").get_json()["id"]

    res = client.patch(f"/api/blessings/{blessing_id}", headers=auth(token), json={"text": " "})

    assert res.get_json()["error"]["code"] == "text_required"


def test_cannot_edit_or_delete_someone_elses(client, join):
    kai, _ = join("阿凱")
    hui, _ = join("小慧")
    blessing_id = _post(client, kai, text="阿凱的祝福").get_json()["id"]

    edit = client.patch(f"/api/blessings/{blessing_id}", headers=auth(hui), json={"text": "改掉"})
    delete = client.delete(f"/api/blessings/{blessing_id}", headers=auth(hui))

    assert edit.status_code == 403 and edit.get_json()["error"]["code"] == "not_your_blessing"
    assert delete.status_code == 403
    assert _wall(client, kai)["items"][0]["text"] == "阿凱的祝福"


def test_delete_my_blessing(client, join):
    token, _ = join("阿凱")
    blessing_id = _post(client, token, text="打錯了").get_json()["id"]

    res = client.delete(f"/api/blessings/{blessing_id}", headers=auth(token))

    assert res.status_code == 204
    assert _wall(client, token)["items"] == []
    assert client.get("/api/me", headers=auth(token)).get_json()["stats"]["blessings"] == 0


def test_delete_blessing_on_photo_clears_it_from_photo(client, join, add_photo):
    token, me = join("小慧")
    photo_id = add_photo(me["id"])
    blessing_id = _post(client, token, text="祝福", photoId=photo_id).get_json()["id"]

    client.delete(f"/api/blessings/{blessing_id}", headers=auth(token))

    photo = client.get(f"/api/photos/{photo_id}", headers=auth(token)).get_json()
    assert photo["blessing"] is None


def test_missing_blessing_is_404(client, join):
    token, _ = join("阿凱")
    assert client.delete("/api/blessings/b_nope", headers=auth(token)).status_code == 404
    res = client.patch("/api/blessings/b_nope", headers=auth(token), json={"text": "x"})
    assert res.get_json()["error"]["code"] == "blessing_not_found"

