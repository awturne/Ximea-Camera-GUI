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
- Timed frame capture that saves PNG images to:
  - `C:\XIMEA\<your_folder_name>` (by default)

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
6. Click **Stop Timed Capture** to end early, if needed.

## Notes
- The app saves images as PNG with timestamped filenames.
- If `ximea-python` import fails, ensure the XiAPI SDK/drivers are installed and visible to Python.
