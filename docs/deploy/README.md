# 部署計畫

婚禮是 **2026-10-17**。這份說明部署的做法與選用理由，以及上線前要驗證、婚禮當天與之後要做的事。
實際要貼的指令在 [deploy/README.md](../../deploy/README.md)（日常更新）與 [deploy/init_steps.md](../../deploy/init_steps.md)（第一次部署），這裡不重複。
各元件的功能與審閱發現見 [architecture.html](architecture.html)（用瀏覽器直接打開）。

## 架構：單機部署，上傳另外分一池

```
手機 → Cloudflare → nginx ─┬─ POST /api/photos → gunicorn 上傳池（:8001）
                           ├─ 其他 /api/...     → gunicorn 一般池（:8000）
                           ├─ /media/...        → 直接讀磁碟
                           └─ 其他              → 前端 dist/
```

- **為什麼分池**：HEIC 轉檔、抓影片封面吃 CPU，分開後上傳高峰不會卡住瀏覽。
- **為什麼照片放主機磁碟**：最少未知數。nginx 直接送檔，Cloudflare 在前面快取，婚禮規模的流量與容量都夠（見下方估算）。
- **沒選的做法**：只用一個池（上傳會卡瀏覽）；照片存 R2（有兩個沒實測的風險，婚禮前沒時間踩）；
  手機直傳 R2（去重、限流要重寫）；自家電腦加 Tunnel（停電斷網就停）。
- **之後升級到 R2**：上傳讓瀏覽變卡、或頻寬／磁碟不夠時再考慮，主要改 `storage.py`。
  要升就**在有真實資料之前**切。

## 網域、Cloudflare、VPS

| 項目 | 選擇 | 理由 |
| --- | --- | --- |
| Cloudflare | 免費方案 | 代理隱藏主機 IP、提供 HTTPS、快取照片，免費方案就夠 |
| 網域 | `hungting.date`，在 Cloudflare 買 | 買了 DNS 直接在 Cloudflare。**Cloudflare 不賣 `.tw`**，要 .tw 得在別家買再把 NS 改過來，要等生效 |
| VPS | **Vultr 東京**，High Performance AMD（`vhp-2c-4gb-amd`）· 2 vCPU · 4 GB · 100 GB NVMe · 5 TB／月 · $24／月 | 設定與計費比 GCP 單純，操作簡單；有 Ubuntu **26.04** 映像，內建 Python 3.14，不必自己裝 |
| VPS 備份 | 開 **Auto Backups**（月費加兩成） | 婚禮後正式備份之前，主機壞掉還有退路 |
| VPS 登入 | 只用 SSH 金鑰，關閉 root 與密碼登入 | 主機直接暴露在網路上 |
| DNS | A 記錄指向 VPS IP，**開代理（橘色雲）** | 流量經過 Cloudflare，才有快取與 HTTPS，IP 也不會從 DNS 曝光 |
| SSL | 模式 **Full (strict)**，主機放 Cloudflare 的 Origin Certificate | Cloudflare 到主機這段也加密並驗證憑證；Origin Certificate 有效 15 年，不必續期 |

- 備案：Vultr 不順就換 DigitalOcean 新加坡（有官方 MCP 與 `doctl`）；GCP 台灣有試用金但設定與計費較複雜。
- **網域定下來就不要換**：會場 QR code 印的是 `https://網域/?code=活動碼`。
- 硬碟：照片每張約 5.5 MB（原檔＋顯示圖＋縮圖）× 3000 ≈ 16 GB，影片 60 MB × 200 ≈ 12 GB，系統、程式、記錄、swap 約 10 GB，
  合計約 40 GB；100 GB 約有兩倍餘裕。婚禮當天用 `df -h` 看。
- 流量：只算送出，收進來免費。方案含 5 TB，帳號另有 2 TB 免費額度，超過是 $0.01／GB。照片影片大多由 Cloudflare 快取送出，
  就算全部從主機送也遠低於額度，最壞情況多付幾美元，不必另外設上限。

## 不在 git 裡的東西

