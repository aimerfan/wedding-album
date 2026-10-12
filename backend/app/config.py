"""設定值。

所有上限都只在這裡定義一份，前端透過 GET /api/config 讀取（見 docs/api.md 的「設定」）。
每一項都可以用同名的環境變數覆蓋，婚禮當天要調整時改環境變數、重啟後端即可，不必改程式。
"""

import os

MB = 1024 * 1024


def _int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return int(value) if value else default


def _bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if not value:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def load() -> dict:
    """讀取設定。每次呼叫都重新讀環境變數，測試時才能個別調整。"""
    return {
        # 相對路徑會放在 backend/instance/ 底下
        "SQLALCHEMY_DATABASE_URI": os.environ.get("DATABASE_URL", "sqlite:///wedding.db"),
        # QR code 網址裡的活動碼。正式環境一定要設；開發與測試時沒設就用 "dev"
        "EVENT_CODE": os.environ.get("EVENT_CODE", ""),
        # 照片檔放哪裡。空字串代表 backend/instance/media/
        "MEDIA_DIR": os.environ.get("MEDIA_DIR", ""),
        # 回給前端的照片網址開頭。換成雲端儲存時改成 CDN 網址即可，前端不用動
        "MEDIA_BASE_URL": os.environ.get("MEDIA_BASE_URL", "/media"),
        "MAX_PHOTO_BYTES": _int("MAX_PHOTO_BYTES", 30 * MB),
        "MAX_VIDEO_BYTES": _int("MAX_VIDEO_BYTES", 200 * MB),
        "MAX_UPLOADS_PER_HOUR": _int("MAX_UPLOADS_PER_HOUR", 300),
        "UPLOAD_CONCURRENCY": _int("UPLOAD_CONCURRENCY", 3),
        "MAX_BLESSING_LENGTH": _int("MAX_BLESSING_LENGTH", 200),
        # 接續碼幾分鐘內有效
        "TRANSFER_CODE_MINUTES": _int("TRANSFER_CODE_MINUTES", 30),
        "UPLOADS_OPEN": _bool("UPLOADS_OPEN", True),
    }
