# Ximea-Camera-GUI

Desktop GUI (Tkinter) for XIMEA camera live preview and interval-based frame capture.

## Features
- Live video preview from XIMEA camera (`MC023MG-SY-UB` supported via XIMEA SDK).
- User controls for:
  - Frame rate (fps)
  - Exposure time (microseconds)
  - Gain (dB)
  - Capture interval (seconds)
  - Capture duration (seconds)
  - Save root path (defaults to `C:\XIMEA`)
  - Output folder name
- Timed frame capture that saves 16-bit raw `.tif` images (Mono12 data in 16-bit container) to:
  - `C:\XIMEA\<your_folder_name>` (by default)
- A single-capture button for one-shot image save.
- Countdown display for remaining timed-capture duration.
- Live telemetry readouts at the bottom of the GUI for active FPS, frame mean DN, and camera temperature (when available from XiAPI).
- Bottom tab switcher with:
  - **Setup**: full controls + preview
  - **Demo**: preview-only view using the same active camera/settings/session

## Prerequisites (Windows)
1. Install **XIMEA camera drivers + XiAPI SDK** from XIMEA.
   - Typical install root: `C:\XIMEA\API` (with subfolders like `Python` and `xiAPI`).
2. Install Python **3.10 - 3.12** (recommended `3.11`).
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Run
```bash
python ximea_gui.py
```

## Typical workflow
1. Click **Connect + Start Preview**.
2. Set frame rate and exposure, then click **Apply Camera Settings**.
3. Set capture interval and total duration.
4. Set save path (`C:\XIMEA`) and folder name.
5. Click **Start Timed Capture**.
6. Watch countdown while the timed capture is running.
7. Click **Single Capture** for one image, or **Stop Timed Capture** to end early.

## Notes
- The app saves monochrome raw `.tif` images with timestamped filenames using uncompressed TIFF output.
- Live preview uses auto-contrast stretching for better on-screen visibility in low-light scenes.
- Camera black level is set to `0` on connect/settings apply (using XiAPI direct method when available, otherwise via sensor feature selector/value params).
- If `ximea-python` import fails on Windows, the app now auto-checks XiAPI locations under `C:\XIMEA\API`.
- The app first tries `from ximea import xiapi`, then falls back to direct `import xiapi` from XiAPI SDK path(s) if available.
- XiAPI SDK Python bindings may live in nested folders under `C:\XIMEA\API\Python` (for example `...\Python\v3\...`); the app probes `Python\v3` and other nested subfolders that contain `ximea` or `xiapi.py`.
- `ximea-python` may not be published for Python 3.13+ / 3.14 yet. If pip reports `No matching distribution found for ximea-python`, install Python 3.10-3.12 and rerun install.
- If your SDK is installed elsewhere, set environment variable `XIAPI_DIR` to your XiAPI root before launching:
  ```bash
  set XIAPI_DIR=D:\Your\Path\To\XIMEA\API
  python ximea_gui.py
  ```
