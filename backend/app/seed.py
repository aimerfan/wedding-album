"""開發用的測試資料：flask seed

建立幾位賓客與十幾張漸層色的測試照片，讓前端接上 API 時有東西可看。
只用在開發環境，正式環境不要執行。
"""

import shutil
from datetime import timedelta

import click
from flask import current_app
from flask.cli import with_appcontext
from PIL import Image, ImageChops

from app import images, storage
from app.auth import issue_token
from app.db import db
from app.models import Blessing, Guest, Like, Photo, WeddingPhoto, now

# (暱稱, 與新人的關係)
GUESTS = [
    ("小慧", "新娘的大學同學"),
    ("阿凱", "新郎的大學室友"),
    ("婷婷", None),
    ("志明", None),
    ("美玲阿姨", "新娘的阿姨"),
    ("建宏", None),
    ("佳穎", None),
    ("俊豪", None),
]

# (上傳者在 GUESTS 的位置, 寬, 高, 分類)。順序就是上傳的先後
PHOTOS = [
    (0, 3, 4, "engagement"),
    (1, 4, 5, "engagement"),
    (2, 1, 1, "engagement"),
    (3, 4, 3, "engagement"),
    (4, 3, 4, "engagement"),
    (2, 3, 4, "engagement"),
    (5, 4, 5, "banquet"),
    (6, 1, 1, "banquet"),
    (7, 3, 4, "banquet"),
    (2, 4, 3, "banquet"),
    (0, 4, 5, "banquet"),
    (1, 3, 2, "banquet"),
]

# 照片說明：{第幾張照片: 說明}，說明是上傳者寫的
CAPTIONS = {
    1: "俊鴻是我大學最好的兄弟，一路看著他追到鈺婷。今天看到你們穿上禮服，眼淚差點掉下來。祝你們白頭偕老！",
    7: "新娘進場的那一刻 ♥",
}

# (作者在 GUESTS 的位置, 祝福)
BLESSINGS = [
    (4, "從小看著婷婷長大，今天看到她當新娘真的好美。願你們的婚姻甜甜蜜蜜，早生貴子。"),
    (3, "恭喜恭喜！"),
    (6, "兩個人在一起的樣子真好看。 ♥"),
]

# (按讚的人在 GUESTS 的位置, 第幾張照片)
LIKES = [(0, 1), (2, 1), (3, 1), (5, 1), (0, 2), (4, 6), (6, 6)]

# 婚紗集的測試照片 (寬, 高)。真的婚紗照用 flask import-wedding 匯入
WEDDING = [(3, 2), (3, 4), (1, 1), (1, 1), (3, 2), (3, 4), (1, 1), (1, 1)]

# 跟前端 PhotoTile 的佔位漸層同一組顏色
GRADIENTS = [
    ("#E8D4C8", "#C9A48E"),
    ("#D4B8A8", "#A88876"),
    ("#EAD9C5", "#C2A179"),
    ("#D9C2B0", "#A88562"),
    ("#E5D0BE", "#B8967A"),
    ("#DBC5B2", "#9C7E68"),
    ("#EFDFC9", "#C49E7C"),
    ("#E0CAB8", "#A8836A"),
    ("#E8D8C5", "#BC9778"),
    ("#D6BCA9", "#9D7B62"),
]

# 原圖長邊。真實照片會更大，測試資料不需要
ORIGINAL_LONG_EDGE = 1600


def _gradient(width: int, height: int, colors: tuple[str, str]) -> Image.Image:
    start = Image.new("RGB", (width, height), colors[0])
    end = Image.new("RGB", (width, height), colors[1])
    # 垂直漸層加上轉 90 度的水平漸層，得到左上淺、右下深的斜向漸層（同前端的 135deg）
    vertical = Image.linear_gradient("L")
    mask = ImageChops.add(vertical, vertical.rotate(90), scale=2.0).resize((width, height))
    return Image.composite(end, start, mask)


