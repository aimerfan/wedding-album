"""Flask 應用程式的進入點。

用 create_app() 產生 app，而不是在模組層級直接建立：
測試時每個測試都能拿到一個乾淨、設定可以個別調整的 app。
"""

from flask import Flask

from app import config, errors


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(config.load())
    if overrides:
        app.config.update(overrides)

    # 中文直接輸出，不要轉成 中 這種跳脫字元
    app.json.ensure_ascii = False

    errors.register(app)

    from app.api import bp

    app.register_blueprint(bp)

    return app
