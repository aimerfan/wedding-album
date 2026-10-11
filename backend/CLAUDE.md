@README.md

## 給 agent 的額外規則

- 套件管理維持 pip + `requirements.txt`。不要建立 `pyproject.toml`、`uv.lock`、`Pipfile`、`poetry.lock`，
  也不要建議改用 uv 或 poetry（使用者已經決定過）。
- 不要加 ruff、black、flake8 這類格式／風格檢查工具，使用者決定先不用。
- 改動 `app/` 之後要跑 `pytest`，結果要回報給使用者。
