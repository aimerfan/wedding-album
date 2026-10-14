# 部署準備

婚禮是 **2026-10-17**。這份是部署的進度表與待辦；**實際要貼的指令都在 [deploy/README.md](../../deploy/README.md)**，這裡不重複。
各元件的功能與審閱發現見 [architecture.html](architecture.html)（用瀏覽器直接打開）。

## 進度

| # | 階段 | 狀態 |
| --- | --- | --- |
| 0 | 架構選定 | ✅ |
| 1 | 程式修正、部署設定檔（`deploy/`） | ✅ |
| 2 | 本機 WSL 演練（Ubuntu 26.04，1～10 步全過） | ✅ |
| 3 | 網域、Cloudflare、VPS | ⬜ **← 從這裡繼續** |
| 4 | VPS 部署 | ⬜ |
| 5 | 實機測試與彩排 | ⬜ |
| 6 | 婚禮當天與之後 | ⬜ |

## 架構：單機部署，上傳另外分一池

```
手機 → Cloudflare → nginx ─┬─ POST /api/photos → gunicorn 上傳池（:8001）
                           ├─ 其他 /api/...     → gunicorn 一般池（:8000）
                           ├─ /media/...        → 直接讀磁碟
                           └─ 其他              → 前端 dist/
```

- **為什麼分池**：HEIC 轉檔、抓影片封面吃 CPU，分開後上傳高峰不會卡住瀏覽。
- **沒選的做法**：只用一個池（上傳會卡瀏覽）；照片存 R2（有兩個沒實測的風險，婚禮前沒時間踩）；
  手機直傳 R2（去重、限流要重寫）；自家電腦加 Tunnel（停電斷網就停）。
- **之後升級到 R2**：彩排發現上傳讓瀏覽變卡、或頻寬／磁碟不夠時再考慮，主要改 `storage.py`。
  要升就**在有真實資料之前**切。

## 3. 網域、Cloudflare、VPS ⬜

| 項目 | 規格 | 過關條件 |
| --- | --- | --- |
| Cloudflare | 免費方案 | 能登入後台 |
| 網域 | 在 Cloudflare 買。**Cloudflare 不賣 `.tw`**，要 .tw 得在別家買再把 NS 改到 Cloudflare（要等生效） | 後台看得到網域，DNS 在 Cloudflare |
| VPS | **Vultr 東京**，High Performance AMD（`vhp-2c-4gb-amd`）· 2 vCPU · 4 GB · 100 GB NVMe · 5 TB／月 · $24／月 · Ubuntu **26.04**（內建 Python 3.14） | 下單頁確認有 26.04 映像 |
| VPS 備份 | 建立時勾 **Auto Backups**（月費加兩成） | 後台看得到備份排程 |
| VPS 登入 | 建立時就放 SSH 公鑰 | 能用金鑰登入 |
| DNS | A 記錄指向 VPS IP，**開代理（橘色雲）** | — |
| SSL | 模式 **Full (strict)**，產生 Origin Certificate | 憑證和私鑰都存下來（私鑰只顯示一次） |

- 備案：Vultr 不順就換 DigitalOcean 新加坡（有官方 MCP 與 `doctl`）；GCP 台灣有試用金但設定與計費較複雜。
- 網域只能自己在 Cloudflare 後台買；主機、DNS、Origin Certificate 可以交給 agent 用 API 建。
- **網域一定下來就不要換**：會場 QR code 印的是 `https://網域/?code=活動碼`。
- 硬碟：照片每張約 5.5 MB（原檔＋顯示圖＋縮圖）× 3000 ≈ 16 GB，影片 60 MB × 200 ≈ 12 GB，系統、程式、記錄、swap 約 10 GB，
  合計約 40 GB；100 GB 約有兩倍餘裕。婚禮當天用 `df -h` 看。
- 流量：只算送出，收進來免費。方案含 5 TB，帳號另有 2 TB 免費額度，超過是 $0.01／GB。照片影片大多由 Cloudflare 快取送出，
  就算全部從主機送也遠低於額度，最壞情況多付幾美元，不必另外設上限。

## 4. VPS 部署 ⬜

照 deploy/README.md 的「第一次部署」1～10 步做。

