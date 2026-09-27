#!/usr/bin/env python3
"""Shared, fixed training configuration for the controlled A-series study."""

from pathlib import Path

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]


def train_branch(
    name: str,
    dataset_config: str,
    series: str = "A_series",
    augmentation: dict | None = None,
    initial_weights: str = "models/pretrained/yolo12n.pt",
) -> None:
    """Train one branch from the shared checkpoint into its series folder."""
    model = YOLO(ROOT / initial_weights)
    train_args = dict(
        data=ROOT / "configs" / dataset_config,
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
        project=ROOT / "outputs" / series / "training",
        name=name,
        exist_ok=False,
        seed=2026,
        plots=True,
    )
    if augmentation:
        train_args.update(augmentation)
    model.train(**train_args)
