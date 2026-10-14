# 部署準備

婚禮是 **2026-10-17**。這份是部署的進度表：選了哪個架構、為什麼、做到哪、接下來做什麼。
**實際要貼的指令都在 [deploy/README.md](../deploy/README.md)**，這裡只寫流程與過關條件，不重複指令。

> 最後更新：2026-10-15 凌晨。本機（WSL）演練全部完成，下一步是買網域、租 VPS。

## 一眼看進度

| # | 階段 | 狀態 |
| --- | --- | --- |
| 0 | 架構選定 | ✅ |
| 1 | 程式先修好的地方 | ✅ |
| 2 | 部署設定檔 | ✅ |
| 3 | 本機 WSL 演練 | ✅ |
| 4 | 網域、Cloudflare、VPS | ⬜ **← 從這裡繼續** |
| 5 | VPS 部署 | ⬜ |
| 6 | 實機測試與彩排 | ⬜ |
| 7 | 婚禮當天與之後 | ⬜ |

## 0. 架構：單機部署，上傳另外分一池 ✅

當初比較過五種做法（討論時叫 A～E）：

| 做法 | 一句話 | 結論 |
| --- | --- | --- |
| A 單機最小 | 一台 VPS，一個 gunicorn 池，照片存本機 | 上傳一多，HEIC 轉檔會佔滿 worker，瀏覽跟著卡 |
| **B 單機分池** | A 再把上傳和其他 API 分成兩個 gunicorn 池 | **婚禮用這個**：幾乎不用改程式，上傳再多也不卡瀏覽 |
| C 分池 + R2 | 照片改存 Cloudflare R2，SQLite 用 Litestream 備份到 R2 | 婚禮後有需要再升級，主要改 `storage.py` |
| D 手機直傳 R2 | 後端只發上傳網址，手機直接傳 R2 | 去重、限流、影片檢查都要重寫，工程量大一個等級 |
| E 自家電腦 + Tunnel | 不租主機 | 停電、斷網、筆電闔上就停，不適合婚禮當天 |

```
手機 → Cloudflare → nginx ─┬─ POST /api/photos → gunicorn 上傳池（:8001）
                           ├─ 其他 /api/...     → gunicorn 一般池（:8000）
                           ├─ /media/...        → 直接讀磁碟
                           └─ 其他              → 前端 dist/
```

- **為什麼不現在就做 C**：C 有兩個沒實測過的風險（95 MB 影片先到 VPS 再轉 R2 能不能在 100 秒內完成；Service Worker 快取跨網域圖片的空間問題），婚禮前沒時間踩。
- **什麼時候值得升 C**：彩排時發現上傳高峰讓瀏覽變卡、或 VPS 頻寬／磁碟不夠。要升的話**在有真實資料之前**切，省掉搬檔。

## 1. 程式先修好的地方 ✅

升不升 C 都用得到，先做了：

- [x] 上傳存到一半失敗（磁碟滿、資料庫鎖住），已存的檔案會清掉，不留孤兒檔
- [x] 正式環境 Flask 不送 `/media`，交給 nginx（漏設時會直接 404，不會悄悄佔住後端）

## 2. 部署設定檔 ✅

都在 [deploy/](../deploy/)：

| 檔案 | 做什麼 |
| --- | --- |
| `nginx/wedding-album.conf` | 分流、照片檔、前端、快取標頭、上傳大小限制 |
| `systemd/wedding-album-{init,api,upload}.service` | init 先建資料表，再起兩個池；開機自動啟動、掛了自動重啟 |
| `wedding-album.env.example` | 活動碼、管理員代碼、資料位置 |
| `smoke-test.sh` | 部署完跑一輪：前端、API、上傳、照片檔、快取、Range |
| `README.md` | **第一次部署 1～10 步的完整指令**、更新版本、WSL 演練 |

## 3. 本機 WSL 演練 ✅

在 Windows 的 WSL（Ubuntu 26.04，跟 VPS 同一版）照 deploy/README.md 整套跑過一遍。

| Checkpoint | 結果 |
| --- | --- |
| Ubuntu 26.04 內建 Python 3.14 | ✅ 3.14.4，不必另外裝 |
| 後端在 Linux 跑測試 | ✅ 202 passed |
| 前端在 Linux 建置（Node 22） | ✅ |
| `nginx -t`、有在 443 監聽 | ✅ |
| 檢查腳本 | ✅ 全過 |
| 上傳只進上傳池，其他都進一般池 | ✅ 看兩邊的存取記錄確認 |
| 瀏覽器上傳照片、影片 | ✅ |
| systemd 開機自動啟動 | ✅ `wsl --shutdown` 後重開，三個服務都起來 |
| 匯入婚紗照 51 張、祝福 31 則 | ✅ 婚紗集、留言牆都有出現 |

演練時踩到、已經修進文件或設定的坑：

