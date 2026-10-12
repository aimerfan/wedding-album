"""資料庫連線。所有 model 都繼承這裡的 db.Model。"""

import sqlite3

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase

# 婚宴高峰會有很多人同時上傳，正式環境又是多個 worker 共用一個 SQLite 檔
BUSY_TIMEOUT_MS = 15_000


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


@event.listens_for(Engine, "connect")
def _sqlite_pragmas(dbapi_conn, _record) -> None:
    """WAL：有人在寫入時，其他人還是可以讀（滑相簿不會被上傳卡住）。
    busy_timeout：同時有兩個寫入時，後到的等前一個寫完，而不是馬上回 database is locked。"""
    if not isinstance(dbapi_conn, sqlite3.Connection):
        return
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
    cursor.close()
