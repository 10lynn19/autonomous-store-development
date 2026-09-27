#!/usr/bin/env python3
"""Train B-AUG2 on B1 data with light transforms and limited composition."""

from train_common import train_branch


if __name__ == "__main__":
    train_branch(
        "b_aug2_mosaic_copy",
        "dataset_b1_camera.yaml",
        series="B_series",
        augmentation={
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
        },
    )
