from app import create_app


def test_config_returns_limits(client):
    res = client.get("/api/config")

    assert res.status_code == 200
    body = res.get_json()
    assert body == {
        "maxPhotoBytes": 30 * 1024 * 1024,
        "maxVideoBytes": 200 * 1024 * 1024,
        "maxUploadsPerHour": 300,
        "uploadConcurrency": 3,
        "maxBlessingLength": 200,
        "uploadsOpen": True,
        "kahootUrl": None,
    }


def test_config_can_be_changed_by_env(monkeypatch):
    # 婚禮當天調整上限的方式：改環境變數、重啟後端
    monkeypatch.setenv("UPLOAD_CONCURRENCY", "1")
    monkeypatch.setenv("UPLOADS_OPEN", "false")

    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    body = app.test_client().get("/api/config").get_json()

    assert body["uploadConcurrency"] == 1
    assert body["uploadsOpen"] is False


def test_unknown_api_returns_error_shape(client):
    res = client.get("/api/does-not-exist")

    assert res.status_code == 404
    assert res.get_json() == {"error": {"code": "not_found", "message": "找不到這個東西"}}
