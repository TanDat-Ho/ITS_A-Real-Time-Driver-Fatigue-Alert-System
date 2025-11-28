"""
src/input_layer/camera_handler.py

Cleaned and optimized threaded camera handler for ITS_A project.

Responsibilities:
- Open video source (camera index or file path)
- Continuously read frames in a separate thread
- Resize / color-convert / normalize frames as configured
- Provide thread-safe queue for downstream processing_layer
- Expose simple API: start(), stop(), get_frame(), snapshot()
"""

import cv2
import threading
import queue
import time
import numpy as np
import logging
from typing import Optional, Tuple, Dict, Union

# Setup centralized logging
logger = logging.getLogger(__name__)

def _setup_module_logger():
    """Setup module-specific logging if not already configured"""
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)

_setup_module_logger()

# Constants
class CameraConstants:
    """Constants for camera handling"""
    DEFAULT_FRAME_WIDTH = 640
    DEFAULT_FRAME_HEIGHT = 480
    DEFAULT_MAX_QUEUE_SIZE = 10
    DEFAULT_FPS_LIMIT = 30.0
    
    # Backend priorities (Windows optimized)
    BACKEND_PRIORITY = [cv2.CAP_DSHOW, cv2.CAP_ANY, cv2.CAP_MSMF]
    BACKEND_NAMES = ["DSHOW", "ANY", "MSMF"]
    
    # Color format mappings
    COLOR_FORMATS = {
        'RGB': cv2.COLOR_BGR2RGB,
        'BGR': None,  # No conversion needed
        'GRAY': cv2.COLOR_BGR2GRAY
    }


