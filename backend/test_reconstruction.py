"""Run sparse reconstruction from an image directory.

Usage:
    python test_reconstruction.py path/to/images --output outputs/reconstruction_test
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from processing.reconstruct import ReconstructionError, reconstruct_images


def main() -> int:
    parser = argparse.ArgumentParser(description="Test AeroReconstruct sparse reconstruction.")
    parser.add_argument("image_dir", help="Directory containing overlapping input images.")
    parser.add_argument(
        "--output",
        default=str(Path("outputs") / "reconstruction_test"),
        help="Directory where reconstruction outputs should be written.",
    )
    args = parser.parse_args()

    try:
        result = reconstruct_images(args.image_dir, args.output)
    except (FileNotFoundError, NotADirectoryError, ReconstructionError) as exc:
        print(f"Reconstruction failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
