#!/usr/bin/env python3
"""Train A4-P: A0 clean plus Camera-clean plus Phone small-object data."""

from train_common import train_branch


if __name__ == "__main__":
    train_branch("a4_p_camera_phone", "dataset_a4_p_camera_phone.yaml")
