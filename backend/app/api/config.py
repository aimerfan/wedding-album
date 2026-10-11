"""GET /api/config：前端要遵守的各種上限。不需要 token。"""

from flask import current_app, jsonify

from app.api import bp


@bp.get("/config")
def get_config():
    c = current_app.config
    return jsonify(
        {
            "maxPhotoBytes": c["MAX_PHOTO_BYTES"],
            "maxVideoBytes": c["MAX_VIDEO_BYTES"],
            "maxUploadsPerHour": c["MAX_UPLOADS_PER_HOUR"],
            "uploadConcurrency": c["UPLOAD_CONCURRENCY"],
            "maxBlessingLength": c["MAX_BLESSING_LENGTH"],
            "uploadsOpen": c["UPLOADS_OPEN"],
        }
    )
