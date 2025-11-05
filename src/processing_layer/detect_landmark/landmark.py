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

    def __init__(self, static_mode=False, max_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5):
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

    def detect(self, frame: np.ndarray, draw: bool = False) -> Tuple[List[Tuple[int, int, float]], np.ndarray]:
        """
        Phát hiện landmarks trên frame.

        Args:
            frame: Input BGR frame
            draw: Whether to draw landmarks on frame
            
        Returns:
            tuple: (face_landmarks, annotated_frame)
        """
        if frame is None or frame.size == 0:
            return [], frame if frame is not None else np.zeros(LandmarkConstants.DEFAULT_FRAME_SIZE, dtype=np.uint8)
            
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
            return landmarks, frame
        except Exception as e:
            logger.error(f"MediaPipe detection error: {e}")
            return [], frame

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
