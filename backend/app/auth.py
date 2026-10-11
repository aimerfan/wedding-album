"""賓客身分：發 token、驗 token。流程見 docs/api.md 的「身分」。

token 只在發出的那一刻以明文回給前端，資料庫只存它的 SHA-256。
"""

import hashlib
import hmac
import secrets
from functools import wraps

from flask import current_app, g, request

from app.db import db
from app.errors import ApiError
from app.models import Guest


def new_token() -> tuple[str, str]:
    """產生 (token 明文, 雜湊值)。明文回給前端，雜湊值存進資料庫。"""
    token = secrets.token_urlsafe(32)
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def check_event_code(code: object) -> None:
    """活動碼不對就擋下來。用 compare_digest 比對，避免從回應時間猜出活動碼。"""
    expected = current_app.config["EVENT_CODE"]
    if not isinstance(code, str) or not hmac.compare_digest(code, expected):
        raise ApiError(401, "invalid_event_code", "活動碼不正確，請重新掃描會場的 QR code")


def _guest_from_request() -> Guest | None:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme != "Bearer" or not token:
        return None
    return db.session.scalar(db.select(Guest).filter_by(token_hash=hash_token(token)))


def require_guest(view):
    """掛在需要 token 的路由上。驗過之後，目前的賓客放在 g.guest。"""

    @wraps(view)
    def wrapper(*args, **kwargs):
        guest = _guest_from_request()
        if guest is None:
            raise ApiError(401, "unauthorized")
        g.guest = guest
        return view(*args, **kwargs)

    return wrapper
