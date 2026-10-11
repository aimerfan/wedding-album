"""身分相關：加入相簿、目前這位賓客的資料。"""

from flask import g, jsonify, request

from app.api import bp
from app.auth import check_event_code, new_token, require_guest
from app.db import db
from app.errors import ApiError
from app.models import NICKNAME_MAX, RELATION_MAX, Guest


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

    token, token_hash = new_token()
    guest = Guest(
        nickname=_clean_nickname(body.get("nickname")),
        relation=_clean_relation(body.get("relation")),
        token_hash=token_hash,
    )
    db.session.add(guest)
    db.session.commit()

    return jsonify({"token": token, "guest": guest.to_json()}), 201


@bp.get("/me")
@require_guest
def get_me():
    return jsonify(
        {
            "guest": g.guest.to_json(),
            # TODO: 照片、收藏、祝福做好之後改成真的數字
            "stats": {"uploaded": 0, "favorited": 0, "likesReceived": 0, "blessings": 0},
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
