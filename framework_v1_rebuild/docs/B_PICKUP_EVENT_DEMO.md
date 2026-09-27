# B-series pickup event prototype

This prototype uses the reviewed B-AUG2 detector and a fixed-camera shelf
occupancy state machine. The same `ShelfEventEngine.update(time_s, detections)`
function consumes sampled frames from a saved video or a live camera. The first
three seconds calibrate stable product positions, so the shelf should be stocked
and unobstructed when a live session starts.

## What the labels mean

- `possible_pickup`: a product previously stable at a shelf position has not
  been detected at that position for at least 1.2 seconds.
- `returned_to_shelf`: that position has been detected again for at least
  0.6 seconds.
- `currently_missing_from_shelf`: the number of calibrated positions currently
  vacant. This is **not** a purchase count.
- `no_reference_objects`: calibration could not find stable products; no event
  inference is possible for that recording.
- An empty event list means no change was **observed at calibrated positions**.
  It does not prove that no pickup occurred. The Coke pickup clip demonstrates
  this failure mode: static Coke units remain visible while the handled unit
  is not consistently detected.

One camera and the current three-class detector do not establish which person
holds a product, whether an unseen product was carried away, or whether the
product was merely moved to another shelf position. Event outputs are therefore
review candidates, not checkout records.

## Initial video check

| Video | Result |
|---|---|
| `test_pickup_oreo` | Possible Oreo pickup around 7.7 s and later return; additional movement candidates appear. |
| `test_pickup_goodwipes` | Possible Goodwipes pickup around 5.8 s and return around 9.8 s; additional movement candidates appear. |
| `test_pickup_coke` | No event; B-AUG2 sees static Coke units, but does not reliably follow the handled unit. This is an unresolved miss. |
| `multiple_new1` | Goodwipes and Coke shelf-change candidates; individual events need manual review. |
| `multiple_new2` | No stable product positions during calibration, so event inference is unavailable. |

The marked video samples and JSON records are under
`outputs/B_series/pickup_demo/rendered/`. Sparse detection traces for all eight
test videos are under `outputs/B_series/pickup_demo/detections/`.

## Run on a video or live source

On the Mac with the EMEET camera, start with detection only (no pickup claims):

```bash
.venv-mac/bin/python src/run_b_pickup_demo.py 'camera:EMEET SmartCam C960' --detect-only --show
```

Press `q` in the preview window to stop. `camera:NAME` resolves the macOS
AVFoundation camera by its exact name and reads it through FFmpeg; OpenCV camera
numbers do not necessarily match FFmpeg's numbers. The optional `--roi X1 Y1 X2 Y2`
uses normalized coordinates to crop before inference, but should be validated
against the uncropped feed before use. The September 22 live check found that
a central crop reduced detections, so full-frame inference remains the default.
Mac inference uses MPS when available. Detection-only mode does not calibrate
shelf slots or claim pickup events.

For a browser dashboard instead of an OpenCV preview window:

```bash
.venv-mac/bin/python src/live_detection_web.py
```

Open `http://127.0.0.1:8765/` on the same Mac. The server binds only to
localhost and shows a single shared camera stream with current-frame candidate
counts. Stop it with Ctrl+C in the launching terminal. An initial September 22
frame found Coke and some Goodwipes, but no Oreo candidates even with
`conf=0.05` and `imgsz=1280` on a 1920×1080 frame. After the shelf arrangement
changed, both Oreo packs became detectable. This illustrates scene sensitivity:
do not interpret a zero count as an empty shelf; collect and annotate this
camera view before using detections for pickup decisions.

The live page now drains the camera continuously and discards old frames before
inference. The browser requests the latest JPEG rather than consuming a queued
MJPEG stream. `Pipeline age` measures from the application's camera read to
encoded output; it is **not** full camera-to-screen latency. For a trustworthy
end-to-end measure, move a visible stopwatch or LED in the camera view and
compare the physical change with its appearance on screen.

From `C:\Market\framework_v1_rebuild` on the Windows GPU computer:

```powershell
.venv\Scripts\python.exe src\run_b_pickup_demo.py data\videos_B\test\test_pickup_oreo.mov --output outputs\B_series\pickup_demo\oreo_review.mp4
.venv\Scripts\python.exe src\run_b_pickup_demo.py 0 --show
```

The second command uses camera device 0. An RTSP URL can be passed as the
source instead. Recorded and live sources share the model, thresholds, shelf
calibration, event logic, and overlay. The input connection and shelf positions
must be checked again when the physical camera or layout changes.

## Before an event-level demo is presented as reliable

1. Add a small event timeline for each rehearsal video: pickup start, put-back,
   product class, and cases where the object becomes invisible. Keep separate
   clips for final validation after tuning the rules.
2. Address the missed handled Coke and the no-calibration case. Consider a
   second view or hand/object tracking if the current viewpoint does not show
   the carried product.
3. Review each candidate against the video and tune dwell times, shelf zones,
   and detection confidence on development clips. A shelf movement should not
   be reported as a completed purchase.
