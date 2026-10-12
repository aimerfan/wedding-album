"""匯入婚紗照：flask import-wedding 資料夾

把新人的婚紗照（約 60 張）放在同一個資料夾，執行一次就會產生顯示用與縮圖、寫進資料庫。
正式環境也會用到，所以不限制開發模式。

- 顯示順序依檔名，數字照大小排：2.jpg 會排在 10.jpg 前面。建議用 01.jpg、02.jpg 這樣命名。
- 只讀資料夾第一層的照片（JPEG、PNG、HEIC、WebP），子資料夾與其他檔案會略過。
- 重複匯入同一個資料夾，已經匯過的檔名會跳過，只加入新的；順序會依全部檔名重新排。
- 加 --replace 會先刪掉所有已匯入的婚紗照再重來（例如換了一批照片）。
- 原檔不會保存：婚紗集僅供觀賞，新人手上本來就有原檔。
"""

import os
import re

import click
from flask.cli import with_appcontext

from app import images, storage
from app.db import db
from app.models import WeddingPhoto

EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"}


def natural_key(filename: str) -> list:
    """「2.jpg」排在「10.jpg」前面：把檔名裡的數字當數字比，其餘當文字比（不分大小寫）。"""
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", filename)]


def _renumber() -> None:
    photos = db.session.scalars(db.select(WeddingPhoto)).all()
    for position, photo in enumerate(sorted(photos, key=lambda p: natural_key(p.filename))):
        photo.position = position


@click.command("import-wedding")
@click.argument("folder", type=click.Path(exists=True, file_okay=False))
@click.option("--replace", is_flag=True, help="先刪掉所有已匯入的婚紗照再匯入")
@click.option("--dry-run", is_flag=True, help="只列出會匯入哪些檔案，不處理也不寫入")
@with_appcontext
def import_wedding_command(folder: str, replace: bool, dry_run: bool):
    """從資料夾匯入婚紗照。"""
    names = sorted(
        (
            name
            for name in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, name))
            and os.path.splitext(name)[1].lower() in EXTENSIONS
        ),
        key=natural_key,
    )
    if not names:
        raise click.ClickException(f"{folder} 裡沒有可以匯入的照片（JPEG、PNG、HEIC、WebP）")

    existing = {p.filename for p in db.session.scalars(db.select(WeddingPhoto))}
    if replace:
        existing = set()
    todo = [n for n in names if n not in existing]

    if dry_run:
        for name in todo:
            click.echo(f"  {name}")
        note = "（會先刪掉現有的）" if replace else ""
        click.echo(f"（預覽）會匯入 {len(todo)} 張{note}，跳過 {len(names) - len(todo)} 張已匯入的。")
        return

    # 先把每張都處理好，有任何一張讀不了就整批不匯入
    processed = []
    errors = []
    with click.progressbar(todo, label="處理照片", show_pos=True) as bar:
        for name in bar:
            with open(os.path.join(folder, name), "rb") as f:
                data = f.read()
            try:
                processed.append((name, images.process_upload(data)))
            except images.UnsupportedImage:
                errors.append(name)
    if errors:
        raise click.ClickException("這些檔案讀不了，沒有匯入任何照片：\n" + "\n".join(errors))

    if replace:
        for old in db.session.scalars(db.select(WeddingPhoto)):
            storage.delete(old.display_key)
            storage.delete(old.thumb_key)
            db.session.delete(old)
        db.session.flush()

    for name, result in processed:
        photo = WeddingPhoto(
            filename=name,
            position=0,
            width=result.width,
            height=result.height,
            display_key="",
            thumb_key="",
        )
        db.session.add(photo)
        db.session.flush()  # 拿到 photo.id 才能決定檔名
        photo.display_key = f"wedding/{photo.id}/display.jpg"
        photo.thumb_key = f"wedding/{photo.id}/thumb.jpg"
        storage.save(photo.display_key, result.display_jpeg)
        storage.save(photo.thumb_key, result.thumb_jpeg)

    _renumber()
    db.session.commit()
    total = db.session.query(WeddingPhoto).count()
    click.echo(f"匯入了 {len(processed)} 張，跳過 {len(names) - len(processed)} 張已匯入的。婚紗集共 {total} 張。")
