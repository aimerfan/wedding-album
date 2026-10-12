from app.db import db
from app.models import Blessing, Guest, Like, Photo, WeddingPhoto
from app.seed import BLESSINGS, GUESTS, LIKES, PHOTOS, WEDDING

# flask 指令執行前會依 FLASK_DEBUG 重設 app.debug，所以用環境變數模擬開發模式與否


def test_seed_creates_guests_and_photos(app, monkeypatch):
    monkeypatch.setenv("FLASK_DEBUG", "1")

    result = app.test_cli_runner().invoke(args=["seed"])

    assert result.exit_code == 0, result.output
    with app.app_context():
        assert db.session.query(Guest).count() == len(GUESTS)
        assert db.session.query(Photo).count() == len(PHOTOS)
        assert db.session.query(Blessing).count() == len(BLESSINGS)
        assert db.session.query(Like).count() == len(LIKES)
        assert db.session.query(WeddingPhoto).count() == len(WEDDING)
        # 掛在照片上的祝福，作者一定是那張照片的上傳者
        for b in db.session.query(Blessing).filter(Blessing.photo_id.is_not(None)):
            assert db.session.get(Photo, b.photo_id).uploader_id == b.guest_id


def test_seed_refuses_outside_dev_mode(app, monkeypatch):
    # --reset 會清掉所有照片，正式環境誤跑就救不回來
    monkeypatch.delenv("FLASK_DEBUG", raising=False)

    result = app.test_cli_runner().invoke(args=["seed", "--reset"])

    assert result.exit_code != 0
    assert "開發模式" in result.output
