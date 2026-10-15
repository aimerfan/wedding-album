"""照片說明與分類：上傳時一起寫、之後修改或刪掉，以及從舊的照片祝福搬過來。"""

import pytest

from app.db import db
from app.models import Blessing, Photo, move_photo_blessings_to_captions
from tests.conftest import auth
from tests.test_upload import make_image, upload


def _patch(client, token, photo_id, **body):
    return client.patch(f"/api/photos/{photo_id}", headers=auth(token), json=body)


def _make_admin(client, token):
    client.post("/api/me/admin", headers=auth(token), json={"adminCode": "admin"})


# --- 上傳時寫說明 ---------------------------------------------------------


def test_upload_with_caption(client, join):
    token, _ = join("小慧")

    res = upload(client, token, make_image(), caption="  新娘進場 ♥  ")

    photo = res.get_json()
    assert photo["caption"] == "新娘進場 ♥"  # 前後空白去掉
    assert photo["captionEditedAt"] is None


@pytest.mark.parametrize("form", [{}, {"caption": ""}, {"caption": "   "}])
def test_caption_is_optional(client, join, form):
    token, _ = join("小慧")
    assert upload(client, token, make_image(), **form).get_json()["caption"] is None


def test_caption_too_long_is_400(app, client, join):
    token, _ = join("小慧")
    limit = app.config["MAX_CAPTION_LENGTH"]

    res = upload(client, token, make_image(), caption="字" * (limit + 1))

    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "caption_too_long"


def test_resend_keeps_first_caption(client, join):
    """重送同一個檔案回傳已經有的那張，不會被這次的說明與分類蓋掉。"""
    token, _ = join("小慧")
    data = make_image()
    upload(client, token, data, caption="第一次", tag="candid")

    photo = upload(client, token, data, caption="第二次", tag="banquet").get_json()

    assert (photo["caption"], photo["tag"]) == ("第一次", "candid")


# --- 修改、刪除說明 -------------------------------------------------------


def test_edit_caption(client, join, add_photo):
    token, me = join("小慧")
    photo_id = add_photo(me["id"])

    res = _patch(client, token, photo_id, caption=" 好美 ")

    assert res.status_code == 200
    photo = res.get_json()
    assert photo["caption"] == "好美"
    assert photo["captionEditedAt"].endswith("+08:00")
    # 回傳完整的照片，前端直接換掉畫面上那張
    assert photo["id"] == photo_id and "likeCount" in photo


def test_same_caption_is_not_marked_edited(client, join):
    token, _ = join("小慧")
    photo_id = upload(client, token, make_image(), caption="好美").get_json()["id"]

    photo = _patch(client, token, photo_id, caption="好美").get_json()

    assert photo["captionEditedAt"] is None


@pytest.mark.parametrize("empty", [None, "", "  "])
def test_delete_caption(client, join, empty):
    token, _ = join("小慧")
    photo_id = upload(client, token, make_image(), caption="好美").get_json()["id"]
    _patch(client, token, photo_id, caption="改過")

    photo = _patch(client, token, photo_id, caption=empty).get_json()

    assert photo["caption"] is None
    assert photo["captionEditedAt"] is None


def test_caption_not_a_string_is_400(client, join, add_photo):
    token, me = join("小慧")
    res = _patch(client, token, add_photo(me["id"]), caption=123)
    assert res.get_json()["error"]["code"] == "invalid_caption"


def test_others_cannot_change_my_photo(client, join, add_photo):
    _, hui = join("小慧")
    kai, _ = join("阿凱")
    photo_id = add_photo(hui["id"])

    for body in ({"caption": "借放"}, {"caption": None}, {"tag": "candid"}):
        res = _patch(client, kai, photo_id, **body)
        assert res.status_code == 403
        assert res.get_json()["error"]["code"] == "not_your_photo"


def test_admin_can_delete_caption_but_not_write_it(client, join):
    hui, _ = join("小慧")
    admin, _ = join("婷婷")
    _make_admin(client, admin)
    photo_id = upload(client, hui, make_image(), caption="不適當的話").get_json()["id"]

    write = _patch(client, admin, photo_id, caption="改掉")
    delete = _patch(client, admin, photo_id, caption=None)

    assert write.status_code == 403
    assert delete.status_code == 200 and delete.get_json()["caption"] is None


