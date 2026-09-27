#!/usr/bin/env python3
"""Create B2 phone-label drafts with B0 and produce a visual QA sheet."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/datasets_B/b2_phone_addition"
MODEL = ROOT / "outputs/B_series/training/b0_base/weights/best.pt"
CLASS_FROM_VIDEO = {"coke": 0, "oreo": 1, "goodwipes": 2}
CLASS_NAMES = ["coke_zero", "oreo", "goodwipes"]


def expected_class(video: str) -> int:
    lowered = video.lower()
    matches = [class_id for token, class_id in CLASS_FROM_VIDEO.items() if token in lowered]
    if len(matches) != 1:
        raise ValueError(f"Cannot determine class from video name: {video}")
    return matches[0]


def main() -> None:
    manifest = json.loads((DATASET / "manifest.json").read_text(encoding="utf-8"))
    items = {item["id"]: item for item in manifest["items"]}
    labels_dir = DATASET / "labels/train"
    review_dir = DATASET / "review"
    labels_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading B0 checkpoint: {MODEL}", flush=True)
    model = YOLO(MODEL)
    image_paths = sorted((DATASET / "images/train").glob("*.jpg"))
    print(f"Running inference on {len(image_paths)} B2 frames...", flush=True)
    rows = []
    previews: dict[str, list[np.ndarray]] = defaultdict(list)
    missing = 0

    for processed, result in enumerate(
        model.predict(image_paths, imgsz=1280, conf=0.001, iou=0.7, device="cpu", verbose=False, stream=True),
        start=1,
    ):
        image_path = Path(result.path)
        item = items[image_path.stem]
        class_id = expected_class(item["video"])
        candidates = []
        if result.boxes is not None:
            for index, predicted_class in enumerate(result.boxes.cls.int().tolist()):
                cx, cy, width, height = result.boxes.xywhn[index].tolist()
                area = width * height
                if (
                    predicted_class == class_id
                    and 0.18 <= cx <= 0.82
                    and 0.35 <= cy <= 0.88
                    and width <= 0.55
                    and height <= 0.55
                    and area <= 0.16
                ):
                    candidates.append(index)

        label_path = labels_dir / f"{image_path.stem}.txt"
        confidence = 0.0
        if candidates:
            best_index = max(candidates, key=lambda index: float(result.boxes.conf[index]))
            confidence = float(result.boxes.conf[best_index])
            x, y, w, h = result.boxes.xywhn[best_index].tolist()
            label_path.write_text(f"{class_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n", encoding="utf-8")
            status = "auto_labeled"
        else:
            label_path.unlink(missing_ok=True)
            missing += 1
            status = "needs_manual"

        rows.append((image_path.stem, item["video"], CLASS_NAMES[class_id], status, confidence))
        if len(previews[item["video"]]) < 4:
            preview = cv2.imread(str(image_path))
            if candidates:
                x1, y1, x2, y2 = map(int, result.boxes.xyxy[best_index].tolist())
                cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 220, 0), 5)
                text = f"{CLASS_NAMES[class_id]} {confidence:.2f}"
            else:
                text = f"MANUAL: {CLASS_NAMES[class_id]}"
            cv2.putText(preview, text, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.1,
                        (0, 170, 0) if candidates else (0, 0, 255), 3)
            previews[item["video"]].append(cv2.resize(preview, (480, 270), interpolation=cv2.INTER_AREA))
        if processed % 12 == 0:
            print(f"Processed {processed}/{len(image_paths)}", flush=True)

    with (review_dir / "pseudo_label_report.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("image", "video", "expected_class", "status", "confidence"))
        writer.writerows(rows)

    lines = []
    for video in sorted(previews):
        row = previews[video]
        while len(row) < 4:
            row.append(np.full((270, 480, 3), 255, dtype=np.uint8))
        lines.append(np.hstack(row))
    cv2.imwrite(str(review_dir / "pseudo_labels_preview.jpg"), np.vstack(lines))
    print(f"B2 phone frames: {len(rows)}")
    print(f"Auto-labeled: {len(rows) - missing}")
    print(f"Needs manual review: {missing}")
    print(f"Preview: {review_dir / 'pseudo_labels_preview.jpg'}")


if __name__ == "__main__":
    main()
