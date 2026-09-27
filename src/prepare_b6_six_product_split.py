#!/usr/bin/env python3
"""Create a deterministic train/validation split for the six-product addition."""

from __future__ import annotations

import argparse
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/datasets_B/b6_six_product_addition"
TARGET = ROOT / "data/datasets_B/b6_six_product_split"
EXPECTED_IMAGES = 299
CLASS_COUNT = 6


def class_counts(labels: list[Path]) -> Counter[int]:
    counts: Counter[int] = Counter()
    for label in labels:
        for line in label.read_text(encoding="utf-8").splitlines():
            if line.strip():
                counts[int(line.split()[0])] += 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    images = sorted((SOURCE / "images/train").glob("*.jpg"))
    labels = sorted((SOURCE / "labels/train").glob("*.txt"))
    if len(images) != EXPECTED_IMAGES or len(labels) != EXPECTED_IMAGES:
        raise SystemExit(
            f"Expected {EXPECTED_IMAGES} images and labels, got {len(images)} images and {len(labels)} labels"
        )
    missing = [image.stem for image in images if not (SOURCE / "labels/train" / f"{image.stem}.txt").is_file()]
    if missing:
        raise SystemExit(f"Missing labels for {len(missing)} images")

    if TARGET.exists():
        if not args.overwrite:
            raise SystemExit(f"Refusing to overwrite {TARGET}; pass --overwrite intentionally")
        shutil.rmtree(TARGET)

    groups: dict[str, list[Path]] = {}
    for image in images:
        video = image.stem.rsplit("__", 1)[0]
        groups.setdefault(video, []).append(image)

    split_labels: dict[str, list[Path]] = {"train": [], "val": []}
    for video, video_images in sorted(groups.items()):
        for index, image in enumerate(video_images):
            split = "val" if index % 5 == 4 else "train"
            image_dir = TARGET / "images" / split
            label_dir = TARGET / "labels" / split
            image_dir.mkdir(parents=True, exist_ok=True)
            label_dir.mkdir(parents=True, exist_ok=True)
            label = SOURCE / "labels/train" / f"{image.stem}.txt"
            shutil.copy2(image, image_dir / image.name)
            shutil.copy2(label, label_dir / label.name)
            split_labels[split].append(label_dir / label.name)

    (TARGET / "classes.txt").write_text(
        "coke_zero\noreo\ngoodwipes\ncheetos\nsprite\nsour_patch_kids\n",
        encoding="utf-8",
    )
    for split in ("train", "val"):
        counts = class_counts(split_labels[split])
        print(f"{split}: {len(split_labels[split])} images; " +
              ", ".join(f"class {class_id}={counts[class_id]}" for class_id in range(CLASS_COUNT)))


if __name__ == "__main__":
    main()