class CameraHandler(threading.Thread):
    """
    Cleaned and optimized threaded camera grabber.
    """

    def __init__(self,
                 src: Optional[Union[int, str]] = 0,
                 queue_size: int = CameraConstants.DEFAULT_MAX_QUEUE_SIZE,
                 target_size: Optional[Tuple[int, int]] = (CameraConstants.DEFAULT_FRAME_WIDTH, CameraConstants.DEFAULT_FRAME_HEIGHT),
                 color: str = "rgb",
                 normalize: bool = False,
                 fps_limit: Optional[float] = CameraConstants.DEFAULT_FPS_LIMIT,
                 auto_reconnect: bool = True,
                 validate_quality: bool = True):
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
        self.validate_quality = validate_quality
        
        # Validation for target_size
        if target_size:
            w, h = target_size
            if w < 320 or h < 240:
                logger.warning(f"Target size {target_size} may be too small for accurate landmark detection")
            if w > 1920 or h > 1080:
                logger.warning(f"Target size {target_size} may impact performance")

        self._cap: Optional[cv2.VideoCapture] = None
        self._stop_event = threading.Event()
        self._is_running = False
        self.stats = {
            "frames_read": 0,
            "frames_dropped_queue_full": 0,
            "frames_poor_quality": 0,
            "last_open_failed": False,
            "open_attempts": 0,
            "avg_brightness": 0.0,
            "avg_contrast": 0.0
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
            # Try different backends for better Windows compatibility
            backends_to_try = CameraConstants.BACKEND_PRIORITY
            backend_names = CameraConstants.BACKEND_NAMES
            cap = None
            
            for i, backend in enumerate(backends_to_try):
                try:
                    logger.debug(f"CameraHandler: Trying {backend_names[i]} backend...")
                    cap = cv2.VideoCapture(self.src, backend)
                    if cap.isOpened():
                        # Test if we can actually read a frame
                        ret, test_frame = cap.read()
                        if ret and test_frame is not None:
                            logger.debug(f"CameraHandler: ✅ Successfully opened source {self.src} with {backend_names[i]} backend")
                            break
                        else:
                            logger.warning(f"CameraHandler: ❌ {backend_names[i]} backend opened but can't read frames")
                            cap.release()
                            cap = None
                    else:
                        logger.warning(f"CameraHandler: ❌ {backend_names[i]} backend failed to open")
                        cap.release()
                        cap = None
                except Exception as e:
                    logger.warning(f"CameraHandler: ❌ {backend_names[i]} backend failed: {e}")
                    if cap:
                        cap.release()
                        cap = None
                    continue
            
            if cap is None or not cap.isOpened():
                logger.warning(f"CameraHandler: cannot open source {self.src} with any backend")
                self.stats["last_open_failed"] = True
                return False
                
            # Set resolution hints (may be ignored by some cameras)
            if self.target_size:
                w, h = self.target_size
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(w))
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(h))
                
            # Set common properties for better performance
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to get latest frame
            cap.set(cv2.CAP_PROP_FPS, 30)  # Set desired FPS
            
            self._cap = cap
            self._configure_camera_properties()
            
            # Verify frame quality
            if self.validate_quality:
                ret, test_frame = self._cap.read()
                if ret and test_frame is not None:
                    quality_ok = self._validate_frame_quality(test_frame)
                    if quality_ok:
                        logger.info("Camera opened with good frame quality")
                    else:
                        logger.warning("Camera frame quality may affect detection accuracy")
            
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
            logger.error("CameraHandler: Could not open source and auto_reconnect=False")
            self._is_running = False
            return

        last_ts = 0.0
        frame_count = 0
        
        while not self._stop_event.is_set():
            if not self._cap or not self._cap.isOpened():
                if self.auto_reconnect:
                    logger.warning("CameraHandler: attempting reconnect...")
                    time.sleep(1.0)
                    opened = self._open_capture()
                    if not opened:
                        continue
                else:
                    logger.error("CameraHandler: no active capture and auto_reconnect=False")
                    break

            # Respect fps_limit
            now = time.time()
            if self._frame_interval and (now - last_ts) < self._frame_interval:
                time.sleep(0.001)  # Small sleep to avoid busy loop
                continue

            try:
                ret, raw_frame = self._cap.read()
                if not ret or raw_frame is None:
                    logger.warning("CameraHandler: failed to read frame")
                    if self.auto_reconnect:
                        time.sleep(0.1)
                        continue
                    else:
                        break

                # Validate frame quality
                if self.validate_quality and not self._validate_frame_quality(raw_frame):
                    self.stats["frames_poor_quality"] += 1
                    continue

                # Process frame
                processed_frame = self._process_frame(raw_frame)
                frame_count += 1
                self.stats["frames_read"] = frame_count

                # Create frame data
                frame_data = {
                    "ts": now,
                    "frame": processed_frame,
                    "meta": {
                        "frame_id": frame_count,
                        "raw_shape": raw_frame.shape,
                        "processed_shape": processed_frame.shape,
                        "color_format": self.color,
                        "normalized": self.normalize
                    }
                }

                # Put to queue (non-blocking)
                try:
                    self.queue.put_nowait(frame_data)
                    last_ts = now
                except queue.Full:
                    # Drop oldest frame and try again
                    try:
                        self.queue.get_nowait()  # Remove oldest
                        self.queue.put_nowait(frame_data)  # Add new
                        self.stats["frames_dropped_queue_full"] += 1
                    except queue.Empty:
                        pass  # Queue became empty somehow

            except Exception as e:
                logger.exception(f"CameraHandler: exception in main loop: {e}")
                if not self.auto_reconnect:
                    break
                time.sleep(0.1)

        # Cleanup
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
        self._is_running = False
        logger.info("CameraHandler: thread exiting")
    
    def _configure_camera_properties(self):
        """Configure camera properties for optimal landmark detection"""
        if self._cap is None:
            return
            
        try:
            # Set auto exposure and focus if possible
            self._cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Auto exposure on
            
            # Set brightness, contrast if supported
            current_brightness = self._cap.get(cv2.CAP_PROP_BRIGHTNESS)
            current_contrast = self._cap.get(cv2.CAP_PROP_CONTRAST)
            
            if current_brightness != -1:  # Property supported
                self._cap.set(cv2.CAP_PROP_BRIGHTNESS, 128)  # Mid-range
            if current_contrast != -1:  # Property supported
                self._cap.set(cv2.CAP_PROP_CONTRAST, 64)   # Mid-range
                
            logger.debug("Camera properties configured")
            
        except Exception as e:
            logger.debug(f"Could not configure camera properties: {e}")
    
    def _validate_frame_quality(self, frame: np.ndarray) -> bool:
        """Validate frame quality for landmark detection"""
        if frame is None or frame.size == 0:
            return False
            
        # Convert to grayscale for analysis
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
            
        # Check brightness
        brightness = np.mean(gray)
        self.stats["avg_brightness"] = float(brightness)
        
        # Only reject extremely dark frames
        if brightness < 30:
            logger.warning(f"Frame too dark (brightness: {brightness:.1f})")
            return False
        
        # Check for extremely bright frames
        if brightness > 220:
            logger.warning(f"Frame too bright (brightness: {brightness:.1f})")
            
        # Check contrast
        contrast = np.std(gray)
        self.stats["avg_contrast"] = float(contrast)
        
        # Only reject if contrast is extremely low
        if contrast < 10:
            logger.warning(f"Frame too low contrast (contrast: {contrast:.1f})")
            return False
            
        return True

    def _process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Process raw frame according to configuration"""
        processed = frame
        
        # Resize if needed
        if self.target_size and frame.shape[:2][::-1] != self.target_size:
            processed = cv2.resize(processed, self.target_size)
        
        # Color conversion
        if self.color == "rgb" and len(processed.shape) == 3:
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
        
        # Normalization
        if self.normalize:
            processed = processed.astype(np.float32) / 255.0
            
        return processed

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
        """
        try:
            return self.queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None
    
    def get_frame_with_metadata(self, block: bool = False, timeout: float = 0.01) -> Optional[Dict]:
        """Enhanced frame retrieval with quality metadata"""
        frame_data = self.get_frame(block, timeout)
        if frame_data is None:
            return None
            
        # Add quality metrics if validation is enabled
        if self.validate_quality:
            frame_data["quality"] = self._calculate_frame_quality(frame_data["frame"])
        
        return frame_data
    
    def _calculate_frame_quality(self, frame: np.ndarray) -> Dict:
        """Calculate frame quality metrics for processing layer"""
        if frame is None or frame.size == 0:
            return {"valid": False, "reason": "empty_frame"}
            
        # Convert to grayscale for analysis
        if len(frame.shape) == 3:
            if self.color == "rgb":
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            else:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
            
        # Calculate quality metrics
        brightness = float(np.mean(gray))
        contrast = float(np.std(gray))
        
        # Blur detection using Laplacian variance
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        
        is_acceptable = (
            40 <= brightness <= 210 and 
            contrast >= 20 and 
            blur_score >= 80
        )
        
        return {
            "valid": True,
            "brightness": brightness,
            "contrast": contrast,
            "blur_score": blur_score,
            "is_acceptable": is_acceptable
        }

    def snapshot(self, path: str) -> bool:
        """Save latest frame (non-blocking). Return True if saved."""
        try:
            # Try to get the most recent frame
            frame_data = self.queue.get_nowait()
        except queue.Empty:
            logger.warning("CameraHandler.snapshot: no frame available")
            return False

        if frame_data is None:
            logger.warning("CameraHandler.snapshot: frame_data is None")
            return False

        frame = frame_data["frame"]
        
        # Prepare frame for saving
        if self.normalize:
            save_frame = (frame * 255).astype(np.uint8)
        else:
            save_frame = frame

        # Convert RGB to BGR for OpenCV imwrite
        if self.color == "rgb" and len(save_frame.shape) == 3:
            save_frame = cv2.cvtColor(save_frame, cv2.COLOR_RGB2BGR)

        success = cv2.imwrite(path, save_frame)
        if success:
            logger.info(f"CameraHandler.snapshot: saved to {path}")
        else:
            logger.error(f"CameraHandler.snapshot: failed to save to {path}")
            
        return success

    def read_frame(self):
        """
        Simple blocking interface for getting latest frame.
        Auto-starts thread if not running.
        """
        if not self._is_running and not self.is_alive():
            logger.info("CameraHandler: auto-starting for read_frame()")
            self.start()
            time.sleep(0.1)  # Give thread time to start
        
        # Get latest frame, dropping old ones
        frame_data = None
        try:
            # Clear queue to get latest
            while not self.queue.empty():
                frame_data = self.queue.get_nowait()
        except queue.Empty:
            logger.warning("CameraHandler.read_frame: no frame available")
        
        return frame_data["frame"] if frame_data else None

    def release(self):
        """Release camera and cleanup resources."""
        self.stop()
        if hasattr(self, 'join') and self.is_alive():
            self.join(timeout=2.0)

    def health(self) -> Dict:
        """Return health metrics for monitoring."""
        return {
            "queue_size": self.queue.qsize(),
            "is_running": self._is_running,
            "thread_alive": self.is_alive(),
            **self.stats
        }