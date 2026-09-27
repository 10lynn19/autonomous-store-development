#!/bin/zsh
set -euo pipefail

echo "B_6 六商品训练进度 / B_6 six-product training progress"
echo "按 Control-C 只会关闭进度窗口，不会中断训练。"
echo ""

ssh -t yolo-gpu \
  "powershell -NoProfile -ExecutionPolicy Bypass -File C:/Market/framework_v1_rebuild/scripts/windows/watch_b6_training.ps1"
