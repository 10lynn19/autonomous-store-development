#!/bin/zsh
set -euo pipefail

PORT=8768
URL="http://127.0.0.1:${PORT}"

echo "B1 Camera 标注 / B1 Camera Annotation"
echo "数据保存在 Windows: C:\\Market\\framework_v1_rebuild\\data\\datasets_B\\b1_camera_addition"
echo "关闭此 Terminal 会停止网页服务，但已经保存的标注不会丢失。"
echo "Closing this Terminal stops the server; saved labels remain on Windows."
echo ""

(sleep 3; open "$URL") &
ssh -t -L "${PORT}:127.0.0.1:${PORT}" yolo-gpu \
  "powershell -NoProfile -Command \"Set-Location 'C:\\Market\\framework_v1_rebuild'; & '.venv\\Scripts\\python.exe' 'src\\annotate_test_videos.py' --dataset 'data\\datasets_B\\b1_camera_addition' --host 127.0.0.1 --port ${PORT} --no-browser\""

echo ""
read -k 1 "?Press any key to close this window..."