- [x] 建 `deploy` 帳號、防火牆補開 80／443、關閉 root 與密碼登入（deploy/README 第 0 步）
- [x] 1～4：裝套件、建使用者、clone（私人 repo 要用 GitHub token）、建前端
- [x] 5：填正式的 `EVENT_CODE`、`ADMIN_CODE`（**不要進 git**，自己另外記好）
- [x] 6：放 Cloudflare 憑證
- [x] 7：nginx 換成實際網域，**確認有 443**
- [x] 8：systemd 啟動，api／upload 是 active
- [x] 9：`bash deploy/smoke-test.sh https://網域 活動碼` 全過（這次不用 `-k`）
- [x] 10：匯入婚紗照與祝福（先 `--dry-run`）
- [x] 用手機打開 `https://網域/admin?code=管理員代碼`，開通管理員

要帶到 VPS 的檔案（**不在 git 裡**，在原本那台電腦的 `D:\Downloads\wedding-album\`）：

| 檔案 | 內容 |
| --- | --- |
| `wedding-photos/` | 婚紗照 51 張 jpg，約 800 MB |
| `blessings.csv` | 預先收到的祝福 31 則（UTF-8） |

用 WinSCP 或 `scp -r` 直接傳資料夾，**不要壓成 zip**（中文檔名可能變亂碼）。

## 5. 實機測試與彩排 ⬜

正式憑證之後才測得到的（本機自簽憑證下 Service Worker 不會註冊）：

**iPhone**

- [ ] Safari 歡迎頁出現「加到主畫面」引導，步驟跟實際分享選單一致
- [ ] 加到主畫面後打開，是不是不同身分；用接續碼能不能接回
- [ ] LINE 內建瀏覽器有提示改用瀏覽器開
- [ ] 鍵盤：祝福輸入框會不會自動放大（字體 15px）、面板會不會被鍵盤蓋住、有沒有彈出鍵盤
- [ ] 字體「特大」時照片詳情頁底部
- [ ] 影片：從相簿選影片會不會先被壓縮、預覽有沒有第一格、HEVC 直拍封面方向、在詳情頁能播（Range）

**多人彩排**

- [ ] 幾支手機同時上傳照片與影片，瀏覽不卡
- [ ] 量一支大影片從選取到完成要幾秒（Cloudflare 要在 100 秒內開始回應）
- [ ] 看 CPU、記憶體，決定兩個池的 worker 數要不要調（現在先抓一般池 4、上傳池 3）
- [ ] 彩排資料清掉：刪掉測試照片，或重建資料庫後重新匯入婚紗照與祝福

**QR code**

- [ ] 網址 `https://網域/?code=活動碼` 用手機掃過能進
- [ ] 印刷來得及（網域與活動碼一定下來就要送印）

**婚禮前一天**

- [ ] 手動 `apt upgrade` 後暫停 `unattended-upgrades` 到婚禮結束，避免當天自動更新重啟服務

## 6. 婚禮當天與之後 ⬜

| 時間 | 要做的事 |
| --- | --- |
| 當天 | 看 `journalctl -u wedding-album-upload -f` 有沒有一直出錯；不改程式 |
| 結束後 | 截止上傳：env 加 `UPLOADS_OPEN=false`，重啟兩個服務 |
| 結束後 | **備份**：資料庫用 `sqlite3 wedding.db ".backup 檔名"`（先 `apt install sqlite3`），照片整個 `/var/lib/wedding-album/media/` 複製出來 |
| 之後 | 從 `media/photos/*/original.*` 打包原檔給新人 |
| 之後 | 有刪掉的不當照片，到 Cloudflare 清那張的快取 |
| 之後 | 要長期留著再考慮升級到 R2 |

## 還沒解決的風險

| 風險 | 影響 | 目前做法 |
| --- | --- | --- |
| 刪掉的照片還在 Cloudflare 快取 | 知道網址的人 30 天內還看得到 | 需要時手動 Purge Cache |
| worker 數沒壓測過 | 高峰可能排隊 | 彩排時看數據調整 |
| Cloudflare 免費方案對影片的規範 | 大量影片流量可能違反服務條款 | 婚禮規模應該還好，還沒查證 |
| 主機 IP 直連可繞過 Cloudflare | 知道 IP 的人能直接連 | IP 不會從 DNS 曝光，先不處理 |

## 換裝置繼續時

1. `git pull`，看這份的進度表和 deploy/README.md。
2. 準備：VPS 的 SSH 金鑰、Cloudflare 帳號、上面那兩個不在 git 裡的匯入檔案。
3. 做完一步就回來把 ⬜ 改成 ✅。
