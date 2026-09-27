#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE="yolo-gpu"
REMOTE_ROOT="C:/Market/autonomous-store-development"

echo "Syncing A0 code, logs/A_series, and training results from Windows..."
ssh "$REMOTE" \
  "tar -czf - -C ${REMOTE_ROOT} src configs scripts docs requirements.txt outputs/A_series/training/a0_base logs/A_series" \
  | tar -xzf - -C "$ROOT"

echo "Saved on Mac under:"
echo "  $ROOT/outputs/A_series/training/a0_base"
echo "  $ROOT/logs/A_series"
