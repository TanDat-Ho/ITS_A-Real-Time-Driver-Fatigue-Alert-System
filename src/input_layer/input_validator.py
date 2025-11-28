"""
input_validator.py
-----------------
Cleaned input validation pipeline for drowsy detection system.

Provides comprehensive validation for:
- Frame quality (brightness, contrast, blur)
- Landmark detection results
- Camera parameters
- System integration validation
"""

import cv2
import numpy as np
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of input validation"""
    valid: bool
    confidence: float
    warnings: List[str]
    errors: List[str]
    metrics: Dict[str, Any]

class InputQualityValidator:
    """Validates input quality for optimal landmark detection"""
    
    def __init__(self):
        self.quality_thresholds = {
            "min_brightness": 30,
            "max_brightness": 280,
            "min_contrast": 20,
            "min_blur_score": 60,
            "min_resolution": (320, 240),
            "max_resolution": (1920, 1080)
        }
        # Motion blur tracking
        self.previous_frame = None
        self.frame_history = deque(maxlen=3)
    
    def validate_frame(self, frame: np.ndarray) -> ValidationResult:
        """Comprehensive frame validation"""
        warnings = []
        errors = []
        metrics = {}
        
        # Basic checks
        if frame is None:
            return ValidationResult(False, 0.0, [], ["Frame is None"], {})
            
        if frame.size == 0:
            return ValidationResult(False, 0.0, [], ["Frame is empty"], {})
        
        # Dimension checks
        h, w = frame.shape[:2]
        metrics["resolution"] = (w, h)
        
        min_w, min_h = self.quality_thresholds["min_resolution"]
        max_w, max_h = self.quality_thresholds["max_resolution"]
        
        if w < min_w or h < min_h:
            errors.append(f"Resolution {w}x{h} too small (minimum {min_w}x{min_h})")
        elif w > max_w or h > max_h:
            warnings.append(f"Resolution {w}x{h} may impact performance")
        
        # Convert to grayscale for analysis
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
            
        # Brightness analysis
        brightness = np.mean(gray)
        metrics["brightness"] = float(brightness)
        
        if brightness < self.quality_thresholds["min_brightness"]:
            warnings.append(f"Low brightness: {brightness:.1f}")
        elif brightness > self.quality_thresholds["max_brightness"]:
            warnings.append(f"High brightness: {brightness:.1f}")
            
        # Contrast analysis
        contrast = np.std(gray)
        metrics["contrast"] = float(contrast)
        
        if contrast < self.quality_thresholds["min_contrast"]:
            warnings.append(f"Low contrast: {contrast:.1f}")
            
        # Blur detection
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        metrics["blur_score"] = float(blur_score)
        
        # Motion blur detection
        motion_score = self._detect_motion_blur(gray)
        metrics["motion_score"] = float(motion_score)
        
        if blur_score < self.quality_thresholds["min_blur_score"]:
            if motion_score > 30:
                warnings.append(f"Motion blur detected: {motion_score:.1f}")
            else:
                warnings.append(f"Frame may be blurry: {blur_score:.1f}")
            
        # Calculate overall confidence
        confidence = self._calculate_confidence(metrics, warnings, errors)
        
        return ValidationResult(
            valid=len(errors) == 0,
            confidence=confidence,
            warnings=warnings,
            errors=errors,
            metrics=metrics
        )
    
    def _calculate_confidence(self, metrics: Dict, warnings: List, errors: List) -> float:
        """Calculate confidence score based on metrics"""
        if errors:
            return 0.0
            
        confidence = 1.0
        
        # Brightness confidence
        brightness = metrics.get("brightness", 0)
        if brightness < 60 or brightness > 180:
            confidence *= 0.7
        elif brightness < 80 or brightness > 160:
            confidence *= 0.85
            
        # Contrast confidence  
        contrast = metrics.get("contrast", 0)
        if contrast < 30:
            confidence *= 0.6
        elif contrast < 40:
            confidence *= 0.8
            
        # Blur confidence
        blur_score = metrics.get("blur_score", 0)
        motion_score = metrics.get("motion_score", 0)
        
        if blur_score < 80:
            confidence *= 0.7
        elif blur_score < 120:
            confidence *= 0.85
            
        # Motion blur penalty
        if motion_score > 30:
            confidence *= 0.6
        elif motion_score > 20:
            confidence *= 0.8
            
        # Warning penalty
        confidence *= max(0.3, 1.0 - len(warnings) * 0.1)
        
        return max(0.0, min(1.0, confidence))
    
    def _detect_motion_blur(self, gray_frame: np.ndarray) -> float:
        """Detect motion blur by comparing consecutive frames"""
        if self.previous_frame is None:
            self.previous_frame = gray_frame.copy()
            return 0.0
            
        # Calculate frame difference
        diff = cv2.absdiff(gray_frame, self.previous_frame)
        motion_score = np.mean(diff)
        
        # Update frame history
        self.frame_history.append(gray_frame.copy())
        self.previous_frame = gray_frame.copy()
        
        return motion_score

class LandmarkQualityValidator:
    """Validates landmark detection quality"""
    
    def validate_landmarks(self, landmarks: List[Tuple], frame_shape: Tuple) -> ValidationResult:
        """Validate landmark detection results"""
        warnings = []
        errors = []
        metrics = {}
        
        if not landmarks:
            return ValidationResult(False, 0.0, [], ["No landmarks detected"], {})
            
        h, w = frame_shape[:2]
        
        # Count valid landmarks
        valid_landmarks = 0
        out_of_bounds = 0
        
        for x, y, z in landmarks:
            if 0 <= x < w and 0 <= y < h:
                valid_landmarks += 1
            else:
                out_of_bounds += 1
                
        metrics["total_landmarks"] = len(landmarks)
        metrics["valid_landmarks"] = valid_landmarks
        metrics["out_of_bounds"] = out_of_bounds
        
        if out_of_bounds > 0:
            warnings.append(f"{out_of_bounds} landmarks out of bounds")
            
        if valid_landmarks < 400:
            warnings.append(f"Only {valid_landmarks} valid landmarks (expected ~468)")
            
        # Calculate landmark distribution quality
        if valid_landmarks > 0:
            # Check distribution across face regions
            x_coords = [x for x, y, z in landmarks if 0 <= x < w]
            y_coords = [y for x, y, z in landmarks if 0 <= y < h]
            
            if x_coords and y_coords:
                x_range = max(x_coords) - min(x_coords)
                y_range = max(y_coords) - min(y_coords)
                metrics["landmark_spread"] = {
                    "x_range": x_range,
                    "y_range": y_range,
                    "aspect_ratio": x_range / y_range if y_range > 0 else 1.0
                }
        
        # Calculate confidence
        confidence = valid_landmarks / 468.0 if valid_landmarks <= 468 else 1.0
        confidence *= max(0.5, 1.0 - out_of_bounds / len(landmarks))
        confidence *= max(0.3, 1.0 - len(warnings) * 0.15)
        
        return ValidationResult(
            valid=valid_landmarks >= 300,
            confidence=confidence,
            warnings=warnings,
            errors=errors,
            metrics=metrics
        )

class CameraParameterValidator:
    """Validates camera configuration parameters"""
    
    def validate_camera_config(self, config: Dict) -> ValidationResult:
        """Validate camera configuration"""
        warnings = []
        errors = []
        metrics = {}
        
        # Check required parameters
        required_params = ["src", "target_size", "fps_limit", "color"]
        for param in required_params:
            if param not in config:
                errors.append(f"Missing required parameter: {param}")
        
        if errors:
            return ValidationResult(False, 0.0, warnings, errors, metrics)
        
        # Validate target_size
        target_size = config.get("target_size")
        if target_size:
            w, h = target_size
            if w < 320 or h < 240:
                warnings.append(f"Target size {target_size} may be too small")
            elif w > 1920 or h > 1080:
                warnings.append(f"Target size {target_size} may impact performance")
        metrics["target_size"] = target_size
        
        # Validate FPS
        fps = config.get("fps_limit", 0)
        if fps <= 0 or fps > 120:
            errors.append(f"Invalid FPS limit: {fps}")
        elif fps < 15:
            warnings.append(f"Low FPS may affect detection: {fps}")
        elif fps > 60:
            warnings.append(f"High FPS may impact performance: {fps}")
        metrics["fps_limit"] = fps
        
        # Validate color format
        color = config.get("color", "").lower()
        if color not in ["rgb", "bgr"]:
            errors.append(f"Invalid color format: {color}")
        elif color == "bgr":
            warnings.append("BGR format may require conversion for some processing")
        metrics["color_format"] = color
        
        # Calculate confidence
        confidence = 1.0
        if warnings:
            confidence *= max(0.5, 1.0 - len(warnings) * 0.1)
        if errors:
            confidence = 0.0
            
        return ValidationResult(
            valid=len(errors) == 0,
            confidence=confidence,
            warnings=warnings,
            errors=errors,
            metrics=metrics
        )

class IntegratedInputValidator:
    """Integrated validator for complete input pipeline"""
    
    def __init__(self):
        self.frame_validator = InputQualityValidator()
        self.landmark_validator = LandmarkQualityValidator()
        self.camera_validator = CameraParameterValidator()
        
    def validate_complete_input(self, frame: np.ndarray, 
                              landmarks: List[Tuple]) -> Dict[str, Any]:
        """Validate complete input pipeline"""
        
        frame_result = self.frame_validator.validate_frame(frame)
        landmark_result = self.landmark_validator.validate_landmarks(landmarks, frame.shape)
        
        overall_valid = frame_result.valid and landmark_result.valid
        overall_confidence = (frame_result.confidence + landmark_result.confidence) / 2.0
        
        return {
            "frame": frame_result,
            "landmarks": landmark_result,
            "overall_valid": overall_valid,
            "overall_confidence": overall_confidence
        }
    
    def validate_system_config(self, camera_config: Dict, mediapipe_config: Dict) -> Dict[str, Any]:
        """Validate complete system configuration"""
        
        camera_result = self.camera_validator.validate_camera_config(camera_config)
        
        # Validate MediaPipe config
        mp_warnings = []
        mp_errors = []
        mp_metrics = {}
        
        # Check MediaPipe confidence thresholds
        det_conf = mediapipe_config.get("min_detection_confidence", 0.5)
        track_conf = mediapipe_config.get("min_tracking_confidence", 0.5)
        
        if det_conf < 0.5:
            mp_warnings.append(f"Low detection confidence: {det_conf}")
        elif det_conf > 0.9:
            mp_warnings.append(f"Very high detection confidence may miss faces: {det_conf}")
            
        if track_conf < 0.5:
            mp_warnings.append(f"Low tracking confidence: {track_conf}")
            
        mp_metrics["detection_confidence"] = det_conf
        mp_metrics["tracking_confidence"] = track_conf
        
        mp_result = ValidationResult(
            valid=len(mp_errors) == 0,
            confidence=max(0.5, 1.0 - len(mp_warnings) * 0.1),
            warnings=mp_warnings,
            errors=mp_errors,
            metrics=mp_metrics
        )
        
        return {
            "camera": camera_result,
            "mediapipe": mp_result,
            "overall_valid": camera_result.valid and mp_result.valid,
            "overall_confidence": (camera_result.confidence + mp_result.confidence) / 2.0
        }

class PerformanceMonitor:
    """Monitor input pipeline performance"""
    
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.metrics_history = {
            "frame_quality": deque(maxlen=window_size),
            "landmark_count": deque(maxlen=window_size),
            "processing_time": deque(maxlen=window_size)
        }
    
    def add_metrics(self, frame_quality: float, landmark_count: int, processing_time: float):
        """Add performance metrics"""
        self.metrics_history["frame_quality"].append(frame_quality)
        self.metrics_history["landmark_count"].append(landmark_count)
        self.metrics_history["processing_time"].append(processing_time)
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        if not any(self.metrics_history.values()):
            return {"status": "no_data"}
        
        summary = {}
        
        # Frame quality stats
        if self.metrics_history["frame_quality"]:
            quality_values = list(self.metrics_history["frame_quality"])
            summary["frame_quality"] = {
                "avg": np.mean(quality_values),
                "min": np.min(quality_values),
                "max": np.max(quality_values),
                "std": np.std(quality_values)
            }
        
        # Landmark count stats
        if self.metrics_history["landmark_count"]:
            count_values = list(self.metrics_history["landmark_count"])
            summary["landmark_count"] = {
                "avg": np.mean(count_values),
                "min": int(np.min(count_values)),
                "max": int(np.max(count_values))
            }
        
        # Processing time stats
        if self.metrics_history["processing_time"]:
            time_values = list(self.metrics_history["processing_time"])
            summary["processing_time"] = {
                "avg_ms": np.mean(time_values) * 1000,
                "max_ms": np.max(time_values) * 1000,
                "fps_estimate": 1.0 / max(0.001, np.mean(time_values))
            }
        
        return summary