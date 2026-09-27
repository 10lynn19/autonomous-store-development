#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "Starting the local test annotation tool..."
echo "Labels are saved immediately. Press Control-C to stop the server."
python3 src/annotate_test_videos.py
