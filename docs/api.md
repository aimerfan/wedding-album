# API 規格（草稿）

前後端共用的介面約定。**目前是草稿**：內容依照前端 8 支畫面的需要起草，
文末「待確認」的項目定案前，前後端都不要當成定案實作。

改動規則：這份文件改了，`frontend/src/types/album.ts` 和後端要一起跟上。

## 通則

### 位址

- 所有 API 都在 `/api` 底下，例如 `GET /api/photos`。
- 開發時前端（`localhost:5173`）透過 Vite 的 proxy 把 `/api` 轉給 Flask，不必處理 CORS。

### 格式

- 請求與回應都是 JSON（上傳照片例外，用 `multipart/form-data`）。
- 欄位名稱用 **camelCase**（`thumbnailUrl`），跟前端型別一致。Flask 端輸出時自行轉換。
- 時間一律 ISO 8601 並帶時區，例如 `2026-10-17T18:42:00+08:00`。
- id 一律是字串，前端不假設它的格式。

### 照片網址

- 回應裡的 `url`、`thumbnailUrl`、`coverUrl` 都是**可以直接使用的完整網址**。
- 前端不自己組網址。後端換儲存位置（本機磁碟 → 雲端）時，前端完全不用改。

### 身分

賓客不註冊、不設密碼，流程如下：

1. 賓客掃會場的 QR code，打開 `https://<網站>/?code=<活動碼>`。
   QR code 裡裝的就是這個網址，活動碼是網址的一部分。
2. 在歡迎頁輸入暱稱後，前端呼叫 `POST /api/guests`，拿到一組 `token`。
3. 前端把 `token` 存在手機（localStorage），之後每個請求都帶上：

   ```
   Authorization: Bearer <token>
   ```

4. 沒帶或帶錯 `token` 的請求一律回 `401`，前端導回歡迎頁。

**換瀏覽器或換裝置**：在「我的」頁產生一個「接續連結」（也可以顯示成 QR code），
在另一個瀏覽器或電腦打開，就會變成同一位賓客。連結裡放的是**一次性、30 分鐘內有效的接續碼**，
不是 token 本身——網址會留在瀏覽紀錄、可能被轉傳，直接放 token 等於把身分永久交出去。

沒有用接續連結就換手機或清除瀏覽器資料，會變成新的賓客，這是刻意接受的取捨（見 `backend/README.md`）。

### 分頁

列表類 API 用 cursor 分頁。cursor 是後端給的一個「書籤」字串，前端看不懂也不需要懂，
只要原封不動地傳回去：

```
GET /api/photos?limit=30                      ← 第一頁，不帶 cursor
GET /api/photos?limit=30&cursor=<nextCursor>  ← 下一頁，帶上一頁回傳的 nextCursor
```

```json
{ "items": [ ... ], "nextCursor": "eyJ0IjoiMjAyNi0xMC0xN1QxODo0MiJ9" }
```

`nextCursor` 為 `null` 代表沒有下一頁。`limit` 預設 30、上限 100。

**為什麼不用「第幾頁」或「從第幾張開始」**：婚禮當下一直有人在上傳。
如果用「從第 30 張開始」，你看完第一頁時前面又多了 5 張新照片，第二頁就會重複看到 5 張舊的。
cursor 記的是「上一頁最後一張是哪張」，不管前面新增多少張，下一頁都從那張之後接著算。

### 錯誤

HTTP 狀態碼表示錯誤類別，回應內容固定是這個形狀：

```json
{ "error": { "code": "photo_not_found", "message": "找不到這張照片" } }
```

- `code`：給程式判斷用的英文代碼，由本專案自訂。
- `message`：可以直接顯示給賓客看的中文訊息。

下表的狀態碼都是 HTTP 標準定義的，不是自訂的：

