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
        "MAX_PHOTO_BYTES": _int("MAX_PHOTO_BYTES", 30 * MB),
        "MAX_VIDEO_BYTES": _int("MAX_VIDEO_BYTES", 200 * MB),
        "MAX_UPLOADS_PER_HOUR": _int("MAX_UPLOADS_PER_HOUR", 300),
        "UPLOAD_CONCURRENCY": _int("UPLOAD_CONCURRENCY", 3),
        "MAX_BLESSING_LENGTH": _int("MAX_BLESSING_LENGTH", 200),
        "UPLOADS_OPEN": _bool("UPLOADS_OPEN", True),
    }
