#!/usr/bin/env python3
"""Check the B5 pickup annotation set before using it for training."""

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/datasets_B/b5_occlusion_addition"
EXPECTED_CLASSES = ["coke_zero", "oreo", "goodwipes"]


def main() -> None:
    manifest = json.loads((DATASET / "manifest.json").read_text(encoding="utf-8"))
    if manifest["classes"] != EXPECTED_CLASSES or manifest["split"] != "train":
        raise SystemExit("Unexpected classes or split in B5 manifest")
    items = manifest["items"]
    if len(items) != 180 or len({item["id"] for item in items}) != 180:
        raise SystemExit(f"Expected 180 unique frames, found {len(items)}")

    videos = Counter()
    classes = Counter()
    empty = 0
    for item in items:
        if not item["video"].startswith("camera_pickup_"):
            raise SystemExit(f"Unexpected source video: {item['video']}")
        image = DATASET / "images/train" / item["image"]
        label = DATASET / "labels/train" / f"{item['id']}.txt"
        if not image.is_file() or not label.is_file():
            raise SystemExit(f"Missing image or completed label: {item['id']}")
        videos[item["video"]] += 1
        lines = label.read_text(encoding="utf-8").splitlines()
        if not lines:
            empty += 1
        for line in lines:
            parts = line.split()
            if len(parts) != 5:
                raise SystemExit(f"Malformed label: {label}")
            class_id = int(parts[0])
            cx, cy, width, height = map(float, parts[1:])
            if class_id not in range(3) or width <= 0 or height <= 0:
                raise SystemExit(f"Invalid class or box size: {label}")
            if not (0 <= cx - width / 2 < cx + width / 2 <= 1):
                raise SystemExit(f"Box outside image width: {label}")
            if not (0 <= cy - height / 2 < cy + height / 2 <= 1):
                raise SystemExit(f"Box outside image height: {label}")
            classes[EXPECTED_CLASSES[class_id]] += 1

    if len(videos) != 3 or any(count != 60 for count in videos.values()):
        raise SystemExit(f"Unexpected source distribution: {dict(videos)}")
    print(json.dumps({
        "images": len(items), "empty_labels": empty,
        "boxes_by_class": dict(classes), "frames_by_video": dict(videos),
    }, indent=2))


if __name__ == "__main__":
    main()
