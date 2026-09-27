#!/usr/bin/env python3
"""Train B_5 by fine-tuning B-AUG2 with new deployment-camera data."""

from train_common import ROOT, train_branch


BRANCH = "b_5"
INITIAL_WEIGHTS = "outputs/B_series/training/b_aug2_mosaic_copy/weights/best.pt"
DATASET = "b_aug2_new_addition"
AUGMENTATION = {
    "hsv_h": 0.005,
    "hsv_s": 0.15,
    "hsv_v": 0.15,
    "degrees": 5.0,
    "translate": 0.05,
    "scale": 0.15,
    "fliplr": 0.0,
    "mosaic": 0.20,
    "copy_paste": 0.10,
    "close_mosaic": 10,
}


def main() -> None:
    if not (ROOT / INITIAL_WEIGHTS).is_file():
        raise SystemExit(f"Missing B-AUG2 checkpoint: {INITIAL_WEIGHTS}")
    labels = sorted((ROOT / "data/datasets_B" / DATASET / "labels/train").glob("*.txt"))
    images = sorted((ROOT / "data/datasets_B" / DATASET / "images/train").glob("*.jpg"))
    if len(labels) != 90 or len(images) != 90:
        raise SystemExit(f"Expected 90 new labeled training frames, got {len(labels)} labels and {len(images)} images")
    if (ROOT / "outputs/B_series/training" / BRANCH).exists():
        raise SystemExit(f"Refusing to overwrite existing experiment: {BRANCH}")
    train_branch(
        BRANCH,
        "dataset_b_aug2_new_camera.yaml",
        series="B_series",
        augmentation=AUGMENTATION,
        initial_weights=INITIAL_WEIGHTS,
    )


if __name__ == "__main__":
    main()
