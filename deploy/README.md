# deploy

正式環境的設定檔：一台 Linux VPS，前面接 Cloudflare。照片存在主機磁碟上，上傳與其他 API 分給兩個 gunicorn 池。

```
手機 → Cloudflare → nginx ─┬─ POST /api/photos → gunicorn 上傳池   127.0.0.1:8001
                           ├─ 其他 /api/...     → gunicorn 一般池   127.0.0.1:8000
                           ├─ /media/...        → 直接讀磁碟（MEDIA_DIR）
                           └─ 其他              → 前端建置結果（frontend/dist）
```

分池的用意：婚宴高峰大家同時上傳時，處理上傳（HEIC 轉檔、抓影片封面）的 worker 再忙，
也不會讓滑相簿、按讚的請求排隊。網路慢的手機由 nginx 先把整個檔案收完才交給後端，不會佔住 worker。

| 檔案 | 放到主機的哪裡 |
| --- | --- |
| `nginx/wedding-album.conf` | `/etc/nginx/sites-available/`，再連到 `sites-enabled/` |
| `systemd/*.service` | `/etc/systemd/system/` |
| `wedding-album.env.example` | 複製成 `/etc/wedding-album/env`，填好再設成 `chmod 600` |
| `smoke-test.sh` | 不用放，部署完在主機上執行，見「第一次部署」第 9 步 |

## 主機上的路徑

設定檔裡寫死了這些路徑，換位置的話三種檔案要一起改：

| 路徑 | 內容 |
| --- | --- |
| `/srv/wedding-album/` | 這個 repo |
| `/srv/wedding-album/backend/.venv/` | 後端的虛擬環境（Python 3.14） |
| `/srv/wedding-album/frontend/dist/` | 前端建置結果 |
| `/var/lib/wedding-album/` | 資料庫與照片檔（`MEDIA_DIR`），擁有者是 `wedding` |

後端以 `wedding` 這個系統使用者執行。照片檔要讓 nginx 讀得到：資料夾 755、檔案 644（Python 預設就是這樣）。

## 第一次部署

1. 主機用 Ubuntu 26.04（內建 Python 3.14，不必另外裝），裝好 `python3-venv`、`git`、nginx、Node（建置前端用）。
2. 建使用者與資料夾：`useradd --system --no-create-home --shell /usr/sbin/nologin wedding`，
   建立 `/var/lib/wedding-album/` 並交給 `wedding`。
3. 抓 repo 到 `/srv/wedding-album/`，在 `backend/` 建虛擬環境並 `pip install -r requirements.txt`。
4. 在 `frontend/` 執行 `npm ci && npm run build`。
5. 填好 `/etc/wedding-album/env`。`EVENT_CODE` 沒設的話後端不會啟動。
   會場 QR code 的網址是 `https://網域/?code=<EVENT_CODE>`：正式版本沒有預設活動碼，直接打開首頁會要求掃 QR code。
6. Cloudflare：DNS 開代理（橘色雲），SSL 模式設 **Full (strict)**。到 SSL/TLS → Origin Server 產生憑證，
   存到 `/etc/ssl/wedding-album/origin.pem` 與 `origin.key`。
7. 放好 nginx 設定，拿掉預設網站（`rm /etc/nginx/sites-enabled/default`），`nginx -t` 通過後 `systemctl reload nginx`。
   用 `ss -tlnp | grep ':443 '` 確認有在 443 監聽：`nginx -t` 只檢查語法，沒 reload 的話跑的還是舊設定。
8. `systemctl daemon-reload && systemctl enable --now wedding-album-api wedding-album-upload`。
   啟動前會先自動跑一次 `wedding-album-init`，建立資料表。
9. 檢查：`bash deploy/smoke-test.sh https://網域 活動碼`，會實際上傳一張照片再刪掉。
   上傳有沒有走到上傳池：`journalctl -u wedding-album-upload` 裡要有 `POST /api/photos`。
10. 匯入婚紗照與祝福（見 backend/README.md），指令要以 `wedding` 身分、帶著同一份環境變數執行。

## 更新版本

```bash
cd /srv/wedding-album && git pull
cd frontend && npm ci && npm run build
cd ../backend && .venv/bin/pip install -r requirements.txt
systemctl restart wedding-album-api wedding-album-upload
```

