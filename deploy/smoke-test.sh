#!/usr/bin/env bash
# 部署後的檢查：透過 nginx 打一輪，確認前端、API 分流、上傳、照片檔與快取標頭都正確。
#
# 用法：bash deploy/smoke-test.sh <網址> <活動碼> [-k]
#   本機 WSL（自簽憑證要加 -k）：bash deploy/smoke-test.sh https://localhost test -k
#   VPS：                        bash deploy/smoke-test.sh https://album.example.com 活動碼
#
# 會建立一位「部署測試」賓客、上傳一張照片再刪掉。賓客會留在資料庫裡，所以只在婚禮前跑。
# 產生測試照片要用後端虛擬環境的 Python（有 Pillow），位置不同時用環境變數 PYTHON 指定。

set -u

usage="用法：bash deploy/smoke-test.sh <網址> <活動碼> [-k]"
BASE=${1:?$usage}
EVENT_CODE=${2:?$usage}
BASE=${BASE%/}
CURL=(curl -s --max-time 60)
[[ "${3:-}" == "-k" ]] && CURL+=(-k)
PYTHON=${PYTHON:-$(dirname "$0")/../backend/.venv/bin/python}

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
failures=0

check() {  # check <說明> <實際值> <預期包含的字串>
    if [[ "$2" == *"$3"* ]]; then
        echo "  ok    $1"
    else
        echo "  FAIL  $1：預期包含「$3」，實際是「$2」"
        failures=$((failures + 1))
    fi
}

status() { "${CURL[@]}" -o /dev/null -w '%{http_code}' "$@"; }

header() {  # header <標頭名稱> <curl 參數…>：只取回應標頭裡的那一個值
    local name=$1; shift
    "${CURL[@]}" -o /dev/null -D - "$@" | tr -d '\r' | grep -i "^$name:" | head -1 | cut -d' ' -f2-
}

json() { python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$1" "$2"; }

if [[ "$(status "$BASE/")" == 000 ]]; then
    echo "連不上 $BASE，後面的檢查都跳過。先確認 nginx 有在 80／443 監聽："
    echo "  sudo ss -tlnp | grep -E ':(80|443) '"
    echo "只看到 80 的話，通常是改了設定之後沒有 reload：sudo systemctl reload nginx"
    exit 1
fi

echo "前端"
check "首頁" "$(status "$BASE/")" 200
check "首頁不快取（改版後才拿得到新版）" "$(header Cache-Control "$BASE/")" no-cache
check "sw.js 不快取" "$(header Cache-Control "$BASE/sw.js")" no-cache
check "前端路由交給 index.html" "$(header Content-Type "$BASE/photos/whatever")" text/html

echo "API"
check "GET /api/config" "$(status "$BASE/api/config")" 200
check "不存在的 API 回 JSON 的 404，不是前端頁面" "$(header Content-Type "$BASE/api/no-such-thing")" application/json
head -c 2000000 /dev/zero > "$TMP/big"
check "上傳以外的 API 擋掉 1 MB 以上的請求" \
    "$(status -X POST --data-binary @"$TMP/big" -H 'Content-Type: application/json' "$BASE/api/blessings")" 413

echo "上傳"
"${CURL[@]}" -o "$TMP/guest.json" -H 'Content-Type: application/json' \
    -d "{\"eventCode\": \"$EVENT_CODE\", \"nickname\": \"部署測試\"}" "$BASE/api/guests"
token=$(json "$TMP/guest.json" token 2>/dev/null)
check "加入相簿拿到 token" "${token:+有}" 有
if [[ -z "$token" ]]; then
    echo "  拿不到 token，後面的檢查跳過。回應：$(cat "$TMP/guest.json")"
    exit 1
fi

# 每次換一個顏色：同一個檔案重傳會被當成重送，回 200 而不是 201
"$PYTHON" -c 'import random, sys; from PIL import Image
Image.new("RGB", (400, 300), tuple(random.randrange(256) for _ in range(3))).save(sys.argv[1], "JPEG")' "$TMP/test.jpg"
code=$("${CURL[@]}" -o "$TMP/photo.json" -w '%{http_code}' -H "Authorization: Bearer $token" \
    -F "file=@$TMP/test.jpg;type=image/jpeg" -F tag=banquet "$BASE/api/photos")
check "POST /api/photos" "$code" 201
if [[ "$code" != 201 ]]; then
    echo "  上傳失敗，後面的檢查跳過。回應：$(cat "$TMP/photo.json")"
    exit 1
fi
photo_id=$(json "$TMP/photo.json" id)
display_url=$(json "$TMP/photo.json" displayUrl)
original_url=$(json "$TMP/photo.json" url)

echo "照片檔"
check "顯示用照片" "$(status "$BASE$display_url")" 200
check "照片的檔案類型" "$(header Content-Type "$BASE$display_url")" image/jpeg
check "照片長效快取" "$(header Cache-Control "$BASE$display_url")" immutable
check "支援 Range（iPhone 播影片要用）" "$(status -H 'Range: bytes=0-99' "$BASE$original_url")" 206

echo "清理"
check "刪掉測試照片" "$(status -X DELETE -H "Authorization: Bearer $token" "$BASE/api/photos/$photo_id")" 204

echo
if ((failures)); then
    echo "有 $failures 項沒通過"
    exit 1
fi
echo "全部通過。上傳有沒有走到上傳池，要看上傳池的記錄裡有沒有 POST /api/photos"
