"""錯誤一律回成 docs/api.md 規定的形狀：

    { "error": { "code": "...", "message": "..." } }

code 給前端程式判斷，message 可以直接顯示給賓客。
"""

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

# Flask 內建錯誤（例如打錯網址的 404）沒有中文訊息，這裡補上預設值
_DEFAULT_MESSAGES = {
    400: "請求的內容有誤",
    401: "請重新從會場的 QR code 進入",
    403: "你沒有權限做這件事",
    404: "找不到這個東西",
    405: "不支援這個操作",
    413: "檔案太大了",
    415: "不支援這種檔案格式",
    429: "操作太頻繁，請稍後再試",
    500: "伺服器出了點問題，請稍後再試",
    501: "這個功能還沒做好",
}


class ApiError(Exception):
    """在路由裡 raise 這個，就會回傳指定的錯誤。

    raise ApiError(404, "photo_not_found", "找不到這張照片")
    """

    def __init__(self, status: int, code: str, message: str | None = None):
        super().__init__(code)
        self.status = status
        self.code = code
        self.message = message or _DEFAULT_MESSAGES.get(status, "發生錯誤")


def _body(status: int, code: str, message: str):
    return jsonify({"error": {"code": code, "message": message}}), status


def register(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(e: ApiError):
        return _body(e.status, e.code, e.message)

    @app.errorhandler(HTTPException)
    def handle_http_error(e: HTTPException):
        status = e.code or 500
        # Werkzeug 的名稱是 "Not Found" 這種格式，轉成 not_found
        code = (e.name or "error").lower().replace(" ", "_")
        return _body(status, code, _DEFAULT_MESSAGES.get(status, "發生錯誤"))

    @app.errorhandler(Exception)
    def handle_unexpected(e: Exception):
        # 不把錯誤細節露給賓客；細節留在伺服器的 log 裡
        app.logger.exception(e)
        return _body(500, "internal_error", _DEFAULT_MESSAGES[500])
