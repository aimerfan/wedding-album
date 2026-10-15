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
## 狀態

- 2026-10-15 已上線：`https://hungting.date`（Vultr 東京）。
- 第一次部署的完整步驟在 [init_steps.md](init_steps.md)，只有換主機或重建主機時才要再做。
- 部署的計畫與選用理由、上線前要驗證與婚禮當天要做的事，見 [docs/deploy/README.md](../docs/deploy/README.md)。

## 檔案

| 檔案 | 放到主機的哪裡 |
| --- | --- |
| `nginx/wedding-album.conf` | `/etc/nginx/sites-available/`，再連到 `sites-enabled/` |
| `systemd/*.service` | `/etc/systemd/system/` |
| `wedding-album.env.example` | 複製成 `/etc/wedding-album/env`，填好再設成 `chmod 600` |
| `update.sh` | 不用放，更新版本時在主機上執行，見「更新版本」 |
| `smoke-test.sh` | 不用放，在主機上執行，見「檢查」 |

## 主機上的路徑

設定檔裡寫死了這些路徑，換位置的話三種檔案要一起改：

| 路徑 | 內容 |
| --- | --- |
| `/srv/wedding-album/` | 這個 repo |
| `/srv/wedding-album/backend/.venv/` | 後端的虛擬環境（Python 3.14） |
| `/srv/wedding-album/frontend/dist/` | 前端建置結果 |
| `/var/lib/wedding-album/` | 資料庫與照片檔（`MEDIA_DIR`），擁有者是 `wedding` |

後端以 `wedding` 這個系統使用者執行。照片檔要讓 nginx 讀得到：資料夾 755、檔案 644（Python 預設就是這樣）。

## 登入主機

```bash
ssh deploy@<主機 IP>
```

- 只能用金鑰登入：root 與密碼登入都關掉了。
- 換一台還沒放金鑰的電腦：用廠商後台的網頁終端機（Vultr 是 View Console）以 `deploy` 加密碼登入，
  把那台的公鑰（`ssh-keygen -t ed25519` 產生的 `~/.ssh/id_ed25519.pub`）加進 `~/.ssh/authorized_keys`。
  網頁終端機不經過 SSH，不受金鑰限制，也可以直接在裡面執行更新。
- `sudo` 要輸入 `deploy` 帳號的密碼。

## 更新版本

以 `deploy` 帳號執行：

```bash
bash /srv/wedding-album/deploy/update.sh
```

腳本會 `git pull`、建前端、裝後端套件、重啟兩個池，最後確認 `/api/config` 有回應。

- `deploy/systemd` 有改會自動重新複製並 `daemon-reload`。
- `deploy/nginx` 有改只會提醒，要自己套用（`hungting.date` 換成實際網域）：

  ```bash
  sudo cp /srv/wedding-album/deploy/nginx/wedding-album.conf /etc/nginx/sites-available/
  sudo sed -i 's/album\.example\.com/hungting.date/g' /etc/nginx/sites-available/wedding-album.conf
  sudo nginx -t && sudo systemctl reload nginx
  sudo ss -tlnp | grep -E ':(80|443) '
  ```

  最後一行一定要看到 443。`nginx -t` 只檢查語法，沒有 reload 成功的話跑的還是舊設定。
- 私人 repo 若主機上沒存 GitHub 憑證，`git pull` 會再問帳號與 token。
- 重啟上傳池時，進行中的上傳最多等 120 秒做完。中斷的上傳前端會自動重送，同一個檔案不會重複。

## 檢查與記錄

完整檢查（前端、API 分流、上傳、照片檔與快取標頭）：

```bash
bash /srv/wedding-album/deploy/smoke-test.sh https://hungting.date 活動碼
```

會建一位「部署測試」賓客、上傳一張照片再刪掉。賓客會留在資料庫，所以**只在婚禮前跑**，`update.sh` 不會自動跑它。

看服務狀態與記錄：

```bash
systemctl status wedding-album-api wedding-album-upload --no-pager | grep -E "●|Active:"
journalctl -u wedding-album-api -u wedding-album-upload --since "10 min ago"
journalctl -u wedding-album-upload -f   # 婚禮當天盯上傳
```

## 要注意的地方

- **刪掉的照片在 Cloudflare 上還會留著。** 照片檔設了 30 天的長效快取，管理員刪掉不適當的照片後，
  知道網址的人仍然看得到。要馬上消失的話，到 Cloudflare 的 Caching → Purge Cache 清掉那張的網址
  （`/media/photos/<照片 id>/` 底下的 original、display、thumb 三個檔）。
- **Cloudflare 的上限**：免費方案單一請求最多 100 MB，回應要在 100 秒內開始，所以後端的影片上限是 95 MB。
- **還沒有備份。** 資料庫與照片都只在這一台主機上。資料庫備份方式見 backend/README.md 的「資料庫」。
- **nginx 的記錄看到的都是 Cloudflare 的 IP。** 目前後端不依 IP 判斷任何事，需要查真實 IP 時
  再加 `real_ip_header CF-Connecting-IP` 與 Cloudflare 的 IP 範圍。
- **worker 數量還沒壓測過**，目前是先抓的數字（一般池 4、上傳池 3），彩排時依 CPU 與記憶體用量再調。
