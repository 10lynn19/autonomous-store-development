#!/usr/bin/env python3
"""Conservative, camera-specific shelf-event logic shared by video and live demos.

Input detections use normalized xyxy boxes. The first few seconds should show
a stocked, unobstructed shelf; each stable detection becomes a reference slot.
Events report evidence about shelf occupancy, not a completed purchase.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path


CLASSES = ["coke_zero", "oreo", "goodwipes"]


def center(detection: dict) -> tuple[float, float]:
    x1, y1, x2, y2 = detection["box"]
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


@dataclass
class Slot:
    class_id: int
    center: tuple[float, float]
    calibration_hits: int = 0
    state: str = "present"
    absent_since: float | None = None
    present_since: float | None = None
    opened_at: float | None = None


@dataclass
class ShelfEventEngine:
    calibration_seconds: float = 3.0
    min_calibration_ratio: float = 0.55
    min_confidence: float = 0.35
    calibration_radius: float = 0.018
    match_radius: float = 0.035
    missing_seconds: float = 1.2
    return_seconds: float = 0.6
    slots: list[Slot] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    calibration_frames: int = 0
    calibrated: bool = False

    def update(self, time_s: float, detections: list[dict]) -> list[dict]:
        """Consume one frame and return newly opened/closed candidate events."""
        detections = [d for d in detections
                      if d["class_id"] in range(len(CLASSES))
                      and d["confidence"] >= self.min_confidence]
        if not self.calibrated:
            if time_s < self.calibration_seconds:
                self._calibrate_frame(detections)
                return []
            self.slots = [s for s in self.slots
                          if s.calibration_hits / max(1, self.calibration_frames)
                          >= self.min_calibration_ratio]
            self.calibrated = True

        emitted = []
        unmatched = list(detections)
        # Match fixed shelf positions, one detection per reference slot.
        for slot in sorted(self.slots, key=lambda s: -s.calibration_hits):
            candidates = [(distance(slot.center, center(d)), i)
                          for i, d in enumerate(unmatched)
                          if d["class_id"] == slot.class_id]
            nearest = min(candidates, default=None)
            visible = nearest is not None and nearest[0] <= self.match_radius
            if visible:
                unmatched.pop(nearest[1])
                slot.absent_since = None
                if slot.state == "missing":
                    if slot.present_since is None:
                        slot.present_since = time_s
                    if time_s - slot.present_since >= self.return_seconds:
                        slot.state = "present"
                        event = self._event("returned_to_shelf", slot, time_s)
                        event["paired_pickup_time_s"] = slot.opened_at
                        slot.opened_at = None
                        emitted.append(event)
                else:
                    slot.present_since = time_s
            else:
                slot.present_since = None
                if slot.absent_since is None:
                    slot.absent_since = time_s
                if slot.state == "present" and time_s - slot.absent_since >= self.missing_seconds:
                    slot.state = "missing"
                    slot.opened_at = slot.absent_since
                    event = self._event("possible_pickup", slot, time_s)
                    event["first_missing_time_s"] = slot.absent_since
                    emitted.append(event)
        self.events.extend(emitted)
        return emitted

    def _calibrate_frame(self, detections: list[dict]) -> None:
        self.calibration_frames += 1
        matched: set[int] = set()
        for detection in detections:
            point = center(detection)
            candidates = [(distance(s.center, point), i) for i, s in enumerate(self.slots)
                          if s.class_id == detection["class_id"] and i not in matched]
            nearest = min(candidates, default=None)
            if nearest is not None and nearest[0] <= self.calibration_radius:
                slot = self.slots[nearest[1]]
                n = slot.calibration_hits
                slot.center = ((slot.center[0] * n + point[0]) / (n + 1),
                               (slot.center[1] * n + point[1]) / (n + 1))
                slot.calibration_hits += 1
                matched.add(nearest[1])
            else:
                self.slots.append(Slot(detection["class_id"], point, 1))
                matched.add(len(self.slots) - 1)

    @staticmethod
    def _event(kind: str, slot: Slot, time_s: float) -> dict:
        return {"event": kind, "class_id": slot.class_id,
                "class_name": CLASSES[slot.class_id], "time_s": round(time_s, 2),
                "shelf_position": [round(v, 3) for v in slot.center]}

    def snapshot(self) -> dict:
        missing = {name: 0 for name in CLASSES}
        for slot in self.slots:
            if slot.state == "missing":
                missing[CLASSES[slot.class_id]] += 1
        status = ("calibrating" if not self.calibrated else
                  "no_reference_objects" if not self.slots else "tracking")
        return {"status": status, "calibrated": self.calibrated,
                "reference_slots": len(self.slots),
                "currently_missing_from_shelf": missing}


def analyze_file(path: Path) -> dict:
    engine = ShelfEventEngine()
    for line in path.read_text(encoding="utf-8").splitlines():
        frame = json.loads(line)
        engine.update(frame["time_s"], frame["detections"])
    return {"video": path.stem, **engine.snapshot(), "events": engine.events}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("detections", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results = [analyze_file(path) for path in args.detections]
    body = json.dumps(results, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body + "\n", encoding="utf-8")
    print(body)


if __name__ == "__main__":
    main()
