import pytest

from tests.conftest import auth

URL = "https://kahoot.it/?pin=1234567"


@pytest.fixture
def admin(client, join):
    token, _ = join("婷婷")
    client.post("/api/me/admin", headers=auth(token), json={"adminCode": "admin"})
    return token


def _config(client):
    return client.get("/api/config").get_json()


def test_no_link_by_default(client):
    assert _config(client)["kahootUrl"] is None


def test_admin_sets_link_and_everyone_sees_it_without_login(client, admin):
    res = client.put("/api/settings/kahoot", headers=auth(admin), json={"url": f"  {URL} "})

    assert res.status_code == 200
    assert res.get_json() == {"kahootUrl": URL}
    # 歡迎頁還沒加入也看得到
    assert _config(client)["kahootUrl"] == URL


def test_change_link(client, admin):
    client.put("/api/settings/kahoot", headers=auth(admin), json={"url": URL})
    client.put("/api/settings/kahoot", headers=auth(admin), json={"url": "https://kahoot.it/?pin=7654321"})

    assert _config(client)["kahootUrl"] == "https://kahoot.it/?pin=7654321"


@pytest.mark.parametrize("empty", ["", "   ", None])
def test_clear_link(client, admin, empty):
    client.put("/api/settings/kahoot", headers=auth(admin), json={"url": URL})

    res = client.put("/api/settings/kahoot", headers=auth(admin), json={"url": empty})

    assert res.get_json() == {"kahootUrl": None}
    assert _config(client)["kahootUrl"] is None


@pytest.mark.parametrize("bad", ["kahoot.it/123", "javascript:alert(1)", "https://" + "a" * 600])
def test_rejects_non_links(client, admin, bad):
    res = client.put("/api/settings/kahoot", headers=auth(admin), json={"url": bad})

    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "invalid_url"
    assert _config(client)["kahootUrl"] is None


def test_only_admin_can_set(client, join):
    token, _ = join("阿凱")

    res = client.put("/api/settings/kahoot", headers=auth(token), json={"url": URL})

    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "not_admin"


def test_requires_token(client):
    assert client.put("/api/settings/kahoot", json={"url": URL}).status_code == 401