| 狀態碼 | 標準名稱 | 本專案何時用 |
| --- | --- | --- |
| `400` | Bad Request | 欄位缺漏或格式錯（例如祝福超過字數） |
| `401` | Unauthorized | 沒帶 token、token 無效、活動碼錯誤 |
| `403` | Forbidden | 有身分但沒權限（例如刪別人的照片） |
| `404` | Not Found | 東西不存在 |
| `413` | Content Too Large | 上傳的檔案太大 |
| `415` | Unsupported Media Type | 不支援的檔案格式 |
| `429` | Too Many Requests | 短時間內上傳太多（防止灌爆） |

## 資料形狀

### Guest

```json
{ "id": "g_1", "nickname": "小慧", "relation": "新娘的大學同學" }
```

`relation`（與新人的關係）是選填的自由文字，可能沒有。

### Photo

```json
{
  "id": "p_1",
  "kind": "photo",
  "url": "https://…/p_1.jpg",
  "thumbnailUrl": "https://…/p_1_thumb.jpg",
  "width": 3024,
  "height": 4032,
  "durationSeconds": null,
  "uploader": { "id": "g_1", "nickname": "小慧" },
  "uploadedAt": "2026-10-17T18:42:00+08:00",
  "takenAt": "2026-10-17T18:40:12+08:00",
  "blessing": "祝你們白頭偕老！",
  "likeCount": 12,
  "likedByMe": false,
  "favoritedByMe": false,
  "tag": "banquet"
}
```

- `kind`：`photo` 或 `video`。`durationSeconds` 只有影片才有。
- `width` / `height`：原圖尺寸，前端拿來算比例排版，**一定要有**。
- `takenAt`：從 EXIF 讀出來的拍攝時間，讀不到就是 `null`。
- `tag`：`welcome`（迎賓）、`ceremony`（儀式）、`banquet`（宴客）其中一個，上傳時由賓客選。
- `likedByMe`：我有沒有按讚。讚是**公開的**，所有人都看得到 `likeCount`，會算進上傳者的「獲得的讚」。
- `favoritedByMe`：我有沒有收藏。收藏是**私人的**書籤，只出現在自己「我的 → 收藏」，別人看不到、也不計數。

> 跟前端現況的差異：
> - `album.ts` 目前是 `tags: PhotoTag[]`（可多選），這裡改成單選的 `tag`。
> - `album.ts` 有 `location`（拍攝地點），這裡拿掉了。所有環節都在同一個婚宴會館，
>   地點不會提供任何資訊；照片是哪個環節拍的，看 `tag` 就知道。

### Blessing

```json
{
  "id": "b_1",
  "guest": { "id": "g_2", "nickname": "阿凱" },
  "text": "祝你們白頭偕老！",
  "createdAt": "2026-10-17T19:30:00+08:00",
  "photoId": "p_2"
}
```

`photoId` 為 `null` 代表是留言牆上的獨立祝福，沒有附照片。

### WeddingCollection / WeddingPhoto

婚紗照是新人自己的照片，沒有上傳者、按讚、收藏，所以**不沿用 Photo**，另外定義：

```json
{
  "id": "w_1",
  "title": "陽明山外景",
  "caption": "陽明山 · 2026 春末 · 共 24 張",
  "coverUrl": "https://…/w_1_cover.jpg",
  "photos": [
    { "id": "wp_1", "url": "https://…", "thumbnailUrl": "https://…", "width": 3000, "height": 2000 }
  ]
}
```

> 跟前端現況的差異：`album.ts` 的 `WeddingCollection.photos` 目前是 `Photo[]`，定案後要改成 `WeddingPhoto[]`。

## API 列表

### 身分

| 方法 | 路徑 | 需要 token | 用途 |
| --- | --- | --- | --- |
| `POST` | `/api/guests` | ✗ | 加入相簿：用活動碼 + 暱稱，向後端領一組 token |
| `POST` | `/api/guests/claim` | ✗ | 用接續碼領回同一位賓客的 token |
| `GET` | `/api/me` | ✓ | 目前這位賓客的資料與統計 |
| `PATCH` | `/api/me` | ✓ | 改暱稱或與新人的關係 |
| `POST` | `/api/me/transfer-codes` | ✓ | 產生接續連結 |

