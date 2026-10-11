"""資料表。欄位對應 docs/api.md 的「資料形狀」；輸出成 JSON 的工作在各個 to_json()。"""

import secrets
from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy import ForeignKey, String, func
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
    # 只存 token 的雜湊值。資料庫外流時，拿到的人也無法冒充賓客。
    # 預先匯入的祝福作者沒有 token（None），他們不會用手機登入，只是掛名在祝福上
    token_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=now)

    def to_json(self) -> dict:
        data = {"id": self.id, "nickname": self.nickname}
        if self.relation:
            data["relation"] = self.relation
        return data

    @property
    def imported(self) -> bool:
        """預先匯入的祝福作者，不是透過 app 加入的賓客。"""
        return self.token_hash is None


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

    def to_json(self, viewer_id: str | None = None) -> dict:
        """單張照片。列表請用 photos_to_json()，一次查好讚數，不必每張各查一次。"""
        return photos_to_json([self], viewer_id)[0]

    def _base_json(self) -> dict:
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
            "tag": self.tag,
        }


class Like(db.Model):
    """按讚。一人對一張照片只會有一筆，所以 (賓客, 照片) 當主鍵。"""

    __tablename__ = "likes"

    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.id"), primary_key=True)
    photo_id: Mapped[str] = mapped_column(ForeignKey("photos.id"), primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=now)


class Favorite(db.Model):
    """收藏：私人書籤，只有自己看得到。"""

    __tablename__ = "favorites"

    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.id"), primary_key=True)
    photo_id: Mapped[str] = mapped_column(ForeignKey("photos.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=now, index=True)


class Blessing(db.Model):
    __tablename__ = "blessings"

    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=lambda: _new_id("b_"))
    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.id"), index=True)
    text: Mapped[str] = mapped_column(String(1000))
    # 上傳照片時一起寫的祝福會掛在那批的第一張上；留言牆上的獨立祝福是 None
    photo_id: Mapped[str | None] = mapped_column(ForeignKey("photos.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(default=now, index=True)
    # 最後一次修改的時間，沒改過就是 None。前端用來標示「已編輯」
    edited_at: Mapped[datetime | None]

    guest: Mapped[Guest] = relationship(lazy="joined")

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "guest": self.guest.to_json(),
            "text": self.text,
            "createdAt": iso(self.created_at),
            "editedAt": iso(self.edited_at),
            "photoId": self.photo_id,
        }


def photos_to_json(photos: list[Photo], viewer_id: str | None) -> list[dict]:
    """照片轉成 JSON，順便算好讚數、我按過讚沒、我收藏了沒、附帶的祝福。

    一整頁的照片各用一次查詢算完，不會變成「每張照片查三次」。
    """
    ids = [p.id for p in photos]
    if not ids:
        return []

    like_counts = dict(
        db.session.execute(
            db.select(Like.photo_id, func.count()).where(Like.photo_id.in_(ids)).group_by(Like.photo_id)
        ).all()
    )
    liked: set[str] = set()
    favorited: set[str] = set()
    if viewer_id:
        liked = set(
            db.session.scalars(
                db.select(Like.photo_id).where(Like.guest_id == viewer_id, Like.photo_id.in_(ids))
            )
        )
        favorited = set(
            db.session.scalars(
                db.select(Favorite.photo_id).where(
                    Favorite.guest_id == viewer_id, Favorite.photo_id.in_(ids)
                )
            )
        )
    # 一張照片理論上只會掛一則祝福；萬一有好幾則，取最早的
    blessings: dict[str, str] = {}
    for photo_id, text in db.session.execute(
        db.select(Blessing.photo_id, Blessing.text)
        .where(Blessing.photo_id.in_(ids))
        .order_by(Blessing.created_at.desc())
    ):
        blessings[photo_id] = text

    result = []
    for p in photos:
        data = p._base_json()
        data["blessing"] = blessings.get(p.id)
        data["likeCount"] = like_counts.get(p.id, 0)
        data["likedByMe"] = p.id in liked
        data["favoritedByMe"] = p.id in favorited
        result.append(data)
    return result
