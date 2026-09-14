@README.md

## 給 agent 的額外規則

- 不要在根目錄建立 `package.json`、`.nvmrc` 這類綁定特定技術棧的檔案。
- 後端尚未選型。不要在 `backend/` 建立任何語言專屬的骨架、設定檔或 `.gitignore`。
- `frontend/src/types/album.ts` 是前端單方面寫的資料形狀，不是雙方談好的契約。
  要接 API 時先確認，不要直接當規格實作。

## 文件分工

- 每一層的 `README.md` 寫給人看：這一層是什麼、怎麼跑、有哪些慣例與坑。
  事實一律寫在這裡，不要複製一份到 `CLAUDE.md`。
- 同層的 `CLAUDE.md` 第一行是 `@README.md`，其後只放「人讀了 README 就會知道、
  但 agent 預設會違反」的行為約束。
- 沒有這種內容就不要建 `CLAUDE.md`。`backend/` 目前就沒有。