前兩支是「領 token」的 API。這時賓客手上還沒有 token，所以這兩支不檢查 token，
改用活動碼或接續碼確認對方有資格進來。

`POST /api/guests`

```json
// 請求：relation 可不帶
{ "eventCode": "A1B2C3", "nickname": "小慧", "relation": "新娘的大學同學" }

// 回應 201
{ "token": "…", "guest": { "id": "g_1", "nickname": "小慧", "relation": "新娘的大學同學" } }
```

`POST /api/me/transfer-codes`

```json
// 回應 201
{
  "url": "https://<網站>/continue?code=7Q2K9M",
  "expiresAt": "2026-10-17T21:30:00+08:00"
}
```

`POST /api/guests/claim`

```json
// 請求
{ "transferCode": "7Q2K9M" }

// 回應 200：跟 POST /api/guests 一樣的形狀。接續碼用過一次就失效
{ "token": "…", "guest": { ... } }
```

`GET /api/me`

```json
{
  "guest": { "id": "g_1", "nickname": "小慧", "relation": "新娘的大學同學" },
  "stats": { "uploaded": 12, "favorited": 8, "likesReceived": 24, "blessings": 1 }
}
```

### 相簿

| 方法 | 路徑 | 用途 |
| --- | --- | --- |
| `GET` | `/api/stats` | 首頁的統計數字 |
| `GET` | `/api/photos` | 照片列表（分頁） |
| `GET` | `/api/photos/{id}` | 單張照片 |
| `POST` | `/api/photos` | 上傳一個檔案 |
| `DELETE` | `/api/photos/{id}` | 刪除自己上傳的照片 |
| `PUT` | `/api/photos/{id}/like` | 按讚 |
| `DELETE` | `/api/photos/{id}/like` | 收回讚 |
| `PUT` | `/api/photos/{id}/favorite` | 收藏 |
| `DELETE` | `/api/photos/{id}/favorite` | 取消收藏 |

以上都需要 token。

`GET /api/stats`

```json
{ "photoCount": 247, "guestCount": 32, "blessingCount": 47 }
```

`GET /api/photos` 的篩選參數（都可以不帶）：

| 參數 | 對應畫面 |
| --- | --- |
| `tag=welcome` / `ceremony` / `banquet` | 首頁的「迎賓／儀式／宴客」 |
| `kind=video` | 首頁的「影片」 |
| `date=today` | 首頁的「今天」（以台灣時間算） |
| `uploader=me` | 個人頁的「我上傳的」 |
| `uploader=<guestId>` | 照片詳情點上傳者 → 這個人拍的所有照片 |
| `favorited=true` | 個人頁的「收藏」 |

排序固定是上傳時間新到舊。

按讚、收藏用 `PUT` / `DELETE`：重複按不會出錯，網路不穩重送也安全。回應是更新後的 Photo。

### 上傳

`POST /api/photos`，`multipart/form-data`，**一個請求傳一個檔案**。
一次選 10 張就送 10 個請求。好處是每張都有自己的進度條，失敗時只要重傳那一張。

| 欄位 | 必填 | 說明 |
| --- | --- | --- |
| `file` | ✓ | 照片或影片檔 |
| `tag` | | `welcome` / `ceremony` / `banquet`，預設 `banquet`（多數賓客只參加宴客） |

回應 `201`，內容是建立好的 Photo。

祝福**不跟著照片一起送**：所有檔案都傳完後，前端再呼叫一次 `POST /api/blessings` 並帶上第一張的 `photoId`。
否則一次傳 10 張，同一句祝福會在留言牆上出現 10 次。

**檔案格式與大小（暫定，可隨時調整，見下方「設定」）**

