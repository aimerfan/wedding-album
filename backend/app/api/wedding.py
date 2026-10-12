"""婚紗集：新人的婚紗照，一串，不分系列、不分頁。"""

from flask import jsonify

from app.api import bp
from app.auth import require_guest
from app.db import db
from app.models import WeddingPhoto


@bp.get("/wedding-photos")
@require_guest
def list_wedding_photos():
    photos = db.session.scalars(db.select(WeddingPhoto).order_by(WeddingPhoto.position)).all()
    return jsonify({"items": [p.to_json() for p in photos]})
