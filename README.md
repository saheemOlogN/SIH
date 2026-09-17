# AeroReconstruct

Python backend scaffold for converting drone video into a 3D point cloud. The reconstruction pipeline is intentionally not implemented yet.

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
