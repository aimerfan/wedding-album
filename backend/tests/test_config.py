from app import create_app


def test_config_returns_limits(client):
    res = client.get("/api/config")

    assert res.status_code == 200
    body = res.get_json()
    assert body == {
        "maxPhotoBytes": 30 * 1024 * 1024,
        "maxVideoBytes": 200 * 1024 * 1024,
        "maxVideoSeconds": 180,
        "maxUploadsPerHour": 300,
        "uploadConcurrency": 3,
        "videoUploadConcurrency": 1,
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


def test_sqlite_uses_wal_and_waits_for_locks(tmp_path):
    # 婚宴高峰多人同時上傳：寫入時別人還能讀，兩個寫入撞在一起時後到的會等，而不是直接失敗
    from sqlalchemy import text

    from app.db import BUSY_TIMEOUT_MS, db

    app = create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'wal.db'}"}
    )
    with app.app_context():
        assert db.session.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert db.session.execute(text("PRAGMA busy_timeout")).scalar() == BUSY_TIMEOUT_MS


def test_existing_database_gets_new_nullable_columns(tmp_path):
    # 舊的資料庫沒有影片長度欄位：啟動時自動補上，不必刪資料庫
    import sqlite3

    path = tmp_path / "old.db"
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}"})
    with app.app_context():
        from app.db import db

        db.engine.dispose()
    with sqlite3.connect(path) as conn:
        conn.execute("ALTER TABLE photos DROP COLUMN duration_seconds")

    create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}"})

    with sqlite3.connect(path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(photos)")}
    assert "duration_seconds" in columns
