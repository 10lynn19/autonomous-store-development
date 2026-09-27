#!/bin/zsh
set -euo pipefail

PORT=8770
URL="http://127.0.0.1:${PORT}"

echo "B 测试集 Ground Truth 标注 / B Test Ground-Truth Annotation"
echo "439 frames from 8 held-out videos"
echo "数据保存在 Windows: C:\\Market\\autonomous-store-development\\data\\datasets_B\\test_ground_truth"
echo "测试帧不会进入训练集 / Test frames will never be used for training."
echo "关闭此 Terminal 会停止网页服务，但已经保存的标注不会丢失。"
echo ""

(sleep 3; open "$URL") &
ssh -t -L "${PORT}:127.0.0.1:${PORT}" yolo-gpu \
  "powershell -NoProfile -Command \"Set-Location 'C:\\Market\\autonomous-store-development'; & '.venv\\Scripts\\python.exe' 'src\\annotate_test_videos.py' --dataset 'data\\datasets_B\\test_ground_truth' --host 127.0.0.1 --port ${PORT} --no-browser\""

echo ""
read -k 1 "?Press any key to close this window..."
