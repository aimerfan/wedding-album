from app.db import db
from app.models import Guest, Photo
from app.seed import GUESTS, PHOTOS

# flask 指令執行前會依 FLASK_DEBUG 重設 app.debug，所以用環境變數模擬開發模式與否


def test_seed_creates_guests_and_photos(app, monkeypatch):
    monkeypatch.setenv("FLASK_DEBUG", "1")

    result = app.test_cli_runner().invoke(args=["seed"])

    assert result.exit_code == 0, result.output
    with app.app_context():
        assert db.session.query(Guest).count() == len(GUESTS)
        assert db.session.query(Photo).count() == len(PHOTOS)


def test_seed_refuses_outside_dev_mode(app, monkeypatch):
    # --reset 會清掉所有照片，正式環境誤跑就救不回來
    monkeypatch.delenv("FLASK_DEBUG", raising=False)

    result = app.test_cli_runner().invoke(args=["seed", "--reset"])

    assert result.exit_code != 0
    assert "開發模式" in result.output
