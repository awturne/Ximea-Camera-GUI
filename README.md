# Ximea-Camera-GUI

Desktop GUI (Tkinter) for XIMEA camera live preview and interval-based frame capture.

## Features
- Live video preview from XIMEA camera (`MC023MG-SY-UB` supported via XIMEA SDK).
- User controls for:
  - Frame rate (fps)
  - Exposure time (microseconds)
  - Capture interval (seconds)
  - Capture duration (seconds)
  - Save root path (defaults to `C:\XIMEA`)
  - Output folder name
- Timed frame capture that saves 16-bit TIFF images (Mono12 data in 16-bit container) to:
  - `C:\XIMEA\<your_folder_name>` (by default)
- A single-capture button for one-shot image save.
- Countdown display for remaining timed-capture duration.

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

## Typical workflow
1. Click **Connect + Start Preview**.
2. Set frame rate and exposure, then click **Apply Camera Settings**.
3. Set capture interval and total duration.
4. Set save path (`C:\XIMEA`) and folder name.
5. Click **Start Timed Capture**.
6. Watch countdown while the timed capture is running.
7. Click **Single Capture** for one image, or **Stop Timed Capture** to end early.

## Notes
- The app saves monochrome TIFF images with timestamped filenames.
- Live preview uses auto-contrast stretching for better on-screen visibility in low-light scenes.
- If `ximea-python` import fails, ensure the XiAPI SDK/drivers are installed and visible to Python.
