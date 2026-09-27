#!/bin/zsh
set -u

echo "B0 live training log — Windows RTX 5070"
echo "Press Control-C to stop watching; training will continue on Windows."
echo ""

ssh -t yolo-gpu \
  "powershell -NoProfile -ExecutionPolicy Bypass -File C:/Market/framework_v1_rebuild/scripts/windows/watch_b0_training.ps1"

echo ""
read -k 1 "?Press any key to close this window..."
