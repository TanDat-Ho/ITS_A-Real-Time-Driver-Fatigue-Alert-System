"""
head_pose.py
-----------------
Head Pose Estimation (Pitch Angle) - Head nodding detection

Principle:
- Use 3D landmark set with standard face model (nose, chin, left/right eyes, left/right mouth)
- From 2D→3D projection using cv2.solvePnP in OpenCV to calculate:
  o rvec (rotation vector)
  o tvec (translation vector)
- Then convert rvec → rotation matrix using cv2.Rodrigues(rvec)
  → extract Euler angles (yaw, pitch, roll)

Where:
- Pitch: nodding angle (tilt up - tilt down)
- Yaw: head rotation left/right  
- Roll: head tilt (ear towards shoulder)

Applied logic:
- |pitch| ≤ 10°: Normal
- |pitch| ≤ 15° for > 1.5s: Head down drowsiness (clear sign of fatigue)
"""

import cv2
import numpy as np
import math
import time
from typing import List, Tuple, Optional, Dict, Any

# Global tracking variables cho Head Pose
_head_pose_state = {
    "drowsy_start_time": None,
    "pitch_history": [],
    "max_history": 30
}

# 3D model points (mô hình khuôn mặt chuẩn)
_MODEL_POINTS = np.array([
    (0.0, 0.0, 0.0),             # Nose tip (mũi)
    (0.0, -330.0, -65.0),        # Chin (cằm)
    (-225.0, 170.0, -135.0),     # Left eye left corner (góc mắt trái)
    (225.0, 170.0, -135.0),      # Right eye right corner (góc mắt phải)
    (-150.0, -150.0, -125.0),    # Left mouth corner (góc miệng trái)
    (150.0, -150.0, -125.0)      # Right mouth corner (góc miệng phải)
], dtype=np.float64)
def get_camera_matrix(frame_width: int, frame_height: int) -> np.ndarray:
    """Tạo camera matrix dựa trên kích thước frame."""
    focal_length = frame_width
    camera_center = (frame_width // 2, frame_height // 2)
    return np.array([
        [focal_length, 0, camera_center[0]],
        [0, focal_length, camera_center[1]],
        [0, 0, 1]
    ], dtype=np.float64)


def extract_2d_points(features: Dict[str, List[Tuple[int, int, float]]]) -> Optional[np.ndarray]:
    """
    Trích xuất các điểm 2D tương ứng với model 3D.
    
    Args:
        features: Dict chứa các vùng đặc trưng từ FaceLandmarkDetector
        
    Returns:
        np.ndarray: Mảng 6 điểm 2D tương ứng hoặc None
    """
    try:
        # Lấy điểm mũi (nose tip)
        if not features.get("nose") or len(features["nose"]) == 0:
            return None
        nose_tip = features["nose"][0]  # (x, y, z)
        
        # Ước tính điểm cằm từ face_outline (điểm thấp nhất)
        face_outline = features.get("face_outline", [])
        if len(face_outline) < 4:
            return None
        chin = max(face_outline, key=lambda p: p[1])  # Điểm có y lớn nhất (thấp nhất)
        
        # Lấy góc mắt
        left_eye = features.get("left_eye", [])
        right_eye = features.get("right_eye", [])
        if len(left_eye) < 6 or len(right_eye) < 6:
            return None
        left_eye_corner = left_eye[0]   # Góc ngoài mắt trái
        right_eye_corner = right_eye[3] # Góc ngoài mắt phải
        
        # Lấy góc miệng từ mouth landmarks
        mouth = features.get("mouth", [])
        if len(mouth) < 6:
            return None
        left_mouth = mouth[0]   # Góc miệng trái
        right_mouth = mouth[3]  # Góc miệng phải
        
        # Tạo mảng image points 2D
        image_points = np.array([
            [nose_tip[0], nose_tip[1]],
            [chin[0], chin[1]],
            [left_eye_corner[0], left_eye_corner[1]],
            [right_eye_corner[0], right_eye_corner[1]],
            [left_mouth[0], left_mouth[1]],
            [right_mouth[0], right_mouth[1]]
        ], dtype=np.float64)
        
        return image_points
        
    except Exception as e:
        print(f"Error extracting 2D points: {e}")
        return None


def calculate_head_pose(features: Dict[str, List[Tuple[int, int, float]]], 
                       frame_shape: Tuple[int, int]) -> Optional[Dict[str, float]]:
    """
    Tính toán góc head pose từ các đặc trưng khuôn mặt.
    
    Args:
        features: Dict chứa các vùng đặc trưng
        frame_shape: (height, width) của frame
        
    Returns:
        Dict chứa các góc pitch, yaw, roll hoặc None
    """
    # Cập nhật camera parameters
    height, width = frame_shape[:2]
    camera_matrix = get_camera_matrix(width, height)
    
    # Distortion coefficients (giả sử camera không bị méo)
    dist_coeffs = np.zeros((4, 1))
    
    # Trích xuất điểm 2D
    image_points = extract_2d_points(features)
    if image_points is None:
        return None
    
    try:
        # Solve PnP
        success, rotation_vector, translation_vector = cv2.solvePnP(
            _MODEL_POINTS,
            image_points,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        
        if not success:
            return None
        
        # Chuyển rotation vector thành rotation matrix
        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
        
        # Tính góc Euler từ rotation matrix
        # Sử dụng công thức chuyển đổi rotation matrix sang Euler angles
        sy = math.sqrt(rotation_matrix[0, 0] * rotation_matrix[0, 0] + 
                      rotation_matrix[1, 0] * rotation_matrix[1, 0])
        
        singular = sy < 1e-6
        
        if not singular:
            x = math.atan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
            y = math.atan2(-rotation_matrix[2, 0], sy)
            z = math.atan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
        else:
            x = math.atan2(-rotation_matrix[1, 2], rotation_matrix[1, 1])
            y = math.atan2(-rotation_matrix[2, 0], sy)
            z = 0
        
        # Chuyển từ radian sang độ
        pitch = math.degrees(x)
        yaw = math.degrees(y)
        roll = math.degrees(z)
        
        return {
            "pitch": pitch,
            "yaw": yaw,
            "roll": roll,
            "rotation_vector": rotation_vector.flatten(),
            "translation_vector": translation_vector.flatten()
        }
        
    except Exception as e:
        print(f"Error in head pose calculation: {e}")
        return None


def analyze_head_pose_state(pose_data: Optional[Dict[str, float]], 
                           normal_threshold: float = 10.0,
                           drowsy_threshold: float = 15.0,
                           drowsy_duration: float = 1.5) -> Dict[str, Any]:
    """
    Analyze head state based on pitch angle.
    
    Args:
        pose_data: Dict containing head angle information
        normal_threshold: Normal pitch angle (degrees)
        drowsy_threshold: Drowsy pitch angle (degrees)
        drowsy_duration: Duration to maintain for drowsiness confirmation (seconds)
        
    Returns:
        Dict containing state information
    """
    current_time = time.time()
    
    if pose_data is None:
        return {
            "pitch": 0.0,
            "state": "UNKNOWN",
            "alert_level": "NONE",
            "drowsy_duration": 0.0
        }
    
    pitch = pose_data["pitch"]
    
    # Lưu vào lịch sử
    _head_pose_state["pitch_history"].append(pitch)
    if len(_head_pose_state["pitch_history"]) > _head_pose_state["max_history"]:
        _head_pose_state["pitch_history"].pop(0)
    
    # Check head down angle
    abs_pitch = abs(pitch)
    
    if abs_pitch > drowsy_threshold:
        if _head_pose_state["drowsy_start_time"] is None:
            _head_pose_state["drowsy_start_time"] = current_time
    else:
        _head_pose_state["drowsy_start_time"] = None
    
    # Calculate head down duration
    drowsy_time = 0.0
    if _head_pose_state["drowsy_start_time"] is not None:
        drowsy_time = current_time - _head_pose_state["drowsy_start_time"]
    
    # Return only numerical data
    return {
        "pitch": pitch,
        "yaw": pose_data.get("yaw", 0.0),
        "roll": pose_data.get("roll", 0.0),
        "abs_pitch": abs_pitch,
        "drowsy_duration": drowsy_time,
        "avg_pitch": np.mean(_head_pose_state["pitch_history"]) if _head_pose_state["pitch_history"] else 0.0,
        "pitch_std": np.std(_head_pose_state["pitch_history"]) if len(_head_pose_state["pitch_history"]) > 1 else 0.0,
        "is_above_normal_threshold": abs_pitch > normal_threshold,
        "is_above_drowsy_threshold": abs_pitch > drowsy_threshold,
        "is_drowsy_duration": drowsy_time >= drowsy_duration
    }


def reset_head_pose_state():
    """Reset tất cả các biến tracking cho Head Pose."""
    global _head_pose_state
    _head_pose_state = {
        "drowsy_start_time": None,
        "pitch_history": [],
        "max_history": 30
    }


def get_head_pose_statistics() -> Dict[str, Any]:
    """Lấy thống kê góc đầu."""
    if not _head_pose_state["pitch_history"]:
        return {}
        
    return {
        "mean_pitch": np.mean(_head_pose_state["pitch_history"]),
        "std_pitch": np.std(_head_pose_state["pitch_history"]),
        "min_pitch": np.min(_head_pose_state["pitch_history"]),
        "max_pitch": np.max(_head_pose_state["pitch_history"]),
        "history_length": len(_head_pose_state["pitch_history"])
    }


# Hàm chính để tính Head Pose và phân tích
def calculate_head_pose_with_analysis(features: Dict[str, List[Tuple[int, int, float]]], 
                                     frame_shape: Tuple[int, int], **kwargs) -> Dict[str, Any]:
    """
    Hàm chính để tính Head Pose và phân tích trạng thái.
    
    Args:
        features: Dict chứa các vùng đặc trưng
        frame_shape: (height, width) của frame
        **kwargs: Các tham số cho analyze_head_pose_state
        
    Returns:
        Dict chứa kết quả phân tích Head Pose
    """
    pose_data = calculate_head_pose(features, frame_shape)
    return analyze_head_pose_state(pose_data, **kwargs)


def calculate_head_pitch(features: Dict[str, List[Tuple[int, int, float]]], 
                        frame_shape: Tuple[int, int]) -> Optional[float]:
    """
    Hàm tiện ích để tính góc pitch nhanh.
    
    Args:
        features: Dict chứa các vùng đặc trưng
        frame_shape: (height, width) của frame
        
    Returns:
        float: Góc pitch hoặc None
    """
    pose_data = calculate_head_pose(features, frame_shape)
    return pose_data["pitch"] if pose_data else None


if __name__ == "__main__":
    # Test với dữ liệu mẫu
    mock_features = {
        "nose": [(320, 240, 0.0)],
        "face_outline": [(300, 400, 0.0), (340, 400, 0.0), (320, 420, 0.0), (320, 450, 0.0)],
        "left_eye": [(280, 220, 0.0), (285, 215, 0.0), (290, 215, 0.0), (295, 220, 0.0), (290, 225, 0.0), (285, 225, 0.0)],
        "right_eye": [(345, 220, 0.0), (350, 215, 0.0), (355, 215, 0.0), (360, 220, 0.0), (355, 225, 0.0), (350, 225, 0.0)],
        "mouth": [(300, 280, 0.0), (310, 275, 0.0), (320, 275, 0.0), (340, 280, 0.0), (320, 285, 0.0), (310, 285, 0.0)]
    }
    
    result = calculate_head_pose_with_analysis(mock_features, (480, 640))
    
    if result and result.get('pitch') is not None:
        print(f"Pitch: {result['pitch']:.2f}°")
        print(f"Yaw: {result['yaw']:.2f}°") 
        print(f"Roll: {result['roll']:.2f}°")
        print(f"State: {result['state']}")
        print(f"Alert Level: {result['alert_level']}")
    else:
        print("Failed to calculate head pose")
    
    stats = get_head_pose_statistics()
    print(f"Statistics: {stats}")
