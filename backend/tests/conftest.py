import pytest

from app import create_app

EVENT_CODE = "test-code"


@pytest.fixture
def app():
    # 每個測試一個全新的記憶體資料庫，互不影響
    return create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "EVENT_CODE": EVENT_CODE,
        }
    )


@pytest.fixture
def client(app):
    """模擬前端打 API 的測試用 client，不必真的啟動伺服器。"""
    return app.test_client()


@pytest.fixture
def join(client):
    """以賓客身分加入相簿，回傳 (token, guest)。"""

    def _join(nickname="小慧", **extra):
        res = client.post(
            "/api/guests", json={"eventCode": EVENT_CODE, "nickname": nickname, **extra}
        )
        assert res.status_code == 201, res.get_json()
        body = res.get_json()
        return body["token"], body["guest"]

    return _join


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
