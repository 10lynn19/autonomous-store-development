#!/usr/bin/env python3
"""Train A4-S: A0 clean plus Camera-clean plus Synthetic small-object data."""

from train_common import train_branch


if __name__ == "__main__":
    train_branch("a4_s_camera_synthetic", "dataset_a4_s_camera_synthetic.yaml")
