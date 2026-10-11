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
from app.auth import new_token
from app.db import db
from app.models import Guest, Photo, now

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
    (0, 3, 4, "welcome"),
    (1, 4, 5, "welcome"),
    (2, 1, 1, "ceremony"),
    (3, 4, 3, "ceremony"),
    (4, 3, 4, "ceremony"),
    (2, 3, 4, "ceremony"),
    (5, 4, 5, "banquet"),
    (6, 1, 1, "banquet"),
    (7, 3, 4, "banquet"),
    (2, 4, 3, "banquet"),
    (0, 4, 5, "banquet"),
    (1, 3, 2, "banquet"),
]

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
        token, token_hash = new_token()
        guest = Guest(nickname=nickname, relation=relation, token_hash=token_hash)
        db.session.add(guest)
        guests.append(guest)
        tokens.append((nickname, token))
    db.session.flush()

    # 最早的一張在 2 小時前，之後每 10 分鐘一張
    started = now() - timedelta(hours=2)
    for i, (guest_index, w, h, tag) in enumerate(PHOTOS):
        width, height = _size(w, h)
        image = _gradient(width, height, GRADIENTS[i % len(GRADIENTS)])

        photo = Photo(
            uploader=guests[guest_index],
            tag=tag,
            width=width,
            height=height,
            uploaded_at=started + timedelta(minutes=10 * i),
            original_key="",
            thumb_key="",
        )
        db.session.add(photo)
        db.session.flush()  # 拿到 photo.id 才能決定檔名

        photo.original_key = f"photos/{photo.id}/original.jpg"
        photo.thumb_key = f"photos/{photo.id}/thumb.jpg"
        storage.save(photo.original_key, images.to_jpeg(image))
        storage.save(photo.thumb_key, images.make_thumbnail(image))

    db.session.commit()

    click.echo(f"建立了 {len(guests)} 位賓客、{len(PHOTOS)} 張照片。")
    click.echo(f"照片檔在 {storage.media_dir()}")
    click.echo("")
    click.echo("測試用 token（打 API 時放在 Authorization: Bearer <token>）：")
    for nickname, token in tokens[:2]:
        click.echo(f"  {nickname}：{token}")
