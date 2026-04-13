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
2. Make sure XiAPI Python bindings are importable by your Python interpreter.
   - Typical SDK Python path is `C:\XIMEA\API\Python\v3`.
   - If needed, set it before launch:
     ```bash
     set PYTHONPATH=C:\XIMEA\API\Python\v3
     ```
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
- Live preview uses fixed mapping (no auto-brightness/auto-contrast): Mono12 counts are displayed from 0..4095.
- On connect, the app explicitly sets image format to `XI_MONO16` (with `XI_RAW16` fallback) and fails fast if neither is accepted.
- Applying camera settings uses direct XiAPI setters (`set_exposure`, `set_framerate`, `set_gain`) and reports errors directly if a command fails.
- Camera black level is set to `0` on connect/settings apply (using XiAPI direct method when available, otherwise via sensor feature selector/value params).
- If your SDK is installed elsewhere, set environment variable `XIAPI_DIR` to your XiAPI root before launching:
  ```bash
  set XIAPI_DIR=D:\Your\Path\To\XIMEA\API
  python ximea_gui.py
  ```
