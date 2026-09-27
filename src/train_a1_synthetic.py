#!/usr/bin/env python3
"""Train A1: A0 clean data plus computer-synthesized small objects."""

from train_common import train_branch


if __name__ == "__main__":
    train_branch("a1_synthetic", "dataset_a1_synthetic.yaml")
