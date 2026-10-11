"""相簿：照片列表、單張照片、首頁統計。"""

import base64
import binascii
import json
from datetime import UTC, datetime, time, timedelta

from flask import g, jsonify, request
from sqlalchemy import and_, func, or_

from app.api import bp
from app.auth import require_guest
from app.db import db
from app.errors import ApiError
from app.models import PHOTO_TAGS, TAIPEI, Guest, Photo

DEFAULT_LIMIT = 30
MAX_LIMIT = 100


# --- cursor ---------------------------------------------------------------
# cursor 記的是「上一頁最後一張」的上傳時間與 id。對前端來說只是一串看不懂的字，原樣傳回來即可。
# 用時間 + id 兩個欄位，是因為同一秒可能有好幾張，只靠時間會漏掉或重複。


def _encode_cursor(photo: Photo) -> str:
    raw = json.dumps({"t": photo.uploaded_at.isoformat(), "id": photo.id})
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        return datetime.fromisoformat(data["t"]), str(data["id"])
    except (binascii.Error, ValueError, KeyError, TypeError) as e:
        raise ApiError(400, "invalid_cursor", "分頁參數不正確") from e


def _limit() -> int:
    raw = request.args.get("limit")
    if raw is None:
        return DEFAULT_LIMIT
    try:
        value = int(raw)
    except ValueError as e:
        raise ApiError(400, "invalid_limit", "limit 必須是數字") from e
    return max(1, min(value, MAX_LIMIT))


def _today_range_utc() -> tuple[datetime, datetime]:
    """台灣時間「今天」的起訖，換成資料庫裡存的 UTC（不帶時區）。"""
    # now() 是不帶時區的 UTC，不能直接 astimezone（會被當成電腦本地時間），這裡直接取台灣時間
    today = datetime.now(TAIPEI).date()
    start = datetime.combine(today, time.min, tzinfo=TAIPEI).astimezone(UTC).replace(tzinfo=None)
    return start, start + timedelta(days=1)


# --- 路由 -----------------------------------------------------------------


@bp.get("/photos")
@require_guest
def list_photos():
    args = request.args
    query = db.select(Photo)

    if tag := args.get("tag"):
        if tag not in PHOTO_TAGS:
            raise ApiError(400, "invalid_tag", "照片分類不正確")
        query = query.where(Photo.tag == tag)

    if kind := args.get("kind"):
        if kind not in ("photo", "video"):
            raise ApiError(400, "invalid_kind", "kind 只能是 photo 或 video")
        query = query.where(Photo.kind == kind)

    if date := args.get("date"):
        if date != "today":
            raise ApiError(400, "invalid_date", "date 目前只支援 today")
        start, end = _today_range_utc()
        query = query.where(Photo.uploaded_at >= start, Photo.uploaded_at < end)

    if uploader := args.get("uploader"):
        query = query.where(Photo.uploader_id == (g.guest.id if uploader == "me" else uploader))

    if args.get("favorited"):
        # TODO: 第五步（收藏）做好之後實作
        raise ApiError(501, "not_implemented", "收藏功能還沒做好")

    if cursor := args.get("cursor"):
        t, last_id = _decode_cursor(cursor)
        query = query.where(
            or_(Photo.uploaded_at < t, and_(Photo.uploaded_at == t, Photo.id < last_id))
        )

    limit = _limit()
    # 多拿一張，用來判斷還有沒有下一頁
    rows = db.session.scalars(
        query.order_by(Photo.uploaded_at.desc(), Photo.id.desc()).limit(limit + 1)
    ).all()
    has_more = len(rows) > limit
    items = rows[:limit]

    return jsonify(
        {
            "items": [p.to_json() for p in items],
            "nextCursor": _encode_cursor(items[-1]) if has_more else None,
        }
    )


@bp.get("/photos/<photo_id>")
@require_guest
def get_photo(photo_id: str):
    photo = db.session.get(Photo, photo_id)
    if photo is None:
        raise ApiError(404, "photo_not_found", "找不到這張照片")
    return jsonify(photo.to_json())


@bp.get("/stats")
@require_guest
def get_stats():
    return jsonify(
        {
            "photoCount": db.session.scalar(db.select(func.count()).select_from(Photo)),
            # 加入過相簿的賓客人數
            "guestCount": db.session.scalar(db.select(func.count()).select_from(Guest)),
            # TODO: 第五步（祝福）做好之後改成真的數字
            "blessingCount": 0,
        }
    )
