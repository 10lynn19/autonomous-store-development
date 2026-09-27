#!/usr/bin/env python3
"""Export sparse B-AUG2 detections for offline pickup-event prototyping."""

import argparse
import json
from pathlib import Path

import cv2
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "outputs/B_series/training/b_aug2_mosaic_copy/weights/best.pt"
VIDEOS = ROOT / "data/videos_B/test"
OUTPUT = ROOT / "outputs/B_series/pickup_demo/detections"


def process(video: Path, model: YOLO, sample_fps: float, device: str) -> None:
    capture = cv2.VideoCapture(str(video))
    native_fps = capture.get(cv2.CAP_PROP_FPS)
    if not capture.isOpened() or native_fps <= 0:
        raise RuntimeError(f"Cannot read video: {video}")
    frame_step = max(1, round(native_fps / sample_fps))
    width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
    output = OUTPUT / f"{video.stem}.jsonl"
    frame_index = 0
    sample_count = 0
    with output.open("w", encoding="utf-8") as handle:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index % frame_step == 0:
                result = model.predict(frame, imgsz=1024, conf=0.25, iou=0.7,
                                       device=device, verbose=False)[0]
                detections = []
                for box in result.boxes:
                    x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].tolist())
                    detections.append({
                        "class_id": int(box.cls[0]),
                        "confidence": round(float(box.conf[0]), 4),
                        "box": [round(x1 / width, 5), round(y1 / height, 5),
                                round(x2 / width, 5), round(y2 / height, 5)],
                    })
                handle.write(json.dumps({"frame": frame_index,
                                         "time_s": round(frame_index / native_fps, 3),
                                         "detections": detections}) + "\n")
                sample_count += 1
            frame_index += 1
    capture.release()
    print(f"{video.name}: {sample_count} sampled frames -> {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("videos", nargs="*", help="Video filenames; default is all B test videos")
    parser.add_argument("--sample-fps", type=float, default=5.0)
    parser.add_argument("--device", default="0")
    args = parser.parse_args()
    if args.sample_fps <= 0:
        raise SystemExit("--sample-fps must be positive")
    names = args.videos or [path.name for path in sorted(VIDEOS.iterdir())
                            if path.suffix.lower() in {".mp4", ".mov"}]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    model = YOLO(MODEL)
    for name in names:
        video = VIDEOS / name
        if not video.is_file():
            raise SystemExit(f"Missing video: {video}")
        process(video, model, args.sample_fps, args.device)


if __name__ == "__main__":
    main()
