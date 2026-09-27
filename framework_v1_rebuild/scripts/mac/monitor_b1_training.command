#!/bin/zsh
set -u

echo "B1 live training log — Windows RTX 5070"
echo "Press Control-C to stop watching; training will continue while SSH remains connected."
echo ""
ssh -t yolo-gpu \
  "powershell -NoProfile -ExecutionPolicy Bypass -File C:/Market/framework_v1_rebuild/scripts/windows/watch_b1_training.ps1"
echo ""
read -k 1 "?Press any key to close this window..."
