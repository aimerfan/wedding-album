import pytest

from app import create_app
from app.db import db
from app.models import Guest
from tests.conftest import EVENT_CODE, auth


# --- 加入相簿 -------------------------------------------------------------


def test_join_returns_token_and_guest(client):
    res = client.post(
        "/api/guests",
        json={"eventCode": EVENT_CODE, "nickname": " 小慧 ", "relation": "新娘的大學同學"},
    )

    assert res.status_code == 201
    body = res.get_json()
    assert body["token"]
    assert body["guest"]["id"].startswith("g_")
    # 前後空白會被去掉
    assert body["guest"]["nickname"] == "小慧"
    assert body["guest"]["relation"] == "新娘的大學同學"


def test_relation_is_optional(join):
    _, guest = join("阿凱")
    assert "relation" not in guest


def test_blank_relation_is_treated_as_none(join):
    _, guest = join("阿凱", relation="   ")
    assert "relation" not in guest


def test_wrong_event_code_is_rejected(client):
    res = client.post("/api/guests", json={"eventCode": "guess", "nickname": "小慧"})

    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "invalid_event_code"


def test_missing_event_code_is_rejected(client):
    res = client.post("/api/guests", json={"nickname": "小慧"})
    assert res.status_code == 401


@pytest.mark.parametrize(
    "nickname, code",
    [("", "nickname_required"), ("   ", "nickname_required"), ("字" * 21, "nickname_too_long")],
)
def test_invalid_nickname_is_rejected(client, nickname, code):
    res = client.post("/api/guests", json={"eventCode": EVENT_CODE, "nickname": nickname})

    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == code


def test_non_json_body_is_rejected(client):
    res = client.post("/api/guests", data="not json", content_type="text/plain")

    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "invalid_body"


def test_token_is_stored_only_as_hash(app, join):
    token, guest = join()

    with app.app_context():
        stored = db.session.get(Guest, guest["id"])
        assert stored.token_hash != token
        assert token not in stored.token_hash


# --- 驗 token -------------------------------------------------------------


def test_me_returns_current_guest(client, join):
    token, guest = join("小慧")

    res = client.get("/api/me", headers=auth(token))

    assert res.status_code == 200
    assert res.get_json()["guest"] == guest


def test_each_token_maps_to_its_own_guest(client, join):
    token_a, _ = join("小慧")
    token_b, _ = join("阿凱")

    assert client.get("/api/me", headers=auth(token_a)).get_json()["guest"]["nickname"] == "小慧"
    assert client.get("/api/me", headers=auth(token_b)).get_json()["guest"]["nickname"] == "阿凱"


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer wrong"}, {"Authorization": "wrong"}, {"Authorization": "Bearer "}],
)
def test_me_without_valid_token_is_401(client, headers):
    res = client.get("/api/me", headers=headers)

    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "unauthorized"


# --- 改資料 ---------------------------------------------------------------


def test_update_nickname_and_relation(client, join):
    token, _ = join("小慧")

    res = client.patch(
        "/api/me", headers=auth(token), json={"nickname": "小明", "relation": "新娘的表哥"}
    )

    assert res.status_code == 200
    assert res.get_json()["guest"]["nickname"] == "小明"
    # 改完再讀一次，確認真的存進去了
    me = client.get("/api/me", headers=auth(token)).get_json()["guest"]
    assert me["nickname"] == "小明"
    assert me["relation"] == "新娘的表哥"


def test_update_only_given_fields(client, join):
    token, _ = join("小慧", relation="新娘的大學同學")

    client.patch("/api/me", headers=auth(token), json={"nickname": "小明"})

    me = client.get("/api/me", headers=auth(token)).get_json()["guest"]
    assert me["relation"] == "新娘的大學同學"


def test_clear_relation(client, join):
    token, _ = join("小慧", relation="新娘的大學同學")

    client.patch("/api/me", headers=auth(token), json={"relation": ""})

    assert "relation" not in client.get("/api/me", headers=auth(token)).get_json()["guest"]


def test_update_rejects_blank_nickname(client, join):
    token, _ = join("小慧")

    res = client.patch("/api/me", headers=auth(token), json={"nickname": " "})

    assert res.status_code == 400


def test_update_requires_token(client):
    assert client.patch("/api/me", json={"nickname": "小明"}).status_code == 401


# --- 活動碼設定 -----------------------------------------------------------


def test_production_without_event_code_refuses_to_start(monkeypatch):
    # 正式環境忘了設活動碼時，寧可啟動失敗，也不要讓 "dev" 變成任何人都能用的通行碼
    monkeypatch.delenv("EVENT_CODE", raising=False)
    monkeypatch.delenv("FLASK_DEBUG", raising=False)

    with pytest.raises(RuntimeError):
        create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})


def test_me_counts_my_uploads(client, join, add_photo):
    token, me = join("小慧")
    _, other = join("阿凱")
    add_photo(me["id"])
    add_photo(me["id"])
    add_photo(other["id"])

    stats = client.get("/api/me", headers=auth(token)).get_json()["stats"]

    assert stats["uploaded"] == 2
