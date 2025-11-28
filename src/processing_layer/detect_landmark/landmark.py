"""
landmark.py
-----------------
Module chịu trách nhiệm phát hiện và trích xuất các đặc trưng khuôn mặt 
(468 landmarks) sử dụng Mediapipe Face Mesh.

Kết quả đầu ra được sử dụng bởi rule-based processor để tính toán:
- EAR (Eye Aspect Ratio)
- MAR (Mouth Aspect Ratio)
- Head Pose (góc cúi/ngẩng/nghiêng đầu)
"""

import cv2
import mediapipe as mp
import numpy as np
import logging
from typing import Optional, Tuple, List, Dict, Any

# Setup module logger
logger = logging.getLogger(__name__)

# Constants
class LandmarkConstants:
    """Constants for landmark detection"""
    DEFAULT_FRAME_SIZE = (640, 480, 3)
    MIN_LANDMARKS_COUNT = 468
    
    # MediaPipe Face Mesh landmark indices
    LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]
    MOUTH_IDX = [13, 14, 78, 308, 82, 312]
    NOSE_TIP_IDX = [1]
    FACE_OUTLINE_IDX = [10, 152, 234, 454]
    
    # Colors for debug visualization (BGR format)
    EYE_COLOR = (0, 255, 0)      # Green for eyes
    MOUTH_COLOR = (255, 0, 0)    # Blue for mouth  
    NOSE_COLOR = (0, 0, 255)     # Red for nose


