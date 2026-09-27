#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "A3 Camera-clean annotation"
echo "Dataset: data/datasets_A/a3_camera_addition (144 frames, 48 per class)"
echo "Pickup/occlusion videos are intentionally excluded."
echo ""
python3 src/annotate_test_videos.py \
  --dataset data/datasets_A/a3_camera_addition \
  --port 8766
