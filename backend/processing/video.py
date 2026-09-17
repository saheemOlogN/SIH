"""Video ingestion and frame extraction helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2


class VideoProcessingError(RuntimeError):
    """Raised when a video cannot be read or frames cannot be extracted."""


def extract_frames(video_path: str, output_dir: str, fps: float = 3.0) -> dict[str, Any]:
    """Extract frames from a video at a target frame rate.

    Args:
        video_path: Path to the input video.
        output_dir: Directory where extracted JPEG frames are written.
        fps: Target extraction rate in frames per second.

    Returns:
        A dictionary with source video metadata and extraction results.
    """

    if fps <= 0:
        raise ValueError("Extraction FPS must be greater than zero.")

    source_path = Path(video_path).expanduser().resolve()
    frames_path = Path(output_dir).expanduser().resolve()

    if not source_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {source_path}")
    if not source_path.is_file():
        raise VideoProcessingError(f"Video path is not a file: {source_path}")

    frames_path.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(source_path))
    if not capture.isOpened():
        raise VideoProcessingError(f"OpenCV could not open video: {source_path}")

    try:
        source_fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        if source_fps <= 0:
            raise VideoProcessingError("Could not determine source video FPS.")

        duration_seconds = total_frames / source_fps if total_frames > 0 else 0.0
        next_capture_time = 0.0
        frame_index = 0
        extracted_count = 0
        frame_paths: list[str] = []

        while True:
            ok, frame = capture.read()
            if not ok:
                break

            current_time = frame_index / source_fps
            if current_time + 1e-9 >= next_capture_time:
                frame_name = f"frame_{extracted_count:06d}.jpg"
                frame_path = frames_path / frame_name
                if not cv2.imwrite(str(frame_path), frame):
                    raise VideoProcessingError(f"Failed to write extracted frame: {frame_path}")
                frame_paths.append(str(frame_path))
                extracted_count += 1
                next_capture_time += 1.0 / fps

            frame_index += 1
    finally:
        capture.release()

    if extracted_count == 0:
        raise VideoProcessingError(f"No frames were extracted from video: {source_path}")

    return {
        "video_path": str(source_path),
        "frames_dir": str(frames_path),
        "source_fps": source_fps,
        "duration_seconds": duration_seconds,
        "total_frames": total_frames,
        "target_fps": fps,
        "extracted_frames": extracted_count,
        "frame_paths": frame_paths,
    }
