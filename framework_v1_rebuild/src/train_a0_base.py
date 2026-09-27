#!/usr/bin/env python3
"""Train the clean A0 baseline without synthetic or online augmentation."""

from pathlib import Path

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    model = YOLO(ROOT / "models/pretrained/yolo12n.pt")
    model.train(
        data=ROOT / "configs/dataset_a0_base.yaml",
        epochs=40,
        imgsz=1024,
        batch=4,
        patience=8,
        device=0,
        workers=4,
        amp=True,
        optimizer="AdamW",
        lr0=0.0003,
        lrf=0.1,
        weight_decay=0.0005,
        hsv_h=0.0,
        hsv_s=0.0,
        hsv_v=0.0,
        degrees=0.0,
        translate=0.0,
        scale=0.0,
        shear=0.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.0,
        mosaic=0.0,
        mixup=0.0,
        cutmix=0.0,
        erasing=0.0,
        project=ROOT / "outputs/A_series/training",
        name="a0_base",
        exist_ok=False,
        seed=2026,
        plots=True,
    )


if __name__ == "__main__":
    main()
