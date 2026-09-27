#!/bin/zsh
set -euo pipefail

PORT=8771
URL="http://127.0.0.1:${PORT}"

echo "B5 Pickup/Occlusion 标注 / B5 Pickup-Occlusion Annotation"
echo "来源：camera_pickup_coke / oreo / goodwipes（每段 60 帧，共 180 帧）"
echo "不读取或使用 data/videos_B/test。"
echo "标签保存在 Windows: C:\\Market\\autonomous-store-development\\data\\datasets_B\\b5_occlusion_addition"
echo "关闭此 Terminal 会停止网页服务；已经保存的标注不会丢失。"
echo ""

(sleep 4; open "$URL") &
ssh -t -L "${PORT}:127.0.0.1:${PORT}" yolo-gpu \
  "powershell -NoProfile -Command \"Set-Location 'C:\\Market\\autonomous-store-development'; & '.venv\\Scripts\\python.exe' 'src\\annotate_test_videos.py' --videos 'data\\videos_B\\camera' --dataset 'data\\datasets_B\\b5_occlusion_addition' --pattern 'camera_pickup_*' --frames-per-video 60 --split train --classes coke_zero oreo goodwipes --prepare --host 127.0.0.1 --port ${PORT} --no-browser\""

echo ""
read -k 1 "?Press any key to close this window..."
