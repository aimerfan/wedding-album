"""圖片處理。縮圖規格只定義在這裡，上傳與測試資料共用。"""

import io

from PIL import Image

# 縮圖長邊的像素數。列表一律載縮圖，兩欄瀑布流在手機上每格約 180px 寬，
# 乘上高解析度螢幕的 2～3 倍，480 足夠清楚
THUMB_LONG_EDGE = 480
JPEG_QUALITY = 85


def to_jpeg(image: Image.Image, quality: int = JPEG_QUALITY) -> bytes:
    buf = io.BytesIO()
    image.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def make_thumbnail(image: Image.Image) -> bytes:
    thumb = image.copy()
    # thumbnail() 會等比縮小、不會放大
    thumb.thumbnail((THUMB_LONG_EDGE, THUMB_LONG_EDGE))
    return to_jpeg(thumb)