| | 格式 | 單檔上限 |
| --- | --- | --- |
| 照片 | JPEG、PNG、HEIC、WebP | 30 MB |
| 影片 | MP4、MOV | 200 MB |

- **原檔原封不動保存**，之後要整批匯出給新人時拿到的就是原始畫質。
- 後端另外產生 JPEG 縮圖給畫面用。iPhone 的 HEIC 很多瀏覽器（例如 Android 的 Chrome）看不懂，
  不轉的話別人會看到破圖。

**同時上傳的人很多時**

以約 200 位賓客估算：

- 前端：每支手機**同時最多傳 3 個檔案**，其餘排隊。不要 10 張同時送，會互搶網路，每張都變慢。
- 後端：每位賓客每小時上限 300 個檔案（暫定），超過回 `429`。正常賓客碰不到，主要是防活動碼外流後被灌爆。
- 真正的瓶頸通常是**會場網路**，不是 API。

### 設定

| 方法 | 路徑 | 需要 token | 用途 |
| --- | --- | --- | --- |
| `GET` | `/api/config` | ✗ | 前端要遵守的各種上限 |

```json
{
  "maxPhotoBytes": 31457280,
  "maxVideoBytes": 209715200,
  "maxUploadsPerHour": 300,
  "uploadConcurrency": 3,
  "maxBlessingLength": 200,
  "uploadsOpen": true
}
```

**所有上限都只在後端設定一份**，前端開啟時向這支 API 讀取，不寫死在前端程式裡。
婚禮當天要臨時調整（例如會場網路太慢，把同時上傳數從 3 降到 1），只要改後端設定、重新啟動後端，
不必重新部署前端，賓客重新整理頁面就會套用。

`uploadsOpen` 為 `false` 時代表相簿已截止上傳，前端隱藏上傳按鈕，`POST /api/photos` 回 `403`。

### 祝福

| 方法 | 路徑 | 用途 |
| --- | --- | --- |
| `GET` | `/api/blessings` | 留言牆（分頁）；`guest=me` 只列自己的 |
| `POST` | `/api/blessings` | 留下祝福 |

`POST /api/blessings`

```json
// 請求：photoId 不帶就是留言牆上的獨立祝福
{ "text": "新婚快樂！", "photoId": "p_1" }

// 回應 201：建立好的 Blessing
```

`text` 上限 200 字，前後空白會被去掉，去掉後是空字串回 `400`。

### 婚紗集

| 方法 | 路徑 | 用途 |
| --- | --- | --- |
| `GET` | `/api/collections` | 所有系列，含每個系列的照片 |

婚紗照只有幾十張，一次全部回傳，不分頁。

## 待確認

下面這些會影響 API 的樣子，定案後更新本文件：

1. **要不要有「管理員」刪照片？** 活動碼外流時，陌生人傳的不當照片會出現在所有賓客眼前。
   建議的最小做法：後端產生一條管理員連結，打開的人就有權刪除任何照片。
   婚禮當天新人很忙，這條連結可以交給一位信任的朋友（或開發者自己）代管。
2. **相簿開放期間。** 預計開放兩週到一個月。截止後要改成「只能看不能傳」（`uploadsOpen: false`），還是整站關閉？
3. **正式環境前後端是不是同一個網域？** 前端放 Cloudflare Pages、後端放別處的話，後端要開 CORS。
4. **首頁的「搜尋」要搜什麼？** 目前先保留按鈕。建議做成「找賓客」：輸入暱稱，列出這個人拍的照片
   （對應 `uploader=<guestId>`，需要再加一支搜尋賓客的 API）。確定不需要的話就把按鈕拿掉。

## 已決定不做

- **「不允許其他賓客看到」的照片**：設計稿的上傳頁有這個開關，目前沒有確認的需求，先不做。新人提出需要再加。
- **附加拍攝地點**：所有環節都在同一個會館，改用照片分類（`tag`）區分環節。
