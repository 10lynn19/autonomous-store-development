#!/usr/bin/env python3
"""Matched C0 and C2 fine-tuning from the best B augmentation checkpoint."""

import argparse
from pathlib import Path

from train_common import ROOT, train_branch


INITIAL_WEIGHTS = "outputs/B_series/training/b_aug2_mosaic_copy/weights/best.pt"
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
BRANCHES = {
    "b_c0_clean_control": "dataset_b1_camera.yaml",
    "b_c2_real_pickup": "dataset_b5_real_pickup.yaml",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("branch", choices=sorted(BRANCHES))
    args = parser.parse_args()
    if not (ROOT / INITIAL_WEIGHTS).is_file():
        raise SystemExit(f"Missing common initialization: {INITIAL_WEIGHTS}")
    output = ROOT / "outputs/B_series/training" / args.branch
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing experiment: {output}")
    train_branch(
        args.branch,
        BRANCHES[args.branch],
        series="B_series",
        augmentation=AUGMENTATION,
        initial_weights=INITIAL_WEIGHTS,
    )


if __name__ == "__main__":
    main()