def test_edit_after_uploads_closed(app, client, join, add_photo):
    token, me = join("小慧")
    photo_id = add_photo(me["id"])
    app.config["UPLOADS_OPEN"] = False

    assert _patch(client, token, photo_id, caption="婚禮後補寫").status_code == 200


def test_patch_missing_photo_is_404(client, join):
    token, _ = join("小慧")
    assert _patch(client, token, "p_nope", caption="x").status_code == 404


def test_patch_needs_json_object(client, join, add_photo):
    token, me = join("小慧")
    photo_id = add_photo(me["id"])
    res = client.patch(f"/api/photos/{photo_id}", headers=auth(token), json=["x"])
    assert res.get_json()["error"]["code"] == "invalid_body"


# --- 修改分類 -------------------------------------------------------------


def test_change_tag(client, join, add_photo):
    token, me = join("小慧")
    photo_id = add_photo(me["id"], tag="banquet")

    photo = _patch(client, token, photo_id, tag="throwback").get_json()

    assert photo["tag"] == "throwback"
    assert photo["captionEditedAt"] is None  # 只改分類不算編輯說明


def test_invalid_tag_is_400(client, join, add_photo):
    token, me = join("小慧")
    res = _patch(client, token, add_photo(me["id"]), tag="party")
    assert res.get_json()["error"]["code"] == "invalid_tag"


def test_admin_can_change_tag(client, join, add_photo):
    _, hui = join("小慧")
    admin, _ = join("婷婷")
    _make_admin(client, admin)

    res = _patch(client, admin, add_photo(hui["id"]), tag="candid")

    assert res.status_code == 200 and res.get_json()["tag"] == "candid"


def test_tag_and_caption_together(client, join, add_photo):
    token, me = join("小慧")
    photo = _patch(client, token, add_photo(me["id"]), tag="candid", caption="花絮").get_json()
    assert (photo["tag"], photo["caption"]) == ("candid", "花絮")


def test_invalid_field_changes_nothing(app, client, join, add_photo):
    token, me = join("小慧")
    photo_id = add_photo(me["id"])

    _patch(client, token, photo_id, tag="candid", caption="字" * 1000)

    with app.app_context():
        photo = db.session.get(Photo, photo_id)
        assert (photo.tag, photo.caption) == ("banquet", None)


# --- 舊的照片祝福搬成說明 -------------------------------------------------


def _old_blessing(guest_id, photo_id, text):
    db.session.add(Blessing(guest_id=guest_id, photo_id=photo_id, text=text))
    db.session.commit()


def test_photo_blessing_becomes_caption(app, join, add_photo):
    _, hui = join("小慧")
    photo_id = add_photo(hui["id"])

    with app.app_context():
        _old_blessing(hui["id"], photo_id, "白頭偕老")
        _old_blessing(hui["id"], None, "留言牆上的")
        move_photo_blessings_to_captions()

        assert db.session.get(Photo, photo_id).caption == "白頭偕老"
        # 搬過去的從留言牆消失，獨立的祝福不受影響
        assert [b.text for b in db.session.scalars(db.select(Blessing))] == ["留言牆上的"]


def test_moving_twice_is_harmless(app, join, add_photo):
    _, hui = join("小慧")
    photo_id = add_photo(hui["id"])

    with app.app_context():
        _old_blessing(hui["id"], photo_id, "白頭偕老")
        move_photo_blessings_to_captions()
        move_photo_blessings_to_captions()

        assert db.session.get(Photo, photo_id).caption == "白頭偕老"
        assert db.session.scalar(db.select(db.func.count()).select_from(Blessing)) == 0


def test_blessing_that_cannot_move_stays_on_wall(app, join, add_photo):
    """照片已經有說明、或作者不是上傳者時不搬，留在留言牆上，一句話都不會不見。"""
    _, hui = join("小慧")
    _, kai = join("阿凱")
    photo_id = add_photo(hui["id"])

    with app.app_context():
        _old_blessing(hui["id"], photo_id, "第一則")
        _old_blessing(hui["id"], photo_id, "第二則")
        _old_blessing(kai["id"], photo_id, "阿凱的")
        move_photo_blessings_to_captions()

        assert db.session.get(Photo, photo_id).caption == "第一則"
        left = db.session.scalars(db.select(Blessing)).all()
        assert sorted(b.text for b in left) == ["第二則", "阿凱的"]
        assert all(b.photo_id is None for b in left)
