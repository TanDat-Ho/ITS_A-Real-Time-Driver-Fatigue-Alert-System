"""
mar.py
-----------------
Mouth Aspect Ratio (MAR) - Yawn detection

MAR = (||u1 - l1|| + ||u2 - l2||) / (2 × ||cleft - cright||)

Where:
- u1, u2: points on upper lip
- l1, l2: corresponding points on lower lip  
- cleft, cright: left and right mouth corners
- ||·||: Euclidean distance

Applied logic:
- Mouth closed/normal speaking: < 0.4
- Mouth slightly open: 0.4 – 0.6 (may be speaking or smiling)
- Yawn/wide open: > 0.6 (if maintained > 1.2s, confirmed as prolonged yawn)
"""

import math
import time
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

# Global tracking variables cho MAR
_mar_state = {
    "yawn_start_time": None,
    "total_yawns": 0,
    "mar_history": [],
    "max_history": 30,
    "is_yawning": False
}
def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Tính khoảng cách Euclid giữa hai điểm."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def calculate_mar(mouth_landmarks: List[Tuple[int, int, float]]) -> float:
    """
    Tính MAR từ các điểm landmark của miệng.
    
    Args:
        mouth_landmarks: List 6 điểm landmark của miệng theo thứ tự:
                       [left_corner, top_left, top_right, right_corner, bottom_right, bottom_left]
                       
    Returns:
        float: Giá trị MAR
    """
    if len(mouth_landmarks) != 6:
        return 0.0
        
    # Chuyển đổi về dạng 2D (x, y)
    points = [(p[0], p[1]) for p in mouth_landmarks]
    
    # Mapping theo công thức MAR
    # cleft, cright: khóe miệng trái và phải  
    # u1, u2: điểm trên môi trên (trái, phải)
    # l1, l2: điểm tương ứng môi dưới (trái, phải)
    left_corner, top_left, top_right, right_corner, bottom_right, bottom_left = points
    
    # Tính khoảng cách dọc (chiều cao miệng)
    vertical_left = calculate_distance(top_left, bottom_left)    # ||u1 - l1||
    vertical_right = calculate_distance(top_right, bottom_right) # ||u2 - l2||
    
    # Tính khoảng cách ngang (chiều rộng miệng)
    horizontal = calculate_distance(left_corner, right_corner)   # ||cleft - cright||
    
    if horizontal == 0:
        return 0.0
        
    # Công thức MAR
    mar = (vertical_left + vertical_right) / (2.0 * horizontal)
    
    # Lưu vào lịch sử
    _mar_state["mar_history"].append(mar)
    if len(_mar_state["mar_history"]) > _mar_state["max_history"]:
        _mar_state["mar_history"].pop(0)
        
    return mar


def analyze_mar_state(mar_value: float, 
                     yawn_threshold: float = 0.6,
                     yawn_duration: float = 1.2,
                     speaking_threshold: float = 0.4) -> Dict[str, Any]:
    """
    Analyze mouth state based on MAR value.
    
    Args:
        mar_value: Current MAR value
        yawn_threshold: MAR threshold to detect yawn
        yawn_duration: Duration (seconds) to confirm prolonged yawn
        speaking_threshold: MAR threshold to distinguish speaking/silence
        
    Returns:
        Dict containing state information
    """
    current_time = time.time()
    
    # Check yawn
    if mar_value >= yawn_threshold:
        if _mar_state["yawn_start_time"] is None:
            _mar_state["yawn_start_time"] = current_time
            _mar_state["is_yawning"] = True
    else:
        # Kết thúc ngáp
        if _mar_state["is_yawning"]:
            if _mar_state["yawn_start_time"] is not None:
                yawn_dur = current_time - _mar_state["yawn_start_time"]
                if yawn_dur >= yawn_duration:
                    _mar_state["total_yawns"] += 1
                    
            _mar_state["yawn_start_time"] = None
            _mar_state["is_yawning"] = False
    
    # Calculate current yawn duration
    current_yawn_duration = 0.0
    if _mar_state["yawn_start_time"] is not None:
        current_yawn_duration = current_time - _mar_state["yawn_start_time"]
    
    # Return only numerical data
    return {
        "mar_value": mar_value,
        "is_yawning": _mar_state["is_yawning"],
        "yawn_duration": current_yawn_duration,
        "total_yawns": _mar_state["total_yawns"],
        "avg_mar": np.mean(_mar_state["mar_history"]) if _mar_state["mar_history"] else 0.0,
        "is_above_yawn_threshold": mar_value >= yawn_threshold,
        "is_above_speaking_threshold": mar_value >= speaking_threshold,
        "is_yawn_duration": current_yawn_duration >= yawn_duration
    }


def reset_mar_state():
    """Reset tất cả các biến tracking cho MAR."""
    global _mar_state
    _mar_state = {
        "yawn_start_time": None,
        "total_yawns": 0,
        "mar_history": [],
        "max_history": 30,
        "is_yawning": False
    }


def get_mar_statistics() -> Dict[str, Any]:
    """Lấy thống kê MAR."""
    if not _mar_state["mar_history"]:
        return {}
        
    return {
        "mean_mar": np.mean(_mar_state["mar_history"]),
        "std_mar": np.std(_mar_state["mar_history"]),
        "min_mar": np.min(_mar_state["mar_history"]),
        "max_mar": np.max(_mar_state["mar_history"]),
        "total_yawns": _mar_state["total_yawns"],
        "history_length": len(_mar_state["mar_history"])
    }


def get_yawn_frequency(time_window: float = 60.0) -> float:
    """
    Tính tần suất ngáp trong khoảng thời gian (yawns/minute).
    
    Args:
        time_window: Cửa sổ thời gian tính toán (giây)
        
    Returns:
        float: Tần suất ngáp/phút
    """
    if _mar_state["total_yawns"] == 0:
        return 0.0
        
    # Giả sử total_yawns được tính trong time_window giây
    yawns_per_minute = (_mar_state["total_yawns"] * 60.0) / time_window
    return yawns_per_minute


# Hàm chính để tính MAR và phân tích
def calculate_mar_with_analysis(mouth_landmarks: List[Tuple[int, int, float]], **kwargs) -> Dict[str, Any]:
    """
    Hàm chính để tính MAR và phân tích trạng thái.
    
    Args:
        mouth_landmarks: 6 điểm landmark của miệng
        **kwargs: Các tham số cho analyze_mar_state
        
    Returns:
        Dict chứa kết quả phân tích MAR
    """
    mar_value = calculate_mar(mouth_landmarks)
    return analyze_mar_state(mar_value, **kwargs)


if __name__ == "__main__":
    # Test với dữ liệu mẫu
    mouth_landmarks = [
        (61, 84, 0.0),    # left corner
        (13, 82, 0.0),    # top left  
        (14, 82, 0.0),    # top right
        (291, 84, 0.0),   # right corner
        (17, 86, 0.0),    # bottom right
        (18, 86, 0.0)     # bottom left
    ]
    
    result = calculate_mar_with_analysis(mouth_landmarks)
    
    print(f"MAR Value: {result['mar_value']:.3f}")
    print(f"State: {result['state']}")
    print(f"Alert Level: {result['alert_level']}")
    print(f"Is Yawning: {result['is_yawning']}")
    
    stats = get_mar_statistics()
    print(f"Statistics: {stats}")
