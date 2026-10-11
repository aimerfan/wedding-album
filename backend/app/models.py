"""資料表。欄位對應 docs/api.md 的「資料形狀」；輸出成 JSON 的工作在各個 to_json()。"""

import secrets
from datetime import UTC, datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import db

# 欄位長度上限，跟前端輸入框的 maxlength 一致
NICKNAME_MAX = 20
RELATION_MAX = 30


def _new_id(prefix: str) -> str:
    """對外的 id，例如 g_Xk3p9QaB。用隨機字串而不是流水號，別人猜不到其他賓客的 id。"""
    return prefix + secrets.token_urlsafe(6)


def _now() -> datetime:
    return datetime.now(UTC)


class Guest(db.Model):
    __tablename__ = "guests"

    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=lambda: _new_id("g_"))
    nickname: Mapped[str] = mapped_column(String(NICKNAME_MAX))
    relation: Mapped[str | None] = mapped_column(String(RELATION_MAX))
    # 只存 token 的雜湊值。資料庫外流時，拿到的人也無法冒充賓客
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=_now)

    def to_json(self) -> dict:
        data = {"id": self.id, "nickname": self.nickname}
        if self.relation:
            data["relation"] = self.relation
        return data
