#!/usr/bin/env bash
# 更新版本：抓最新程式、建前端、裝後端套件、重啟兩個池。在主機上以 deploy 帳號執行。
#
# 用法：bash /srv/wedding-album/deploy/update.sh
#
# deploy/systemd 有改會自動套用；nginx 設定要換網域，不自動套用，有改到時只提醒。

set -euo pipefail

REPO=$(cd "$(dirname "$0")/.." && pwd)
cd "$REPO"

# 先 pull，再改跑新版的自己：bash 邊讀邊執行，pull 改到這個檔案時繼續跑舊的會亂掉
if [[ "${1:-}" != --pulled ]]; then
    sudo -v   # 先問 sudo 密碼，不要建置到一半才停下來等
    before=$(git rev-parse HEAD)
    git pull --ff-only
    exec bash "$REPO/deploy/update.sh" --pulled "$before"
fi
before=$2

if [[ "$before" == "$(git rev-parse HEAD)" ]]; then
    echo "沒有新的 commit，照樣重建與重啟"
else
    git log --oneline "$before..HEAD"
fi
changed() { [[ -n "$(git diff --name-only "$before" HEAD -- "$@")" ]]; }

echo "== 前端"
cd "$REPO/frontend" && npm ci && npm run build

echo "== 後端"
cd "$REPO/backend" && .venv/bin/pip install -r requirements.txt

if changed deploy/systemd; then
    echo "== systemd 設定有改，重新複製"
    sudo cp "$REPO"/deploy/systemd/*.service /etc/systemd/system/
    sudo systemctl daemon-reload
fi

echo "== 重啟（上傳池最多等 120 秒讓進行中的上傳做完）"
sudo systemctl restart wedding-album-api wedding-album-upload

for _ in $(seq 15); do
    if curl -sf -o /dev/null http://127.0.0.1:8000/api/config; then
        break
    fi
    sleep 1
done
if ! systemctl is-active --quiet wedding-album-api wedding-album-upload \
    || ! curl -sf -o /dev/null http://127.0.0.1:8000/api/config; then
    echo "後端沒有正常起來，看記錄："
    echo "  sudo journalctl -u wedding-album-api -u wedding-album-upload --since '5 min ago'"
    exit 1
fi
echo "api、upload 都在跑，/api/config 正常"

if changed deploy/nginx; then
    echo
    echo "注意：deploy/nginx 有改，要手動套用（見 deploy/README.md 的「更新版本」，記得換網域）"
fi
if changed deploy/wedding-album.env.example; then
    echo
    echo "注意：環境變數範本有改，對照 /etc/wedding-album/env 看要不要補新的設定"
fi
