"""Flask 應用程式的進入點。

用 create_app() 產生 app，而不是在模組層級直接建立：
測試時每個測試都能拿到一個乾淨、設定可以個別調整的 app。
"""

import os

from flask import Flask

from app import config, errors
from app.db import db

DEV_EVENT_CODE = "dev"


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(config.load())
    if overrides:
        app.config.update(overrides)

    if not app.config["EVENT_CODE"]:
        # 正式環境忘了設活動碼，等於任何人輸入 "dev" 都能進來，寧可啟動失敗
        if not (app.debug or app.testing):
            raise RuntimeError(
                "沒有設定環境變數 EVENT_CODE。正式環境一定要設；"
                "開發時請在 backend/ 底下執行 flask 指令（會讀 .flaskenv 進入開發模式）"
            )
        app.config["EVENT_CODE"] = DEV_EVENT_CODE

    # 整個請求的大小上限 = 單張照片上限（預設 30 MB）+ 1 MB 給表單的其他欄位（例如 tag）。
    # 超過這個大小的請求，Flask 在讀進記憶體之前就直接回 413，
    # 所以就算有人故意傳一個超大的檔案，也不會先被整個收進伺服器的記憶體
    app.config["MAX_CONTENT_LENGTH"] = app.config["MAX_PHOTO_BYTES"] + 1024 * 1024

    # 中文直接輸出，不要轉成 \u 開頭的跳脫字元
    app.json.ensure_ascii = False

    errors.register(app)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    from app import models, seed, storage  # noqa: F401  models：讓 create_all 知道有哪些資料表
    from app.api import bp

    app.register_blueprint(bp)
    app.register_blueprint(storage.bp)
    app.cli.add_command(seed.seed_command)

    with app.app_context():
        # 只會建立還不存在的資料表，不會動到已有的資料。
        # 改了既有欄位不會自動套用，見 README 的「資料庫」
        db.create_all()

    return app
