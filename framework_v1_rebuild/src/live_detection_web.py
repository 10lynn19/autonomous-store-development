#!/usr/bin/env python3
"""Small localhost MJPEG dashboard for the B_5 shelf detector."""

from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
from ultralytics import YOLO

from run_b_pickup_demo import (CLASSES, COLORS, DEFAULT_MODEL, NamedMacCamera,
                               resolve_camera_source, resolve_device)


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Live Shelf Intelligence · Detection Demo</title><style>
:root{font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#eaf2f8;background:#0b1220}
*{box-sizing:border-box}body{max-width:1480px;margin:0 auto;padding:24px 32px 38px}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-bottom:22px;border-bottom:1px solid #27354a}
.brand{display:flex;align-items:center;gap:12px;font-size:17px;font-weight:750;letter-spacing:.015em}
.mark{display:grid;place-items:center;width:36px;height:36px;border-radius:11px;background:linear-gradient(135deg,#32cfbd,#4788f3);color:#091521;font-weight:900}
.eyebrow{color:#64d6c6;font-size:12px;font-weight:750;letter-spacing:.18em;text-transform:uppercase;margin:34px 0 8px}
h1{font-size:clamp(30px,3.1vw,46px);line-height:1.12;letter-spacing:-.035em;margin:0 0 10px}
.subtitle{color:#a7b7ca;font-size:16px;margin:0 0 30px}
.live{display:inline-flex;align-items:center;gap:9px;border:1px solid #28685e;background:#103a39;color:#91eedc;border-radius:100px;padding:9px 14px;font-size:12px;font-weight:750;letter-spacing:.1em;text-transform:uppercase}
.dot{width:8px;height:8px;background:#49e5bd;border-radius:50%;box-shadow:0 0 0 4px #49e5bd22}
.live.off{border-color:#855049;background:#422722;color:#ffb0a3}.live.off .dot{background:#ff806d;box-shadow:none}
.layout{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:22px;align-items:start}
.card{border:1px solid #2a3a51;background:#111c2e;border-radius:18px;overflow:hidden;box-shadow:0 20px 50px #0002}
.cardhead{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:17px 20px;border-bottom:1px solid #26374d}
.cardtitle{font-size:14px;font-weight:700}.meta{color:#8ea5bb;font-size:12px}.video{background:#02060c;min-height:360px;display:grid;place-items:center}
.video img{display:block;width:100%;height:auto}.side{display:flex;flex-direction:column;gap:18px}.side .card{padding:20px}
.sectionlabel{font-size:11px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:#8fa8bf;margin:0 0 12px}
.product{display:flex;align-items:center;gap:12px;padding:14px 0;border-bottom:1px solid #26374d}.product:last-child{border-bottom:0}
.swatch{width:9px;height:36px;border-radius:9px;flex:none}.coke{background:#f79060}.oreo{background:#55bf71}.wipes{background:#ecc970}
.productname{flex:1;font-weight:650}.count{font-size:28px;font-weight:800;line-height:1;font-variant-numeric:tabular-nums}
.stat{display:flex;justify-content:space-between;padding:9px 0;color:#abc0d1;font-size:13px}.stat strong{color:#e7f0f8;font-weight:700}
.note{border-left:3px solid #46c8bc;padding:13px 16px;color:#aebfd0;background:#112d39;border-radius:0 10px 10px 0;font-size:12px;line-height:1.6}
.foot{display:flex;justify-content:space-between;gap:20px;color:#7890a9;font-size:12px;margin-top:22px}
@media(max-width:960px){.layout{grid-template-columns:1fr}.side{display:grid;grid-template-columns:1fr 1fr}}
@media(max-width:640px){body{padding:18px}.side{display:flex}.topbar{align-items:flex-start}.video{min-height:220px}.foot{display:block}}
</style></head><body>
<header class="topbar"><div class="brand"><span class="mark">S</span><span>Shelf Intelligence</span></div><span class="live" id="live"><span class="dot"></span><span id="state">CONNECTING</span></span></header>
<div class="eyebrow">Computer vision prototype</div><h1>Live Product Detection</h1>
<p class="subtitle">Real-time object recognition from the in-store shelf camera.</p>
<main class="layout"><section class="card"><div class="cardhead"><span class="cardtitle">Camera Feed</span><span class="meta">EMEET SmartCam C960 · Live</span></div>
<div class="video"><img id="feed" alt="Live shelf camera with product detection boxes"></div></section>
<aside class="side"><section class="card"><p class="sectionlabel">Detected in current frame</p>
<div class="product"><span class="swatch coke"></span><span class="productname">Coke Zero</span><span class="count" id="coke_zero">–</span></div>
<div class="product"><span class="swatch oreo"></span><span class="productname">Oreo</span><span class="count" id="oreo">–</span></div>
<div class="product"><span class="swatch wipes"></span><span class="productname">Goodwipes</span><span class="count" id="goodwipes">–</span></div></section>
<section class="card"><p class="sectionlabel">System</p><div class="stat"><span>Detector</span><strong>B_5 / YOLO12</strong></div>
<div class="stat"><span>Compute</span><strong id="device">–</strong></div><div class="stat"><span>Processing rate</span><strong id="fps">–</strong></div>
<div class="stat" title="From application camera read to encoded frame; not full camera-to-screen latency"><span>Pipeline age</span><strong id="pipeline">–</strong></div>
<div class="stat"><span>Confidence threshold</span><strong id="confidence">–</strong></div></section>
<div class="note">Detection counts are frame-level model outputs, not inventory or checkout decisions. Objects may be missed under occlusion or changing viewpoints.</div></aside></main>
<footer class="foot"><span>Autonomous Store · Live Detection Demo</span><span>Prototype output · For demonstration only</span></footer>
<script>async function refresh(){try{const r=await fetch('/api/status',{cache:'no-store'});const s=await r.json();
const active=s.ready&&!s.error&&Date.now()/1000-s.updated_at<3;const chip=document.getElementById('live');chip.classList.toggle('off',!active);
document.getElementById('state').textContent=s.error?'CAMERA ERROR':active?'LIVE':'CONNECTING';
document.getElementById('device').textContent=s.device==='mps'?'Apple GPU (MPS)':s.device==='0'?'NVIDIA GPU':s.device.toUpperCase();
document.getElementById('fps').textContent=active?s.fps.toFixed(1)+' FPS':'–';
document.getElementById('pipeline').textContent=active?Math.round(s.pipeline_ms)+' ms':'–';
document.getElementById('confidence').textContent=Number(s.confidence).toFixed(2);
for(const k of ['coke_zero','oreo','goodwipes'])document.getElementById(k).textContent=active?s.counts[k]:'–';
}catch(e){document.getElementById('live').classList.add('off');document.getElementById('state').textContent='DISCONNECTED'}}
const feed=document.getElementById('feed');function nextFrame(){feed.src='/frame.jpg?t='+Date.now()}
feed.onload=()=>setTimeout(nextFrame,80);feed.onerror=()=>setTimeout(nextFrame,500);nextFrame();
setInterval(refresh,700);refresh();</script></body></html>"""


class LatestFrameCapture:
    """Drain the camera continuously and give inference only the newest frame."""

    def __init__(self, capture):
        self.capture = capture
        self.condition = threading.Condition()
        self.latest = None
        self.captured_at = 0.0
        self.sequence = 0
        self.consumed = 0
        self.ended = False
        threading.Thread(target=self._drain, daemon=True).start()

    def _drain(self) -> None:
        try:
            while True:
                ok, frame = self.capture.read()
                if not ok:
                    break
                with self.condition:
                    self.latest = frame
                    self.captured_at = time.monotonic()
                    self.sequence += 1
                    self.condition.notify_all()
        finally:
            with self.condition:
                self.ended = True
                self.condition.notify_all()

    def read(self):
        with self.condition:
            self.condition.wait_for(lambda: self.sequence > self.consumed or self.ended,
                                    timeout=5)
            if self.sequence <= self.consumed:
                return False, None, None
            self.consumed = self.sequence
            return True, self.latest.copy(), self.captured_at

    def release(self) -> None:
        self.capture.release()


class Shared:
    def __init__(self, device: str, confidence: float):
        self.lock = threading.Lock()
        self.jpeg: bytes | None = None
        self.status = {"ready": False, "error": None, "fps": 0.0,
                       "pipeline_ms": 0.0,
                       "updated_at": 0.0,
                       "device": device, "confidence": confidence,
                       "counts": {name: 0 for name in CLASSES}}


def detect_loop(shared: Shared, source: str, model_path: Path, imgsz: int) -> None:
    capture = None
    try:
        source = resolve_camera_source(source)
        source_capture = (NamedMacCamera(source.removeprefix("camera:").strip())
                          if isinstance(source, str) and source.startswith("camera:")
                          else cv2.VideoCapture(source))
        if not source_capture.isOpened():
            raise RuntimeError(f"Cannot open camera: {source}")
        capture = LatestFrameCapture(source_capture)
        model = YOLO(model_path)
        display_names = {"coke_zero": "Coke Zero", "oreo": "Oreo", "goodwipes": "Goodwipes"}
        previous = None
        fps = 0.0
        while True:
            ok, frame, captured_at = capture.read()
            if not ok:
                raise RuntimeError("Camera stream ended")
            result = model.predict(frame, imgsz=imgsz, conf=shared.status["confidence"],
                                   iou=0.7, device=shared.status["device"], verbose=False)[0]
            now = time.monotonic()
            if previous is not None:
                instant = 1.0 / max(1e-6, now - previous)
                fps = instant if fps == 0 else 0.8 * fps + 0.2 * instant
            previous = now
            counts = {name: 0 for name in CLASSES}
            for box in result.boxes:
                class_id = int(box.cls[0])
                if class_id not in range(len(CLASSES)):
                    continue
                counts[CLASSES[class_id]] += 1
                x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
                color = COLORS[class_id]
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{display_names[CLASSES[class_id]]} {float(box.conf[0]):.2f}",
                            (x1, max(22, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
            if ok:
                with shared.lock:
                    shared.jpeg = encoded.tobytes()
                    shared.status.update(ready=True, error=None, fps=fps, counts=counts,
                                         pipeline_ms=round((time.monotonic() - captured_at) * 1000),
                                         updated_at=time.time())
    except Exception as exc:
        with shared.lock:
            shared.status.update(error=str(exc), ready=False)
    finally:
        if capture is not None:
            capture.release()


def make_handler(shared: Shared):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                body = PAGE.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/api/status":
                with shared.lock:
                    body = json.dumps(shared.status, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif self.path.startswith("/frame.jpg"):
                with shared.lock:
                    jpeg = shared.jpeg
                if jpeg is None:
                    self.send_error(503, "Waiting for camera")
                    return
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(jpeg)))
                self.send_header("Cache-Control", "no-store, max-age=0")
                self.end_headers()
                self.wfile.write(jpeg)
            elif self.path == "/video.mjpg":
                self.send_response(200)
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                last_jpeg = None
                try:
                    while True:
                        with shared.lock:
                            jpeg = shared.jpeg
                            failed = shared.status["error"] is not None
                        if failed:
                            break
                        if jpeg and jpeg is not last_jpeg:
                            self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " +
                                             str(len(jpeg)).encode() + b"\r\n\r\n" + jpeg + b"\r\n")
                            self.wfile.flush()
                            last_jpeg = jpeg
                        time.sleep(0.05)
                except (BrokenPipeError, ConnectionResetError):
                    pass
            else:
                self.send_error(404)

        def log_message(self, format, *args):
            if args and str(args[1] if len(args) > 1 else args[0]).startswith(("4", "5")):
                super().log_message(format, *args)

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="camera:EMEET SmartCam C960")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--confidence", type=float, default=0.35)
    parser.add_argument("--imgsz", type=int, default=1024)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 0 < args.confidence < 1:
        parser.error("--confidence must be between 0 and 1")
    shared = Shared(resolve_device(args.device), args.confidence)
    threading.Thread(target=detect_loop, args=(shared, args.source, args.model, args.imgsz),
                     daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(shared))
    print(f"Open http://127.0.0.1:{args.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
