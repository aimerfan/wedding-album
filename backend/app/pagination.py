"""列表 API 的 cursor 分頁，照片、祝福共用。見 docs/api.md 的「分頁」。

cursor 記的是「上一頁最後一筆」的時間與 id。對前端來說只是一串看不懂的字，原樣傳回來即可。
用時間 + id 兩個欄位，是因為同一秒可能有好幾筆，只靠時間會漏掉或重複。
"""

import base64
import binascii
import json
from datetime import datetime

from flask import request
from sqlalchemy import Select, and_, or_
from sqlalchemy.orm import InstrumentedAttribute

from app.db import db
from app.errors import ApiError

DEFAULT_LIMIT = 30
MAX_LIMIT = 100


def _encode(t: datetime, id_: str) -> str:
    raw = json.dumps({"t": t.isoformat(), "id": id_})
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode(cursor: str) -> tuple[datetime, str]:
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


def paginate(
    query: Select, time_col: InstrumentedAttribute, id_col: InstrumentedAttribute
) -> tuple[list, str | None]:
    """依 (時間, id) 由新到舊分頁。回傳 (這一頁的資料, 下一頁的 cursor 或 None)。"""
    if cursor := request.args.get("cursor"):
        t, last_id = _decode(cursor)
        query = query.where(or_(time_col < t, and_(time_col == t, id_col < last_id)))

    limit = _limit()
    # 多拿一筆，用來判斷還有沒有下一頁
    rows = db.session.scalars(query.order_by(time_col.desc(), id_col.desc()).limit(limit + 1)).all()
    items = list(rows[:limit])
    if len(rows) <= limit:
        return items, None
    last = items[-1]
    return items, _encode(getattr(last, time_col.key), getattr(last, id_col.key))
