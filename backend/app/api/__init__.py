"""所有 API 都掛在 /api 底下。每一類功能一個模組，在這裡 import 進來註冊路由。"""

from flask import Blueprint

bp = Blueprint("api", __name__, url_prefix="/api")

# 放在最後 import：各模組要用到上面的 bp
from app.api import blessings, comments, config, guests, photos, wedding  # noqa: E402, F401
