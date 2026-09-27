#!/usr/bin/env python3
"""Evaluate A-series branches on the one fixed ground-truth set and videos."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]
TEST_CONFIG = ROOT / "configs/dataset_test_ground_truth.yaml"
VIDEO_DIR = ROOT / "data/videos_A/test"
CLASSES = {0: "coke_zero", 1: "think_protein_bar", 2: "ziploc_box"}
BRANCHES = {
    "a1_synthetic": ROOT / "outputs/A_series/training/a1_synthetic/weights/best.pt",
    "a2_phone": ROOT / "outputs/A_series/training/a2_phone/weights/best.pt",
    "a3_camera": ROOT / "outputs/A_series/training/a3_camera/weights/best.pt",
    "a4_p_camera_phone": ROOT / "outputs/A_series/training/a4_p_camera_phone/weights/best.pt",
    "a4_s_camera_synthetic": ROOT / "outputs/A_series/training/a4_s_camera_synthetic/weights/best.pt",
    "a5_balanced_camera": ROOT / "outputs/A_series/training/a5_balanced_camera/weights/best.pt",
    "a6_p_balanced_camera_phone": ROOT / "outputs/A_series/training/a6_p_balanced_camera_phone/weights/best.pt",
}


def json_safe(value):
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def evaluate(branch: str, model_path: Path) -> None:
    output = ROOT / "outputs/A_series/tests" / f"{branch}_img1024_conf035"
    model = YOLO(model_path)
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
        project=output,
        name="ground_truth_metrics",
        exist_ok=True,
    )
    output.mkdir(parents=True, exist_ok=True)
    (output / "ground_truth_metrics.json").write_text(json.dumps({
        "branch": branch,
        "model": str(model_path),
        "test_images": 241,
        "ground_truth_boxes": 1031,
        "imgsz": 1024,
        "ap_confidence_floor": 0.001,
        "video_confidence": 0.35,
        "nms_iou": 0.7,
        "metrics": json_safe(metrics.results_dict),
        "speed_ms_per_image": json_safe(metrics.speed),
    }, indent=2), encoding="utf-8")

    rows = []
    for video in sorted(VIDEO_DIR.glob("*")):
        if video.suffix.lower() not in {".mp4", ".mov"}:
            continue
        frame_count = frames_with_detection = total_detections = 0
        class_frames, class_detections = Counter(), Counter()
        class_confidences = defaultdict(list)
        results = model.predict(
            source=video, imgsz=1024, conf=0.35, iou=0.7, device=0,
            save=True, project=output / "videos", name=video.stem,
            exist_ok=True, stream=True, verbose=False,
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
            "video": video.name, "frames": frame_count,
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
    with (output / "video_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{branch} test complete: {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("branches", nargs="+", choices=sorted(BRANCHES))
    args = parser.parse_args()
    for branch in args.branches:
        model_path = BRANCHES[branch]
        if not model_path.exists():
            raise SystemExit(f"Missing model: {model_path}")
        evaluate(branch, model_path)


if __name__ == "__main__":
    main()
