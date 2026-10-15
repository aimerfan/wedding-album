"""照片下的留言：新增、列出、修改、刪除，以及照片上的留言數。"""

from datetime import timedelta

from app.db import db
from app.models import Comment, now
from tests.conftest import auth


def _post(client, token, photo_id, **body):
    return client.post(f"/api/photos/{photo_id}/comments", headers=auth(token), json=body)


def _list(client, token, photo_id):
    return client.get(f"/api/photos/{photo_id}/comments", headers=auth(token)).get_json()


def _make_admin(client, token):
    client.post("/api/me/admin", headers=auth(token), json={"adminCode": "admin"})


# --- 留言 -----------------------------------------------------------------


def test_anyone_can_comment(client, join, add_photo):
    """不只上傳者，任何賓客都能在照片下留言。"""
    _, hui = join("小慧")
    kai, kai_guest = join("阿凱")
    photo_id = add_photo(hui["id"])

    res = _post(client, kai, photo_id, text="  拍得真好！  ")

    assert res.status_code == 201
    comment = res.get_json()
    assert comment["text"] == "拍得真好！"  # 前後空白去掉
    assert comment["guest"] == kai_guest
    assert comment["photoId"] == photo_id
    assert comment["createdAt"].endswith("+08:00")
    assert comment["editedAt"] is None


def test_list_is_oldest_first(app, client, join, add_photo):
    token, me = join("小慧")
    photo_id = add_photo(me["id"])
    with app.app_context():
        for i in range(3):
            # 故意倒著寫進去，確認是照時間排而不是照寫入順序
            db.session.add(
                Comment(
                    photo_id=photo_id,
                    guest_id=me["id"],
                    text=f"第 {3 - i} 則",
                    created_at=now() - timedelta(minutes=i),
                )
            )
        db.session.commit()

    items = _list(client, token, photo_id)["items"]

    assert [c["text"] for c in items] == ["第 1 則", "第 2 則", "第 3 則"]


def test_comments_stay_on_their_photo(client, join, add_photo):
    token, me = join("小慧")
    a, b = add_photo(me["id"]), add_photo(me["id"])
    _post(client, token, a, text="給 A 的")

    assert _list(client, token, b)["items"] == []


def test_comment_count_on_photo(client, join, add_photo):
    token, me = join("小慧")
    kai, _ = join("阿凱")
    photo_id = add_photo(me["id"])
    assert client.get(f"/api/photos/{photo_id}", headers=auth(token)).get_json()["commentCount"] == 0

    _post(client, token, photo_id, text="一")
    _post(client, kai, photo_id, text="二")

    photo = client.get(f"/api/photos/{photo_id}", headers=auth(token)).get_json()
    assert photo["commentCount"] == 2
    # 列表也有
    listed = client.get("/api/photos", headers=auth(token)).get_json()["items"][0]
    assert listed["commentCount"] == 2


def test_comments_are_not_blessings(client, join, add_photo):
    """留言不出現在留言牆，也不算進任何統計。"""
    token, me = join("小慧")
    _post(client, token, add_photo(me["id"]), text="留言")

    assert client.get("/api/blessings", headers=auth(token)).get_json()["items"] == []
    assert client.get("/api/stats", headers=auth(token)).get_json()["blessingCount"] == 0
    assert client.get("/api/me", headers=auth(token)).get_json()["stats"]["blessings"] == 0


def test_comment_after_uploads_closed(app, client, join, add_photo):
    token, me = join("小慧")
    photo_id = add_photo(me["id"])
    app.config["UPLOADS_OPEN"] = False

    assert _post(client, token, photo_id, text="婚禮後補留言").status_code == 201


# --- 錯誤 -----------------------------------------------------------------


def test_empty_comment_is_400(client, join, add_photo):
    token, me = join("小慧")
    photo_id = add_photo(me["id"])

    for body in ({"text": "   "}, {}, {"text": 123}):
        res = _post(client, token, photo_id, **body)
        assert res.status_code == 400
        assert res.get_json()["error"]["code"] == "text_required"


def test_comment_too_long_is_400(app, client, join, add_photo):
    token, me = join("小慧")
    limit = app.config["MAX_COMMENT_LENGTH"]

    res = _post(client, token, add_photo(me["id"]), text="字" * (limit + 1))

    assert res.get_json()["error"]["code"] == "text_too_long"


