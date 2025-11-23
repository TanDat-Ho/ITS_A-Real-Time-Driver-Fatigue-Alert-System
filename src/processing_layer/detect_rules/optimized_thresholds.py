"""
Optimized Thresholds Configuration
Tối ưu hóa các ngưỡng phát hiện cho độ chính xác cao nhất
"""

import json
from typing import Dict, Any
from pathlib import Path

class OptimizedThresholds:
    """
    Class quản lý các ngưỡng tối ưu cho detection rules
    """
    
    # Optimized thresholds dựa trên research và testing
    DEFAULT_THRESHOLDS = {
        # EAR (Eye Aspect Ratio) thresholds
        "ear": {
            "blink_threshold": 0.25,      # Tăng từ 0.2 - giảm false positive
            "blink_frames": 2,            # Giảm từ 3 - responsive hơn
            "drowsy_threshold": 0.22,     # Tăng từ 0.2 - stability
            "drowsy_duration": 1.2,       # Giảm từ 1.5 - faster detection
            "smoothing_window": 3         # Moving average window
        },
        
        # MAR (Mouth Aspect Ratio) thresholds  
        "mar": {
            "yawn_threshold": 0.65,       # Tăng từ 0.6 - accuracy
            "yawn_duration": 1.0,         # Giảm từ 1.2 - responsiveness
            "speaking_threshold": 0.35,   # Giảm từ 0.4 - better differentiation
            "mouth_width_min": 10,        # Pixels - validation
            "mouth_height_min": 5         # Pixels - validation
        },
        
        # Head Pose thresholds
        "head_pose": {
            "normal_threshold": 12.0,     # Tăng từ 10.0 - tolerance
            "drowsy_threshold": 18.0,     # Tăng từ 15.0 - reduce false alarms
            "drowsy_duration": 1.3,       # Giảm từ 1.5 - faster response
            "max_angle": 45.0,            # Maximum reasonable head angle
            "pitch_weight": 1.2,          # Pitch angle weight (forward/backward)
            "yaw_weight": 1.0,            # Yaw angle weight (left/right)
            "roll_weight": 0.8            # Roll angle weight (tilt)
        },
        
        # Combined detection logic
        "combined": {
            "confidence_threshold": 0.7,   # Overall confidence threshold
            "alert_cooldown": 3.0,         # Seconds between alerts
            "severity_levels": {
                "mild": 0.3,
                "moderate": 0.6, 
                "severe": 0.8
            }
        }
    }
    
    @classmethod
    def get_threshold(cls, category: str, key: str, default: Any = None) -> Any:
        """
        Lấy threshold value theo category và key
        
        Args:
            category: Loại threshold (ear, mar, head_pose, combined)
            key: Tên threshold
            default: Giá trị mặc định nếu không tìm thấy
            
        Returns:
            Threshold value
        """
        return cls.DEFAULT_THRESHOLDS.get(category, {}).get(key, default)
    
    @classmethod
    def get_category_thresholds(cls, category: str) -> Dict[str, Any]:
        """
        Lấy tất cả thresholds của một category
        
        Args:
            category: Loại threshold
            
        Returns:
            Dict chứa các thresholds
        """
        return cls.DEFAULT_THRESHOLDS.get(category, {})
    
    @classmethod
    def save_to_file(cls, filepath: str):
        """
        Lưu thresholds ra file JSON
        
        Args:
            filepath: Đường dẫn file
        """
        with open(filepath, 'w') as f:
            json.dump(cls.DEFAULT_THRESHOLDS, f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str):
        """
        Load thresholds từ file JSON
        
        Args:
            filepath: Đường dẫn file
        """
        if Path(filepath).exists():
            with open(filepath, 'r') as f:
                cls.DEFAULT_THRESHOLDS.update(json.load(f))

    @classmethod
    def get_adaptive_thresholds(cls, lighting_condition: str = "normal", 
                               camera_quality: str = "medium") -> Dict[str, Any]:
        """
        Lấy thresholds thích ứng theo điều kiện môi trường
        
        Args:
            lighting_condition: Điều kiện ánh sáng (low, normal, bright)
            camera_quality: Chất lượng camera (low, medium, high)
            
        Returns:
            Adaptive thresholds
        """
        base_thresholds = cls.DEFAULT_THRESHOLDS.copy()
        
        # Điều chỉnh theo ánh sáng
        if lighting_condition == "low":
            # Ánh sáng yếu - tăng threshold để giảm noise
            base_thresholds["ear"]["blink_threshold"] += 0.02
            base_thresholds["mar"]["yawn_threshold"] += 0.05
            base_thresholds["head_pose"]["drowsy_threshold"] += 2.0
            
        elif lighting_condition == "bright":
            # Ánh sáng mạnh - giảm threshold để tăng sensitivity
            base_thresholds["ear"]["blink_threshold"] -= 0.01
            base_thresholds["mar"]["yawn_threshold"] -= 0.02
            base_thresholds["head_pose"]["drowsy_threshold"] -= 1.0
        
        # Điều chỉnh theo chất lượng camera
        if camera_quality == "low":
            # Camera kém - tăng tolerance
            base_thresholds["ear"]["smoothing_window"] = 5
            base_thresholds["combined"]["confidence_threshold"] = 0.6
            
        elif camera_quality == "high":
            # Camera tốt - tăng precision
            base_thresholds["ear"]["smoothing_window"] = 2
            base_thresholds["combined"]["confidence_threshold"] = 0.8
        
        return base_thresholds

# Quick access functions
def get_ear_thresholds(**kwargs) -> Dict[str, Any]:
    """Lấy EAR thresholds với optional overrides"""
    thresholds = OptimizedThresholds.get_category_thresholds("ear")
    thresholds.update(kwargs)
    return thresholds

def get_mar_thresholds(**kwargs) -> Dict[str, Any]:
    """Lấy MAR thresholds với optional overrides""" 
    thresholds = OptimizedThresholds.get_category_thresholds("mar")
    thresholds.update(kwargs)
    return thresholds

def get_head_pose_thresholds(**kwargs) -> Dict[str, Any]:
    """Lấy Head Pose thresholds với optional overrides"""
    thresholds = OptimizedThresholds.get_category_thresholds("head_pose")
    thresholds.update(kwargs)
    return thresholds

if __name__ == "__main__":
    # Test thresholds
    print("=== OPTIMIZED THRESHOLDS ===")
    print(f"EAR blink threshold: {OptimizedThresholds.get_threshold('ear', 'blink_threshold')}")
    print(f"MAR yawn threshold: {OptimizedThresholds.get_threshold('mar', 'yawn_threshold')}")
    print(f"Head pose drowsy threshold: {OptimizedThresholds.get_threshold('head_pose', 'drowsy_threshold')}")
    
    print("\n=== ADAPTIVE THRESHOLDS (Low Light) ===")
    adaptive = OptimizedThresholds.get_adaptive_thresholds("low", "medium")
    print(f"Adaptive EAR blink threshold: {adaptive['ear']['blink_threshold']}")
    print(f"Adaptive MAR yawn threshold: {adaptive['mar']['yawn_threshold']}")