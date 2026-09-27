#!/usr/bin/env python3
"""Run the same B-series pickup event loop on a video or live camera source."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from pickup_events import CLASSES, ShelfEventEngine


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "outputs/B_series/training/b_5/weights/best.pt"
COLORS = [(45, 110, 240), (65, 185, 75), (35, 170, 235)]


def resolve_device(requested: str) -> str:
    if requested != "auto":
        return requested
    import torch

    if torch.cuda.is_available():
        return "0"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def resolve_camera_source(source: str) -> int | str:
    if source.isdecimal():
        return int(source)
    if not source.startswith("camera:"):
        return source
    if sys.platform != "darwin":
        raise SystemExit("camera:NAME is supported on macOS; use a camera number on Windows")
    name = source.removeprefix("camera:").strip()
    listing = subprocess.run(
        ["ffmpeg", "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
        capture_output=True, text=True, check=False,
    ).stderr
    video_section = listing.split("AVFoundation video devices:", 1)
    if len(video_section) < 2:
        raise SystemExit("Could not list macOS cameras; is ffmpeg installed?")
    matches = re.findall(r"\[(\d+)\] ([^\n]+)", video_section[1].split("AVFoundation audio devices:")[0])
    matched = [(int(index), label.strip()) for index, label in matches if label.strip() == name]
    if len(matched) != 1:
        available = ", ".join(label for _, label in matches)
        raise SystemExit(f"Camera {name!r} not found uniquely. Available: {available}")
    print(f"Camera: {matched[0][1]} (FFmpeg index {matched[0][0]})", flush=True)
    return source


class NamedMacCamera:
    """Read by AVFoundation device name; OpenCV's camera indexes can differ."""

    def __init__(self, name: str, width: int = 1280, height: int = 720):
        self.width, self.height = width, height
        self.process = subprocess.Popen(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "avfoundation",
             "-framerate", "30", "-video_size", f"{width}x{height}",
             "-i", f"{name}:none", "-pix_fmt", "bgr24", "-f", "rawvideo", "pipe:1"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )

    def isOpened(self) -> bool:
        return self.process.poll() is None

    def get(self, prop: int) -> float:
        return 30.0 if prop == cv2.CAP_PROP_FPS else 0.0

    def read(self):
        size = self.width * self.height * 3
        chunks = bytearray()
        while len(chunks) < size:
            part = self.process.stdout.read(size - len(chunks))
            if not part:
                return False, None
            chunks.extend(part)
        return True, np.frombuffer(chunks, dtype=np.uint8).reshape(self.height, self.width, 3)

    def release(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
        self.process.stdout.close()
        self.process.wait(timeout=5)


def draw_overlay(frame, detections: list[dict], engine: ShelfEventEngine,
                 recent_events: list[dict], time_s: float, detect_only: bool = False,
                 fps: float = 0.0) -> None:
    height, width = frame.shape[:2]
    for detection in detections:
        x1, y1, x2, y2 = detection["box"]
        class_id = detection["class_id"]
        p1, p2 = (int(x1 * width), int(y1 * height)), (int(x2 * width), int(y2 * height))
        cv2.rectangle(frame, p1, p2, COLORS[class_id], 2)
        cv2.putText(frame, f"{CLASSES[class_id]} {detection['confidence']:.2f}",
                    (p1[0], max(22, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, COLORS[class_id], 2)

    if detect_only:
        counts = {name: 0 for name in CLASSES}
        for detection in detections:
            counts[CLASSES[detection["class_id"]]] += 1
        cv2.rectangle(frame, (0, 0), (width, 74), (22, 22, 22), -1)
        cv2.putText(frame, f"B_5 live detection | {fps:.1f} FPS | press q to quit",
                    (16, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.putText(frame, "  ".join(f"{name}: {count}" for name, count in counts.items()),
                    (16, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        return

    for slot in engine.slots if engine.calibrated else []:
        x, y = (int(slot.center[0] * width), int(slot.center[1] * height))
        color = (0, 0, 255) if slot.state == "missing" else (255, 255, 255)
        cv2.circle(frame, (x, y), 8, color, 2)
    cv2.rectangle(frame, (0, 0), (width, 75 + 30 * min(3, len(recent_events))),
                  (22, 22, 22), -1)
    status = ("Calibrating shelf: keep it stocked and unobstructed"
              if not engine.calibrated else
              "NO REFERENCE PRODUCTS: restart with clear stocked shelf"
              if not engine.slots else
              "Shelf event prototype | red circles = missing slots")
    cv2.putText(frame, status, (16, 27), cv2.FONT_HERSHEY_SIMPLEX,
                0.65, (255, 255, 255), 2)
    missing = engine.snapshot()["currently_missing_from_shelf"]
    line = "Missing from shelf: " + ", ".join(
        f"{name} {count}" for name, count in missing.items() if count
    ) if any(missing.values()) else "No calibrated slot missing; unseen pickups remain possible"
    cv2.putText(frame, line, (16, 56), cv2.FONT_HERSHEY_SIMPLEX,
                0.65, (255, 255, 255), 2)
    for index, event in enumerate(recent_events[-3:]):
        label = ("POSSIBLE PICKUP" if event["event"] == "possible_pickup"
                 else "RETURNED TO SHELF")
        cv2.putText(frame, f"{event['time_s']:.1f}s {label}: {event['class_name']}",
                    (16, 88 + 30 * index), cv2.FONT_HERSHEY_SIMPLEX,
                    0.65, (255, 255, 255), 2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Video file, camera number, camera:NAME on macOS, or RTSP URL")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--sample-fps", type=float, default=10.0)
    parser.add_argument("--confidence", type=float, default=0.35)
    parser.add_argument("--device", default="auto",
                        help="auto chooses CUDA, then Apple MPS, then CPU")
    parser.add_argument("--detect-only", action="store_true",
                        help="Show live product detections without shelf calibration")
    parser.add_argument("--imgsz", type=int, default=1024)
    parser.add_argument("--roi", nargs=4, type=float, metavar=("X1", "Y1", "X2", "Y2"),
                        help="Normalized region to magnify before inference, e.g. .3 .3 .7 .8")
    parser.add_argument("--max-frames", type=int, default=0,
                        help="Stop after this many processed frames (0 means unlimited)")
    parser.add_argument("--output", type=Path, help="Write annotated MP4 and companion JSON")
    parser.add_argument("--show", action="store_true", help="Display a live preview window")
    args = parser.parse_args()
    if args.sample_fps <= 0:
        parser.error("--sample-fps must be positive")
    if args.roi and not (0 <= args.roi[0] < args.roi[2] <= 1 and
                         0 <= args.roi[1] < args.roi[3] <= 1):
        parser.error("--roi must satisfy 0 <= X1 < X2 <= 1 and 0 <= Y1 < Y2 <= 1")
    source = resolve_camera_source(args.source)
    device = resolve_device(args.device)
    print(f"Inference device: {device}", flush=True)
    if isinstance(source, str) and source.startswith("camera:"):
        capture = NamedMacCamera(source.removeprefix("camera:").strip())
    else:
        capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        raise SystemExit(f"Cannot open source: {args.source}")
    native_fps = float(capture.get(cv2.CAP_PROP_FPS))
    is_file = isinstance(source, str) and Path(source).is_file()
    if is_file and native_fps <= 0:
        raise SystemExit("Cannot read video FPS")
    frame_step = max(1, round(native_fps / args.sample_fps)) if is_file else 1
    output_fps = native_fps / frame_step if is_file else args.sample_fps
    model = YOLO(args.model)
    engine = ShelfEventEngine()
    writer = None
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
    frame_index = 0
    processed = 0
    last_processed_at = None
    fps = 0.0
    start = time.monotonic()
    next_live_sample = start
    recent_events: list[dict] = []
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if is_file and frame_index % frame_step:
                frame_index += 1
                continue
            if not is_file:
                now = time.monotonic()
                if now < next_live_sample:
                    frame_index += 1
                    continue
                next_live_sample = now + 1.0 / args.sample_fps
            time_s = frame_index / native_fps if is_file else time.monotonic() - start
            height, width = frame.shape[:2]
            if args.roi:
                left, top, right, bottom = (int(args.roi[0] * width), int(args.roi[1] * height),
                                            int(args.roi[2] * width), int(args.roi[3] * height))
                inference_frame = frame[top:bottom, left:right]
            else:
                left = top = 0
                inference_frame = frame
            result = model.predict(inference_frame, imgsz=args.imgsz, conf=args.confidence,
                                   iou=0.7, device=device, verbose=False)[0]
            completed_at = time.monotonic()
            if last_processed_at is not None:
                instant_fps = 1.0 / max(1e-6, completed_at - last_processed_at)
                fps = instant_fps if fps == 0 else 0.8 * fps + 0.2 * instant_fps
            last_processed_at = completed_at
            detections = []
            for box in result.boxes:
                x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].tolist())
                detections.append({
                    "class_id": int(box.cls[0]),
                    "confidence": float(box.conf[0]),
                    "box": [(x1 + left) / width, (y1 + top) / height,
                            (x2 + left) / width, (y2 + top) / height],
                })
            new_events = [] if args.detect_only else engine.update(time_s, detections)
            if new_events:
                recent_events.extend(new_events)
                for event in new_events:
                    print(json.dumps(event, ensure_ascii=False), flush=True)
            recent_events = [event for event in recent_events
                             if time_s - event["time_s"] < 5.0]
            draw_overlay(frame, detections, engine, recent_events, time_s,
                         detect_only=args.detect_only, fps=fps)
            if args.output:
                if writer is None:
                    writer = cv2.VideoWriter(str(args.output), cv2.VideoWriter_fourcc(*"mp4v"),
                                             output_fps, (width, height))
                    if not writer.isOpened():
                        raise RuntimeError(f"Cannot write video: {args.output}")
                writer.write(frame)
            if args.show:
                cv2.imshow("B-series pickup event demo", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            frame_index += 1
            processed += 1
            if args.max_frames and processed >= args.max_frames:
                break
    finally:
        capture.release()
        if writer is not None:
            writer.release()
        if args.show:
            cv2.destroyAllWindows()

    summary = {"source": args.source, "model": str(args.model),
               "mode": "detection" if args.detect_only else "pickup_events",
               "device": device, "average_processed_fps": round(processed / max(1e-6, time.monotonic() - start), 2),
               "processed_frames": processed}
    if not args.detect_only:
        summary.update(engine.snapshot())
        summary["events"] = engine.events
        summary["interpretation"] = (
            "No event means no change was observed at calibrated product positions; "
            "it does not prove that no product was picked up."
        )
    if args.output:
        args.output.with_suffix(".json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
