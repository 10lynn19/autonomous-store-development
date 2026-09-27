#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

DATASET="data/datasets_A/camera_more_thinkbar_ziploc"

echo "新增 Think Bar + Ziploc 相机数据标注 / Additional camera-data annotation"
echo "Dataset: $DATASET"
echo "8 videos × 30 frames = approximately 240 frames"
echo "旧数据不会被覆盖 / Existing datasets will not be overwritten"
echo ""

if [[ ! -f "$DATASET/manifest.json" ]]; then
  python3 src/annotate_test_videos.py \
    --videos data/videos_A/camera \
    --dataset "$DATASET" \
    --recursive \
    --pattern '*_more*.mov' \
    --frames-per-video 30 \
    --split train \
    --prepare \
    --prepare-only
fi

python3 src/annotate_test_videos.py \
  --dataset "$DATASET" \
  --port 8767
