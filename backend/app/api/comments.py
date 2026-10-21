"""照片下的留言：任何賓客都能留，作者可以改、刪，管理員可以刪任何一則。"""

from flask import current_app, g, jsonify, request

from app.api import bp
from app.api.photos import get_visible_photo
from app.auth import require_guest
from app.db import db
from app.errors import ApiError
from app.models import Comment, now


def _clean_text(raw: object) -> str:
    """前後空白去掉；只有空白也算沒寫。"""
    text = raw.strip() if isinstance(raw, str) else ""
    if not text:
        raise ApiError(400, "text_required", "請寫下留言內容")
    limit = current_app.config["MAX_COMMENT_LENGTH"]
    if len(text) > limit:
        raise ApiError(400, "text_too_long", f"留言最多 {limit} 個字")
    return text


def _body_text() -> str:
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ApiError(400, "invalid_body", "請求內容必須是 JSON 物件")
    return _clean_text(body.get("text"))


def _my_comment(comment_id: str, allow_admin: bool = False) -> Comment:
    """只能改、刪自己的留言；allow_admin 時管理員也可以（刪除用，管理員不能改別人的內容）。"""
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        raise ApiError(404, "comment_not_found", "找不到這則留言")
    if comment.guest_id != g.guest.id and not (allow_admin and g.guest.is_admin):
        raise ApiError(403, "not_your_comment", "只能修改自己的留言")
    return comment


@bp.get("/photos/<photo_id>/comments")
@require_guest
def list_comments(photo_id: str):
    """一張照片的所有留言，舊的在前（像聊天一樣往下接）。

    一張照片的留言不會多到需要分頁，一次全部回傳。
    """
    photo = get_visible_photo(photo_id)
    comments = db.session.scalars(
        db.select(Comment)
        .where(Comment.photo_id == photo.id)
        .order_by(Comment.created_at, Comment.id)
    ).all()
    return jsonify({"items": [c.to_json() for c in comments]})


@bp.post("/photos/<photo_id>/comments")
@require_guest
def create_comment(photo_id: str):
    """截止上傳後也可以留言：截止只是不再收新的檔案。"""
    photo = get_visible_photo(photo_id)
    comment = Comment(photo_id=photo.id, guest_id=g.guest.id, text=_body_text())
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_json()), 201


@bp.patch("/comments/<comment_id>")
@require_guest
def update_comment(comment_id: str):
    """修改內容，只能改文字。內容沒變時不算修改。"""
    comment = _my_comment(comment_id)
    text = _body_text()
    if text != comment.text:
        comment.text = text
        comment.edited_at = now()
        db.session.commit()
    return jsonify(comment.to_json())


@bp.delete("/comments/<comment_id>")
@require_guest
def delete_comment(comment_id: str):
    db.session.delete(_my_comment(comment_id, allow_admin=True))
    db.session.commit()
    return "", 204
