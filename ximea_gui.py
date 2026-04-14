import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

import cv2
import numpy as np
from PIL import Image, ImageTk

try:
    from ximea import xiapi
except Exception:  # pragma: no cover
    xiapi = None


@dataclass
class CaptureConfig:
    frame_rate: float
    exposure_us: int
    gain_db: float
    interval_s: float
    duration_s: float
    output_root: Path
    folder_name: str


class XimeaApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("XIMEA Live View + Timed Capture")
        self.root.geometry("1150x760")

        self.camera = None
        self.image = None
        self.preview_running = False
        self.capture_running = False
        self.preview_thread = None
        self.capture_thread = None
        self.latest_frame = None
        self.latest_preview_rgb = None
        self._latest_lock = threading.Lock()
        self.preview_refresh_ms = 15
        self.capture_end_time = None
        self.countdown_var = tk.StringVar(value="Countdown: --")
        self.active_fps = 0.0
        self.mean_intensity = 0.0
        self.temperature_c = None
        self._last_frame_ts = None
        self._last_temp_ts = 0.0
        self.fps_var = tk.StringVar(value="FPS: --")
        self.mean_var = tk.StringVar(value="Mean DN: --")
        self.temp_var = tk.StringVar(value="Temp: --")
        self.auto_preview_brightness_var = tk.BooleanVar(value=False)
        self.preview_gain_var = tk.StringVar(value="1.0")
        self.preview_gamma_var = tk.StringVar(value="1.0")
        self.demo_capture_thumbnails = []

        self._build_ui()
        self._set_status("Disconnected")
        self.root.after(self.preview_refresh_ms, self._ui_preview_tick)
        self.root.after(200, self._countdown_tick)
        self.root.after(400, self._telemetry_tick)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        notebook_style = ttk.Style(self.root)
        try:
            notebook_style.configure("Bottom.TNotebook", tabposition="s")
        except Exception:
            notebook_style.configure("Bottom.TNotebook")
        self.main_notebook = ttk.Notebook(self.root, style="Bottom.TNotebook")
        self.main_notebook.pack(fill=tk.BOTH, expand=True)

        setup_tab = ttk.Frame(self.main_notebook)
        demo_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(setup_tab, text="Setup")
        self.main_notebook.add(demo_tab, text="Demo")

        left = ttk.Frame(setup_tab, padding=12)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right = ttk.Frame(setup_tab, padding=12)
        right.pack(side=tk.RIGHT, fill=tk.Y)

        self.preview_label = ttk.Label(left, text="No preview yet", anchor="center")
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        demo_left = ttk.Frame(demo_tab, padding=12)
        demo_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        demo_right = ttk.Frame(demo_tab, padding=12)
        demo_right.pack(side=tk.RIGHT, fill=tk.Y)

        self.demo_preview_label = ttk.Label(demo_left, text="No preview yet", anchor="center")
        self.demo_preview_label.pack(fill=tk.BOTH, expand=True)

        ttk.Button(demo_right, text="Capture Image", command=self.demo_single_capture).pack(fill=tk.X, pady=(0, 10))
        ttk.Label(demo_right, text="Captured previews").pack(anchor="w")
        self.demo_captured_container = ttk.Frame(demo_right)
        self.demo_captured_container.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        self.demo_thumb_labels = []
        for i in range(8):
            lbl = ttk.Label(self.demo_captured_container, text="No capture yet" if i == 0 else "", anchor="center")
            lbl.pack(fill=tk.X, pady=(0, 8))
            self.demo_thumb_labels.append(lbl)

        controls = ttk.LabelFrame(right, text="Camera Controls", padding=10)
        controls.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(controls, text="Frame rate (fps)").grid(row=0, column=0, sticky="w")
        self.frame_rate_var = tk.StringVar(value="30")
        ttk.Entry(controls, textvariable=self.frame_rate_var, width=18).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(controls, text="Exposure (microseconds)").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.exposure_var = tk.StringVar(value="10000")
        ttk.Entry(controls, textvariable=self.exposure_var, width=18).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Label(controls, text="Gain (dB)").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.gain_var = tk.StringVar(value="0")
        ttk.Entry(controls, textvariable=self.gain_var, width=18).grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Button(controls, text="Apply Camera Settings", command=self.apply_camera_settings).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0)
        )
        ttk.Checkbutton(
            controls,
            text="Auto brightness (preview only)",
            variable=self.auto_preview_brightness_var,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Label(controls, text="Preview gain (x)").grid(row=5, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(controls, textvariable=self.preview_gain_var, width=18).grid(
            row=5, column=1, sticky="ew", padx=(8, 0), pady=(8, 0)
        )
        ttk.Label(controls, text="Preview gamma").grid(row=6, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(controls, textvariable=self.preview_gamma_var, width=18).grid(
            row=6, column=1, sticky="ew", padx=(8, 0), pady=(8, 0)
        )

        timed = ttk.LabelFrame(right, text="Timed Capture", padding=10)
        timed.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(timed, text="Capture interval (seconds)").grid(row=0, column=0, sticky="w")
        self.interval_var = tk.StringVar(value="1")
        ttk.Entry(timed, textvariable=self.interval_var, width=18).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(timed, text="Total duration (seconds)").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.duration_var = tk.StringVar(value="60")
        ttk.Entry(timed, textvariable=self.duration_var, width=18).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Label(timed, text="Root save path").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.path_var = tk.StringVar(value=r"C:\XIMEA")
        ttk.Entry(timed, textvariable=self.path_var, width=18).grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Label(timed, text="Folder name").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.folder_var = tk.StringVar(value=datetime.now().strftime("capture_%Y%m%d_%H%M%S"))
        ttk.Entry(timed, textvariable=self.folder_var, width=18).grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Button(timed, text="Start Timed Capture", command=self.start_timed_capture).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0)
        )
        ttk.Button(timed, text="Single Capture", command=self.single_capture).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )
        ttk.Button(timed, text="Stop Timed Capture", command=self.stop_timed_capture).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )
        ttk.Label(timed, textvariable=self.countdown_var).grid(row=7, column=0, columnspan=2, sticky="w", pady=(8, 0))

        actions = ttk.LabelFrame(right, text="Connection", padding=10)
        actions.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(actions, text="Connect + Start Preview", command=self.connect_and_start).pack(fill=tk.X)
        ttk.Button(actions, text="Stop Preview", command=self.stop_preview).pack(fill=tk.X, pady=(8, 0))

        self.status_var = tk.StringVar(value="")
        ttk.Label(right, textvariable=self.status_var, wraplength=320, justify=tk.LEFT).pack(fill=tk.X)
        ttk.Separator(right, orient="horizontal").pack(fill=tk.X, pady=(8, 6))
        ttk.Label(right, textvariable=self.fps_var, justify=tk.LEFT).pack(fill=tk.X)
        ttk.Label(right, textvariable=self.mean_var, justify=tk.LEFT).pack(fill=tk.X)
        ttk.Label(right, textvariable=self.temp_var, justify=tk.LEFT).pack(fill=tk.X)

        for frame in (controls, timed):
            frame.columnconfigure(1, weight=1)

    def _set_status(self, text: str) -> None:
        self.status_var.set(f"Status: {text}")

    def _parse_config(self) -> CaptureConfig:
        frame_rate = float(self.frame_rate_var.get())
        exposure = int(float(self.exposure_var.get()))
        gain = float(self.gain_var.get())
        interval = float(self.interval_var.get())
        duration = float(self.duration_var.get())
        root_path = Path(self.path_var.get().strip())
        folder_name = self.folder_var.get().strip()
        if not folder_name:
            raise ValueError("Folder name cannot be empty.")
        if frame_rate <= 0 or exposure <= 0 or interval <= 0 or duration <= 0:
            raise ValueError("Frame rate, exposure, interval, and duration must all be > 0.")
        if gain < 0:
            raise ValueError("Gain must be >= 0.")
        return CaptureConfig(
            frame_rate=frame_rate,
            exposure_us=exposure,
            gain_db=gain,
            interval_s=interval,
            duration_s=duration,
            output_root=root_path,
            folder_name=folder_name,
        )

    def connect_and_start(self) -> None:
        if xiapi is None:
            messagebox.showerror("Missing dependency", "ximea-python was not found. Install requirements first.")
            return
        if self.preview_running:
            self._set_status("Preview already running")
            return
        try:
            self.camera = xiapi.Camera()
            self.camera.open_device()
            self.image = xiapi.Image()
            self.camera.set_imgdataformat("XI_MONO16")
            black_ok = self._set_black_level_zero()
            self.apply_camera_settings(show_message=False)
            self.camera.start_acquisition()
        except Exception as exc:
            self._set_status(f"Connection failed: {exc}")
            messagebox.showerror("Camera error", f"Could not start camera: {exc}")
            self._safe_close_camera()
            return

        self.preview_running = True
        self.preview_thread = threading.Thread(target=self._preview_loop, daemon=True)
        self.preview_thread.start()
        if black_ok:
            self._set_status("Preview running")
        else:
            self._set_status("Preview running (warning: could not set sensor black level offset to 0)")

    def _preview_loop(self) -> None:
        while self.preview_running and self.camera is not None:
            try:
                self.camera.get_image(self.image)
                frame = self._to_mono16(self.image.get_image_data_numpy())
                preview_rgb = self._mono16_to_preview_rgb(frame)
                now = time.monotonic()
                if self._last_frame_ts is not None:
                    dt = now - self._last_frame_ts
                    if dt > 0:
                        inst_fps = 1.0 / dt
                        self.active_fps = (0.85 * self.active_fps) + (0.15 * inst_fps) if self.active_fps > 0 else inst_fps
                self._last_frame_ts = now
                self.mean_intensity = float(frame.mean())
                if now - self._last_temp_ts >= 1.0:
                    self.temperature_c = self._read_camera_temperature()
                    self._last_temp_ts = now
                with self._latest_lock:
                    self.latest_frame = frame.copy()
                    self.latest_preview_rgb = preview_rgb
            except Exception as exc:
                self.root.after(0, lambda e=exc: self._set_status(f"Preview error: {e}"))
                time.sleep(0.2)

    def _to_mono16(self, frame):
        if len(frame.shape) == 3:
            frame = frame[:, :, 0]
        if frame.dtype == "uint16":
            return frame
        if frame.dtype == "uint8":
            return frame.astype("uint16") << 8
        return frame.astype("uint16")

    def _mono16_to_preview_rgb(self, frame):
        if self.auto_preview_brightness_var.get():
            sample = frame[::4, ::4]
            low = float(np.percentile(sample, 1.0))
            high = float(np.percentile(sample, 99.5))
            if high <= low:
                preview_u8 = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            else:
                clipped = np.clip(frame, low, high)
                preview_u8 = ((clipped - low) * (255.0 / (high - low))).astype("uint8")
        else:
            preview_f = (frame.astype("float32") / 65535.0) * self._get_preview_gain()
            preview_f = np.clip(preview_f, 0.0, 1.0)
            gamma = self._get_preview_gamma()
            if gamma != 1.0:
                preview_f = np.power(preview_f, gamma)
            preview_u8 = (preview_f * 255.0).astype("uint8")
        return cv2.cvtColor(preview_u8, cv2.COLOR_GRAY2RGB)

    def _get_preview_gain(self) -> float:
        try:
            gain = float(self.preview_gain_var.get())
            return min(16.0, max(0.1, gain))
        except Exception:
            return 1.0

    def _get_preview_gamma(self) -> float:
        try:
            gamma = float(self.preview_gamma_var.get())
            return min(3.0, max(0.2, gamma))
        except Exception:
            return 1.0

    def _ui_preview_tick(self) -> None:
        if self.preview_running:
            with self._latest_lock:
                rgb = None if self.latest_preview_rgb is None else self.latest_preview_rgb.copy()
            if rgb is not None:
                self._update_preview_labels(rgb)
        self.root.after(self.preview_refresh_ms, self._ui_preview_tick)

    def _fit_rgb_to_box(self, rgb, max_w: int, max_h: int):
        h, w = rgb.shape[:2]
        scale = min(max_w / w, max_h / h)
        return cv2.resize(rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    def _center_crop_demo_square(self, rgb):
        h, w = rgb.shape[:2]
        if w >= h:
            # Keep full Y and crop equally from left/right to create a square.
            crop_size = h
            x0 = max(0, (w - crop_size) // 2)
            return rgb[:, x0 : x0 + crop_size]
        # Fallback for portrait-like frames.
        crop_size = w
        y0 = max(0, (h - crop_size) // 2)
        return rgb[y0 : y0 + crop_size, :]

    def _update_preview_labels(self, rgb) -> None:
        setup_disp = self._fit_rgb_to_box(rgb, 900, 680)
        setup_img = ImageTk.PhotoImage(Image.fromarray(setup_disp))
        self.preview_label.configure(image=setup_img, text="")
        self.preview_label.image = setup_img

        demo_disp = self._center_crop_demo_square(setup_disp)
        demo_img = ImageTk.PhotoImage(Image.fromarray(demo_disp))
        self.demo_preview_label.configure(image=demo_img, text="")
        self.demo_preview_label.image = demo_img

    def _capture_frame_to_output(self, prefix: str):
        if not self.preview_running:
            messagebox.showwarning("Not connected", "Connect and start preview first.")
            return None, None
        try:
            cfg = self._parse_config()
        except Exception as exc:
            messagebox.showerror("Input error", str(exc))
            return None, None

        capture_dir = cfg.output_root / cfg.folder_name
        capture_dir.mkdir(parents=True, exist_ok=True)
        with self._latest_lock:
            frame = None if self.latest_frame is None else self.latest_frame.copy()
        if frame is None:
            self._set_status("No frame available yet for capture")
            return None, None

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        file_path = capture_dir / f"{prefix}_{stamp}.tif"
        self._save_uncompressed_tif(file_path, frame)
        return file_path, frame

    def _push_demo_capture_preview(self, frame, file_name: str) -> None:
        rgb = self._mono16_to_preview_rgb(frame)
        thumb_rgb = self._fit_rgb_to_box(rgb, 260, 180)
        thumb_img = ImageTk.PhotoImage(Image.fromarray(thumb_rgb))
        self.demo_capture_thumbnails.insert(0, (thumb_img, file_name))
        self.demo_capture_thumbnails = self.demo_capture_thumbnails[: len(self.demo_thumb_labels)]
        for idx, lbl in enumerate(self.demo_thumb_labels):
            if idx < len(self.demo_capture_thumbnails):
                img, name = self.demo_capture_thumbnails[idx]
                lbl.configure(image=img, text=name, compound="top")
                lbl.image = img
            else:
                lbl.configure(image="", text="No capture yet" if idx == 0 else "")
                lbl.image = None

    def _set_black_level_zero(self) -> bool:
        if self.camera is None:
            return False

        restarted = False
        if self.preview_running:
            try:
                self.camera.stop_acquisition()
                restarted = True
            except Exception:
                restarted = False

        success = False
        try:
            if hasattr(self.camera, "set_black_level"):
                self.camera.set_black_level(0)
                success = True
            else:
                selector_names = ["sensor_feature_selector", "XI_PRM_SENSOR_FEATURE_SELECTOR"]
                value_names = ["sensor_feature_value", "XI_PRM_SENSOR_FEATURE_VALUE"]
                for selector_name in selector_names:
                    for value_name in value_names:
                        try:
                            self.camera.set_param(selector_name, "XI_SENSOR_FEATURE_ACQUISITION_RUNNING_STATUS")
                            self.camera.set_param(value_name, 0)
                            self.camera.set_param(selector_name, "XI_SENSOR_FEATURE_BLACK_LEVEL_OFFSET_RAW")
                            self.camera.set_param(value_name, 0)
                            success = True
                            break
                        except Exception:
                            continue
                    if success:
                        break
        finally:
            if restarted:
                try:
                    self.camera.start_acquisition()
                except Exception:
                    pass
        return success

    def apply_camera_settings(self, show_message: bool = True) -> None:
        if self.camera is None:
            if show_message:
                self._set_status("Connect to camera first")
            return
        try:
            cfg = self._parse_config()
            self.camera.set_framerate(cfg.frame_rate)
            self.camera.set_exposure(cfg.exposure_us)
            self.camera.set_gain(cfg.gain_db)
            black_ok = self._set_black_level_zero()
            self._set_status(
                f"Applied frame rate={cfg.frame_rate} fps, exposure={cfg.exposure_us} us, gain={cfg.gain_db} dB"
                + (", black level=0" if black_ok else ", black level=0 not supported by current XiAPI binding")
            )
        except Exception as exc:
            messagebox.showerror("Settings error", str(exc))
            self._set_status(f"Failed to apply settings: {exc}")

    def start_timed_capture(self) -> None:
        if not self.preview_running:
            messagebox.showwarning("Not connected", "Connect and start preview first.")
            return
        if self.capture_running:
            self._set_status("Timed capture already running")
            return
        try:
            cfg = self._parse_config()
        except Exception as exc:
            messagebox.showerror("Input error", str(exc))
            return

        capture_dir = cfg.output_root / cfg.folder_name
        capture_dir.mkdir(parents=True, exist_ok=True)

        self.capture_running = True
        self.capture_end_time = time.monotonic() + cfg.duration_s
        self.capture_thread = threading.Thread(target=self._timed_capture_loop, args=(cfg, capture_dir), daemon=True)
        self.capture_thread.start()
        self._set_status(f"Timed capture running -> {capture_dir} (Mono12 in 16-bit TIFF)")

    def _timed_capture_loop(self, cfg: CaptureConfig, capture_dir: Path) -> None:
        start = time.monotonic()
        next_shot = start
        count = 0

        while self.capture_running and (time.monotonic() - start) <= cfg.duration_s:
            now = time.monotonic()
            if now >= next_shot:
                with self._latest_lock:
                    frame = None if self.latest_frame is None else self.latest_frame.copy()
                if frame is not None:
                    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    file_path = capture_dir / f"frame_{count:06d}_{stamp}.tif"
                    self._save_uncompressed_tif(file_path, frame)
                    count += 1
                    self.root.after(0, lambda c=count, p=file_path: self._set_status(f"Saved {c} frames. Latest: {p.name}"))
                next_shot += cfg.interval_s
            else:
                time.sleep(0.01)

        self.capture_running = False
        self.capture_end_time = None
        self.root.after(0, lambda: self.countdown_var.set("Countdown: --"))
        self.root.after(0, lambda: self._set_status(f"Timed capture completed. Total saved: {count}"))

    def stop_timed_capture(self) -> None:
        if not self.capture_running:
            self._set_status("Timed capture is not running")
            return
        self.capture_running = False
        self.capture_end_time = None
        self.countdown_var.set("Countdown: --")
        self._set_status("Stopping timed capture...")

    def single_capture(self) -> None:
        file_path, _ = self._capture_frame_to_output("single")
        if file_path is not None:
            self._set_status(f"Single capture saved: {file_path.name}")

    def demo_single_capture(self) -> None:
        file_path, frame = self._capture_frame_to_output("demo")
        if file_path is None or frame is None:
            return
        self._push_demo_capture_preview(frame, file_path.name)
        self._set_status(f"Demo capture saved: {file_path.name}")

    def _countdown_tick(self) -> None:
        if self.capture_running and self.capture_end_time is not None:
            remaining = max(0.0, self.capture_end_time - time.monotonic())
            self.countdown_var.set(f"Countdown: {remaining:0.1f}s")
        else:
            self.countdown_var.set("Countdown: --")
        self.root.after(200, self._countdown_tick)

    def _save_uncompressed_tif(self, file_path: Path, frame) -> bool:
        return bool(cv2.imwrite(str(file_path), frame, [cv2.IMWRITE_TIFF_COMPRESSION, 1]))

    def _read_camera_temperature(self):
        if self.camera is None:
            return None
        getter_names = ["get_temp", "get_sensor_board_temp", "get_device_temperature"]
        for getter_name in getter_names:
            if hasattr(self.camera, getter_name):
                try:
                    return float(getattr(self.camera, getter_name)())
                except Exception:
                    continue
        param_names = [
            "device_temperature",
            "sensor_board_temp",
            "XI_PRM_DEVICE_TEMPERATURE",
            "XI_PRM_SENSOR_BOARD_TEMP",
        ]
        for param_name in param_names:
            try:
                return float(self.camera.get_param(param_name))
            except Exception:
                continue
        return None

    def _telemetry_tick(self) -> None:
        if self.preview_running:
            self.fps_var.set(f"FPS: {self.active_fps:0.2f}")
            self.mean_var.set(f"Mean DN: {self.mean_intensity:0.1f}")
            if self.temperature_c is None:
                self.temp_var.set("Temp: N/A")
            else:
                self.temp_var.set(f"Temp: {self.temperature_c:0.1f} °C")
        else:
            self.fps_var.set("FPS: --")
            self.mean_var.set("Mean DN: --")
            self.temp_var.set("Temp: --")
        self.root.after(400, self._telemetry_tick)

    def stop_preview(self) -> None:
        self.capture_running = False
        self.capture_end_time = None
        self.countdown_var.set("Countdown: --")
        self.preview_running = False
        self.active_fps = 0.0
        self.mean_intensity = 0.0
        self.temperature_c = None
        self._last_frame_ts = None
        with self._latest_lock:
            self.latest_frame = None
            self.latest_preview_rgb = None
        self._safe_close_camera()
        self._set_status("Preview stopped")

    def _safe_close_camera(self) -> None:
        if self.camera is None:
            return
        try:
            self.camera.stop_acquisition()
        except Exception:
            pass
        try:
            self.camera.close_device()
        except Exception:
            pass
        self.camera = None
        self.image = None

    def on_close(self) -> None:
        self.stop_preview()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    app = XimeaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
