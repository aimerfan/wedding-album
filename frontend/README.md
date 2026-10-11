# frontend

Vue 3 + TypeScript + Vite，以 PWA 形式提供。

## 環境需求

Node.js `^20.19.0 || >=22.12.0`（Vite 8 的要求，建議 Node 24 LTS）。

```bash
cd frontend
npm install
npm run dev
```

| 指令 | 用途 |
| --- | --- |
| `npm run dev` | 開發伺服器（http://localhost:5173） |
| `npm run build` | 型別檢查 + 產出 `dist/` |
| `npm run preview` | 預覽 build 產物 |
| `npm run type-check` | 只跑 `vue-tsc -b` |
| `npm run lint` | ESLint 檢查並自動修正 |
| `npm run format` | Prettier 格式化 |

## 慣例

- `@/` 指向 `src/`。
- 呼叫 API 一律寫相對路徑 `/api/...`。開發時 Vite 會轉給 `localhost:5000` 的 Flask，
  要用到 API 的畫面得先把後端跑起來（見 `backend/README.md`）。
- 所有 API 呼叫都經過 `src/api/client.ts`，它負責帶 token、把錯誤統一成 `ApiError`。
- 活動碼從會場 QR code 的網址 `?code=...` 讀取並記在手機上；開發時沒有 QR code，自動用後端的開發值 `dev`。
- 色票與版面尺寸的唯一來源是 `src/assets/tokens.css`，不要在元件裡寫死顏色。
  `docs/design/extracted/` 裡的 `A` 物件是設計稿的凍結快照，不是現行來源。
- `src/mock/` 是為了讓畫面長出來的假資料，目前各支 view 直接 import 它。
  接上 API 後整個資料夾要刪掉。

## PWA

- `vite-plugin-pwa`，`registerType: 'autoUpdate'`
- 相片走執行期快取（`CacheFirst`，上限 300 張／30 天），不進 precache
- `public/` 下的圖示目前是佔位圖，待設計稿確定後替換
- iOS 沒有安裝提示 API，需另外做「加到主畫面」的引導畫面

## 已知的坑

- `vite.config.ts` 的 `devOptions.enabled` 讓 Service Worker 在 dev 也註冊。
  改了程式碼沒生效時，先到 DevTools → Application → Service Workers 點 Unregister。
