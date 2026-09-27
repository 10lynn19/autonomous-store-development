#!/bin/zsh
set -u

REMOTE="yolo-gpu"
WATCHER="C:/Market/autonomous-store-development/scripts/windows/watch_a4_s_training.ps1"

echo "A4-S live training log — Windows RTX 5070"
echo "Press Control-C to stop watching; it will not stop training."
echo ""
ssh -t "$REMOTE" "powershell -NoProfile -ExecutionPolicy Bypass -File ${WATCHER}"

echo ""
read -k 1 "?Press any key to close this window..."
