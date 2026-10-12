"""圖片處理。尺寸規格只定義在這裡，上傳與測試資料共用。

每張上傳的照片存三份：
- 原檔：原封不動，之後整批匯出給新人用
- 顯示用：長邊 1600px 的 JPEG，照片詳情頁用。原檔動輒 5～10 MB，會場網路載不動
- 縮圖：長邊 480px 的 JPEG，列表用
"""

import io
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone

import pillow_heif
from PIL import Image, ImageOps, UnidentifiedImageError

# 讓 Pillow 讀得懂 iPhone 的 HEIC
pillow_heif.register_heif_opener()

# 兩欄瀑布流在手機上每格約 180px 寬，乘上高解析度螢幕的 2～3 倍，480 足夠清楚
THUMB_LONG_EDGE = 480
# 手機全螢幕看照片，1600 在高解析度螢幕上也夠清楚
DISPLAY_LONG_EDGE = 1600
JPEG_QUALITY = 85

# Pillow 認出的格式 → 原檔的副檔名。MPO 是部分手機拍的 JPEG（內含多張），一樣當 JPEG
ACCEPTED_FORMATS = {"JPEG": "jpg", "MPO": "jpg", "PNG": "png", "WEBP": "webp", "HEIF": "heic"}

# EXIF 裡沒寫時區時，當成台灣時間（婚禮在台灣拍的）
_LOCAL_TZ = timezone(timedelta(hours=8))

_EXIF_IFD = 0x8769
_DATETIME_ORIGINAL = 36867
_OFFSET_TIME_ORIGINAL = 36881
_DATETIME = 306


class UnsupportedImage(Exception):
    """不是照片、壞掉的檔案，或不支援的格式。"""


@dataclass
class ProcessedImage:
    extension: str
    width: int
    height: int
    # 不帶時區的 UTC，讀不到就是 None
    taken_at: datetime | None
    display_jpeg: bytes
    thumb_jpeg: bytes


def to_jpeg(image: Image.Image, quality: int = JPEG_QUALITY) -> bytes:
    buf = io.BytesIO()
    image.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def _resized_jpeg(image: Image.Image, long_edge: int) -> bytes:
    copy = image.copy()
    # thumbnail() 會等比縮小、不會放大
    copy.thumbnail((long_edge, long_edge))
    return to_jpeg(copy)


def make_thumbnail(image: Image.Image) -> bytes:
    return _resized_jpeg(image, THUMB_LONG_EDGE)


def make_display(image: Image.Image) -> bytes:
    return _resized_jpeg(image, DISPLAY_LONG_EDGE)


def _taken_at(image: Image.Image) -> datetime | None:
    exif = image.getexif()
    ifd = exif.get_ifd(_EXIF_IFD)
    raw = ifd.get(_DATETIME_ORIGINAL) or exif.get(_DATETIME)
    if not isinstance(raw, str):
        return None
    try:
        local = datetime.strptime(raw.strip(), "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None

    tz = _LOCAL_TZ
    offset = ifd.get(_OFFSET_TIME_ORIGINAL)
    if isinstance(offset, str):
        try:
            tz = datetime.strptime(offset.strip(), "%z").tzinfo or _LOCAL_TZ
        except ValueError:
            pass
    return local.replace(tzinfo=tz).astimezone(UTC).replace(tzinfo=None)


def process_upload(data: bytes) -> ProcessedImage:
    try:
        image = Image.open(io.BytesIO(data))
        extension = ACCEPTED_FORMATS.get(image.format or "")
        if extension is None:
            raise UnsupportedImage(image.format)
        taken_at = _taken_at(image)
        # 手機直拍的照片，像素其實是橫的，靠 EXIF 記錄要轉幾度。轉正之後尺寸才是對的
        upright = ImageOps.exif_transpose(image)
        upright.load()
    # 壞掉的 HEIC，pillow-heif 會依壞的地方丟 ValueError 或 EOFError，不是 OSError
    except (UnidentifiedImageError, OSError, ValueError, EOFError, Image.DecompressionBombError) as e:
        raise UnsupportedImage(str(e)) from e

    return ProcessedImage(
        extension=extension,
        width=upright.width,
        height=upright.height,
        taken_at=taken_at,
        display_jpeg=make_display(upright),
        thumb_jpeg=make_thumbnail(upright),
    )
