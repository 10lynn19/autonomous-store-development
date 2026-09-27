#!/usr/bin/env python3
"""Evaluate B-series branches on fixed ground truth and export MP4 videos."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]
TEST_CONFIG = ROOT / "configs/dataset_b_test_ground_truth.yaml"
VIDEO_DIR = ROOT / "data/videos_B/test"
CLASSES = {0: "coke_zero", 1: "oreo", 2: "goodwipes"}
BRANCHES = {
    "b0_base": ROOT / "outputs/B_series/training/b0_base/weights/best.pt",
    "b1_camera": ROOT / "outputs/B_series/training/b1_camera/weights/best.pt",
    "b2_phone": ROOT / "outputs/B_series/training/b2_phone/weights/best.pt",
    "b4_camera_phone": ROOT / "outputs/B_series/training/b4_camera_phone/weights/best.pt",
    "b_aug1_light": ROOT / "outputs/B_series/training/b_aug1_light/weights/best.pt",
    "b_aug2_mosaic_copy": ROOT / "outputs/B_series/training/b_aug2_mosaic_copy/weights/best.pt",
    "b_c0_clean_control": ROOT / "outputs/B_series/training/b_c0_clean_control/weights/best.pt",
    "b_c2_real_pickup": ROOT / "outputs/B_series/training/b_c2_real_pickup/weights/best.pt",
}


def ffmpeg_executable() -> str | None:
    """Find system ffmpeg or the binary bundled by imageio-ffmpeg."""
    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError):
        return None


def convert_rendered_videos_to_mp4(video_output: Path) -> None:
    """Convert Ultralytics' Windows AVI output to portable H.264 MP4."""
    executable = ffmpeg_executable()
    if executable is None:
        print("WARNING: ffmpeg unavailable; rendered AVI was not converted to MP4.")
        return
    for avi in sorted(video_output.rglob("*.avi")):
        mp4 = avi.with_suffix(".mp4")
        temporary = avi.with_suffix(".tmp.mp4")
        subprocess.run([
            executable, "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(avi), "-c:v", "libx264", "-preset", "medium",
            "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-an", str(temporary),
        ], check=True)
        temporary.replace(mp4)


def json_safe(value):
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def evaluate(branch: str, model_path: Path, device: str) -> None:
    output = ROOT / "outputs/B_series/tests" / f"{branch}_img1024_conf035"
    output.mkdir(parents=True, exist_ok=True)
    model = YOLO(model_path)
    metrics = model.val(
        data=TEST_CONFIG,
        split="test",
        imgsz=1024,
        batch=4 if device != "cpu" else 1,
        conf=0.001,
        iou=0.7,
        device=device,
        workers=4 if device != "cpu" else 0,
        plots=True,
        project=output,
        name="ground_truth_metrics",
        exist_ok=True,
    )
    image_count = len(list((ROOT / "data/datasets_B/test_ground_truth/images/test").glob("*.jpg")))
    label_count = sum(
        len(path.read_text(encoding="utf-8").splitlines())
        for path in (ROOT / "data/datasets_B/test_ground_truth/labels/test").glob("*.txt")
    )
    (output / "ground_truth_metrics.json").write_text(json.dumps({
        "branch": branch,
        "model": str(model_path),
        "test_images": image_count,
        "ground_truth_boxes": label_count,
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
            source=video, imgsz=1024, conf=0.35, iou=0.7, device=device,
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
        convert_rendered_videos_to_mp4(output / "videos" / video.stem)
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
    with (output / "video_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{branch} test complete: {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("branches", nargs="+", choices=sorted(BRANCHES))
    parser.add_argument("--device", default="0")
    args = parser.parse_args()
    for branch in args.branches:
        model_path = BRANCHES[branch]
        if not model_path.exists():
            raise SystemExit(f"Missing model: {model_path}")
        evaluate(branch, model_path, args.device)


if __name__ == "__main__":
    main()
