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

## Prerequisites (Windows)
1. Install **XIMEA camera drivers + XiAPI SDK** from XIMEA.
2. Install Python 3.10+.
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Run
```bash
python ximea_gui.py
```

## Share as a standalone Windows app (no Python required on target PC)
You can build an `.exe` for teammates who do not have Python installed.

1. On your build machine (with Python), install runtime deps:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the PowerShell build script:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_exe.ps1
   ```
3. Share the generated artifact:
   - One-file mode (default): `dist\XimeaCameraGUI.exe`
   - One-dir mode: run script with `-OneFile:$false` and share `dist\XimeaCameraGUI\`

### Important
- Target PCs still must install **XIMEA drivers + XiAPI SDK** before launching the app.
- If the camera is not detected, verify XiAPI installation and USB/camera permissions.

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
- If `ximea-python` import fails, ensure the XiAPI SDK/drivers are installed and visible to Python.
