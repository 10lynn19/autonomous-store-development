#!/bin/zsh
set -euo pipefail

echo "B 系列遮挡训练进度 / B-series occlusion training progress"
echo "训练顺序：C0 clean control → C2 real pickup"
echo "按 Control-C 只会关闭此进度窗口，不会中断训练。"
echo ""

ssh -t yolo-gpu \
  "powershell -NoProfile -ExecutionPolicy Bypass -File C:/Market/framework_v1_rebuild/scripts/windows/watch_b_occlusion_training.ps1"
