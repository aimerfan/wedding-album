"""相簿：照片列表、單張照片、首頁統計。"""

from datetime import UTC, datetime, time, timedelta

from flask import current_app, g, jsonify, request
from sqlalchemy import func

from app import images, storage
from app.api import bp
from app.auth import require_guest
from app.db import db
from app.errors import ApiError
from app.models import (
    PHOTO_TAGS,
    TAIPEI,
    Blessing,
    Favorite,
    Guest,
    Like,
    Photo,
    now,
    photos_to_json,
)
from app.pagination import paginate


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

    if args.get("favorited") == "true":
        # 收藏是私人的，只能看自己的
        query = query.join(
            Favorite, (Favorite.photo_id == Photo.id) & (Favorite.guest_id == g.guest.id)
        )

    items, next_cursor = paginate(query, Photo.uploaded_at, Photo.id)
    return jsonify({"items": photos_to_json(items, g.guest.id), "nextCursor": next_cursor})


@bp.post("/photos")
@require_guest
def upload_photo():
    """上傳一張照片。multipart/form-data，欄位 file（必填）、tag（選填，預設 banquet）。"""
    config = current_app.config
    if not config["UPLOADS_OPEN"]:
        raise ApiError(403, "uploads_closed", "相簿已經截止上傳，謝謝你的參與")

    file = request.files.get("file")
    if file is None or not file.filename:
        raise ApiError(400, "file_required", "請選擇要上傳的照片")

    if (file.mimetype or "").startswith("video/"):
        raise ApiError(415, "video_not_supported", "目前只能上傳照片，暫不開放影片")

    tag = request.form.get("tag") or "banquet"
    if tag not in PHOTO_TAGS:
        raise ApiError(400, "invalid_tag", "照片分類不正確")

    # 每人每小時的上限：正常賓客碰不到，主要防活動碼外流後被灌爆
    recent = db.session.scalar(
        db.select(func.count())
        .select_from(Photo)
        .where(Photo.uploader_id == g.guest.id, Photo.uploaded_at >= now() - timedelta(hours=1))
    )
    if recent >= config["MAX_UPLOADS_PER_HOUR"]:
        raise ApiError(429, "too_many_uploads", "上傳得太快了，請休息一下再繼續")

    data = file.read()
    if len(data) > config["MAX_PHOTO_BYTES"]:
        mb = config["MAX_PHOTO_BYTES"] // (1024 * 1024)
        raise ApiError(413, "file_too_large", f"照片太大了，單張上限 {mb} MB")

    try:
        processed = images.process_upload(data)
    except images.UnsupportedImage as e:
        raise ApiError(415, "unsupported_format", "看不懂這個檔案，請上傳 JPEG、PNG、HEIC 或 WebP 照片") from e

    photo = Photo(
        uploader_id=g.guest.id,
        tag=tag,
        width=processed.width,
        height=processed.height,
        taken_at=processed.taken_at,
        original_key="",
        display_key="",
        thumb_key="",
    )
    db.session.add(photo)
    db.session.flush()  # 拿到 photo.id 才能決定檔名

    folder = f"photos/{photo.id}"
    photo.original_key = f"{folder}/original.{processed.extension}"
    photo.display_key = f"{folder}/display.jpg"
    photo.thumb_key = f"{folder}/thumb.jpg"
    # 原檔原封不動地存，之後匯出給新人時就是原始畫質
    storage.save(photo.original_key, data)
    storage.save(photo.display_key, processed.display_jpeg)
    storage.save(photo.thumb_key, processed.thumb_jpeg)
    db.session.commit()

    return jsonify(photo.to_json(g.guest.id)), 201


def _get_photo_or_404(photo_id: str) -> Photo:
    photo = db.session.get(Photo, photo_id)
    if photo is None:
        raise ApiError(404, "photo_not_found", "找不到這張照片")
    return photo


@bp.get("/photos/<photo_id>")
@require_guest
def get_photo(photo_id: str):
    return jsonify(_get_photo_or_404(photo_id).to_json(g.guest.id))


# --- 按讚、收藏 -----------------------------------------------------------
# 用 PUT / DELETE 而不是「切換」：重複按、網路不穩重送，結果都一樣，不會讚了又被收回。
# 回應是更新後的照片，前端直接拿來換掉畫面上的那張。


def _set_mark(model, photo_id: str, on: bool):
    photo = _get_photo_or_404(photo_id)
    existing = db.session.get(model, (g.guest.id, photo.id))
    if on and existing is None:
        db.session.add(model(guest_id=g.guest.id, photo_id=photo.id))
    elif not on and existing is not None:
        db.session.delete(existing)
    db.session.commit()
    return jsonify(photo.to_json(g.guest.id))


@bp.put("/photos/<photo_id>/like")
@require_guest
def like_photo(photo_id: str):
    return _set_mark(Like, photo_id, True)


@bp.delete("/photos/<photo_id>/like")
@require_guest
def unlike_photo(photo_id: str):
    return _set_mark(Like, photo_id, False)


@bp.put("/photos/<photo_id>/favorite")
@require_guest
def favorite_photo(photo_id: str):
    return _set_mark(Favorite, photo_id, True)


@bp.delete("/photos/<photo_id>/favorite")
@require_guest
def unfavorite_photo(photo_id: str):
    return _set_mark(Favorite, photo_id, False)


@bp.get("/stats")
@require_guest
def get_stats():
    def count(query):
        return db.session.scalar(query)

    return jsonify(
        {
            "photoCount": count(db.select(func.count()).select_from(Photo)),
            # 透過 app 加入相簿的賓客人數，不含預先匯入的祝福作者
            "guestCount": count(
                db.select(func.count()).select_from(Guest).where(Guest.imported.is_(False))
            ),
            "blessingCount": count(db.select(func.count()).select_from(Blessing)),
            # 留言牆標題「32 位賓客留下了 47 則祝福」的 32：留過祝福的人數，含預先匯入的
            "blessingGuestCount": count(db.select(func.count(func.distinct(Blessing.guest_id)))),
        }
    )
