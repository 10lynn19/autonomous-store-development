#!/usr/bin/env python3
"""Train B4: B0 plus labeled clean camera and phone frames."""

from train_common import train_branch


if __name__ == "__main__":
    train_branch(
        "b4_camera_phone",
        "dataset_b4_camera_phone.yaml",
        series="B_series",
    )
