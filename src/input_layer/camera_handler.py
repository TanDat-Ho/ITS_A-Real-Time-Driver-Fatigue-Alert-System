"""
src/input_layer/camera_handler.py

Threaded camera handler for ITS_A project.

Responsibilities:
- Open video source (camera index or file path).
- Continuously read frames in a separate thread.
- Resize / color-convert / normalize frames as configured.
- Provide thread-safe queue for downstream processing_layer.
- Expose simple API: start(), stop(), get_frame(), snapshot()
"""

import cv2
import time
import threading
import queue
import logging
from typing import Optional, Tuple, Dict, Union

# Nếu bạn có app.config, import các tham số mặc định từ đó.
# from ..app.config import CAMERA_SRC, FRAME_WIDTH, FRAME_HEIGHT, MAX_QUEUE_SIZE, COLOR_FORMAT

logger = logging.getLogger("camera_handler")
logger.setLevel(logging.INFO)
# Simple handler if logging not configured elsewhere
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(ch)


class CameraHandler(threading.Thread):
    """
    Threaded camera grabber.

    Params:
      src: int (camera index) or str (video file) or None
      queue_size: max frames to buffer for consumer
      target_size: (w,h) to which frames are resized. If None, keep original
      color: "bgr" or "rgb" - color format returned to consumer
      normalize: if True, returns float32 frame in [0,1], else uint8 [0,255]
      fps_limit: max read FPS (None -> no limit)
      auto_reconnect: if True, try to reopen camera on failure
    """

    def __init__(self,
                 src: Optional[Union[int, str]] = 0,
                 queue_size: int = 8,
                 target_size: Optional[Tuple[int, int]] = (640, 360),
                 color: str = "rgb",
                 normalize: bool = False,
                 fps_limit: Optional[float] = None,
                 auto_reconnect: bool = True):
        super().__init__(daemon=True)
        self.src = src
        self.queue = queue.Queue(maxsize=queue_size)
        self.target_size = target_size
        self.color = color.lower()
        assert self.color in ("rgb", "bgr")
        self.normalize = normalize
        self.fps_limit = fps_limit
        self._frame_interval = (1.0 / fps_limit) if fps_limit and fps_limit > 0 else None
        self.auto_reconnect = auto_reconnect

        self._cap: Optional[cv2.VideoCapture] = None
        self._stop_event = threading.Event()
        self._is_running = False
        self.stats = {
            "frames_read": 0,
            "frames_dropped_queue_full": 0,
            "last_open_failed": False,
            "open_attempts": 0
        }

    def _open_capture(self):
        """Open video capture. Return True if success."""
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

        self.stats["open_attempts"] += 1
        try:
            cap = cv2.VideoCapture(self.src, cv2.CAP_ANY)
            # Optional: set resolution hints (may be ignored by some cameras)
            if self.target_size:
                w, h = self.target_size
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(w))
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(h))
            if not cap.isOpened():
                logger.warning(f"CameraHandler: cannot open source {self.src}")
                self.stats["last_open_failed"] = True
                return False
            self._cap = cap
            self.stats["last_open_failed"] = False
            logger.info(f"CameraHandler: opened source {self.src}")
            return True
        except Exception as e:
            logger.exception("CameraHandler: exception opening capture")
            self.stats["last_open_failed"] = True
            return False

    def run(self):
        """Main thread loop: read frames and push to queue."""
        self._is_running = True
        # Try open first
        opened = self._open_capture()
        if not opened and not self.auto_reconnect:
            logger.error("CameraHandler: failed to open capture and auto_reconnect disabled. Exiting thread.")
            self._is_running = False
            return

        last_ts = 0.0
        while not self._stop_event.is_set():
            if self._cap is None:
                # try reopen
                if self.auto_reconnect:
                    time.sleep(0.5)
                    if not self._open_capture():
                        time.sleep(1.0)
                        continue
                else:
                    break
            ret, frame = self._cap.read()
            if not ret:
                logger.warning("CameraHandler: read failed (no frame). Will retry.")
                # release and set None to trigger reconnect
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
                time.sleep(0.2)
                continue

            now = time.time()
            # FPS limiter (if set)
            if self._frame_interval is not None:
                elapsed = now - last_ts
                if elapsed < self._frame_interval:
                    time.sleep(self._frame_interval - elapsed)
                last_ts = time.time()

            # Preprocess: resize if needed
            if self.target_size is not None:
                # keep aspect by interpolation? We just resize to target to reduce workload.
                frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_LINEAR)

            # Color conversion
            if self.color == "rgb":
                frame_out = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                frame_out = frame  # BGR

            # Normalize if required
            if self.normalize:
                frame_proc = (frame_out.astype("float32") / 255.0)
            else:
                frame_proc = frame_out

            # Put frame into queue (non-blocking with drop policy)
            try:
                self.queue.put_nowait({
                    "ts": now,
                    "frame": frame_proc,
                    "meta": {
                        "orig_size": (int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                      int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))),
                        "target_size": self.target_size,
                        "src": self.src
                    }
                })
                self.stats["frames_read"] += 1
            except queue.Full:
                # Drop oldest or drop this frame? Here we drop newest and count
                self.stats["frames_dropped_queue_full"] += 1
                # Option: drop one oldest to make room: self.queue.get_nowait(); self.queue.put_nowait(...)
                # For deterministic latency, dropping new frames is ok.
                logger.debug("CameraHandler: queue full, dropping frame")

        # cleanup
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
        self._is_running = False
        logger.info("CameraHandler: thread exiting")

    def start(self):
        """Start thread (override to ensure thread begins)."""
        self._stop_event.clear()
        if not self.is_alive():
            super().start()
        logger.info("CameraHandler: started")

    def stop(self):
        """Signal thread to stop and wait briefly."""
        self._stop_event.set()
        # Give a moment to stop
        timeout = 1.0
        t0 = time.time()
        while self._is_running and (time.time() - t0) < timeout:
            time.sleep(0.01)
        logger.info("CameraHandler: stopped")

    def get_frame(self, block: bool = False, timeout: float = 0.01) -> Optional[Dict]:
        """
        Consumer calls this to get newest frame.

        Returns dict: {"ts": float, "frame": np.ndarray, "meta": {...}} or None
        by default a non-blocking quick poll is used.
        """
        try:
            return self.queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def snapshot(self, path: str) -> bool:
        """Save latest frame (non-blocking). Return True if saved."""
        item = None
        # We try to get the most recent frame
        try:
            while True:
                item = self.queue.get_nowait()
        except queue.Empty:
            pass

        if item is None:
            logger.warning("CameraHandler.snapshot: no frame available to save")
            return False

        frame = item["frame"]
        if self.normalize:
            save_frame = (frame * 255.0).astype("uint8")
        else:
            save_frame = frame

        # If in RGB, convert to BGR for imwrite
        if self.color == "rgb":
            save_frame = cv2.cvtColor(save_frame, cv2.COLOR_RGB2BGR)

        cv2.imwrite(path, save_frame)
        logger.info(f"CameraHandler.snapshot: saved to {path}")
        return True

    def read_frame(self):
        """
        Simple blocking interface for getting latest frame.
        Compatibility method for non-threaded usage.
        Auto-starts thread if not running.
        """
        if not self._is_running and not self.is_alive():
            self.start()
            # Give thread a moment to initialize
            time.sleep(0.1)
        
        # Get latest frame, dropping old ones
        frame_data = None
        try:
            # Drain queue to get most recent frame
            while True:
                frame_data = self.queue.get_nowait()
        except queue.Empty:
            pass
        
        if frame_data is None:
            # Try once more with blocking
            frame_data = self.get_frame(block=True, timeout=1.0)
        
        return frame_data["frame"] if frame_data else None

    def release(self):
        """Release camera and cleanup resources."""
        self.stop()
        if hasattr(self, 'join'):
            try:
                self.join(timeout=2.0)
            except Exception:
                pass

    def health(self) -> Dict:
        """Return simple health metrics for monitoring."""
        return {
            "queue_size": self.queue.qsize(),
            **self.stats
        }