| 東西 | 放在哪 |
| --- | --- |
| `EVENT_CODE`、`ADMIN_CODE` | 主機的 `/etc/wedding-album/env`，自己另外記一份 |
| VPS 的 SSH 金鑰、Cloudflare 與 Vultr 帳號 | 各自保管 |
| 婚紗照 `wedding-photos/`（51 張 jpg，約 800 MB）、祝福 `blessings.csv`（31 則，UTF-8） | 原本那台電腦的 `D:\Downloads\wedding-album\`，已匯入主機 |

匯入檔用 WinSCP 或 `scp -r` 直接傳資料夾，**不要壓成 zip**（中文檔名可能變亂碼）。

## 上線前要驗證的事

這些要正式憑證才測得到：本機自簽憑證下 Service Worker 不會註冊，WSL 演練測不到。

- **網域與內容**：`.date` 網域在各家電信、一般瀏覽器與 LINE 內建瀏覽器都打得開；新人確認婚紗集的順序與方向、留言牆的內容。
- **iPhone**：
  - Safari 歡迎頁的「加到主畫面」引導，步驟要跟實際的分享選單一致。
  - 掃 QR code 後先不加入、直接加到主畫面，從主畫面打開要能加入相簿。主畫面 app 讀不到 Safari 存的活動碼，
    要靠 manifest 的 `start_url` 帶過去（見 docs/api.md 的 `/api/manifest`）；這個修正之前加到主畫面的人，要刪掉圖示從 Safari 重加。
  - 加到主畫面後打開是不同身分（iPhone 主畫面 app 跟 Safari 資料分開），用接續碼要能接回。
  - LINE 內建瀏覽器要提示改用瀏覽器開。
  - 鍵盤：祝福輸入框會不會自動放大（字體 15px）、面板會不會被鍵盤蓋住。
  - 字體「特大」時照片詳情頁的底部。
  - 影片：從相簿選影片會不會先被壓縮、預覽有沒有第一格、HEVC 直拍的封面方向、詳情頁能播（Range）。
- **多人彩排**：幾支手機同時上傳照片與影片，瀏覽不能卡；量一支大影片從選取到完成要幾秒
  （Cloudflare 要在 100 秒內開始回應）；看 CPU、記憶體決定兩個池的 worker 數（先抓一般池 4、上傳池 3）。
  彩排完要清掉測試資料：刪掉測試照片，或重建資料庫後重新匯入婚紗照與祝福。
- **QR code**：`https://網域/?code=活動碼` 用手機掃過能進，再送印。
- **婚禮前一天**：手動 `apt upgrade`，再暫停 `unattended-upgrades` 到婚禮結束，避免當天自動更新重啟服務。

## 婚禮當天與之後

| 時間 | 要做的事 |
| --- | --- |
| 當天 | 看 `journalctl -u wedding-album-upload -f` 有沒有一直出錯；不改程式 |
| 結束後 | 截止上傳：env 加 `UPLOADS_OPEN=false`，重啟兩個服務 |
| 結束後 | **備份**：資料庫用 `sqlite3 wedding.db ".backup 檔名"`（先 `apt install sqlite3`），照片整個 `/var/lib/wedding-album/media/` 複製出來 |
| 之後 | 從 `media/photos/*/original.*` 打包原檔給新人 |
| 之後 | 有刪掉的不當照片，到 Cloudflare 清那張的快取 |
| 之後 | 要長期留著再考慮升級到 R2 |
| 開放期滿 | 相簿預計開放兩週到一個月。**還沒決定**期滿後要繼續唯讀開著，還是整站關閉（見下方） |

**整站關閉的做法**（不用改程式或 API）：先完成上面的備份與打包原檔，再擇一：

- nginx 改成所有請求都回一個「相簿已結束」的靜態頁，保留主機與資料，之後還能重開。
- 直接退租 VPS。網域到期前可以把 DNS 指到別處，或讓它失效。

## 還沒解決的風險

| 風險 | 影響 | 目前做法 |
| --- | --- | --- |
| 刪掉的照片還在 Cloudflare 快取 | 知道網址的人 30 天內還看得到 | 需要時手動 Purge Cache |
| worker 數沒壓測過 | 高峰可能排隊 | 彩排時看數據調整 |
| Cloudflare 免費方案對影片的規範 | 大量影片流量可能違反服務條款 | 婚禮規模應該還好，還沒查證 |
| 主機 IP 直連可繞過 Cloudflare | 知道 IP 的人能直接連 | IP 不會從 DNS 曝光，先不處理 |
