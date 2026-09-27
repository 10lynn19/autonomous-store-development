#!/usr/bin/env python3
"""Train A2: A0 clean data plus real phone small-object frames."""

from train_common import train_branch


if __name__ == "__main__":
    train_branch("a2_phone", "dataset_a2_phone.yaml")