重啟上傳池時，進行中的上傳最多等 120 秒做完。但前端只要發現上傳失敗就會自動重送，同一個檔案也不會重複。

## 在 Windows 上用 WSL 演練

上 VPS 之前，先在本機的 WSL（Ubuntu 26.04，跟 VPS 同一版）把整套跑一遍。gunicorn 不支援 Windows，所以要在 Linux 裡測。
測不到的只有 Cloudflare 本身（100 MB 上限、快取）與正式憑證。

1. 系統管理員 PowerShell：`wsl --install --web-download --no-distribution`，裝完重開機。
   Windows 內建的舊版 `wsl` 不認得 `--update`，清單裡也只有不帶版本的 `Ubuntu`，所以要先裝新版 WSL。
2. `wsl --install -d Ubuntu-26.04`，設定使用者名稱與密碼（metrics 那題選什麼都可以）。
3. 在 Ubuntu 裡：

   ```bash
   sudo apt update && sudo apt upgrade -y && sudo apt install -y python3-venv git
   sudo mkdir -p /srv/wedding-album && sudo chown $USER:$USER /srv/wedding-album
   git clone /mnt/d/Code/wedding-album /srv/wedding-album
   cd /srv/wedding-album/backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
   .venv/bin/pytest -q
   ```

   - 從 D 槽的 repo 直接 clone，**只會拿到已經 commit 的內容**。之後更新用 `git pull`。
   - clone 時出現 `detected dubious ownership`：先執行
     `git config --global --add safe.directory /mnt/d/Code/wedding-album/.git`。
   - repo 一定要放在 Linux 這邊（`/srv/...`），不要直接在 `/mnt/d/...` 底下跑：很慢，權限也會讓 nginx 讀不到照片。
     WSL 跳出「在 Windows 磁碟上操作效能不佳」的提示，就是在說這件事。
4. 接著照「第一次部署」的 2、4、5、7、8、9 步做（第 1 步只剩 nginx、nodejs、npm 要裝，apt 的 Node 22 就夠）。跟 VPS 不同的地方：
   - 沒有 Cloudflare 的憑證，在同樣的路徑放自簽憑證，設定檔就不必改：

     ```bash
     sudo mkdir -p /etc/ssl/wedding-album && sudo openssl req -x509 -nodes -newkey rsa:2048 -days 30 -subj "/CN=localhost" \n         -keyout /etc/ssl/wedding-album/origin.key -out /etc/ssl/wedding-album/origin.pem
     ```

   - `deploy/` 底下改了還沒 commit 的檔案，可以直接從 `/mnt/d/Code/wedding-album/deploy/` 複製來試。
   - 檢查腳本要加 `-k`（自簽憑證）：`bash deploy/smoke-test.sh https://localhost 活動碼 -k`。
5. Windows 的瀏覽器打開 `https://localhost/?code=活動碼`（WSL 會把 port 轉到 Windows）。
   自簽憑證會被警告，按「繼續前往」即可；Service Worker 遇到憑證錯誤不會註冊，離線與加到主畫面在本機測不到。
6. 測重開機：PowerShell 執行 `wsl --shutdown`，重新打開 Ubuntu 後不做任何事，
   `systemctl status nginx wedding-album-api wedding-album-upload` 三個都要是 active。

## 要注意的地方

- **刪掉的照片在 Cloudflare 上還會留著。** 照片檔設了 30 天的長效快取，管理員刪掉不適當的照片後，
  知道網址的人仍然看得到。要馬上消失的話，到 Cloudflare 的 Caching → Purge Cache 清掉那張的網址
  （`/media/photos/<照片 id>/` 底下的 original、display、thumb 三個檔）。
- **Cloudflare 的上限**：免費方案單一請求最多 100 MB，回應要在 100 秒內開始，所以後端的影片上限是 95 MB。
- **還沒有備份。** 資料庫與照片都只在這一台主機上。資料庫備份方式見 backend/README.md 的「資料庫」。
- **nginx 的記錄看到的都是 Cloudflare 的 IP。** 目前後端不依 IP 判斷任何事，需要查真實 IP 時
  再加 `real_ip_header CF-Connecting-IP` 與 Cloudflare 的 IP 範圍。
- **worker 數量還沒壓測過**，目前是先抓的數字（一般池 4、上傳池 3），彩排時依 CPU 與記憶體用量再調。
