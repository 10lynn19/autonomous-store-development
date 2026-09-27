#!/bin/zsh
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE="yolo-gpu"
WATCHER="C:/Market/framework_v1_rebuild/scripts/windows/watch_a0_training.ps1"

echo "A0 live training log — Windows RTX 5070"
echo "Press Control-C only if you want to stop watching; it will not stop training."
echo ""

ssh -t "$REMOTE" \
  "powershell -NoProfile -ExecutionPolicy Bypass -File ${WATCHER}"
STATUS=$?

if [[ $STATUS -eq 0 ]]; then
  echo ""
  "$ROOT/scripts/mac/sync_a0_results_from_windows.command"
else
  echo "Monitor ended with status $STATUS. Training may still be running."
fi

echo ""
read -k 1 "?Press any key to close this window..."