| 現象 | 原因 | 處理 |
| --- | --- | --- |
| `wsl --install -d Ubuntu-24.04` 說名稱不對 | Windows 內建的舊版 wsl | 先 `wsl --install --web-download --no-distribution` |
| 檢查腳本全部 `000` | nginx 沒 reload，只聽 80 | 文件加上 `ss` 確認 443；腳本連不上時直接提示 |
| 首頁要求掃 QR code | 正式版本沒有預設活動碼 | 網址帶 `?code=活動碼`，已寫進文件 |
| `Control server error: /home/wedding` | gunicorn 26 預設在家目錄建控制 socket | 兩個服務加 `--no-control-socket` |
| 匯入指令讀不到環境變數 | env 檔只有 root 能讀 | 改成 `sudo grep` 讀出再交給 `wedding` |

## 4. 網域、Cloudflare、VPS ⬜ ← 從這裡繼續

| 項目 | 建議 | 過關條件 |
| --- | --- | --- |
| 網域 | 直接在 Cloudflare 買，DNS 就在 Cloudflare | Cloudflare 後台看得到這個網域 |
| VPS | Ubuntu **26.04**；東京／新加坡／台灣機房；2 vCPU、4 GB、50～80 GB 硬碟 | 能用 SSH 金鑰登入；防火牆只開 22、80、443 |
| DNS | A 記錄指向 VPS IP，**開代理（橘色雲）** | — |
| SSL | 模式 **Full (strict)**，產生 Origin Certificate | 憑證和私鑰都存下來（私鑰只顯示一次） |

- **網域一定下來就不要換**：會場 QR code 印的是 `https://網域/?code=活動碼`。
- 硬碟估算：約 3000 張照片 × 5 MB ＋ 200 支影片 × 60 MB ≈ 30 GB，加上婚紗照與餘裕。

## 5. VPS 部署 ⬜

照 [deploy/README.md](../deploy/README.md) 的「第一次部署（VPS 的完整流程）」1～10 步做，WSL 上全部跑過。

- [ ] 1～4：裝套件、建使用者、clone（私人 repo 要用 GitHub token）、建前端
- [ ] 5：填正式的 `EVENT_CODE`、`ADMIN_CODE`（**不要進 git**，自己另外記好）
- [ ] 6：放 Cloudflare 憑證
- [ ] 7：nginx 換成實際網域，**確認有 443**
- [ ] 8：systemd 啟動，api／upload 是 active
- [ ] 9：`bash deploy/smoke-test.sh https://網域 活動碼` 全過（這次不用 `-k`）
- [ ] 10：匯入婚紗照與祝福（先 `--dry-run`）
- [ ] 用手機打開 `https://網域/admin?code=管理員代碼`，開通管理員

要帶到新裝置／VPS 的檔案（**不在 git 裡**，在原本那台電腦的 `D:\Downloads\wedding-album\`）：

| 檔案 | 內容 |
| --- | --- |
| `wedding-photos/` | 婚紗照 51 張 jpg，約 800 MB |
| `blessings.csv` | 預先收到的祝福 31 則（UTF-8） |

傳到 VPS 用 WinSCP 或 `scp -r` 直接傳資料夾，**不要壓成 zip**（中文檔名可能變亂碼）。

## 6. 實機測試與彩排 ⬜

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
- [ ] 彩排資料清掉：刪掉測試照片，或婚禮前重建資料庫後重新匯入婚紗照與祝福

**QR code**

- [ ] 網址 `https://網域/?code=活動碼` 用手機掃過能進
- [ ] 印刷來得及（網域與活動碼一定下來就要送印）

## 7. 婚禮當天與之後 ⬜

| 時間 | 要做的事 |
| --- | --- |
| 當天 | 看 `journalctl -u wedding-album-upload -f` 有沒有一直出錯；不改程式 |
| 結束後 | 截止上傳：env 加 `UPLOADS_OPEN=false`，重啟兩個服務 |
| 結束後 | **備份**：資料庫用 `sqlite3 wedding.db ".backup 檔名"`（先 `apt install sqlite3`），照片整個 `/var/lib/wedding-album/media/` 複製出來 |
| 之後 | 從 `media/photos/*/original.*` 打包原檔給新人 |
| 之後 | 有刪掉的不當照片，到 Cloudflare 清那張的快取 |
| 之後 | 要長期留著再考慮升級到 R2（上面的 C） |

## 還沒解決的風險

| 風險 | 影響 | 目前做法 |
| --- | --- | --- |
| **沒有自動備份** | 主機壞掉，照片和資料庫都沒了 | 婚禮後立刻手動備份；要更保險可以婚禮前加每小時 rsync |
| 刪掉的照片還在 Cloudflare 快取 | 知道網址的人 30 天內還看得到 | 需要時手動 Purge Cache |
| worker 數沒壓測過 | 高峰可能排隊 | 彩排時看數據調整 |
| Cloudflare 免費方案對影片的規範 | 大量影片流量可能違反服務條款 | 婚禮規模應該還好，還沒查證 |

## 換裝置繼續時

1. `git pull`，看這份文件的進度表和 deploy/README.md。
2. 準備：VPS 的 SSH 金鑰、Cloudflare 帳號、上面那兩個不在 git 裡的匯入檔案。
3. 要再演練的話，照 deploy/README.md 的「在 Windows 上用 WSL 演練」（不是 Windows 就直接上 VPS）。
4. 做完一步就回來把這份的 ⬜ 改成 ✅，順便更新最上面的「最後更新」。
