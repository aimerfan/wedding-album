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

1. 主機裝好 nginx、Python 3.14、Node（建置前端用）。
2. 建使用者與資料夾：`useradd --system wedding`，建立 `/var/lib/wedding-album/` 並交給 `wedding`。
3. 抓 repo 到 `/srv/wedding-album/`，在 `backend/` 建虛擬環境並 `pip install -r requirements.txt`。
4. 在 `frontend/` 執行 `npm ci && npm run build`。
5. 填好 `/etc/wedding-album/env`。`EVENT_CODE` 沒設的話後端不會啟動。
6. Cloudflare：DNS 開代理（橘色雲），SSL 模式設 **Full (strict)**。到 SSL/TLS → Origin Server 產生憑證，
   存到 `/etc/ssl/wedding-album/origin.pem` 與 `origin.key`。
7. 放好 nginx 設定，`nginx -t` 通過後 `systemctl reload nginx`。
8. `systemctl daemon-reload && systemctl enable --now wedding-album-api wedding-album-upload`。
   啟動前會先自動跑一次 `wedding-album-init`，建立資料表。
9. 匯入婚紗照與祝福（見 backend/README.md），指令要以 `wedding` 身分、帶著同一份環境變數執行。

## 更新版本

```bash
cd /srv/wedding-album && git pull
cd frontend && npm ci && npm run build
cd ../backend && .venv/bin/pip install -r requirements.txt
systemctl restart wedding-album-api wedding-album-upload
```

重啟上傳池時，進行中的上傳最多等 120 秒做完。但前端只要發現上傳失敗就會自動重送，同一個檔案也不會重複。

## 要注意的地方

- **刪掉的照片在 Cloudflare 上還會留著。** 照片檔設了 30 天的長效快取，管理員刪掉不適當的照片後，
  知道網址的人仍然看得到。要馬上消失的話，到 Cloudflare 的 Caching → Purge Cache 清掉那張的網址
  （`/media/photos/<照片 id>/` 底下的 original、display、thumb 三個檔）。
- **Cloudflare 的上限**：免費方案單一請求最多 100 MB，回應要在 100 秒內開始，所以後端的影片上限是 95 MB。
- **還沒有備份。** 資料庫與照片都只在這一台主機上。資料庫備份方式見 backend/README.md 的「資料庫」。
- **nginx 的記錄看到的都是 Cloudflare 的 IP。** 目前後端不依 IP 判斷任何事，需要查真實 IP 時
  再加 `real_ip_header CF-Connecting-IP` 與 Cloudflare 的 IP 範圍。
- **worker 數量還沒壓測過**，目前是先抓的數字（一般池 4、上傳池 3），彩排時依 CPU 與記憶體用量再調。
