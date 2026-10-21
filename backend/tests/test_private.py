"""只給新人看的照片：只有上傳者與管理員（新人與家人）看得到，不出現在相簿裡。"""

import pytest

from tests.conftest import auth
from tests.test_upload import make_image, upload


def _make_admin(client, token):
    client.post("/api/me/admin", headers=auth(token), json={"adminCode": "admin"})


def _ids(client, token, **params):
    res = client.get("/api/photos", headers=auth(token), query_string=params)
    assert res.status_code == 200, res.get_json()
    return [p["id"] for p in res.get_json()["items"]]


@pytest.fixture
def setup(client, join):
    """小慧傳了一張公開、一張只給新人看的；阿凱是一般賓客；婷婷是管理員（新人）。"""
    hui, hui_guest = join("小慧")
    kai, _ = join("阿凱")
    couple, _ = join("婷婷")
    _make_admin(client, couple)
    public = upload(client, hui, make_image(size=(400, 300))).get_json()["id"]
    private = upload(client, hui, make_image(size=(300, 400)), private="true").get_json()["id"]
    return {
        "hui": hui,
        "hui_id": hui_guest["id"],
        "kai": kai,
        "couple": couple,
        "public": public,
        "private": private,
    }


# --- 上傳 -----------------------------------------------------------------


def test_upload_private(client, join):
    token, _ = join("小慧")

    photo = upload(client, token, make_image(), private="true").get_json()

    assert photo["private"] is True


@pytest.mark.parametrize("form", [{}, {"private": "false"}, {"private": ""}])
def test_upload_is_public_by_default(client, join, form):
    token, _ = join("小慧")
    assert upload(client, token, make_image(), **form).get_json()["private"] is False


def test_invalid_private_is_400(client, join):
    token, _ = join("小慧")
    res = upload(client, token, make_image(), private="yes")
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "invalid_private"


# --- 誰看得到 -------------------------------------------------------------


def test_album_only_shows_public(client, setup):
    """首頁、分類、別人的照片：只列公開的。管理員看到的也跟大家一樣。"""
    for who in ("hui", "kai", "couple"):
        assert _ids(client, setup[who]) == [setup["public"]]
        assert _ids(client, setup[who], tag="banquet") == [setup["public"]]
        assert _ids(client, setup[who], uploader=setup["hui_id"]) == [setup["public"]]


def test_my_uploads_include_private(client, setup):
    assert _ids(client, setup["hui"], uploader="me") == [setup["private"], setup["public"]]


def test_couple_sees_private_list(client, setup):
    """「給我們的」：所有只給新人看的照片，只有管理員能看。"""
    assert _ids(client, setup["couple"], private="true") == [setup["private"]]

    res = client.get("/api/photos", headers=auth(setup["kai"]), query_string={"private": "true"})
    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "not_admin"


def test_search_hides_private(client, setup):
    assert _ids(client, setup["kai"], q="小慧") == [setup["public"]]


@pytest.mark.parametrize("who,visible", [("hui", True), ("couple", True), ("kai", False)])
def test_single_photo(client, setup, who, visible):
    res = client.get(f"/api/photos/{setup['private']}", headers=auth(setup[who]))
    if visible:
        assert res.status_code == 200 and res.get_json()["private"] is True
    else:
        # 跟不存在一樣，不讓人知道有這張
        assert res.status_code == 404
        assert res.get_json()["error"]["code"] == "photo_not_found"


def test_others_cannot_touch_private_photo(client, setup):
    kai, photo = setup["kai"], setup["private"]
    h = auth(kai)

    assert client.put(f"/api/photos/{photo}/like", headers=h).status_code == 404
    assert client.put(f"/api/photos/{photo}/favorite", headers=h).status_code == 404
    assert client.get(f"/api/photos/{photo}/comments", headers=h).status_code == 404
    assert client.post(f"/api/photos/{photo}/comments", headers=h, json={"text": "嗨"}).status_code == 404
    assert client.patch(f"/api/photos/{photo}", headers=h, json={"tag": "candid"}).status_code == 404
    assert client.delete(f"/api/photos/{photo}", headers=h).status_code == 404


