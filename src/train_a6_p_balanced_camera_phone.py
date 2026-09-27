#!/usr/bin/env python3
"""Train A6-P: A5 balanced Camera data plus the reviewed Phone addition."""

from train_common import train_branch


if __name__ == "__main__":
    train_branch("a6_p_balanced_camera_phone", "dataset_a6_p_balanced_camera_phone.yaml")
