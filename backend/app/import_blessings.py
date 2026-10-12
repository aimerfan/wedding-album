"""預先匯入祝福留言：flask import-blessings 檔案.csv

婚禮前收到的祝福（例如卡片、訊息）整理成 CSV 後匯入，會出現在留言牆上。
正式環境也會用到，所以不像 seed 那樣限制開發模式。

CSV 格式（第一列是標題，欄位名稱中英文都可以）：

    名字,祝福,關係
    阿凱,祝你們白頭偕老！,新郎的大學室友
    美玲阿姨,新婚快樂,

- 「名字」「祝福」必填，「關係」可留空或整欄省略。
- 用 Excel 存成「CSV UTF-8」即可，開頭的 BOM 會自動處理。
- 檔案裡的順序就是留言牆上的順序（第一列在最上面）。
- 重複匯入同一個檔案不會重複新增：同一個名字已經有一模一樣的祝福就跳過。

作者不是透過 app 加入的賓客，沒有 token，不能登入。之後同名的人用手機加入，會是另一位賓客。
"""

import csv
from datetime import timedelta

import click
from flask.cli import with_appcontext

from app.db import db
from app.models import NICKNAME_MAX, RELATION_MAX, Blessing, Guest, now

# 預先寫好的祝福可能比 app 裡的上限長（例如整張卡片），放寬到資料表欄位的長度
IMPORT_TEXT_MAX = 1000

COLUMNS = {
    "nickname": ("名字", "暱稱", "name", "nickname"),
    "text": ("祝福", "內容", "text", "blessing"),
    "relation": ("關係", "與新人的關係", "relation"),
}


def _find_columns(header: list[str]) -> dict[str, int]:
    normalized = [h.strip().lower() for h in header]
    found = {}
    for key, names in COLUMNS.items():
        for name in names:
            if name.lower() in normalized:
                found[key] = normalized.index(name.lower())
                break
    missing = [COLUMNS[k][0] for k in ("nickname", "text") if k not in found]
    if missing:
        raise click.ClickException(f"CSV 第一列找不到欄位：{'、'.join(missing)}（目前是：{header}）")
    return found


@click.command("import-blessings")
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.option("--dry-run", is_flag=True, help="只檢查、列出會匯入什麼，不寫進資料庫")
@with_appcontext
def import_blessings_command(path: str, dry_run: bool):
    """從 CSV 匯入預先收到的祝福留言。"""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        raise click.ClickException("檔案是空的")

    cols = _find_columns(rows[0])
    data_rows = rows[1:]

    def cell(row: list[str], key: str) -> str:
        i = cols.get(key)
        return row[i].strip() if i is not None and i < len(row) else ""

    # 先全部檢查過，有錯就整批不匯入，不會只匯一半
    entries = []
    errors = []
    for line_no, row in enumerate(data_rows, start=2):
        if not any(c.strip() for c in row):
            continue  # 空白列
        nickname, text, relation = cell(row, "nickname"), cell(row, "text"), cell(row, "relation")
        if not nickname:
            errors.append(f"第 {line_no} 列：沒有名字")
        elif len(nickname) > NICKNAME_MAX:
            errors.append(f"第 {line_no} 列：名字超過 {NICKNAME_MAX} 字")
        if not text:
            errors.append(f"第 {line_no} 列：沒有祝福內容")
        elif len(text) > IMPORT_TEXT_MAX:
            errors.append(f"第 {line_no} 列：祝福超過 {IMPORT_TEXT_MAX} 字")
        if len(relation) > RELATION_MAX:
            errors.append(f"第 {line_no} 列：關係超過 {RELATION_MAX} 字")
        entries.append((nickname, text, relation or None))
    if errors:
        raise click.ClickException("檔案有問題，沒有匯入任何資料：\n" + "\n".join(errors))

    # 同名的匯入作者共用一筆賓客資料；app 裡的賓客不會被拿來用
    authors: dict[str, Guest] = {
        g.nickname: g
        for g in db.session.scalars(db.select(Guest).where(Guest.imported.is_(True)))
    }

    created = skipped = 0
    base = now()
    for i, (nickname, text, relation) in enumerate(entries):
        author = authors.get(nickname)
        if author is not None and db.session.scalar(
            db.select(Blessing).where(Blessing.guest_id == author.id, Blessing.text == text)
        ):
            skipped += 1
            continue
        if author is None:
            author = Guest(nickname=nickname, relation=relation, imported=True)
            db.session.add(author)
            authors[nickname] = author
        # 留言牆新的在上面：第一列的時間最晚，才會排在最上面
        db.session.add(Blessing(guest=author, text=text, created_at=base - timedelta(seconds=i)))
        created += 1
        click.echo(f"  {nickname}：{text[:30]}{'…' if len(text) > 30 else ''}")

    if dry_run:
        db.session.rollback()
        click.echo(f"（預覽）會匯入 {created} 則，跳過 {skipped} 則已存在的。沒有寫進資料庫。")
    else:
        db.session.commit()
        click.echo(f"匯入了 {created} 則祝福，跳過 {skipped} 則已存在的。")
