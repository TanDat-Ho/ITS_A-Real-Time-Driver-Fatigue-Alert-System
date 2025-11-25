"""
ear.py
-----------------
Eye Aspect Ratio (EAR) - Eye blink detection

EAR = (||p2 - p6|| + ||p3 - p5||) / (2 × ||p1 - p4||)

Where:
- p1, p2, p3, p4, p5, p6: 6 landmark points around one eye
- ||pi - pj||: Euclidean distance between two points

Applied logic:
- Open eyes: ≈ 0.25 – 0.3
- Blink: < 0.2 for < 1.5s  
- Prolonged closure: EAR < 0.2 for ≥ 1.5 – 2.0s (dangerous)
"""

import math
import time
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

# Global tracking variables (có thể reset khi cần)
_ear_state = {
    "consecutive_frames": 0,
    "drowsy_start_time": None,
    "total_blinks": 0,
    "ear_history": [],
    "max_history": 30
}

def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Tính khoảng cách Euclid giữa hai điểm."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def calculate_ear_single_eye(eye_landmarks: List[Tuple[int, int, float]]) -> float:
    """
    Tính EAR cho một mắt.
    
    Args:
        eye_landmarks: List 6 điểm landmark của mắt theo thứ tự:
                      [outer_corner, top1, top2, inner_corner, bottom2, bottom1]
                      
    Returns:
        float: Giá trị EAR
    """
    if len(eye_landmarks) != 6:
        return 0.0
        
    # Chuyển đổi về dạng 2D (x, y)
    points = [(p[0], p[1]) for p in eye_landmarks]
    
    # Theo công thức EAR
    # p1, p4: outer corner, inner corner (chiều ngang)
    # p2, p6: điểm trên và dưới bên ngoài (chiều dọc 1)
    # p3, p5: điểm trên và dưới bên trong (chiều dọc 2)
    p1, p2, p3, p4, p5, p6 = points
    
    # Tính khoảng cách dọc
    vertical_1 = calculate_distance(p2, p6)  # ||p2 - p6||
    vertical_2 = calculate_distance(p3, p5)  # ||p3 - p5||
    
    # Tính khoảng cách ngang
    horizontal = calculate_distance(p1, p4)  # ||p1 - p4||
    
    if horizontal == 0:
        return 0.0
        
    # Công thức EAR
    ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
    return ear


def calculate_ear_both_eyes(left_eye: List[Tuple[int, int, float]], 
                           right_eye: List[Tuple[int, int, float]]) -> float:
    """
    Tính EAR trung bình cho cả hai mắt.
    
    Args:
        left_eye: 6 điểm landmark mắt trái
        right_eye: 6 điểm landmark mắt phải
        
    Returns:
        float: EAR trung bình
    """
    left_ear = calculate_ear_single_eye(left_eye)
    right_ear = calculate_ear_single_eye(right_eye)
    
    # Kiểm tra tính hợp lệ của giá trị EAR
    if left_ear <= 0 or right_ear <= 0:
        return 0.0
        
    # Trên và hành bình cộng với weighted average (giảm noise)
    # Nếu một mắt có EAR bất thường, giảm trọng số
    weight_left = 1.0 if 0.1 <= left_ear <= 0.5 else 0.7
    weight_right = 1.0 if 0.1 <= right_ear <= 0.5 else 0.7
    
    total_weight = weight_left + weight_right
    avg_ear = (left_ear * weight_left + right_ear * weight_right) / total_weight
    
    # Smoothing với moving average
    _ear_state["ear_history"].append(avg_ear)
    if len(_ear_state["ear_history"]) > _ear_state["max_history"]:
        _ear_state["ear_history"].pop(0)
        
    # Trả về smoothed value nếu có đủ lịch sử
    if len(_ear_state["ear_history"]) >= 3:
        # Simple moving average 3 frames để giảm noise
        return np.mean(_ear_state["ear_history"][-3:])
    
    return avg_ear

# Compatibility alias
def calculate_ear(eye_landmarks: List[Tuple[int, int, float]]) -> float:
    """
    Alias cho calculate_ear_single_eye để compatibility
    
    Args:
        eye_landmarks: List 6 điểm landmark của một mắt
        
    Returns:
        EAR value cho một mắt
    """
    return calculate_ear_single_eye(eye_landmarks)


