@README.md

## 給 agent 的額外規則

- 不要在根目錄建立 `package.json`、`.nvmrc` 這類綁定特定技術棧的檔案。

## 文件分工

- 每一層的 `README.md` 寫給人看：這一層是什麼、怎麼跑、有哪些慣例與坑。
  事實一律寫在這裡，不要複製一份到 `CLAUDE.md`。
- 同層的 `CLAUDE.md` 第一行是 `@README.md`，其後只放「人讀了 README 就會知道、
  但 agent 預設會違反」的行為約束。
- 沒有這種內容就不要建 `CLAUDE.md`。
