#!/usr/bin/env python3
"""Create the controlled A1 synthetic addition (48 images per class).

The object scale/position distribution is copied from A2's annotations, while
the pixels come only from A0 clean-background images.  Each image contains one
scaled object with a small rotation and Gaussian sensor noise.
"""

from __future__ import annotations

import argparse
import csv
import random
import shutil
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CLASS_NAMES = {0: "coke_zero", 1: "think_protein_bar", 2: "ziploc_box"}


def read_box(path: Path) -> tuple[int, float, float, float, float]:
    parts = path.read_text(encoding="utf-8").strip().split()
    if len(parts) != 5:
        raise ValueError(f"Expected one YOLO box in {path}")
    return int(parts[0]), *(float(value) for value in parts[1:])


def cutout(image: np.ndarray, box: tuple[float, float, float, float]) -> tuple[np.ndarray, np.ndarray, tuple[int, int, int, int]]:
    height, width = image.shape[:2]
    cx, cy, bw, bh = box
    x1 = int((cx - bw / 2) * width)
    y1 = int((cy - bh / 2) * height)
    x2 = int((cx + bw / 2) * width)
    y2 = int((cy + bh / 2) * height)
    margin = max(16, int(0.10 * max(x2 - x1, y2 - y1)))
    rx1, ry1 = max(0, x1 - margin), max(0, y1 - margin)
    rx2, ry2 = min(width, x2 + margin), min(height, y2 + margin)
    crop = image[ry1:ry2, rx1:rx2].copy()
    local = (x1 - rx1, y1 - ry1, x2 - rx1, y2 - ry1)

    mask = np.zeros(crop.shape[:2], np.uint8)
    lx1, ly1, lx2, ly2 = local
    rect = (max(1, lx1), max(1, ly1), max(2, lx2 - lx1), max(2, ly2 - ly1))
    bg_model = np.zeros((1, 65), np.float64)
    fg_model = np.zeros((1, 65), np.float64)
    try:
        cv2.grabCut(crop, mask, rect, bg_model, fg_model, 4, cv2.GC_INIT_WITH_RECT)
        alpha = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    except cv2.error:
        alpha = np.zeros(crop.shape[:2], np.uint8)
        alpha[ly1:ly2, lx1:lx2] = 255
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    alpha = cv2.GaussianBlur(alpha, (5, 5), 0)
    return crop, alpha, local


