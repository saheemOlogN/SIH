"""Extract video frames and run sparse reconstruction.

Usage:
    python test_video_to_reconstruction.py test_data/drone.mp4
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from processing.reconstruct import ReconstructionError, reconstruct_images
from processing.video import VideoProcessingError, extract_frames


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract video frames and run AeroReconstruct sparse reconstruction."
    )
    parser.add_argument("video_path", help="Path to the input video.")
    parser.add_argument(
        "--fps",
        type=float,
        default=3.0,
        help="Frame extraction rate in frames per second. Default: 3",
    )
    args = parser.parse_args()

    run_name = f"{Path(args.video_path).stem}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
    run_dir = Path("outputs") / "video_reconstruction" / run_name
    frames_dir = run_dir / "frames"
    reconstruction_dir = run_dir / "reconstruction"

    print(f"Video: {args.video_path}")
    print(f"Output run directory: {run_dir}")

    try:
        extraction = extract_frames(args.video_path, str(frames_dir), fps=args.fps)
    except (FileNotFoundError, ValueError, VideoProcessingError) as exc:
        print(f"Frame extraction failed: {exc}", file=sys.stderr)
        print(f"Preserved output directory: {run_dir}", file=sys.stderr)
        return 1

    print("Frame extraction:")
    print(f"  Original FPS: {extraction['source_fps']:.3f}")
    print(f"  Duration seconds: {extraction['duration_seconds']:.3f}")
    print(f"  Total frames: {extraction['total_frames']}")
    print(f"  Extracted frames: {extraction['extracted_frames']}")
    print(f"  Frames directory: {extraction['frames_dir']}")

    try:
        reconstruction = reconstruct_images(str(frames_dir), str(reconstruction_dir))
    except (FileNotFoundError, NotADirectoryError, ReconstructionError) as exc:
        print(f"Reconstruction failed: {exc}", file=sys.stderr)
        print(f"Preserved frames directory: {frames_dir}", file=sys.stderr)
        print(f"Preserved reconstruction directory: {reconstruction_dir}", file=sys.stderr)
        return 1

    print("Reconstruction:")
    print(f"  PLY path: {reconstruction['ply_path']}")
    print(f"  Registered images: {reconstruction['registered_images']}")
    print(f"  Reconstructed 3D points: {reconstruction['reconstructed_points']}")
    compact_extraction = {key: value for key, value in extraction.items() if key != "frame_paths"}
    print(json.dumps({"extraction": compact_extraction, "reconstruction": reconstruction}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
