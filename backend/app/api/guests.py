"""身分相關：加入相簿、目前這位賓客的資料、換裝置的接續碼。"""

import hmac
import secrets
from datetime import timedelta

from flask import current_app, g, jsonify, request
from sqlalchemy import func

from app.api import bp
from app.auth import check_event_code, issue_token, require_guest
from app.db import db
from app.errors import ApiError
from app.models import (
    NICKNAME_MAX,
    RELATION_MAX,
    Blessing,
    Favorite,
    Guest,
    Like,
    Photo,
    TransferCode,
    iso,
    now,
)


def _json_body() -> dict:
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ApiError(400, "invalid_body", "請求內容必須是 JSON 物件")
    return body


def _clean_nickname(value: object) -> str:
    nickname = value.strip() if isinstance(value, str) else ""
    if not nickname:
        raise ApiError(400, "nickname_required", "請輸入你的名字")
    if len(nickname) > NICKNAME_MAX:
        raise ApiError(400, "nickname_too_long", f"名字最多 {NICKNAME_MAX} 個字")
    return nickname


def _clean_relation(value: object) -> str | None:
    """選填。沒帶、空字串都當作沒有。"""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ApiError(400, "invalid_relation", "與新人的關係格式不正確")
    relation = value.strip()
    if len(relation) > RELATION_MAX:
        raise ApiError(400, "relation_too_long", f"與新人的關係最多 {RELATION_MAX} 個字")
    return relation or None


@bp.post("/guests")
def create_guest():
    """加入相簿：用活動碼 + 暱稱領一組 token。這時還沒有 token，所以不檢查 token。"""
    body = _json_body()
    check_event_code(body.get("eventCode"))

    guest = Guest(
        nickname=_clean_nickname(body.get("nickname")),
        relation=_clean_relation(body.get("relation")),
    )
    db.session.add(guest)
    token = issue_token(guest)
    db.session.commit()

    return jsonify({"token": token, "guest": guest.to_json()}), 201


@bp.get("/me")
@require_guest
def get_me():
    me = g.guest.id

    def count(query):
        return db.session.scalar(query)

    return jsonify(
        {
            "guest": g.guest.to_json(),
            # 只回給本人，不放進公開的 Guest 資料
            "isAdmin": g.guest.is_admin,
            "stats": {
                "uploaded": count(
                    db.select(func.count()).select_from(Photo).where(Photo.uploader_id == me)
                ),
                "favorited": count(
                    db.select(func.count()).select_from(Favorite).where(Favorite.guest_id == me)
                ),
                # 別人在我上傳的照片按的讚
                "likesReceived": count(
                    db.select(func.count())
                    .select_from(Like)
                    .join(Photo, Like.photo_id == Photo.id)
                    .where(Photo.uploader_id == me)
                ),
                "blessings": count(
                    db.select(func.count()).select_from(Blessing).where(Blessing.guest_id == me)
                ),
            },
        }
    )


@bp.patch("/me")
@require_guest
def update_me():
    """改暱稱或與新人的關係。只改有帶的欄位。"""
    body = _json_body()
    if "nickname" in body:
        g.guest.nickname = _clean_nickname(body["nickname"])
    if "relation" in body:
        g.guest.relation = _clean_relation(body["relation"])
    db.session.commit()

    return jsonify({"guest": g.guest.to_json()})


# --- 接續碼 ---------------------------------------------------------------
# 換瀏覽器或裝置時延續同一位賓客。連結裡放的是一次性、限時的接續碼，不是 token 本身：
# 網址會留在瀏覽紀錄、可能被轉傳，直接放 token 等於把身分永久交出去。

# 去掉容易看錯的 0/O、1/I/L，萬一要手動輸入也不會打錯
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 8


def _new_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))


@bp.post("/me/transfer-codes")
@require_guest
def create_transfer_code():
    """產生接續碼。完整連結由前端組（前端才知道自己的網址）。"""
    minutes = current_app.config["TRANSFER_CODE_MINUTES"]
    transfer = TransferCode(
        code=_new_code(),
        guest_id=g.guest.id,
        expires_at=now() + timedelta(minutes=minutes),
    )
    db.session.add(transfer)
    db.session.commit()
    return jsonify({"code": transfer.code, "expiresAt": iso(transfer.expires_at)}), 201


@bp.post("/guests/claim")
def claim_transfer_code():
    """用接續碼在這個裝置領一組新的 token。這時還沒有 token，所以不檢查 token。

    原本的裝置不會被登出：每個裝置各有自己的 token。
    """
    body = _json_body()
    raw = body.get("transferCode")
    code = raw.strip().upper() if isinstance(raw, str) else ""

    transfer = db.session.get(TransferCode, code) if code else None
    if transfer is None or transfer.used_at is not None:
        raise ApiError(401, "invalid_transfer_code", "這個連結已經用過或無效，請在原本的裝置重新產生")
    if transfer.expires_at <= now():
        raise ApiError(401, "transfer_code_expired", "這個連結已經過期，請在原本的裝置重新產生")

    transfer.used_at = now()
    guest = db.session.get(Guest, transfer.guest_id)
    token = issue_token(guest)
    db.session.commit()
    return jsonify({"token": token, "guest": guest.to_json()})


# --- 管理員 ---------------------------------------------------------------


@bp.post("/me/admin")
@require_guest
def become_admin():
    """用管理員代碼把自己開通成管理員。先照一般流程加入相簿，再打開 /admin?code=…"""
    expected = current_app.config["ADMIN_CODE"]
    if not expected:
        raise ApiError(403, "admin_disabled", "這個相簿沒有開放管理員")
    code = _json_body().get("adminCode")
    # 用 compare_digest 比對，避免從回應時間猜出代碼
    if not isinstance(code, str) or not hmac.compare_digest(code, expected):
        raise ApiError(403, "invalid_admin_code", "管理員代碼不正確")
    g.guest.is_admin = True
    db.session.commit()
    return jsonify({"guest": g.guest.to_json(), "isAdmin": True})
