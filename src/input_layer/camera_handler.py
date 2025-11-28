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
import numpy as np
from typing import Optional, Tuple, Dict, Union

# Nếu bạn có app.config, import các tham số mặc định từ đó.
# from ..app.config import CAMERA_SRC, FRAME_WIDTH, FRAME_HEIGHT, MAX_QUEUE_SIZE, COLOR_FORMAT

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
                 queue_size: int = CameraConstants.DEFAULT_MAX_QUEUE_SIZE,
                 target_size: Optional[Tuple[int, int]] = (CameraConstants.DEFAULT_FRAME_WIDTH, CameraConstants.DEFAULT_FRAME_HEIGHT),
                 color: str = "rgb",
                 normalize: bool = False,
                 fps_limit: Optional[float] = CameraConstants.DEFAULT_FPS_LIMIT,
                 auto_reconnect: bool = True,
                 # Enhanced parameters for face detection optimization
                 exposure: Optional[int] = None,
                 brightness: Optional[int] = None,
                 contrast: Optional[int] = None,
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
        
        # Camera properties for optimization
        self.camera_properties = {
            'exposure': exposure,
            'brightness': brightness,
            'contrast': contrast
        }
        
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
                
            # Optional: set resolution hints (may be ignored by some cameras)
            if self.target_size:
                w, h = self.target_size
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(w))
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(h))
                
            # Set some common properties for better performance
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to get latest frame
            cap.set(cv2.CAP_PROP_FPS, 30)  # Set desired FPS
            
            self._cap = cap
            # Configure additional camera properties
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
            if not ret or frame is None:
                logger.warning("CameraHandler: read failed (no frame). Will retry.")
                # release and set None to trigger reconnect
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
                time.sleep(0.5)  # Wait a bit longer before retry
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

            # Validate frame quality if enabled
            if self.validate_quality and not self._validate_frame_quality(frame_proc):
                self.stats["frames_poor_quality"] += 1
                # Add counter for debugging
                if not hasattr(self, '_dropped_frame_count'):
                    self._dropped_frame_count = 0
                self._dropped_frame_count += 1
                
                # Log every 10 dropped frames to understand the issue
                if self._dropped_frame_count % 10 == 1:
                    logger.warning(f"Dropping frame #{self._dropped_frame_count} due to quality validation")
                continue
            
            # Add success counter for debugging
            if not hasattr(self, '_successful_frame_count'):
                self._successful_frame_count = 0
            self._successful_frame_count += 1
            
            # Log successful frame processing occasionally
            if self._successful_frame_count % 100 == 1:
                logger.info(f"Successfully processed {self._successful_frame_count} frames")
            
            # Put frame into queue (non-blocking with drop policy)
            try:
                frame_data = {
                    "ts": now,
                    "frame": frame_proc,
                    "meta": {
                        "orig_size": (int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                      int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))),
                        "target_size": self.target_size,
                        "src": self.src,
                        "validated": self.validate_quality,
                        "brightness": self.stats.get("avg_brightness", 0),
                        "contrast": self.stats.get("avg_contrast", 0)
                    }
                }
                
                self.queue.put_nowait(frame_data)
                self.stats["frames_read"] += 1
                
                # Log first few successful frame puts
                if self.stats["frames_read"] <= 3:
                    logger.info(f"Successfully queued frame #{self.stats['frames_read']} - brightness: {self.stats.get('avg_brightness', 0):.1f}")
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
    
    def _configure_camera_properties(self):
        """Configure camera properties for optimal landmark detection"""
        if self._cap is None:
            return False
            
        try:
            # Set properties for better face detection
            if self.camera_properties['exposure'] is not None:
                self._cap.set(cv2.CAP_PROP_EXPOSURE, self.camera_properties['exposure'])
            
            if self.camera_properties['brightness'] is not None:
                self._cap.set(cv2.CAP_PROP_BRIGHTNESS, self.camera_properties['brightness'])
                
            if self.camera_properties['contrast'] is not None:
                self._cap.set(cv2.CAP_PROP_CONTRAST, self.camera_properties['contrast'])
            
            # Auto focus for better face clarity if available
            try:
                self._cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            except Exception:
                pass  # Not all cameras support this
            
            logger.debug("Camera properties configured for landmark detection")
            return True
            
        except Exception as e:
            logger.warning(f"Could not set camera properties: {e}")
            return False
    
    def _validate_frame_quality(self, frame: np.ndarray) -> bool:
        """Validate frame quality for landmark detection"""
        if frame is None or frame.size == 0:
            return False
            
        # Convert to grayscale for analysis
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
            
        # Check brightness (warn but don't reject bright frames)
        brightness = np.mean(gray)
        self.stats["avg_brightness"] = float(brightness)
        
        # Only reject extremely dark frames
        if brightness < 30:
            logger.warning(f"Frame too dark (brightness: {brightness:.1f})")
            return False
        
        # For bright frames, just warn but allow processing
        if brightness > 250:
            # Only log once every 50 frames to reduce spam
            if not hasattr(self, '_bright_frame_counter'):
                self._bright_frame_counter = 0
            self._bright_frame_counter += 1
            if self._bright_frame_counter % 50 == 1:
                logger.info(f"Bright lighting detected (brightness: {brightness:.1f}) - continuing processing")
        elif brightness > 220:
            # Occasional warning for moderately bright frames
            if not hasattr(self, '_moderate_bright_warned'):
                logger.info(f"Moderately bright frame (brightness: {brightness:.1f}) - acceptable for processing")
                self._moderate_bright_warned = True
            
        # Check contrast (more lenient)
        contrast = np.std(gray)
        self.stats["avg_contrast"] = float(contrast)
        
        # Only reject if contrast is extremely low
        if contrast < 10:
            logger.warning(f"Very low contrast detected (contrast: {contrast:.1f})")
            return False
        elif contrast < 20:
            # Just warn, don't reject
            if not hasattr(self, '_low_contrast_warned'):
                logger.info(f"Low contrast detected (contrast: {contrast:.1f}) - continuing processing")
                self._low_contrast_warned = True
            
        return True

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
    
    def get_frame_with_metadata(self, block: bool = False, timeout: float = 0.01) -> Optional[Dict]:
        """Enhanced frame retrieval with quality metadata"""
        frame_data = self.get_frame(block, timeout)
        if frame_data is None:
            return None
            
        frame = frame_data["frame"]
        
        # Add quality metrics if validation is enabled
        if self.validate_quality:
            quality_metrics = self._calculate_frame_quality(frame)
            frame_data["quality"] = quality_metrics
        
        return frame_data
    
    def _calculate_frame_quality(self, frame: np.ndarray) -> Dict:
        """Calculate frame quality metrics for processing layer"""
        if frame is None or frame.size == 0:
            return {"valid": False}
            
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
