"""
roi_detector.py
--------------
ROI (Region of Interest) Detector for optimized face processing
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List
import logging
from collections import deque

logger = logging.getLogger(__name__)

class ROIDetector:
    """Detect and track Region of Interest (face area) for optimized processing"""
    
    def __init__(self, 
                 roi_scale_factor: float = 1.3,  # Expand ROI 30% beyond face
                 min_roi_size: int = 200,        # Minimum ROI size 200x200
                 max_roi_size: int = 600,        # Maximum ROI size 600x600
                 tracking_frames: int = 5):      # Frames for ROI smoothing
        
        self.roi_scale_factor = roi_scale_factor
        self.min_roi_size = min_roi_size
        self.max_roi_size = max_roi_size
        self.tracking_frames = tracking_frames
        
        # ROI tracking state
        self.roi_history = deque(maxlen=tracking_frames)
        self.current_roi = None
        
        # Face detector (faster than MediaPipe for ROI)
        self.face_detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
    def detect_roi(self, frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect ROI from frame
        Returns: (x, y, width, height) or None
        """
        if frame is None or frame.size == 0:
            return None
            
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        
        # Detect faces
        faces = self.face_detector.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
        )
        
        if len(faces) > 0:
            # Take largest face
            face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = face
            
            # Expand ROI
            roi = self._expand_roi(x, y, w, h, frame.shape[:2])
            
            # Add to history for smoothing
            self.roi_history.append(roi)
            
            # Calculate smoothed ROI
            self.current_roi = self._smooth_roi()
            return self.current_roi
            
        elif self.current_roi is not None:
            # Use last known ROI if face temporarily not detected
            return self.current_roi
            
        return None
    
    def _expand_roi(self, x: int, y: int, w: int, h: int, 
                   frame_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
        """Expand face rectangle to ROI"""
        frame_h, frame_w = frame_shape
        
        # Calculate expanded dimensions
        new_w = int(w * self.roi_scale_factor)
        new_h = int(h * self.roi_scale_factor)
        
        # Ensure minimum and maximum sizes
        new_w = max(self.min_roi_size, min(new_w, self.max_roi_size))
        new_h = max(self.min_roi_size, min(new_h, self.max_roi_size))
        
        # Center the expanded ROI
        new_x = max(0, x + w//2 - new_w//2)
        new_y = max(0, y + h//2 - new_h//2)
        
        # Ensure ROI stays within frame bounds
        new_x = min(new_x, frame_w - new_w)
        new_y = min(new_y, frame_h - new_h)
        
        return (new_x, new_y, new_w, new_h)
    
    def _smooth_roi(self) -> Tuple[int, int, int, int]:
        """Smooth ROI using moving average"""
        if not self.roi_history:
            return self.current_roi
            
        # Calculate average of recent ROIs
        avg_x = int(np.mean([roi[0] for roi in self.roi_history]))
        avg_y = int(np.mean([roi[1] for roi in self.roi_history]))
        avg_w = int(np.mean([roi[2] for roi in self.roi_history]))
        avg_h = int(np.mean([roi[3] for roi in self.roi_history]))
        
        return (avg_x, avg_y, avg_w, avg_h)
    
    def extract_roi(self, frame: np.ndarray, 
                   roi: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """Extract ROI from frame"""
        if frame is None or frame.size == 0:
            return None
            
        if roi is None:
            roi = self.detect_roi(frame)
            
        if roi is None:
            return frame  # Return full frame if no ROI
            
        x, y, w, h = roi
        roi_frame = frame[y:y+h, x:x+w]
        
        return roi_frame if roi_frame.size > 0 else frame
    
    def draw_roi(self, frame: np.ndarray, 
                roi: Optional[Tuple[int, int, int, int]] = None,
                color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
        """Draw ROI rectangle on frame for visualization"""
        if roi is None:
            roi = self.current_roi
            
        if roi is None:
            return frame
            
        x, y, w, h = roi
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.putText(frame, "ROI", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        return frame

class GPUAccelerator:
    """GPU acceleration helper for OpenCV operations"""
    
    def __init__(self):
        self.gpu_available = False
        self._check_gpu_support()
    
    def _check_gpu_support(self):
        """Check if GPU acceleration is available"""
        try:
            if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                self.gpu_available = True
                logger.info("CUDA GPU support detected")
            else:
                logger.info("No CUDA GPU detected")
        except:
            logger.info("GPU acceleration not available")
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Apply GPU-accelerated preprocessing"""
        if not self.gpu_available:
            return self._cpu_process_frame(frame)
            
        try:
            # Upload to GPU
            gpu_frame = cv2.cuda_GpuMat()
            gpu_frame.upload(frame)
            
            # GPU operations (noise reduction)
            gpu_processed = cv2.cuda.bilateralFilter(gpu_frame, -1, 50, 50)
            
            # Download back to CPU
            processed_frame = gpu_processed.download()
            return processed_frame
            
        except Exception as e:
            logger.warning(f"GPU processing failed, using CPU: {e}")
            return self._cpu_process_frame(frame)
    
    def _cpu_process_frame(self, frame: np.ndarray) -> np.ndarray:
        """CPU fallback processing"""
        return cv2.bilateralFilter(frame, 5, 50, 50)