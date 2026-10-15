"""PWA 的 manifest：GET /api/manifest?code=<活動碼>。

iPhone 從主畫面打開時，網址就是 manifest 的 start_url，而且主畫面 app 讀不到 Safari 存下的活動碼。
所以前端有活動碼時改用這份 manifest，讓 start_url 帶上 ?code=，從主畫面打開也能加入相簿。

內容要跟前端 vite.config.ts 裡的 manifest 一致，只有 start_url 不同；改一邊要改另一邊。
"""

from urllib.parse import urlencode

from flask import jsonify, request

from app.api import bp
from app.auth import check_event_code
from app.errors import ApiError


@bp.get("/manifest")
def get_manifest():
    """不需要 token。活動碼正確才放進 start_url，錯的或沒帶就跟前端的靜態 manifest 一樣。"""
    code = request.args.get("code", "")
    try:
        check_event_code(code)
        start_url = "/?" + urlencode({"code": code})
    except ApiError:
        start_url = "/"

    res = jsonify(
        {
            # 固定 id：start_url 帶不帶活動碼，都是同一個 app
            "id": "/",
            "name": "婚禮相簿",
            "short_name": "婚禮相簿",
            "description": "婚禮相片分享相簿",
            "lang": "zh-Hant",
            "display": "standalone",
            "start_url": start_url,
            "scope": "/",
            "theme_color": "#FAF6F0",
            "background_color": "#FAF6F0",
            # 這份 manifest 在 /api/ 底下，圖示要寫絕對路徑
            "icons": [
                {"src": "/pwa-192x192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/pwa-512x512.png", "sizes": "512x512", "type": "image/png"},
                {
                    "src": "/pwa-maskable-512x512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "maskable",
                },
            ],
        }
    )
    res.mimetype = "application/manifest+json"
    res.headers["Cache-Control"] = "no-cache"
    return res