def test_comment_needs_json_object(client, join, add_photo):
    token, me = join("小慧")
    photo_id = add_photo(me["id"])
    res = client.post(f"/api/photos/{photo_id}/comments", headers=auth(token), json=["嗨"])
    assert res.get_json()["error"]["code"] == "invalid_body"


def test_comment_on_missing_photo_is_404(client, join):
    token, _ = join("小慧")
    assert _post(client, token, "p_nope", text="嗨").get_json()["error"]["code"] == "photo_not_found"
    res = client.get("/api/photos/p_nope/comments", headers=auth(token))
    assert res.status_code == 404


def test_comments_need_token(client):
    assert client.get("/api/photos/p_x/comments").status_code == 401
    assert client.post("/api/photos/p_x/comments", json={"text": "嗨"}).status_code == 401


# --- 修改、刪除 -----------------------------------------------------------


def test_edit_my_comment(client, join, add_photo):
    token, me = join("小慧")
    photo_id = add_photo(me["id"])
    comment = _post(client, token, photo_id, text="打錯子").get_json()

    res = client.patch(f"/api/comments/{comment['id']}", headers=auth(token), json={"text": " 打錯字 "})

    assert res.status_code == 200
    edited = res.get_json()
    assert edited["text"] == "打錯字"
    assert edited["editedAt"].endswith("+08:00")
    assert edited["createdAt"] == comment["createdAt"]  # 順序不會因為改過而跳動


def test_same_text_is_not_marked_edited(client, join, add_photo):
    token, me = join("小慧")
    comment = _post(client, token, add_photo(me["id"]), text="恭喜").get_json()

    res = client.patch(f"/api/comments/{comment['id']}", headers=auth(token), json={"text": "恭喜"})

    assert res.get_json()["editedAt"] is None


def test_delete_my_comment(client, join, add_photo):
    token, me = join("小慧")
    photo_id = add_photo(me["id"])
    comment_id = _post(client, token, photo_id, text="刪掉我").get_json()["id"]

    res = client.delete(f"/api/comments/{comment_id}", headers=auth(token))

    assert res.status_code == 204
    assert _list(client, token, photo_id)["items"] == []


def test_cannot_touch_others_comment(client, join, add_photo):
    """照片的上傳者也不能改、刪別人在自己照片下的留言，跟祝福一樣只有作者與管理員。"""
    hui, hui_guest = join("小慧")
    kai, _ = join("阿凱")
    comment_id = _post(client, kai, add_photo(hui_guest["id"]), text="阿凱的留言").get_json()["id"]

    edit = client.patch(f"/api/comments/{comment_id}", headers=auth(hui), json={"text": "改掉"})
    delete = client.delete(f"/api/comments/{comment_id}", headers=auth(hui))

    assert edit.status_code == 403 and edit.get_json()["error"]["code"] == "not_your_comment"
    assert delete.status_code == 403


def test_admin_can_delete_but_not_edit(client, join, add_photo):
    _, hui = join("小慧")
    kai, _ = join("阿凱")
    admin, _ = join("婷婷")
    _make_admin(client, admin)
    comment_id = _post(client, kai, add_photo(hui["id"]), text="不適當的留言").get_json()["id"]

    edit = client.patch(f"/api/comments/{comment_id}", headers=auth(admin), json={"text": "改掉"})
    delete = client.delete(f"/api/comments/{comment_id}", headers=auth(admin))

    assert edit.status_code == 403
    assert delete.status_code == 204


def test_missing_comment_is_404(client, join):
    token, _ = join("小慧")
    res = client.patch("/api/comments/c_nope", headers=auth(token), json={"text": "x"})
    assert res.get_json()["error"]["code"] == "comment_not_found"
    assert client.delete("/api/comments/c_nope", headers=auth(token)).status_code == 404


def test_deleting_photo_deletes_its_comments(app, client, join, add_photo):
    token, me = join("小慧")
    kai, _ = join("阿凱")
    photo_id = add_photo(me["id"])
    _post(client, kai, photo_id, text="留言")

    client.delete(f"/api/photos/{photo_id}", headers=auth(token))

    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(Comment)) == 0
