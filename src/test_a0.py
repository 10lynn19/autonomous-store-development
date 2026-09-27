#!/usr/bin/env python3
"""Evaluate A0 on annotated test frames and render the eight test videos."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "outputs/A_series/training/a0_base/weights/best.pt"
TEST_CONFIG = ROOT / "configs/dataset_test_ground_truth.yaml"
VIDEO_DIR = ROOT / "data/videos_A/test"
OUTPUT = ROOT / "outputs/A_series/tests/a0_img1024_conf035"
CLASSES = {0: "coke_zero", 1: "think_protein_bar", 2: "ziploc_box"}


def json_safe(value):
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def evaluate_frames(model: YOLO) -> None:
    metrics = model.val(
        data=TEST_CONFIG,
        split="test",
        imgsz=1024,
        batch=4,
        conf=0.001,
        iou=0.7,
        device=0,
        workers=4,
        plots=True,
        project=OUTPUT,
        name="ground_truth_metrics",
        exist_ok=True,
    )
    summary = {
        "model": str(MODEL),
        "test_images": 241,
        "ground_truth_boxes": 1031,
        "imgsz": 1024,
        "ap_confidence_floor": 0.001,
        "nms_iou": 0.7,
        "metrics": json_safe(metrics.results_dict),
        "speed_ms_per_image": json_safe(metrics.speed),
    }
    output_path = OUTPUT / "ground_truth_metrics.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def predict_videos(model: YOLO) -> None:
    rows = []
    for video in sorted(VIDEO_DIR.glob("*")):
        if video.suffix.lower() not in {".mp4", ".mov"}:
            continue
        frame_count = 0
        frames_with_detection = 0
        total_detections = 0
        class_frames = Counter()
        class_detections = Counter()
        class_confidences = defaultdict(list)

        results = model.predict(
            source=video,
            imgsz=1024,
            conf=0.35,
            iou=0.7,
            device=0,
            save=True,
            project=OUTPUT / "videos",
            name=video.stem,
            exist_ok=True,
            stream=True,
            verbose=False,
        )
        for result in results:
            frame_count += 1
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                continue
            frames_with_detection += 1
            total_detections += len(boxes)
            classes = [int(value) for value in boxes.cls.cpu().tolist()]
            confidences = [float(value) for value in boxes.conf.cpu().tolist()]
            for class_id in set(classes):
                class_frames[class_id] += 1
            for class_id, confidence in zip(classes, confidences):
                class_detections[class_id] += 1
                class_confidences[class_id].append(confidence)

        row = {
            "video": video.name,
            "frames": frame_count,
            "frames_any_detection": frames_with_detection,
            "any_detection_rate": frames_with_detection / frame_count if frame_count else 0.0,
            "total_detections": total_detections,
        }
        for class_id, class_name in CLASSES.items():
            values = class_confidences[class_id]
            row[f"{class_name}_frame_rate"] = class_frames[class_id] / frame_count if frame_count else 0.0
            row[f"{class_name}_detections"] = class_detections[class_id]
            row[f"{class_name}_mean_conf"] = sum(values) / len(values) if values else 0.0
        rows.append(row)

    summary_path = OUTPUT / "video_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if not MODEL.exists():
        raise SystemExit(f"Missing model: {MODEL}")
    model = YOLO(MODEL)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    evaluate_frames(model)
    predict_videos(model)
    print("A0 test complete:", OUTPUT)


if __name__ == "__main__":
    main()
