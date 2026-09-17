# AeroReconstruct

Python backend for converting overlapping drone imagery into a sparse 3D point cloud.

## Backend setup

From the project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the backend:

```powershell
python app.py
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/health
```

Expected response:

```json
{
  "service": "AeroReconstruct Backend",
  "status": "ok"
}
```

## Image reconstruction test

The current core pipeline reconstructs from a folder of still images. Video frame extraction and Flask upload APIs will be added later.

### Prepare an image dataset

Use a small folder of real, overlapping images of the same scene:

- Use at least 10-20 sharp images for a meaningful first test.
- Keep strong overlap between neighboring images, ideally 60% or more.
- Avoid motion blur, blank walls, reflective surfaces, sky-only frames, and repeated textures.
- Use supported formats: `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.bmp`, `.webp`.
- Put only readable image files in the dataset folder or remove corrupt files before running.

Example:

```text
datasets/
  sample_scene/
    IMG_0001.jpg
    IMG_0002.jpg
    IMG_0003.jpg
```

### Run the reconstruction test

From the project root:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python test_reconstruction.py ..\datasets\sample_scene --output outputs\sample_scene
```

The script prints JSON on success. The exact counts depend on the dataset:

```json
{
  "status": "ok",
  "pycolmap_version": "4.2.0",
  "ply_path": "C:\\path\\to\\backend\\outputs\\sample_scene\\reconstruction_...\\point_cloud.ply",
  "input_images": 20,
  "registered_images": 18,
  "reconstructed_points": 12453
}
```

The returned `ply_path` points to the exported sparse point cloud. COLMAP binary model files are written under the returned `model_dir`.

### Common failure reasons

- The image directory does not exist.
- The folder contains no supported image files.
- One or more files have image extensions but cannot be read by OpenCV.
- The images do not overlap enough for matching.
- The scene has too little texture or too much blur.
- The dataset has too few usable images for incremental mapping.
- PyCOLMAP registers no images or triangulates no 3D points.