def rotate(crop: np.ndarray, alpha: np.ndarray, box: tuple[int, int, int, int], angle: float):
    height, width = crop.shape[:2]
    center = (width / 2, height / 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    cosine, sine = abs(matrix[0, 0]), abs(matrix[0, 1])
    out_width = int(height * sine + width * cosine)
    out_height = int(height * cosine + width * sine)
    matrix[0, 2] += out_width / 2 - center[0]
    matrix[1, 2] += out_height / 2 - center[1]
    color = cv2.warpAffine(crop, matrix, (out_width, out_height), borderValue=(245, 245, 245))
    mask = cv2.warpAffine(alpha, matrix, (out_width, out_height), borderValue=0)
    x1, y1, x2, y2 = box
    corners = np.array([[x1, y1, 1], [x2, y1, 1], [x2, y2, 1], [x1, y2, 1]], np.float32)
    transformed = corners @ matrix.T
    new_box = (
        float(transformed[:, 0].min()), float(transformed[:, 1].min()),
        float(transformed[:, 0].max()), float(transformed[:, 1].max()),
    )
    return color, mask, new_box


def background(width: int, height: int, rng: np.random.Generator) -> np.ndarray:
    base = rng.uniform(235, 252)
    vertical = np.linspace(rng.uniform(-6, 2), rng.uniform(-2, 6), height, dtype=np.float32)[:, None, None]
    canvas = np.full((height, width, 3), base, np.float32) + vertical
    return np.clip(canvas, 0, 255).astype(np.uint8)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--a0", type=Path, default=ROOT / "data/datasets_A/a0_base")
    parser.add_argument("--scale-reference", type=Path, default=ROOT / "data/datasets_A/a2_phone_addition")
    parser.add_argument("--output", type=Path, default=ROOT / "data/datasets_A/a1_synthetic_addition")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.output.exists():
        if not args.overwrite:
            raise SystemExit(f"{args.output} exists; pass --overwrite to replace it")
        shutil.rmtree(args.output)
    image_out = args.output / "images/train"
    label_out = args.output / "labels/train"
    review_out = args.output / "review"
    image_out.mkdir(parents=True)
    label_out.mkdir(parents=True)
    review_out.mkdir(parents=True)

    py_rng = random.Random(args.seed)
    rng = np.random.default_rng(args.seed)
    source_by_class: dict[int, list[Path]] = {key: [] for key in CLASS_NAMES}
    for label_path in sorted((args.a0 / "labels/train").glob("*.txt")):
        class_id, *_ = read_box(label_path)
        source_by_class[class_id].append(label_path)
    targets_by_class: dict[int, list[tuple[float, float, float, float]]] = {key: [] for key in CLASS_NAMES}
    for label_path in sorted((args.scale_reference / "labels/train").glob("*.txt")):
        class_id, cx, cy, bw, bh = read_box(label_path)
        targets_by_class[class_id].append((cx, cy, bw, bh))
    if any(len(values) != 48 for values in targets_by_class.values()):
        raise SystemExit("Scale reference must contain exactly 48 annotations per class")

    review_cells: list[np.ndarray] = []
    manifest = []
    canvas_width, canvas_height = 1920, 1080
    for class_id, class_name in CLASS_NAMES.items():
        sources = source_by_class[class_id]
        targets = targets_by_class[class_id].copy()
        py_rng.shuffle(sources)
        py_rng.shuffle(targets)
        for sequence, target in enumerate(targets):
            source_label = sources[sequence % len(sources)]
            source_image = args.a0 / "images/train" / f"{source_label.stem}.jpg"
            image = cv2.imread(str(source_image))
            _, scx, scy, sbw, sbh = read_box(source_label)
            crop, alpha, local_box = cutout(image, (scx, scy, sbw, sbh))
            angle = py_rng.uniform(-15.0, 15.0)
            crop, alpha, rotated_box = rotate(crop, alpha, local_box, angle)

            tcx, tcy, target_w, target_h = target
            rw = rotated_box[2] - rotated_box[0]
            rh = rotated_box[3] - rotated_box[1]
            scale = min(target_w * canvas_width / rw, target_h * canvas_height / rh)
            new_width = max(8, round(crop.shape[1] * scale))
            new_height = max(8, round(crop.shape[0] * scale))
            crop = cv2.resize(crop, (new_width, new_height), interpolation=cv2.INTER_AREA)
            alpha = cv2.resize(alpha, (new_width, new_height), interpolation=cv2.INTER_AREA)
            scaled_box = tuple(value * scale for value in rotated_box)

            object_center_x = (scaled_box[0] + scaled_box[2]) / 2
            object_center_y = (scaled_box[1] + scaled_box[3]) / 2
            left = round(tcx * canvas_width - object_center_x)
            top = round(tcy * canvas_height - object_center_y)
            left = max(0, min(canvas_width - new_width, left))
            top = max(0, min(canvas_height - new_height, top))
            canvas = background(canvas_width, canvas_height, rng)
            region = canvas[top : top + new_height, left : left + new_width]
            blend = alpha.astype(np.float32)[:, :, None] / 255.0
            region[:] = (crop * blend + region * (1.0 - blend)).astype(np.uint8)

            sigma = py_rng.uniform(2.0, 10.0)
            noise = rng.normal(0, sigma, canvas.shape).astype(np.float32)
            canvas = np.clip(canvas.astype(np.float32) + noise, 0, 255).astype(np.uint8)
            x1, y1, x2, y2 = (
                left + scaled_box[0], top + scaled_box[1],
                left + scaled_box[2], top + scaled_box[3],
            )
            x1, y1 = max(0.0, x1), max(0.0, y1)
            x2, y2 = min(float(canvas_width), x2), min(float(canvas_height), y2)
            stem = f"synthetic_{class_name}_{sequence:03d}"
            cv2.imwrite(str(image_out / f"{stem}.jpg"), canvas, [cv2.IMWRITE_JPEG_QUALITY, 94])
            line = (
                f"{class_id} {(x1+x2)/(2*canvas_width):.6f} {(y1+y2)/(2*canvas_height):.6f} "
                f"{(x2-x1)/canvas_width:.6f} {(y2-y1)/canvas_height:.6f}\n"
            )
            (label_out / f"{stem}.txt").write_text(line, encoding="utf-8")
            manifest.append((stem, class_name, source_image.name, f"{angle:.3f}", f"{sigma:.3f}"))
            if sequence in {0, 12, 24, 36}:
                preview = cv2.resize(canvas, (480, 270), interpolation=cv2.INTER_AREA)
                px1, py1, px2, py2 = [round(value / 4) for value in (x1, y1, x2, y2)]
                cv2.rectangle(preview, (px1, py1), (px2, py2), (0, 220, 0), 2)
                cv2.putText(preview, class_name, (px1, max(18, py1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 150, 0), 1)
                review_cells.append(preview)

    with (args.output / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("image", "class", "source_image", "rotation_degrees", "noise_sigma"))
        writer.writerows(manifest)
    rows = [np.hstack(review_cells[start:start + 4]) for start in range(0, len(review_cells), 4)]
    cv2.imwrite(str(review_out / "labels_preview.jpg"), np.vstack(rows))
    print("Created A1 synthetic addition: 144 images, 48 per class")
    print("Review:", review_out / "labels_preview.jpg")


if __name__ == "__main__":
    main()
