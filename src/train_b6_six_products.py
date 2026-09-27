#!/usr/bin/env python3
"""Train B_6 by expanding B_5 from three to six product classes."""

from train_common import ROOT, train_branch


BRANCH = "b_6"
INITIAL_WEIGHTS = "outputs/B_series/training/b_5/weights/best.pt"
DATASET = ROOT / "data/datasets_B/b6_six_product_split"
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
        raise SystemExit(f"Missing B_5 checkpoint: {INITIAL_WEIGHTS}")
    train_images = sorted((DATASET / "images/train").glob("*.jpg"))
    train_labels = sorted((DATASET / "labels/train").glob("*.txt"))
    val_images = sorted((DATASET / "images/val").glob("*.jpg"))
    val_labels = sorted((DATASET / "labels/val").glob("*.txt"))
    if (len(train_images), len(train_labels), len(val_images), len(val_labels)) != (241, 241, 58, 58):
        raise SystemExit(
            "Expected B_6 split of 241 train and 58 validation images; "
            f"got {len(train_images)}/{len(train_labels)} train and {len(val_images)}/{len(val_labels)} val"
        )
    if (ROOT / "outputs/B_series/training" / BRANCH).exists():
        raise SystemExit(f"Refusing to overwrite existing experiment: {BRANCH}")
    train_branch(
        BRANCH,
        "dataset_b6_six_products.yaml",
        series="B_series",
        augmentation=AUGMENTATION,
        initial_weights=INITIAL_WEIGHTS,
    )


if __name__ == "__main__":
    main()
