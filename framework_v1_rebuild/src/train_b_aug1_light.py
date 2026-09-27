#!/usr/bin/env python3
"""Train B-AUG1 on B1 data with conservative online augmentation."""

from train_common import train_branch


if __name__ == "__main__":
    train_branch(
        "b_aug1_light",
        "dataset_b1_camera.yaml",
        series="B_series",
        augmentation={
            # Preserve product identity and packaging colors while modeling
            # modest camera/placement variation.
            "hsv_h": 0.005,
            "hsv_s": 0.15,
            "hsv_v": 0.15,
            "degrees": 5.0,
            "translate": 0.05,
            "scale": 0.15,
            "fliplr": 0.0,
        },
    )
