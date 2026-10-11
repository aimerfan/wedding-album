"""資料表。欄位對應 docs/api.md 的「資料形狀」；輸出成 JSON 的工作在各個 to_json()。"""

import secrets
from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import storage
from app.db import db

# 欄位長度上限，跟前端輸入框的 maxlength 一致
NICKNAME_MAX = 20
RELATION_MAX = 30

PHOTO_TAGS = ("welcome", "ceremony", "banquet")

# 回給前端的時間一律用台灣時間。台灣沒有日光節約，固定 +08:00 即可
TAIPEI = timezone(timedelta(hours=8), "Asia/Taipei")


def _new_id(prefix: str) -> str:
    """對外的 id，例如 g_Xk3p9QaB。用隨機字串而不是流水號，別人猜不到其他賓客的 id。"""
    return prefix + secrets.token_urlsafe(6)


def now() -> datetime:
    """現在的 UTC 時間，不帶時區。SQLite 不保存時區，統一存不帶時區的 UTC，比較時才不會出錯。"""
    return datetime.now(UTC).replace(tzinfo=None)


def iso(dt: datetime | None) -> str | None:
    """轉成 2026-10-17T18:42:00+08:00。資料庫裡的時間都是不帶時區的 UTC（見 now()）。"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(TAIPEI).isoformat(timespec="seconds")


class Guest(db.Model):
    __tablename__ = "guests"

    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=lambda: _new_id("g_"))
    nickname: Mapped[str] = mapped_column(String(NICKNAME_MAX))
    relation: Mapped[str | None] = mapped_column(String(RELATION_MAX))
    # 只存 token 的雜湊值。資料庫外流時，拿到的人也無法冒充賓客
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=now)

    def to_json(self) -> dict:
        data = {"id": self.id, "nickname": self.nickname}
        if self.relation:
            data["relation"] = self.relation
        return data


class Photo(db.Model):
    __tablename__ = "photos"

    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=lambda: _new_id("p_"))
    uploader_id: Mapped[str] = mapped_column(ForeignKey("guests.id"), index=True)
    # 目前只收照片；欄位先留著，之後開放影片時不必改資料表
    kind: Mapped[str] = mapped_column(String(8), default="photo")
    tag: Mapped[str] = mapped_column(String(16), default="banquet")
    # 原圖尺寸，前端用來算比例排版
    width: Mapped[int]
    height: Mapped[int]
    # 從 EXIF 讀出的拍攝時間，讀不到就是 None
    taken_at: Mapped[datetime | None]
    uploaded_at: Mapped[datetime] = mapped_column(default=now, index=True)
    # 檔案在儲存層的位置（見 app/storage.py），不是網址
    original_key: Mapped[str] = mapped_column(String(128))
    display_key: Mapped[str] = mapped_column(String(128))
    thumb_key: Mapped[str] = mapped_column(String(128))

    uploader: Mapped[Guest] = relationship(lazy="joined")

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "url": storage.url(self.original_key),
            "displayUrl": storage.url(self.display_key),
            "thumbnailUrl": storage.url(self.thumb_key),
            "width": self.width,
            "height": self.height,
            "durationSeconds": None,
            "uploader": self.uploader.to_json(),
            "uploadedAt": iso(self.uploaded_at),
            "takenAt": iso(self.taken_at),
            # TODO: 第五步（按讚、收藏、祝福）做好之後改成真的值
            "blessing": None,
            "likeCount": 0,
            "likedByMe": False,
            "favoritedByMe": False,
            "tag": self.tag,
        }
