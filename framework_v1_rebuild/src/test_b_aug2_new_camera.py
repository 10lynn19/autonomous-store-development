#!/usr/bin/env python3
"""Compare B-AUG2 and B_5 on held-out new-camera data."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import yaml
from ultralytics import YOLO

from run_b_pickup_demo import COLORS, resolve_device


ROOT = Path(__file__).resolve().parents[1]
CLASSES = {0: "coke_zero", 1: "oreo", 2: "goodwipes"}
MODELS = {
    "b_aug2_mosaic_copy": ROOT / "outputs/B_series/training/b_aug2_mosaic_copy/weights/best.pt",
    "B_5": ROOT / "outputs/B_series/training/b_5/weights/best.pt",
}
DATASET = ROOT / "data/datasets_B/b_aug2_new_test_ground_truth"
VIDEO = ROOT / "data/videos_B/test/test_b_aug2_new.mov"
OUTPUT = ROOT / "outputs/B_series/tests/b_aug2_new_camera_comparison"


def safe(value):
    if hasattr(value, "tolist"):
        return value.tolist()
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, dict):
        return {str(key): safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe(item) for item in value]
    return value


def draw(frame, result, title: str) -> tuple[Counter, dict[int, list[float]]]:
    counts = Counter()
    confidences: dict[int, list[float]] = defaultdict(list)
    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        counts[class_id] += 1
        confidences[class_id].append(confidence)
        x1, y1, x2, y2 = (int(value) for value in box.xyxy[0].tolist())
        color = COLORS[class_id]
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{CLASSES[class_id]} {confidence:.2f}",
                    (x1, max(22, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 42), (18, 25, 36), -1)
    cv2.putText(frame, title, (14, 28), cv2.FONT_HERSHEY_SIMPLEX,
                0.72, (255, 255, 255), 2)
    return counts, confidences


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    device = resolve_device("auto")
    local_yaml = OUTPUT / "dataset_local.yaml"
    local_yaml.write_text(yaml.safe_dump({
        "path": str(DATASET), "train": "images/test", "val": "images/test",
        "test": "images/test", "names": CLASSES,
    }, sort_keys=False), encoding="utf-8")

    models = {name: YOLO(path) for name, path in MODELS.items()}
    evaluation = {}
    for name, model in models.items():
        metrics = model.val(
            data=local_yaml, split="test", imgsz=1024, batch=1, conf=0.001,
            iou=0.7, device=device, workers=0, plots=True,
            project=OUTPUT, name=f"{name}_metrics", exist_ok=True, verbose=False,
        )
        evaluation[name] = {
            "model": str(MODELS[name]), "images": 30, "ground_truth_boxes": 179,
            "device": device, "imgsz": 1024, "confidence_floor": 0.001,
            "results": safe(metrics.results_dict), "class_map50_95": {
                CLASSES[index]: float(value) for index, value in enumerate(metrics.box.maps)
            }, "speed_ms_per_image": safe(metrics.speed),
        }

    capture = cv2.VideoCapture(str(VIDEO))
    if not capture.isOpened():
        raise SystemExit(f"Cannot open {VIDEO}")
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    width, height = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    panel_width = 960
    panel_height = round(height * panel_width / width)
    output_video = OUTPUT / "b_aug2_old_vs_new.mp4"
    writer = cv2.VideoWriter(str(output_video), cv2.VideoWriter_fourcc(*"mp4v"),
                             fps, (panel_width * 2, panel_height))
    if not writer.isOpened():
        raise SystemExit(f"Cannot create {output_video}")
    frame_rows = []
    frame_index = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            panels = []
            for name, model in models.items():
                result = model.predict(frame, imgsz=1024, conf=0.35, iou=0.7,
                                       device=device, verbose=False)[0]
                panel = frame.copy()
                counts, confidences = draw(panel, result, name)
                panels.append(cv2.resize(panel, (panel_width, panel_height)))
                row = {"frame": frame_index, "time_s": frame_index / fps, "model": name}
                for class_id, class_name in CLASSES.items():
                    values = confidences[class_id]
                    row[f"{class_name}_count"] = counts[class_id]
                    row[f"{class_name}_mean_conf"] = sum(values) / len(values) if values else 0.0
                frame_rows.append(row)
            writer.write(cv2.hconcat(panels))
            frame_index += 1
    finally:
        capture.release()
        writer.release()

    with (OUTPUT / "frame_detections.csv").open("w", newline="", encoding="utf-8") as handle:
        writer_csv = csv.DictWriter(handle, fieldnames=list(frame_rows[0]))
        writer_csv.writeheader()
        writer_csv.writerows(frame_rows)
    (OUTPUT / "metrics.json").write_text(
        json.dumps(evaluation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(evaluation, indent=2, ensure_ascii=False))
    print(f"Comparison video: {output_video}")


if __name__ == "__main__":
    main()
