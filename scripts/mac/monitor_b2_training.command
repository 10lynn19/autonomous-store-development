#!/bin/zsh
set -u

echo "B2 live training log — Windows RTX 5070"
echo "Press Control-C to stop watching; training will continue while SSH remains connected."
echo ""
ssh -t yolo-gpu \
  "powershell -NoProfile -ExecutionPolicy Bypass -File C:/Market/autonomous-store-development/scripts/windows/watch_b2_training.ps1"
echo ""
read -k 1 "?Press any key to close this window..."