def _size(w_ratio: int, h_ratio: int) -> tuple[int, int]:
    scale = ORIGINAL_LONG_EDGE / max(w_ratio, h_ratio)
    return round(w_ratio * scale), round(h_ratio * scale)


@click.command("seed")
@click.option("--reset", is_flag=True, help="先清空所有賓客、照片與照片檔")
@with_appcontext
def seed_command(reset: bool):
    """建立開發用的測試賓客與照片。"""
    # --reset 會清掉所有賓客的照片，正式環境絕對不能跑
    if not current_app.debug:
        raise click.ClickException("seed 只能在開發模式執行（在 backend/ 底下用 flask 指令會自動進入）")

    if reset:
        db.drop_all()
        db.create_all()
        shutil.rmtree(storage.media_dir(), ignore_errors=True)
    elif db.session.scalar(db.select(Photo).limit(1)):
        raise click.ClickException("已經有照片了。要重建請加 --reset（會清掉所有資料）")

    tokens = []
    guests = []
    for nickname, relation in GUESTS:
        guest = Guest(nickname=nickname, relation=relation)
        db.session.add(guest)
        token = issue_token(guest)
        guests.append(guest)
        tokens.append((nickname, token))
    db.session.flush()

    # 最早的一張在 2 小時前，之後每 10 分鐘一張
    started = now() - timedelta(hours=2)
    photos = []
    for i, (guest_index, w, h, tag) in enumerate(PHOTOS):
        width, height = _size(w, h)
        image = _gradient(width, height, GRADIENTS[i % len(GRADIENTS)])

        photo = Photo(
            uploader=guests[guest_index],
            tag=tag,
            caption=CAPTIONS.get(i),
            width=width,
            height=height,
            uploaded_at=started + timedelta(minutes=10 * i),
            original_key="",
            display_key="",
            thumb_key="",
        )
        db.session.add(photo)
        photos.append(photo)
        db.session.flush()  # 拿到 photo.id 才能決定檔名

        photo.original_key = f"photos/{photo.id}/original.jpg"
        # 測試用的原圖本來就只有 1600px，顯示用的直接用原圖
        photo.display_key = photo.original_key
        photo.thumb_key = f"photos/{photo.id}/thumb.jpg"
        storage.save(photo.original_key, images.to_jpeg(image))
        storage.save(photo.thumb_key, images.make_thumbnail(image))

    for i, (guest_index, text) in enumerate(BLESSINGS):
        db.session.add(
            Blessing(
                guest=guests[guest_index],
                text=text,
                # 第一則最新
                created_at=now() - timedelta(minutes=5 * i),
            )
        )
    for guest_index, photo_index in LIKES:
        db.session.add(Like(guest_id=guests[guest_index].id, photo_id=photos[photo_index].id))

    for i, (w, h) in enumerate(WEDDING):
        width, height = _size(w, h)
        image = _gradient(width, height, GRADIENTS[(i + 3) % len(GRADIENTS)])
        wedding = WeddingPhoto(
            filename=f"{i + 1:02}.jpg",
            position=i,
            width=width,
            height=height,
            display_key="",
            thumb_key="",
        )
        db.session.add(wedding)
        db.session.flush()
        wedding.display_key = f"wedding/{wedding.id}/display.jpg"
        wedding.thumb_key = f"wedding/{wedding.id}/thumb.jpg"
        storage.save(wedding.display_key, images.to_jpeg(image))
        storage.save(wedding.thumb_key, images.make_thumbnail(image))

    db.session.commit()

    click.echo(
        f"建立了 {len(guests)} 位賓客、{len(PHOTOS)} 張照片、{len(BLESSINGS)} 則祝福、"
        f"{len(LIKES)} 個讚、{len(WEDDING)} 張婚紗照。"
    )
    click.echo(f"照片檔在 {storage.media_dir()}")
    click.echo("")
    click.echo("測試用 token（打 API 時放在 Authorization: Bearer <token>）：")
    for nickname, token in tokens[:2]:
        click.echo(f"  {nickname}：{token}")
