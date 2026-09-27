#!/usr/bin/env python3
"""Build B0 from isolated Coke Zero, Oreo, and Goodwipes videos."""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

import cv2
import numpy as np

from prepare_a0_base import estimate_box, make_review_sheet, yolo_line


ROOT = Path(__file__).resolve().parents[1]
VIDEOS = {
    "clean_background_coke.mp4": (0, "coke_zero"),
    "clean_background_oreo.mp4": (1, "oreo"),
    "clean_background_goodwipes.mp4": (2, "goodwipes"),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "data/videos_B/clean_background")
    parser.add_argument("--output", type=Path, default=ROOT / "data/datasets_B/b0_base")
    parser.add_argument("--frames-per-video", type=int, default=120)
    parser.add_argument("--val-fraction", type=float, default=0.20)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.output.exists():
        if not args.overwrite:
            raise SystemExit(f"{args.output} exists; pass --overwrite to replace it")
        shutil.rmtree(args.output)
    for split in ("train", "val"):
        (args.output / "images" / split).mkdir(parents=True)
        (args.output / "labels" / split).mkdir(parents=True)
    (args.output / "review").mkdir(parents=True)

    manifest_rows: list[tuple[str, str, int, str, str]] = []
    review_samples = []
    totals = {"train": 0, "val": 0}
    for filename, (class_id, class_name) in VIDEOS.items():
        video_path = args.source / filename
        capture = cv2.VideoCapture(str(video_path))
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            raise SystemExit(f"Cannot read {video_path}")
        indices = np.linspace(0, total_frames - 1, min(args.frames_per_video, total_frames), dtype=int)
        val_start = round(len(indices) * (1.0 - args.val_fraction))
        review_indices = set(np.linspace(0, len(indices) - 1, 8, dtype=int))
        for sequence, frame_index in enumerate(indices):
            capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
            ok, frame = capture.read()
            if not ok:
                continue
            split = "val" if sequence >= val_start else "train"
            box = estimate_box(frame)
            stem = f"{class_name}_{sequence:04d}"
            image_path = args.output / "images" / split / f"{stem}.jpg"
            label_path = args.output / "labels" / split / f"{stem}.txt"
            cv2.imwrite(str(image_path), frame)
            height, width = frame.shape[:2]
            label_path.write_text(yolo_line(class_id, box, width, height), encoding="utf-8")
            manifest_rows.append((stem, filename, int(frame_index), split, class_name))
            totals[split] += 1
            if sequence in review_indices:
                review_samples.append((frame, box, f"{class_name} #{sequence}"))
        capture.release()

    with (args.output / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("image", "source_video", "source_frame", "split", "class"))
        writer.writerows(manifest_rows)
    make_review_sheet(review_samples, args.output / "review/labels_preview.jpg")
    (args.output / "classes.txt").write_text("coke_zero\noreo\ngoodwipes\n", encoding="utf-8")
    print(f"Created B0 dataset: train={totals['train']}, val={totals['val']}")
    print("REQUIRED REVIEW:", args.output / "review/labels_preview.jpg")


if __name__ == "__main__":
    main()
