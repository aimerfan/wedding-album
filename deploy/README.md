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

## 第一次部署（VPS 的完整流程）

以下都在主機上、用有 sudo 權限的一般帳號執行。`album.example.com` 換成實際網域。

### 1. 安裝套件

Ubuntu 26.04 內建 Python 3.14，不必另外裝；apt 的 Node 22 也符合前端的要求。

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv git nginx nodejs npm
```

### 2. 建立執行後端的使用者與資料夾

`wedding` 不能登入、沒有家目錄，只用來跑後端。資料庫與照片放在 `/var/lib/wedding-album/`，跟程式分開。

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin wedding
sudo mkdir -p /var/lib/wedding-album && sudo chown wedding:wedding /var/lib/wedding-album
```

### 3. 抓程式、裝後端

```bash
sudo mkdir -p /srv/wedding-album && sudo chown $USER:$USER /srv/wedding-album
git clone https://github.com/aimerfan/wedding-album.git /srv/wedding-album
cd /srv/wedding-album/backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

repo 是私人的話，clone 時要用 GitHub 的 personal access token 當密碼（或設定 deploy key）。

### 4. 建置前端

```bash
cd /srv/wedding-album/frontend && npm ci && npm run build && ls dist
```

`dist` 裡要看到 `index.html`、`sw.js`、`assets/`。

### 5. 環境變數

```bash
sudo mkdir -p /etc/wedding-album
sudo cp /srv/wedding-album/deploy/wedding-album.env.example /etc/wedding-album/env
sudo nano /etc/wedding-album/env   # 填 EVENT_CODE、ADMIN_CODE
sudo chmod 600 /etc/wedding-album/env
```

- `EVENT_CODE` 沒設，後端不會啟動。
- 會場 QR code 的網址是 `https://album.example.com/?code=<EVENT_CODE>`。
  正式版本沒有預設活動碼，直接打開首頁會要求掃 QR code。
- 管理員：用手機打開 `https://album.example.com/admin?code=<ADMIN_CODE>`。

### 6. 憑證（Cloudflare）

1. Cloudflare 的 DNS 加一筆 A 記錄指向主機 IP，開代理（橘色雲）。
2. SSL/TLS 模式設 **Full (strict)**。
3. SSL/TLS → Origin Server → Create Certificate，把產生的憑證與私鑰存起來：

```bash
sudo mkdir -p /etc/ssl/wedding-album
sudo nano /etc/ssl/wedding-album/origin.pem   # 貼上 Origin Certificate
sudo nano /etc/ssl/wedding-album/origin.key   # 貼上 Private Key
sudo chmod 600 /etc/ssl/wedding-album/origin.key
```

私鑰只會在 Cloudflare 產生的當下顯示一次。

### 7. nginx

放好設定、換上實際網域、拿掉 Ubuntu 的預設網站（不拿掉的話請求會被它接走，只看到 nginx 歡迎頁）：

```bash
sudo cp /srv/wedding-album/deploy/nginx/wedding-album.conf /etc/nginx/sites-available/
sudo sed -i 's/album\.example\.com/你的網域/g' /etc/nginx/sites-available/wedding-album.conf
sudo ln -s /etc/nginx/sites-available/wedding-album.conf /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
sudo ss -tlnp | grep -E ':(80|443) '
```

- `nginx -t` 看到 `listen ... http2` 已過時的警告是正常的。
- **最後一行一定要看到 443。** `nginx -t` 只檢查語法，沒有 reload 成功的話，跑的還是舊設定（只會有 80）。

### 8. 啟動後端

```bash
sudo cp /srv/wedding-album/deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now wedding-album-api wedding-album-upload
systemctl status wedding-album-init wedding-album-api wedding-album-upload --no-pager | grep -E "●|Active:"
```

- api、upload 要是 `active (running)`；init 跑完就結束，是 `inactive (dead)` 而且沒有錯誤。
- 啟動 api、upload 之前會先自動跑一次 init 建立資料表，不必手動做。
- 記錄：`sudo journalctl -u wedding-album-api -u wedding-album-upload --since "10 min ago"`，
  兩個池各有一行 `Listening at`，不該有 error。

### 9. 檢查

```bash
bash /srv/wedding-album/deploy/smoke-test.sh https://album.example.com 你的活動碼
sudo journalctl -u wedding-album-upload --no-pager | tail -5
```

- 檢查腳本會建一位「部署測試」賓客、上傳一張照片再刪掉。賓客會留在資料庫，所以只在婚禮前跑。
- 第二行要看到 `POST /api/photos`：代表上傳確實走到上傳池。其他 API 會出現在 `wedding-album-api` 的記錄裡。
- 用手機打開 QR code 的網址，加入、上傳照片與影片、播放影片、加到主畫面。

### 10. 匯入婚紗照與祝福

格式與規則見 backend/README.md 的「匯入婚紗照」「預先匯入祝福」。

先把檔案放到 `wedding` 讀得到的地方。從 Windows 傳到 VPS 用 WinSCP 或 `scp -r` 直接傳資料夾，
**不要先壓成 zip**：Windows 內建的壓縮可能把中文檔名存成 Big5，到 Linux 解開會變亂碼。

