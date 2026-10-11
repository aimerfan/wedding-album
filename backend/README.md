# backend

Python 3.14 + Flask。API 規格寫在 [docs/api.md](../docs/api.md)（目前是草稿）。

## 環境需求

Python 3.14。套件用 pip + `requirements.txt` 管理。

## 第一次設定

以下指令都在 `backend/` 底下執行（Windows）：

```bash
py -3.14 -m venv .venv
```

啟動虛擬環境（Git Bash 用 `source .venv/Scripts/activate`，cmd 用 `.venv\Scripts\activate`），再安裝套件：

```bash
pip install -r requirements-dev.txt
```

| 指令 | 用途 |
| --- | --- |
| `flask --app app run --debug` | 開發伺服器（http://localhost:5000），改程式會自動重啟 |
| `pytest` | 跑全部測試 |

## 結構

```
backend/
├── app/
│   ├── __init__.py    # create_app()：組裝 Flask app
│   ├── config.py      # 設定與各種上限，都可用環境變數覆蓋
│   ├── errors.py      # 錯誤一律回 { "error": { code, message } }
│   ├── db.py          # 資料庫連線
│   ├── models.py      # 資料表
│   ├── auth.py        # 發 token、驗 token（@require_guest）
│   └── api/           # 一類功能一個模組，都掛在 /api 底下
├── tests/
├── requirements.txt       # 正式環境的套件
└── requirements-dev.txt   # 開發用（pytest 等），會連同 requirements.txt 一起裝
```

## 設定（環境變數）

| 名稱 | 預設 | 說明 |
| --- | --- | --- |
| `EVENT_CODE` | 開發時為 `dev` | QR code 網址裡的活動碼。**正式環境沒設會拒絕啟動** |
| `DATABASE_URL` | `sqlite:///wedding.db` | 相對路徑放在 `instance/` 底下 |

各種上限（同時上傳數、檔案大小、截止上傳）也都能用環境變數調整，名稱見 `app/config.py`。

## 資料庫

- 開發用的資料庫在 `instance/wedding.db`，已被 git 忽略。
- 啟動時會自動建立還不存在的資料表，但**不會修改已存在的資料表**。
  改了 `app/models.py` 既有的欄位後，刪掉 `instance/wedding.db` 再啟動即可（開發資料會一起清掉）。
- 正式上線前會加上 migration 工具，屆時改欄位就不必刪資料庫。

## 慣例

- **新增套件**：寫進 `requirements.txt`（開發才用的寫進 `requirements-dev.txt`），用 `==` 釘死版本，
  上方加一行註解說明用途。不要用 `pip freeze` 整包倒進去，會分不清哪些是自己要的。
- **改了程式就跑 `pytest`**。這個 repo 沒有 CI，測試是後端唯一的把關。

## 已定

- **資料庫**：SQLite（透過 SQLAlchemy 存取，之後要換 PostgreSQL 改動很小）。
- **上傳**：照片先傳給 Flask，再由 Flask 存檔。不讓手機直接傳到雲端儲存。
- **照片網址**：一律由 API 回傳，前端不自己組網址。
- **存檔**：包成獨立的一層。開發時存本機磁碟，之後換雲端只換這一層。
- **進入相簿**：會場提供 QR code。
- **賓客身分**：第一次進來時由後端發一個匿名代號，存在手機裡。不做帳號密碼。
  換手機或清除瀏覽器資料會變成新的賓客，這是刻意接受的取捨。

## 待決

- 正式環境的相片儲存（研究中，候選 AWS S3 等物件儲存）

`frontend/src/types/album.ts` 描述了前端目前假設的資料形狀，但那是前端單方面寫的，
不是雙方談好的 API 規格——要當規格用之前先確認。