class FaceLandmarkDetector:
    """
    Lớp xử lý phát hiện khuôn mặt và lấy tọa độ landmarks sử dụng Mediapipe.
    """

    def __init__(self, static_mode=False, max_faces=1, refine_landmarks=True, min_detection_confidence=0.7, min_tracking_confidence=0.7):
        # Validate parameters
        self._validate_parameters(static_mode, max_faces, refine_landmarks, 
                                min_detection_confidence, min_tracking_confidence)
        
        try:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=static_mode,
                max_num_faces=max_faces,
                refine_landmarks=refine_landmarks,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence
            )
            self.mp_draw = mp.solutions.drawing_utils
            self.draw_spec = self.mp_draw.DrawingSpec(thickness=1, circle_radius=1, color=(0, 255, 0))
            
            # Tracking state for stability
            self.tracking_state = {
                "consecutive_detections": 0,
                "consecutive_failures": 0,
                "last_landmarks": None,
                "stability_threshold": 5,
                "confidence_history": [],
                "landmark_history": [],  # For temporal smoothing
                "smoothing_factor": 0.7   # Smoothing strength (0-1)
            }
            
            # ROI support
            self.use_roi = True
            self.roi_detector = None
            self._initialize_roi_detector()
            
        except Exception as e:
            logger.error(f"Failed to initialize MediaPipe Face Mesh: {e}")
            raise
    
    def _validate_parameters(self, static_mode, max_faces, refine_landmarks, 
                           min_detection_confidence, min_tracking_confidence):
        """Validate MediaPipe parameters"""
        if not isinstance(static_mode, bool):
            raise ValueError("static_mode must be boolean")
            
        if not isinstance(max_faces, int) or max_faces < 1 or max_faces > 10:
            raise ValueError("max_faces must be integer between 1-10")
            
        if not isinstance(refine_landmarks, bool):
            raise ValueError("refine_landmarks must be boolean")
            
        if not (0.0 <= min_detection_confidence <= 1.0):
            raise ValueError("min_detection_confidence must be between 0.0-1.0")
            
        if not (0.0 <= min_tracking_confidence <= 1.0):
            raise ValueError("min_tracking_confidence must be between 0.0-1.0")
    
    def _initialize_roi_detector(self):
        """Initialize ROI detector for optimized processing"""
        try:
            # Import here to avoid circular imports
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent.parent / "input_layer"))
            from roi_detector import ROIDetector
            
            self.roi_detector = ROIDetector()
            logger.info("ROI detector initialized for landmark processing")
        except Exception as e:
            logger.warning(f"Could not initialize ROI detector: {e}")
            self.use_roi = False
    
    def _validate_input_frame(self, frame: np.ndarray) -> Dict:
        """Validate input frame quality for landmark detection"""
        result = {"valid": True, "warnings": []}
        
        if frame is None:
            return {"valid": False, "error": "Frame is None"}
            
        if frame.size == 0:
            return {"valid": False, "error": "Frame is empty"}
            
        # Check frame dimensions
        if len(frame.shape) != 3:
            result["warnings"].append("Frame is not 3-channel color image")
            
        h, w = frame.shape[:2]
        if w < 320 or h < 240:
            result["warnings"].append(f"Frame resolution ({w}x{h}) may be too low for accurate detection")
            
        # Check frame quality
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        if brightness < 30:
            result["warnings"].append(f"Frame too dark (brightness: {brightness:.1f})")
        elif brightness > 220:
            result["warnings"].append(f"Frame too bright (brightness: {brightness:.1f})")
            
        if contrast < 20:
            result["warnings"].append(f"Low contrast (contrast: {contrast:.1f})")
            
        result["frame_quality"] = {
            "brightness": float(brightness),
            "contrast": float(contrast),
            "resolution": (w, h)
        }
        
        return result
    
    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for better landmark detection"""
        processed = frame.copy()
        
        # Light noise reduction
        processed = cv2.bilateralFilter(processed, 5, 50, 50)
        
        # Histogram equalization for better contrast
        if len(processed.shape) == 3:
            # Convert to YUV and equalize Y channel
            yuv = cv2.cvtColor(processed, cv2.COLOR_BGR2YUV)
            yuv[:,:,0] = cv2.equalizeHist(yuv[:,:,0])
            processed = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        else:
            processed = cv2.equalizeHist(processed)
            
        return processed

    def detect(self, frame: np.ndarray, draw: bool = False) -> Tuple[List[Tuple[int, int, float]], np.ndarray, Dict]:
        """
        Phát hiện landmarks trên frame.

        Args:
            frame: Input BGR frame
            draw: Whether to draw landmarks on frame
            
        Returns:
            tuple: (face_landmarks, annotated_frame)
        """
        if frame is None or frame.size == 0:
            detection_result = {"valid": False, "error": "Frame is None or empty"}
            return [], frame if frame is not None else np.zeros(LandmarkConstants.DEFAULT_FRAME_SIZE, dtype=np.uint8), detection_result
            
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            landmarks = []

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    h, w, _ = frame.shape
                    for lm in face_landmarks.landmark:
                        x, y, z = int(lm.x * w), int(lm.y * h), lm.z
                        landmarks.append((x, y, z))
                    if draw:
                        self.mp_draw.draw_landmarks(
                            frame,
                            face_landmarks,
                            self.mp_face_mesh.FACEMESH_CONTOURS,
                            self.draw_spec,
                            self.draw_spec
                        )
            detection_result = {"valid": True, "face_detected": len(landmarks) > 0, "landmarks_count": len(landmarks)}
            return landmarks, frame, detection_result
        except Exception as e:
            logger.error(f"MediaPipe detection error: {e}")
            detection_result = {"valid": False, "error": str(e), "face_detected": False}
            return [], frame, detection_result

    def extract_important_points(self, landmarks: List[Tuple[int, int, float]]) -> Optional[Dict[str, List[Tuple[int, int, float]]]]:
        """
        Lấy ra các điểm quan trọng cho các phép tính EAR, MAR, Head Pose.
        
        MediaPipe Face Mesh có 468 landmarks (0-467):
        - Eyes: outer/inner corners, top/bottom eyelids
        - Mouth: corners, top/bottom lips  
        - Nose: tip, bridge points
        - Face outline: chin, cheeks, forehead
        """
        if not landmarks or len(landmarks) < 468:
            return None

        # Eye landmarks (6 points each for EAR calculation)
        left_eye_idx = LandmarkConstants.LEFT_EYE_IDX      # Left eye contour
        right_eye_idx = LandmarkConstants.RIGHT_EYE_IDX    # Right eye contour
        
        # Mouth landmarks (6 points for MAR calculation)  
        mouth_idx = LandmarkConstants.MOUTH_IDX             # Mouth corners + top/bottom
        
        # Head pose landmarks
        nose_tip_idx = LandmarkConstants.NOSE_TIP_IDX       # Nose tip
        face_outline_idx = LandmarkConstants.FACE_OUTLINE_IDX # Face boundary points

        def get_points(idxs):
            return [landmarks[i] for i in idxs if i < len(landmarks)]

        return {
            "left_eye": get_points(left_eye_idx),
            "right_eye": get_points(right_eye_idx),
            "mouth": get_points(mouth_idx),
            "nose": get_points(nose_tip_idx),
            "face_outline": get_points(face_outline_idx)
        }

    def draw_debug_overlay(self, frame, features):
        """
        Vẽ các vùng đặc trưng (mắt, miệng, mũi...) bằng màu khác nhau để debug.

        Args:
            frame (np.ndarray): Ảnh BGR đầu vào.
            features (dict): Output của extract_important_points().
        """
        if features is None:
            return frame

        # Màu sắc cho từng vùng
        COLORS = {
            "left_eye": LandmarkConstants.EYE_COLOR,     # Green for eyes
            "right_eye": LandmarkConstants.EYE_COLOR,    # Green for eyes  
            "mouth": LandmarkConstants.MOUTH_COLOR,      # Blue for mouth
            "nose": LandmarkConstants.NOSE_COLOR,        # Red for nose
            "face_outline": (255, 255, 0) # Cyan for face outline
        }

        for region, pts in features.items():
            if not pts:
                continue
            color = COLORS.get(region, (255, 255, 255))
            for (x, y, _) in pts:
                cv2.circle(frame, (x, y), 2, color, -1)
            # Nối các điểm chính (giúp nhìn rõ hình dạng)
            if len(pts) > 1:
                cv2.polylines(frame, [np.array([(x, y) for (x, y, _) in pts], np.int32)], isClosed=True, color=color, thickness=1)

        return frame

    def release(self):
        """Giải phóng tài nguyên Mediapipe."""
        if hasattr(self, 'face_mesh') and self.face_mesh:
            try:
                self.face_mesh.close()
            except (ValueError, RuntimeError) as e:
                # MediaPipe already closed or invalid state - ignore
                pass
            finally:
                self.face_mesh = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
        return False

    def __del__(self):
        """Destructor - cleanup khi object bị garbage collected."""
        try:
            self.release()
        except Exception:
            pass  # Ignore all errors during garbage collection
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance and stability statistics"""
        return {
            "consecutive_detections": self.tracking_state["consecutive_detections"],
            "consecutive_failures": self.tracking_state["consecutive_failures"],
            "stability_score": self._calculate_stability_score(),
            "landmark_count": len(self.tracking_state.get("last_landmarks", [])),
            "roi_enabled": self.use_roi and self.roi_detector is not None,
            "smoothing_factor": self.tracking_state["smoothing_factor"]
        }
    
    def _calculate_stability_score(self) -> float:
        """Calculate landmark stability score (0-1)"""
        consecutive = self.tracking_state["consecutive_detections"]
        failures = self.tracking_state["consecutive_failures"]
        
        # Base score from consecutive detections
        stability = min(1.0, consecutive / 10.0)
        
        # Penalty for recent failures
        if failures > 0:
            stability *= max(0.3, 1.0 - failures * 0.1)
            
        return stability