```bash
mkdir -p /tmp/wedding-import   # 把 blessings.csv 與婚紗照資料夾 wedding-photos/ 放進來
chmod -R a+rX /tmp/wedding-import
```

指令要以 `wedding` 身分（新檔案的擁有者才對）、帶著同一份環境變數執行。先加 `--dry-run` 預覽，沒問題再拿掉：

```bash
cd /srv/wedding-album/backend
sudo -u wedding env $(sudo grep -v '^#' /etc/wedding-album/env | xargs) FLASK_SKIP_DOTENV=1 \
    .venv/bin/flask --app app import-blessings /tmp/wedding-import/blessings.csv --dry-run
sudo -u wedding env $(sudo grep -v '^#' /etc/wedding-album/env | xargs) FLASK_SKIP_DOTENV=1 \
    .venv/bin/flask --app app import-wedding /tmp/wedding-import/wedding-photos --dry-run
```

- 環境變數檔只有 root 讀得到，所以由 `sudo grep` 讀出來再交給 `wedding`。
- `FLASK_SKIP_DOTENV=1`：不讀開發用的 `.flaskenv`（裡面有 `FLASK_DEBUG=1`）。
- 婚紗照每張要產生顯示用與縮圖，50 張左右約一兩分鐘。
- 匯入後 `ls -l /var/lib/wedding-album/media/` 的擁有者要是 `wedding`；是 root 的話，之後後端刪不掉這些檔案。

## 更新版本

```bash
cd /srv/wedding-album && git pull
cd frontend && npm ci && npm run build
cd ../backend && .venv/bin/pip install -r requirements.txt
sudo systemctl restart wedding-album-api wedding-album-upload
```

- `deploy/` 底下的設定有改：nginx 設定要重新複製（記得再換一次網域）並 `nginx -t && systemctl reload nginx`；
  systemd 設定要重新複製並 `systemctl daemon-reload` 再 restart。
- 重啟上傳池時，進行中的上傳最多等 120 秒做完。中斷的上傳前端會自動重送，同一個檔案不會重複。

## 在 Windows 上用 WSL 演練

上 VPS 之前，先在本機的 WSL（Ubuntu 26.04，跟 VPS 同一版）照「第一次部署」整套跑一遍（1～10 步）。gunicorn 不支援 Windows，所以要在 Linux 裡測。
測不到的只有 Cloudflare 本身（100 MB 上限、快取）、正式憑證與 Service Worker。

### 安裝 WSL 與 Ubuntu

1. 系統管理員 PowerShell：`wsl --install --web-download --no-distribution`，裝完重開機。
   Windows 內建的舊版 `wsl` 不認得 `--update`，清單裡也只有不帶版本的 `Ubuntu`，所以要先裝新版 WSL。
2. `wsl --install -d Ubuntu-26.04`，設定使用者名稱與密碼（metrics 那題選什麼都可以）。

### 跟 VPS 不同的地方

照「第一次部署」的 1～10 步做，以下幾步改成這樣，其他步驟原樣照做：

- **第 3 步**：直接從 D 槽的 repo clone，不必登入 GitHub。順便裝開發套件，在 Linux 上跑一次測試：

  ```bash
  git clone /mnt/d/Code/wedding-album /srv/wedding-album
  cd /srv/wedding-album/backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
  .venv/bin/pytest -q
  ```

  - **只會拿到已經 commit 的內容**，之後更新用 `git pull`。`deploy/` 底下改了還沒 commit 的檔案，
    可以直接從 `/mnt/d/Code/wedding-album/deploy/` 複製來試。
  - 出現 `detected dubious ownership`：先執行 `git config --global --add safe.directory /mnt/d/Code/wedding-album/.git`。
  - repo 一定要放在 Linux 這邊（`/srv/...`），不要直接在 `/mnt/d/...` 底下跑：很慢，權限也會讓 nginx 讀不到照片。
    WSL 跳出「在 Windows 磁碟上操作效能不佳」的提示，就是在說這件事，按「不再顯示」即可。
- **第 5 步**：活動碼隨便填，例如 `test`。
- **第 6 步**：沒有 Cloudflare，在同樣的路徑放自簽憑證，nginx 設定就不必改：

  ```bash
  sudo mkdir -p /etc/ssl/wedding-album && sudo openssl req -x509 -nodes -newkey rsa:2048 -days 30 -subj "/CN=localhost" \
      -keyout /etc/ssl/wedding-album/origin.key -out /etc/ssl/wedding-album/origin.pem
  ```

- **第 7 步**：不用換網域（`sed` 那行跳過）。預設網站拿掉之後，用 `localhost` 連進來也會落到這份設定。
- **第 9 步**：網址用 `https://localhost`，自簽憑證要加 `-k`：
  `bash deploy/smoke-test.sh https://localhost test -k`。
  Windows 的瀏覽器打開 `https://localhost/?code=test`（WSL 會把 port 轉到 Windows），
  憑證警告按「繼續前往」即可；Service Worker 遇到憑證錯誤不會註冊，離線與加到主畫面在本機測不到。

最後測重開機：PowerShell 執行 `wsl --shutdown`，重新打開 Ubuntu 後什麼都不做，
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
