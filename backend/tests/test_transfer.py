from datetime import timedelta

from app.db import db
from app.models import TransferCode, now
from tests.conftest import auth


def _new_code(client, token):
    res = client.post("/api/me/transfer-codes", headers=auth(token))
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def _claim(client, code):
    return client.post("/api/guests/claim", json={"transferCode": code})


def test_claim_on_another_device_is_same_guest(client, join):
    phone_token, me = join("小慧")
    code = _new_code(client, phone_token)["code"]

    res = _claim(client, code)

    assert res.status_code == 200
    laptop_token = res.get_json()["token"]
    assert laptop_token != phone_token
    assert res.get_json()["guest"] == me
    laptop_me = client.get("/api/me", headers=auth(laptop_token)).get_json()["guest"]
    assert laptop_me == me


def test_original_device_stays_logged_in(client, join):
    # 每個裝置各有自己的 token，換到電腦不會把手機登出
    phone_token, _ = join("小慧")
    _claim(client, _new_code(client, phone_token)["code"])

    assert client.get("/api/me", headers=auth(phone_token)).status_code == 200


def test_both_devices_share_the_same_data(client, join):
    phone_token, _ = join("小慧")
    laptop_token = _claim(client, _new_code(client, phone_token)["code"]).get_json()["token"]

    client.post("/api/blessings", headers=auth(laptop_token), json={"text": "在電腦上寫的"})

    mine = client.get("/api/blessings", headers=auth(phone_token), query_string={"guest": "me"})
    assert [b["text"] for b in mine.get_json()["items"]] == ["在電腦上寫的"]


def test_code_shape_and_expiry(app, client, join):
    token, _ = join("小慧")

    body = _new_code(client, token)

    assert len(body["code"]) == 8
    # 沒有容易看錯的 0、O、1、I、L
    assert not set(body["code"]) & set("0O1IL")
    assert body["expiresAt"].endswith("+08:00")


def test_code_is_single_use(client, join):
    token, _ = join("小慧")
    code = _new_code(client, token)["code"]
    _claim(client, code)

    res = _claim(client, code)

    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "invalid_transfer_code"


def test_expired_code(app, client, join):
    token, _ = join("小慧")
    code = _new_code(client, token)["code"]
    with app.app_context():
        db.session.get(TransferCode, code).expires_at = now() - timedelta(seconds=1)
        db.session.commit()

    res = _claim(client, code)

    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "transfer_code_expired"


def test_lowercase_and_spaces_are_accepted(client, join):
    # 萬一是手動輸入的
    token, _ = join("小慧")
    code = _new_code(client, token)["code"]

    assert _claim(client, f"  {code.lower()} ").status_code == 200


def test_unknown_or_missing_code(client):
    assert _claim(client, "ABCDEFGH").status_code == 401
    assert client.post("/api/guests/claim", json={}).status_code == 401
    assert client.post("/api/guests/claim", json={"transferCode": 123}).status_code == 401


def test_create_requires_token(client):
    assert client.post("/api/me/transfer-codes").status_code == 401


def test_expiry_minutes_follow_config(app, client, join):
    app.config["TRANSFER_CODE_MINUTES"] = 5
    token, _ = join("小慧")
    code = _new_code(client, token)["code"]

    with app.app_context():
        transfer = db.session.get(TransferCode, code)
        remaining = transfer.expires_at - now()
    assert timedelta(minutes=4) < remaining <= timedelta(minutes=5)


# --- 管理員替別人產生 -----------------------------------------------------


def _admin(client, join, nickname="婷婷"):
    token, _ = join(nickname)
    res = client.post("/api/me/admin", headers=auth(token), json={"adminCode": "admin"})
    assert res.status_code == 200
    return token


def test_admin_issues_code_for_lost_guest(client, join):
    # 小慧的手機不見了，管理員替她產生接續碼，她在新手機上接回原本的身分
    _, hui = join("小慧")
    admin = _admin(client, join)

    res = client.post(f"/api/guests/{hui['id']}/transfer-codes", headers=auth(admin))

    assert res.status_code == 201
    body = res.get_json()
    assert len(body["code"]) == 8
    assert body["expiresAt"].endswith("+08:00")
    claimed = _claim(client, body["code"])
    assert claimed.status_code == 200
    assert claimed.get_json()["guest"] == hui


def test_admin_issued_code_is_single_use(client, join):
    _, hui = join("小慧")
    admin = _admin(client, join)
    code = client.post(f"/api/guests/{hui['id']}/transfer-codes", headers=auth(admin)).get_json()

    assert _claim(client, code["code"]).status_code == 200
    assert _claim(client, code["code"]).status_code == 401


def test_only_admin_can_issue_for_others(client, join):
    _, hui = join("小慧")
    kai, _ = join("阿凱")

    res = client.post(f"/api/guests/{hui['id']}/transfer-codes", headers=auth(kai))

    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "not_admin"
    assert client.post(f"/api/guests/{hui['id']}/transfer-codes").status_code == 401


def test_issue_for_unknown_guest(client, join):
    admin = _admin(client, join)

    res = client.post("/api/guests/g_nobody/transfer-codes", headers=auth(admin))

    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "guest_not_found"
