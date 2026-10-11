import pytest

from app import create_app


@pytest.fixture
def app():
    return create_app({"TESTING": True})


@pytest.fixture
def client(app):
    """模擬前端打 API 的測試用 client，不必真的啟動伺服器。"""
    return app.test_client()
