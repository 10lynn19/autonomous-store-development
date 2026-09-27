#!/bin/zsh
set -euo pipefail

PORT=8769
URL="http://127.0.0.1:${PORT}"

echo "B2 Phone 标注 / B2 Phone Annotation"
echo "数据保存在 Windows: C:\\Market\\autonomous-store-development\\data\\datasets_B\\b2_phone_addition"
echo "关闭此 Terminal 会停止网页服务，但已经保存的标注不会丢失。"
echo "Closing this Terminal stops the server; saved labels remain on Windows."
echo ""

(sleep 3; open "$URL") &
ssh -t -L "${PORT}:127.0.0.1:${PORT}" yolo-gpu \
  "powershell -NoProfile -Command \"Set-Location 'C:\\Market\\autonomous-store-development'; & '.venv\\Scripts\\python.exe' 'src\\annotate_test_videos.py' --dataset 'data\\datasets_B\\b2_phone_addition' --host 127.0.0.1 --port ${PORT} --no-browser\""

echo ""
read -k 1 "?Press any key to close this window..."
