from flask import Flask

from app import create_app


def test_config_returns_limits(client):
    res = client.get("/api/config")

    assert res.status_code == 200
    body = res.get_json()
    assert body == {
        "maxPhotoBytes": 30 * 1024 * 1024,
        "maxVideoBytes": 95 * 1024 * 1024,
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
    # 舊的資料庫沒有影片長度、檔案雜湊欄位與索引：啟動時自動補上，不必刪資料庫
    import sqlite3

    path = tmp_path / "old.db"
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}"})
    with app.app_context():
        from app.db import db

        db.engine.dispose()
    with sqlite3.connect(path) as conn:
        conn.execute("DROP INDEX ix_photos_uploader_hash")
        conn.execute("ALTER TABLE photos DROP COLUMN duration_seconds")
        conn.execute("ALTER TABLE photos DROP COLUMN content_hash")

    create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}"})

    with sqlite3.connect(path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(photos)")}
        indexes = {row[1] for row in conn.execute("PRAGMA index_list(photos)")}
    assert {"duration_seconds", "content_hash"} <= columns
    assert "ix_photos_uploader_hash" in indexes


def test_production_paths_do_not_create_instance_folder(monkeypatch, tmp_path):
    # 正式環境資料庫與照片都在程式資料夾外，執行後端的帳號沒權限在 instance/ 建資料夾
    instance = tmp_path / "instance"
    monkeypatch.setattr(Flask, "auto_find_instance_path", lambda self: str(instance))
    (tmp_path / "data").mkdir()

    create_app(
        {
            "EVENT_CODE": "prod-code",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'data' / 'wedding.db'}",
            "MEDIA_DIR": str(tmp_path / "data" / "media"),
        }
    )

    assert not instance.exists()


def test_relative_database_path_still_goes_in_instance_folder(monkeypatch, tmp_path):
    # 開發時的預設：相對路徑的資料庫放在 instance/，資料夾不存在要自動建
    instance = tmp_path / "instance"
    monkeypatch.setattr(Flask, "auto_find_instance_path", lambda self: str(instance))

    create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///wedding.db"})

    assert (instance / "wedding.db").exists()
