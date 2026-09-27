#!/usr/bin/env python3
"""Evaluate B_6 on the independent six-product test set and render its video."""

from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import yaml
from ultralytics import YOLO

from run_b_pickup_demo import resolve_device


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "outputs/B_series/training/b_6/weights/best.pt"
DATASET = ROOT / "data/datasets_B/b6_six_product_test_ground_truth"
VIDEO = ROOT / "data/videos_B/test/test_6_items.mov"
OUTPUT = ROOT / "outputs/B_series/tests/b_6_six_products"
CLASSES = {
    0: "coke_zero",
    1: "oreo",
    2: "goodwipes",
    3: "cheetos",
    4: "sprite",
    5: "sour_patch_kids",
}
COLORS = [
    (45, 110, 240),
    (65, 185, 75),
    (35, 170, 235),
    (190, 85, 220),
    (230, 155, 50),
    (170, 80, 245),
]


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


def draw(frame, result, fps_value: float) -> tuple[Counter, dict[int, list[float]]]:
    counts: Counter = Counter()
    confidences: dict[int, list[float]] = defaultdict(list)
    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        counts[class_id] += 1
        confidences[class_id].append(confidence)
        x1, y1, x2, y2 = (int(value) for value in box.xyxy[0].tolist())
        color = COLORS[class_id]
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"{CLASSES[class_id]} {confidence:.2f}"
        cv2.putText(frame, label, (x1, max(23, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

    cv2.rectangle(frame, (0, 0), (frame.shape[1], 68), (16, 23, 34), -1)
    cv2.putText(frame, f"B_6 independent test | {fps_value:.1f} FPS",
                (16, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (255, 255, 255), 2)
    summary = "  ".join(f"{CLASSES[class_id]}:{counts[class_id]}" for class_id in CLASSES)
    cv2.putText(frame, summary, (16, 55), cv2.FONT_HERSHEY_SIMPLEX,
                0.48, (218, 229, 240), 1)
    return counts, confidences


def main() -> None:
    if not MODEL.is_file():
        raise SystemExit(f"Missing B_6 checkpoint: {MODEL}")
    images = sorted((DATASET / "images/test").glob("*.jpg"))
    labels = sorted((DATASET / "labels/test").glob("*.txt"))
    if len(images) != 44 or len(labels) != 44:
        raise SystemExit(f"Expected 44 test images and labels, got {len(images)} and {len(labels)}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    device = resolve_device("auto")
    local_yaml = OUTPUT / "dataset_local.yaml"
    local_yaml.write_text(yaml.safe_dump({
        "path": str(DATASET),
        "train": "images/test",
        "val": "images/test",
        "test": "images/test",
        "names": CLASSES,
    }, sort_keys=False), encoding="utf-8")

    model = YOLO(MODEL)
    metrics = model.val(
        data=local_yaml,
        split="test",
        imgsz=1024,
        batch=1,
        conf=0.001,
        iou=0.7,
        device=device,
        workers=0,
        plots=True,
        project=OUTPUT,
        name="metrics",
        exist_ok=True,
        verbose=False,
    )
    evaluation = {
        "model": str(MODEL),
        "images": len(images),
        "ground_truth_boxes": sum(1 for label in labels for line in label.read_text().splitlines() if line.strip()),
        "device": device,
        "imgsz": 1024,
        "confidence_floor": 0.001,
        "results": safe(metrics.results_dict),
        "class_metrics": {
            CLASSES[index]: {
                "precision": float(metrics.box.p[index]),
                "recall": float(metrics.box.r[index]),
                "map50": float(metrics.box.ap50[index]),
                "map50_95": float(metrics.box.maps[index]),
            }
            for index in CLASSES
        },
        "speed_ms_per_image": safe(metrics.speed),
    }

    capture = cv2.VideoCapture(str(VIDEO))
    if not capture.isOpened():
        raise SystemExit(f"Cannot open {VIDEO}")
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    temporary_video = OUTPUT / "test_6_items_b6_mp4v.mp4"
    final_video = OUTPUT / "test_6_items_b6.mp4"
    writer = cv2.VideoWriter(
        str(temporary_video), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    if not writer.isOpened():
        raise SystemExit(f"Cannot write {temporary_video}")

    rows = []
    coverage: Counter = Counter()
    frame_index = 0
    started = cv2.getTickCount()
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        result = model.predict(
            frame, imgsz=1024, conf=0.35, iou=0.7,
            device=device, verbose=False,
        )[0]
        elapsed = (cv2.getTickCount() - started) / cv2.getTickFrequency()
        processing_fps = (frame_index + 1) / elapsed if elapsed else 0.0
        counts, confidences = draw(frame, result, processing_fps)
        writer.write(frame)
        row = {"frame": frame_index, "time_s": frame_index / fps}
        for class_id, name in CLASSES.items():
            count = counts[class_id]
            if count:
                coverage[class_id] += 1
            row[f"{name}_count"] = count
            row[f"{name}_mean_confidence"] = (
                sum(confidences[class_id]) / len(confidences[class_id])
                if confidences[class_id] else ""
            )
        rows.append(row)
        frame_index += 1
        if frame_index % 100 == 0:
            print(f"Rendered {frame_index}/{frame_total} frames", flush=True)

    capture.release()
    writer.release()
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(temporary_video), "-c:v", "libx264", "-preset", "fast",
        "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(final_video),
    ], check=True)
    temporary_video.unlink()

    with (OUTPUT / "frame_detections.csv").open("w", newline="", encoding="utf-8") as handle:
        writer_csv = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer_csv.writeheader()
        writer_csv.writerows(rows)

    evaluation["render"] = {
        "source_video": str(VIDEO),
        "output_video": str(final_video),
        "frames": frame_index,
        "fps": fps,
        "confidence": 0.35,
        "coverage_percent": {
            CLASSES[class_id]: 100.0 * coverage[class_id] / frame_index for class_id in CLASSES
        },
    }
    (OUTPUT / "metrics.json").write_text(
        json.dumps(evaluation, indent=2), encoding="utf-8"
    )
    print(json.dumps(evaluation, indent=2), flush=True)


if __name__ == "__main__":
    main()
