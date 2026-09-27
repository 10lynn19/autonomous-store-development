#!/usr/bin/env python3
"""Build the clean A0 baseline dataset from the new isolated-object videos.

Automatic boxes are only an annotation draft. Review and correct them before
starting training.
"""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
VIDEOS = {
    "clean_background_coke.mp4": (0, "coke_zero"),
    "clean_background_thinkbar.mp4": (1, "think_protein_bar"),
    "clean_background_ziploc.mp4": (2, "ziploc_box"),
}


def estimate_box(frame: np.ndarray) -> tuple[int, int, int, int]:
    """Estimate the centered product box against the light background."""
    height, width = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mask = ((hsv[:, :, 1] > 38) | (gray < 150)).astype(np.uint8) * 255

    roi = np.zeros_like(mask)
    roi[int(0.01 * height) : int(0.74 * height), int(0.08 * width) : int(0.92 * width)] = 255
    mask = cv2.bitwise_and(mask, roi)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.dilate(mask, np.ones((11, 11), np.uint8), iterations=1)

    count, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    components = []
    for index in range(1, count):
        x, y, box_width, box_height, area = stats[index]
        center_x = x + box_width / 2
        center_y = y + box_height / 2
        if area > 250 and abs(center_x - width / 2) < 0.27 * width and center_y < 0.65 * height:
            components.append((x, y, x + box_width, y + box_height))
    if not components:
        raise RuntimeError("Could not estimate a product box")

    x1 = max(0, min(box[0] for box in components) - 12)
    y1 = max(0, min(box[1] for box in components) - 12)
    x2 = min(width - 1, max(box[2] for box in components) + 12)
    y2 = min(int(0.74 * height), max(box[3] for box in components) + 12)
    return x1, y1, x2, y2


def yolo_line(class_id: int, box: tuple[int, int, int, int], width: int, height: int) -> str:
    x1, y1, x2, y2 = box
    return (
        f"{class_id} {(x1 + x2) / (2 * width):.6f} "
        f"{(y1 + y2) / (2 * height):.6f} "
        f"{(x2 - x1) / width:.6f} {(y2 - y1) / height:.6f}\n"
    )


def make_review_sheet(samples: list[tuple[np.ndarray, tuple[int, int, int, int], str]], output: Path) -> None:
    cells = []
    for frame, box, label in samples:
        preview = frame.copy()
        x1, y1, x2, y2 = box
        cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 220, 0), 5)
        cv2.putText(preview, label, (x1, max(35, y1 - 12)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (0, 170, 0), 3)
        cells.append(cv2.resize(preview, (480, 270), interpolation=cv2.INTER_AREA))
    rows = []
    for start in range(0, len(cells), 4):
        row = cells[start : start + 4]
        while len(row) < 4:
            row.append(np.full_like(cells[0], 255))
        rows.append(np.hstack(row))
    cv2.imwrite(str(output), np.vstack(rows))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "data/videos_A/clean_background")
    parser.add_argument("--output", type=Path, default=ROOT / "data/datasets_A/a0_base")
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

    manifest_rows = []
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
            if sequence in np.linspace(0, len(indices) - 1, 8, dtype=int):
                review_samples.append((frame, box, f"{class_name} #{sequence}"))
        capture.release()

    with (args.output / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("image", "source_video", "source_frame", "split", "class"))
        writer.writerows(manifest_rows)
    make_review_sheet(review_samples, args.output / "review/labels_preview.jpg")
    print(f"Created A0 dataset: train={totals['train']}, val={totals['val']}")
    print("REQUIRED REVIEW:", args.output / "review/labels_preview.jpg")
    print("Do not train until the bounding boxes have been reviewed.")


if __name__ == "__main__":
    main()
