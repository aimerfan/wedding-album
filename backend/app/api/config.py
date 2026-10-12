"""設定：GET /api/config（前端要遵守的各種上限），以及管理員在 app 裡改的設定。"""

from flask import current_app, g, jsonify, request

from app.api import bp
from app.auth import require_guest
from app.db import db
from app.errors import ApiError
from app.models import Setting

KAHOOT_KEY = "kahoot_url"
URL_MAX = 500


@bp.get("/config")
def get_config():
    """不需要 token：歡迎頁（還沒加入）也要用到，例如 Kahoot! 連結。"""
    c = current_app.config
    kahoot = db.session.get(Setting, KAHOOT_KEY)
    return jsonify(
        {
            "maxPhotoBytes": c["MAX_PHOTO_BYTES"],
            "maxVideoBytes": c["MAX_VIDEO_BYTES"],
            "maxUploadsPerHour": c["MAX_UPLOADS_PER_HOUR"],
            "uploadConcurrency": c["UPLOAD_CONCURRENCY"],
            "maxBlessingLength": c["MAX_BLESSING_LENGTH"],
            "uploadsOpen": c["UPLOADS_OPEN"],
            # 婚禮當天主持人開了遊戲才知道連結，所以由管理員在 app 裡設定；沒設是 null
            "kahootUrl": kahoot.value if kahoot else None,
        }
    )


@bp.put("/settings/kahoot")
@require_guest
def set_kahoot_url():
    """管理員設定 Kahoot! 連結。url 傳空字串或 null 代表拿掉（按鈕就不顯示）。"""
    if not g.guest.is_admin:
        raise ApiError(403, "not_admin", "只有管理員可以修改")
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ApiError(400, "invalid_body", "請求內容必須是 JSON 物件")

    raw = body.get("url")
    url = raw.strip() if isinstance(raw, str) else ""
    existing = db.session.get(Setting, KAHOOT_KEY)

    if not url:
        if existing:
            db.session.delete(existing)
        db.session.commit()
        return jsonify({"kahootUrl": None})

    # 只收網址：這個值會變成所有人都看得到的按鈕連結，不能是 javascript: 之類的東西
    if not url.lower().startswith(("https://", "http://")) or len(url) > URL_MAX:
        raise ApiError(400, "invalid_url", "請貼上以 https:// 開頭的完整連結")

    if existing:
        existing.value = url
    else:
        db.session.add(Setting(key=KAHOOT_KEY, value=url))
    db.session.commit()
    return jsonify({"kahootUrl": url})
