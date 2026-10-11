"""祝福留言：留言牆，以及上傳照片時一起寫的祝福。"""

from flask import current_app, g, jsonify, request

from app.api import bp
from app.auth import require_guest
from app.db import db
from app.errors import ApiError
from app.models import Blessing, Photo, now
from app.pagination import paginate


def _json_body() -> dict:
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ApiError(400, "invalid_body", "請求內容必須是 JSON 物件")
    return body


def _clean_text(raw: object) -> str:
    text = raw.strip() if isinstance(raw, str) else ""
    if not text:
        raise ApiError(400, "text_required", "請寫下你的祝福")
    limit = current_app.config["MAX_BLESSING_LENGTH"]
    if len(text) > limit:
        raise ApiError(400, "text_too_long", f"祝福最多 {limit} 個字")
    return text


def _my_blessing(blessing_id: str) -> Blessing:
    """只能改、刪自己的祝福。預先匯入的祝福作者沒有 token，所以自然沒人能改。"""
    blessing = db.session.get(Blessing, blessing_id)
    if blessing is None:
        raise ApiError(404, "blessing_not_found", "找不到這則祝福")
    if blessing.guest_id != g.guest.id:
        raise ApiError(403, "not_your_blessing", "只能修改自己的祝福")
    return blessing


@bp.get("/blessings")
@require_guest
def list_blessings():
    """留言牆，新的在前。guest=me 只列自己的（「我的 → 我的祝福」）。"""
    query = db.select(Blessing)
    if request.args.get("guest") == "me":
        query = query.where(Blessing.guest_id == g.guest.id)

    items, next_cursor = paginate(query, Blessing.created_at, Blessing.id)
    return jsonify({"items": [b.to_json() for b in items], "nextCursor": next_cursor})


@bp.post("/blessings")
@require_guest
def create_blessing():
    body = _json_body()
    text = _clean_text(body.get("text"))

    photo_id = body.get("photoId")
    if photo_id is not None:
        photo = db.session.get(Photo, photo_id) if isinstance(photo_id, str) else None
        if photo is None:
            raise ApiError(404, "photo_not_found", "找不到這張照片")
        # 照片上的祝福顯示在上傳者名字下方，看起來就是上傳者說的，所以只有上傳者自己能掛
        if photo.uploader_id != g.guest.id:
            raise ApiError(403, "not_your_photo", "只能在自己上傳的照片附上祝福")

    blessing = Blessing(guest_id=g.guest.id, text=text, photo_id=photo_id)
    db.session.add(blessing)
    db.session.commit()
    return jsonify(blessing.to_json()), 201


@bp.patch("/blessings/<blessing_id>")
@require_guest
def update_blessing(blessing_id: str):
    """修改內容。只改文字，不能換掛的照片。"""
    blessing = _my_blessing(blessing_id)
    text = _clean_text(_json_body().get("text"))
    if text != blessing.text:
        blessing.text = text
        blessing.edited_at = now()
        db.session.commit()
    return jsonify(blessing.to_json())


@bp.delete("/blessings/<blessing_id>")
@require_guest
def delete_blessing(blessing_id: str):
    db.session.delete(_my_blessing(blessing_id))
    db.session.commit()
    return "", 204