def test_uploader_and_couple_can_talk(client, setup):
    """看得到的人照常可以按讚、留言：實際上就是上傳者與新人之間的對話。"""
    photo = setup["private"]
    client.post(f"/api/photos/{photo}/comments", headers=auth(setup["couple"]), json={"text": "謝謝你！"})
    client.post(f"/api/photos/{photo}/comments", headers=auth(setup["hui"]), json={"text": "不客氣"})
    client.put(f"/api/photos/{photo}/like", headers=auth(setup["couple"]))

    texts = [c["text"] for c in client.get(f"/api/photos/{photo}/comments", headers=auth(setup["hui"])).get_json()["items"]]
    assert texts == ["謝謝你！", "不客氣"]
    assert client.get(f"/api/photos/{photo}", headers=auth(setup["hui"])).get_json()["likeCount"] == 1


def test_favorites_only_list_what_you_can_see(client, setup):
    """管理員收藏了私下的照片，自己的收藏看得到；它不會因此出現在別人那裡。"""
    client.put(f"/api/photos/{setup['private']}/favorite", headers=auth(setup["couple"]))
    client.put(f"/api/photos/{setup['private']}/favorite", headers=auth(setup["hui"]))

    assert _ids(client, setup["couple"], favorited="true") == [setup["private"]]
    assert _ids(client, setup["hui"], favorited="true") == [setup["private"]]


def test_favorite_disappears_when_made_private(client, setup):
    """阿凱收藏了公開的照片，之後上傳者改成只給新人看：阿凱的收藏就看不到了。"""
    client.put(f"/api/photos/{setup['public']}/favorite", headers=auth(setup["kai"]))
    client.patch(f"/api/photos/{setup['public']}", headers=auth(setup["hui"]), json={"private": True})

    assert _ids(client, setup["kai"], favorited="true") == []


def test_stats_count_only_public(client, setup):
    stats = client.get("/api/stats", headers=auth(setup["kai"])).get_json()
    assert stats["photoCount"] == 1
    # 自己的「我上傳的」數字兩張都算
    me = client.get("/api/me", headers=auth(setup["hui"])).get_json()
    assert me["stats"]["uploaded"] == 2


# --- 上傳後改公開或私下 ---------------------------------------------------


def test_uploader_can_switch(client, setup):
    photo = setup["private"]

    res = client.patch(f"/api/photos/{photo}", headers=auth(setup["hui"]), json={"private": False})

    assert res.get_json()["private"] is False
    assert photo in _ids(client, setup["kai"])


def test_admin_cannot_switch(client, setup):
    """管理員不能把別人私下給的照片公開出去，也不能替人改成私下。"""
    for photo, value in ((setup["private"], False), (setup["public"], True)):
        res = client.patch(f"/api/photos/{photo}", headers=auth(setup["couple"]), json={"private": value})
        assert res.status_code == 403
        assert res.get_json()["error"]["code"] == "not_your_photo"


def test_admin_can_still_tag_and_delete_private(client, setup):
    photo = setup["private"]
    h = auth(setup["couple"])

    assert client.patch(f"/api/photos/{photo}", headers=h, json={"tag": "candid"}).status_code == 200
    assert client.delete(f"/api/photos/{photo}", headers=h).status_code == 204


def test_private_must_be_boolean(client, setup):
    res = client.patch(f"/api/photos/{setup['public']}", headers=auth(setup["hui"]), json={"private": "true"})
    assert res.get_json()["error"]["code"] == "invalid_private"


def test_old_photos_without_flag_are_public(app, client, join, add_photo):
    """欄位加上之前的照片 private 是 NULL，要當成公開。"""
    from app.db import db
    from app.models import Photo

    token, me = join("小慧")
    photo_id = add_photo(me["id"])
    with app.app_context():
        db.session.get(Photo, photo_id).private = None
        db.session.commit()

    kai, _ = join("阿凱")
    assert _ids(client, kai) == [photo_id]
    assert client.get(f"/api/photos/{photo_id}", headers=auth(kai)).get_json()["private"] is False