def analyze_ear_state(ear_value: float, 
                     blink_threshold: float = 0.25,  # Tăng từ 0.22 cho chính xác hơn
                     blink_frames: int = 2,  # Giảm từ 3 cho responsive hơn
                     drowsy_threshold: float = 0.22,  # Tăng từ 0.2 giảm false positive
                     drowsy_duration: float = 1.2) -> Dict[str, Any]:
    """
    Analyze eye state based on EAR value - Returns numerical data only.
    
    Args:
        ear_value: Current EAR value
        blink_threshold: EAR threshold to detect blink
        blink_frames: Consecutive frames to confirm blink
        drowsy_threshold: EAR threshold to detect drowsiness
        drowsy_duration: Duration (seconds) to confirm drowsiness
        
    Returns:
        Dict containing numerical analysis only (no state labels)
    """
    current_time = time.time()
    
    # Track blink/closure
    if ear_value < blink_threshold:
        _ear_state["consecutive_frames"] += 1
        
        # Start counting drowsiness time
        if _ear_state["drowsy_start_time"] is None:
            _ear_state["drowsy_start_time"] = current_time
    else:
        # Eyes open - count blink if it was a short closure
        if _ear_state["consecutive_frames"] >= blink_frames:
            _ear_state["total_blinks"] += 1
        
        # Reset counters
        _ear_state["consecutive_frames"] = 0
        _ear_state["drowsy_start_time"] = None
    
    # Calculate drowsy duration
    drowsy_time = 0.0
    if _ear_state["drowsy_start_time"] is not None:
        drowsy_time = current_time - _ear_state["drowsy_start_time"]
    
    # Return only numerical data
    return {
        "ear_value": ear_value,
        "consecutive_frames": _ear_state["consecutive_frames"],
        "drowsy_duration": drowsy_time,
        "total_blinks": _ear_state["total_blinks"],
        "avg_ear": np.mean(_ear_state["ear_history"]) if _ear_state["ear_history"] else 0.0,
        "is_below_threshold": ear_value < drowsy_threshold,
        "is_drowsy_duration": drowsy_time >= drowsy_duration
    }


def reset_ear_state():
    """Reset all tracking variables for EAR."""
    global _ear_state
    _ear_state = {
        "consecutive_frames": 0,
        "drowsy_start_time": None,
        "total_blinks": 0,
        "ear_history": [],
        "max_history": 30
    }


def get_ear_statistics() -> Dict[str, Any]:
    """Lấy thống kê EAR."""
    if not _ear_state["ear_history"]:
        return {}
        
    return {
        "mean_ear": np.mean(_ear_state["ear_history"]),
        "std_ear": np.std(_ear_state["ear_history"]),
        "min_ear": np.min(_ear_state["ear_history"]),
        "max_ear": np.max(_ear_state["ear_history"]),
        "total_blinks": _ear_state["total_blinks"],
        "history_length": len(_ear_state["ear_history"])
    }


# Main utility function cho backward compatibility
def calculate_ear_full(left_eye_landmarks: List[Tuple[int, int, float]], 
                      right_eye_landmarks: List[Tuple[int, int, float]],
                      **kwargs) -> Dict[str, Any]:
    """
    Hàm chính để tính EAR và phân tích trạng thái cả hai mắt.
    
    Args:
        left_eye_landmarks: 6 điểm landmark mắt trái
        right_eye_landmarks: 6 điểm landmark mắt phải
        **kwargs: Các tham số cho analyze_ear_state
        
    Returns:
        Dict chứa kết quả phân tích EAR
    """
    ear_value = calculate_ear_both_eyes(left_eye_landmarks, right_eye_landmarks)
    return analyze_ear_state(ear_value, **kwargs)


if __name__ == "__main__":
    # Test với dữ liệu mẫu
    left_eye = [(33, 160, 0.0), (160, 158, 0.0), (158, 133, 0.0), (133, 153, 0.0), (153, 144, 0.0), (144, 33, 0.0)]
    right_eye = [(362, 385, 0.0), (385, 387, 0.0), (387, 263, 0.0), (263, 373, 0.0), (373, 380, 0.0), (380, 362, 0.0)]
    
    
    result = calculate_ear(left_eye, right_eye)

    print(f"EAR Value: {result['ear_value']}")

 
    
    stats = get_ear_statistics()
    print(f"Statistics: {stats}")
