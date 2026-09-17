"""Sparse image-based 3D reconstruction with PyCOLMAP."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
import pycolmap


SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
}


class ReconstructionError(RuntimeError):
    """Raised when image validation or sparse reconstruction fails."""


def reconstruct_images(image_dir: str, output_dir: str) -> dict[str, Any]:
    """Reconstruct a sparse point cloud from images and export it as PLY.

    Args:
        image_dir: Directory containing input images.
        output_dir: Directory where the COLMAP workspace and PLY are written.

    Returns:
        A dictionary with real reconstruction paths and statistics.

    Raises:
        FileNotFoundError: If image_dir does not exist.
        NotADirectoryError: If image_dir is not a directory.
        ReconstructionError: If inputs are invalid or reconstruction fails.
    """

    images_path = Path(image_dir).expanduser().resolve()
    outputs_path = Path(output_dir).expanduser().resolve()

    image_files = _validate_image_dir(images_path)
    outputs_path.mkdir(parents=True, exist_ok=True)

    run_dir = outputs_path / _new_run_name()
    sparse_dir = run_dir / "sparse"
    model_dir = run_dir / "sparse_model"
    database_path = run_dir / "database.db"
    ply_path = run_dir / "point_cloud.ply"

    sparse_dir.mkdir(parents=True, exist_ok=False)
    model_dir.mkdir(parents=True, exist_ok=False)

    image_names = [_relative_image_name(path, images_path) for path in image_files]

    try:
        extraction_options = pycolmap.FeatureExtractionOptions()
        extraction_options.use_gpu = False

        matching_options = pycolmap.FeatureMatchingOptions()
        matching_options.use_gpu = False

        mapping_options = pycolmap.IncrementalPipelineOptions()
        mapping_options.ba_use_gpu = False

        pycolmap.extract_features(
            database_path=database_path,
            image_path=images_path,
            image_names=image_names,
            extraction_options=extraction_options,
        )
        pycolmap.match_exhaustive(
            database_path=database_path,
            matching_options=matching_options,
        )
        reconstructions = pycolmap.incremental_mapping(
            database_path=database_path,
            image_path=images_path,
            output_path=sparse_dir,
            options=mapping_options,
        )
    except Exception as exc:
        raise ReconstructionError(f"PyCOLMAP reconstruction failed: {exc}") from exc

    if not reconstructions:
        raise ReconstructionError("Reconstruction failed: PyCOLMAP returned no sparse models.")

    model_id, reconstruction = _select_best_reconstruction(reconstructions)
    registered_images = reconstruction.num_reg_images()
    points_3d = reconstruction.num_points3D()

    if registered_images == 0:
        raise ReconstructionError("Reconstruction failed: no images were registered.")
    if points_3d == 0:
        raise ReconstructionError("Reconstruction failed: no 3D points were reconstructed.")

    reconstruction.write(model_dir)
    reconstruction.export_PLY(ply_path)

    return {
        "status": "ok",
        "pycolmap_version": getattr(pycolmap, "__version__", "unknown"),
        "input_image_dir": str(images_path),
        "output_dir": str(outputs_path),
        "run_dir": str(run_dir),
        "database_path": str(database_path),
        "sparse_dir": str(sparse_dir),
        "model_dir": str(model_dir),
        "ply_path": str(ply_path),
        "model_id": model_id,
        "input_images": len(image_files),
        "registered_images": registered_images,
        "reconstructed_points": points_3d,
    }


def _validate_image_dir(image_dir: Path) -> list[Path]:
    if not image_dir.exists():
        raise FileNotFoundError(f"Image directory does not exist: {image_dir}")
    if not image_dir.is_dir():
        raise NotADirectoryError(f"Image path is not a directory: {image_dir}")

    image_files = sorted(
        path
        for path in image_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    )

    if not image_files:
        raise ReconstructionError(
            f"No supported images found in {image_dir}. "
            f"Supported extensions: {', '.join(sorted(SUPPORTED_IMAGE_EXTENSIONS))}"
        )

    invalid_images = [path for path in image_files if cv2.imread(str(path)) is None]
    if invalid_images:
        invalid_list = ", ".join(str(path) for path in invalid_images[:5])
        extra = "" if len(invalid_images) <= 5 else f" and {len(invalid_images) - 5} more"
        raise ReconstructionError(f"Invalid or unreadable image files: {invalid_list}{extra}")

    return image_files


def _new_run_name() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
    return f"reconstruction_{timestamp}"


def _relative_image_name(image_path: Path, image_dir: Path) -> str:
    return image_path.relative_to(image_dir).as_posix()


def _select_best_reconstruction(
    reconstructions: dict[int, pycolmap.Reconstruction],
) -> tuple[int, pycolmap.Reconstruction]:
    return max(
        reconstructions.items(),
        key=lambda item: (item[1].num_reg_images(), item[1].num_points3D()),
    )
