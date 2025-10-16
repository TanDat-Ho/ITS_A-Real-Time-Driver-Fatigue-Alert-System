"""
rule_based.py
-----------------
Rule-based Fatigue Detection Processor

Tích hợp ba chỉ số EAR + MAR + Head Pose để đưa ra quyết định cuối cùng:

Tích hợp ba chỉ số (EAR + MAR + Head Pose):
┌─────────────┬─────────────────────┬──────────────────────┐
│ Biểu hiện   │ Điều kiện kết hợp   │ Nhận diện            │
├─────────────┼─────────────────────┼──────────────────────┤
│ Ngủ gật     │ EAR < 0.2 trong ≥1.5s│ Mắt nhắm lâu        │
├─────────────┼─────────────────────┼──────────────────────┤
│ Ngáp kéo dài│ MAR > 0.6 trong >1.2s│ Mệt mỏi             │
├─────────────┼─────────────────────┼──────────────────────┤
│ Cúi đầu     │ |pitch| ≤ 15° trong>1.5s│ Buồn ngủ hoặc mất tập trung │
└─────────────┴─────────────────────┴──────────────────────┘

Nếu 2 trong 3 điều kiện đồng thời xảy ra, hệ thống phát cảnh báo cấp cao (âm thanh / 
hiển thị / log dữ liệu).
"""

import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import numpy as np

from ..detect_rules.ear import calculate_ear, reset_ear_state, get_ear_statistics
from ..detect_rules.mar import calculate_mar_with_analysis, reset_mar_state, get_mar_statistics  
from ..detect_rules.head_pose import calculate_head_pose_with_analysis, reset_head_pose_state, get_head_pose_statistics


class AlertLevel(Enum):
    """Enum định nghĩa các mức độ cảnh báo."""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FatigueState(Enum):
    """Enum định nghĩa các trạng thái mệt mỏi."""
    AWAKE = "AWAKE"
    SLIGHTLY_TIRED = "SLIGHTLY_TIRED"
    MODERATELY_TIRED = "MODERATELY_TIRED"
    SEVERELY_TIRED = "SEVERELY_TIRED"
    DANGEROUSLY_DROWSY = "DANGEROUSLY_DROWSY"


class RuleBasedFatigueDetector:
    """
    Lớp chính để phát hiện mệt mỏi dựa trên rule-based kết hợp EAR, MAR, Head Pose.
    """
    
    def __init__(self,
                 ear_config: Optional[Dict] = None,
                 mar_config: Optional[Dict] = None,
                 head_pose_config: Optional[Dict] = None,
                 combination_threshold: int = 2,
                 critical_duration: float = 3.0):
        """
        Args:
            ear_config: Cấu hình cho EAR functions
            mar_config: Cấu hình cho MAR functions
            head_pose_config: Cấu hình cho HeadPose functions
            combination_threshold: Số lượng điều kiện tối thiểu để báo HIGH alert
            critical_duration: Thời gian duy trì HIGH alert để chuyển thành CRITICAL
        """
        # Lưu cấu hình để truyền vào functions
        self.ear_config = ear_config or {}
        self.mar_config = mar_config or {}
        self.head_pose_config = head_pose_config or {}
        
        # Cấu hình rule-based
        self.combination_threshold = combination_threshold
        self.critical_duration = critical_duration
        
        # Tracking variables
        self.high_alert_start_time = None
        self.detection_history = []
        self.max_history = 50
        self.total_alerts = 0
        
        # Logging
        self.logger = logging.getLogger("FatigueDetector")
        
    def process_frame(self, 
                     features: Dict[str, List[Tuple[int, int, float]]], 
                     frame_shape: Tuple[int, int]) -> Dict[str, Any]:
        """
        Xử lý một frame và trả về kết quả phát hiện mệt mỏi.
        
        Args:
            features: Các đặc trưng khuôn mặt từ FaceLandmarkDetector
            frame_shape: Kích thước frame (height, width)
            
        Returns:
            Dict chứa tất cả thông tin phát hiện
        """
        timestamp = time.time()
        
        # 1. Tính toán EAR
        ear_result = None
        if features.get("left_eye") and features.get("right_eye"):
            ear_result = calculate_ear(
                features["left_eye"], features["right_eye"], **self.ear_config
            )
        
        # 2. Tính toán MAR
        mar_result = None
        if features.get("mouth"):
            mar_result = calculate_mar_with_analysis(features["mouth"], **self.mar_config)
        
        # 3. Tính toán Head Pose
        head_pose_result = None
        if features:
            head_pose_result = calculate_head_pose_with_analysis(features, frame_shape, **self.head_pose_config)
        
        # 4. Kết hợp các kết quả
        combined_result = self._combine_results(ear_result, mar_result, head_pose_result, timestamp)
        
        # 5. Lưu vào lịch sử
        self.detection_history.append(combined_result)
        if len(self.detection_history) > self.max_history:
            self.detection_history.pop(0)
        
        return combined_result
    
    def _combine_results(self, 
                        ear_result: Optional[Dict], 
                        mar_result: Optional[Dict], 
                        head_pose_result: Optional[Dict],
                        timestamp: float) -> Dict[str, Any]:
        """
        Kết hợp kết quả từ 3 detector để đưa ra quyết định cuối cùng.
        """
        # Khởi tạo kết quả
        result = {
            "timestamp": timestamp,
            "ear": ear_result,
            "mar": mar_result, 
            "head_pose": head_pose_result,
            "alert_conditions": [],
            "alert_level": AlertLevel.NONE,
            "fatigue_state": FatigueState.AWAKE,
            "confidence": 0.0,
            "recommendation": "Continue driving safely"
        }
        
        # Đếm số điều kiện báo động
        high_alert_conditions = 0
        medium_alert_conditions = 0
        
        # Kiểm tra EAR
        if ear_result and ear_result["alert_level"] == "HIGH":
            high_alert_conditions += 1
            result["alert_conditions"].append("Eyes closed for extended period")
        elif ear_result and ear_result["alert_level"] == "MEDIUM":
            medium_alert_conditions += 1
        
        # Kiểm tra MAR  
        if mar_result and mar_result["alert_level"] == "HIGH":
            high_alert_conditions += 1
            result["alert_conditions"].append("Yawning detected")
        elif mar_result and mar_result["alert_level"] == "MEDIUM":
            medium_alert_conditions += 1
        
        # Kiểm tra Head Pose
        if head_pose_result and head_pose_result["alert_level"] == "HIGH":
            high_alert_conditions += 1
            result["alert_conditions"].append("Head down for extended period")
        elif head_pose_result and head_pose_result["alert_level"] == "MEDIUM":
            medium_alert_conditions += 1
        
        # Xác định mức độ cảnh báo dựa trên rule-based
        if high_alert_conditions >= self.combination_threshold:
            # HIGH alert khi có ít nhất 2/3 điều kiện nghiêm trọng
            result["alert_level"] = AlertLevel.HIGH
            result["fatigue_state"] = FatigueState.SEVERELY_TIRED
            result["confidence"] = min(1.0, high_alert_conditions / 3.0 + 0.3)
            
            # Bắt đầu đếm thời gian HIGH alert
            if self.high_alert_start_time is None:
                self.high_alert_start_time = timestamp
                
            # Kiểm tra có chuyển thành CRITICAL không
            alert_duration = timestamp - self.high_alert_start_time
            if alert_duration >= self.critical_duration:
                result["alert_level"] = AlertLevel.CRITICAL
                result["fatigue_state"] = FatigueState.DANGEROUSLY_DROWSY
                result["confidence"] = 1.0
                result["recommendation"] = "STOP DRIVING IMMEDIATELY - Find safe place to rest"
            else:
                result["recommendation"] = "High fatigue detected - Consider taking a break"
                
        elif high_alert_conditions >= 1 or medium_alert_conditions >= 2:
            # MEDIUM alert
            result["alert_level"] = AlertLevel.MEDIUM
            result["fatigue_state"] = FatigueState.MODERATELY_TIRED
            result["confidence"] = min(0.8, (high_alert_conditions + medium_alert_conditions * 0.5) / 3.0 + 0.2)
            result["recommendation"] = "Moderate fatigue - Take a break soon"
            self.high_alert_start_time = None
            
        elif medium_alert_conditions >= 1:
            # LOW alert
            result["alert_level"] = AlertLevel.LOW
            result["fatigue_state"] = FatigueState.SLIGHTLY_TIRED
            result["confidence"] = min(0.5, medium_alert_conditions / 3.0 + 0.1)
            result["recommendation"] = "Slight fatigue detected - Stay alert"
            self.high_alert_start_time = None
            
        else:
            # NONE alert
            result["alert_level"] = AlertLevel.NONE
            result["fatigue_state"] = FatigueState.AWAKE
            result["confidence"] = 0.0
            result["recommendation"] = "Continue driving safely"
            self.high_alert_start_time = None
        
        # Cập nhật số lượng cảnh báo
        if result["alert_level"] in [AlertLevel.HIGH, AlertLevel.CRITICAL]:
            self.total_alerts += 1
        
        # Log nếu có cảnh báo
        if result["alert_level"] != AlertLevel.NONE:
            self.logger.warning(f"Fatigue Alert: {result['alert_level'].value} - {result['recommendation']}")
        
        return result
    
    def get_detection_summary(self, time_window: float = 60.0) -> Dict[str, Any]:
        """
        Lấy tóm tắt phát hiện trong khoảng thời gian gần đây.
        
        Args:
            time_window: Cửa sổ thời gian tính toán (giây)
            
        Returns:
            Dict chứa thông tin tóm tắt
        """
        current_time = time.time()
        recent_detections = [
            d for d in self.detection_history 
            if current_time - d["timestamp"] <= time_window
        ]
        
        if not recent_detections:
            return {"status": "No recent data"}
        
        # Thống kê alerts
        alert_counts = {level.value: 0 for level in AlertLevel}
        for detection in recent_detections:
            alert_counts[detection["alert_level"].value] += 1
        
        # Tính confidence trung bình
        avg_confidence = np.mean([d["confidence"] for d in recent_detections])
        
        # Lấy thống kê từ các detector con
        ear_stats = get_ear_statistics()
        mar_stats = get_mar_statistics()
        head_pose_stats = get_head_pose_statistics()
        
        return {
            "time_window": time_window,
            "total_detections": len(recent_detections),
            "alert_distribution": alert_counts,
            "average_confidence": avg_confidence,
            "total_alerts_session": self.total_alerts,
            "ear_statistics": ear_stats,
            "mar_statistics": mar_stats,
            "head_pose_statistics": head_pose_stats,
            "latest_state": recent_detections[-1]["fatigue_state"].value if recent_detections else "UNKNOWN"
        }
    
    def reset_session(self):
        """Reset tất cả dữ liệu session."""
        reset_ear_state()
        reset_mar_state()
        reset_head_pose_state()
        self.high_alert_start_time = None
        self.detection_history = []
        self.total_alerts = 0
        self.logger.info("Fatigue detection session reset")
    
    def export_session_data(self) -> Dict[str, Any]:
        """Export toàn bộ dữ liệu session để phân tích."""
        return {
            "detection_history": self.detection_history,
            "ear_statistics": self.ear_calculator.get_statistics(),
            "mar_statistics": self.mar_calculator.get_statistics(),
            "head_pose_statistics": self.head_pose_estimator.get_statistics(),
            "total_alerts": self.total_alerts,
            "session_summary": self.get_detection_summary()
        }


class FatigueDetectionConfig:
    """Lớp cấu hình cho FatigueDetector."""
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Lấy cấu hình mặc định."""
        return {
            "ear_config": {
                "blink_threshold": 0.2,
                "blink_frames": 3,
                "drowsy_threshold": 0.2,
                "drowsy_duration": 1.5
            },
            "mar_config": {
                "yawn_threshold": 0.6,
                "yawn_duration": 1.2,
                "speaking_threshold": 0.4
            },
            "head_pose_config": {
                "normal_threshold": 10.0,
                "drowsy_threshold": 15.0,
                "drowsy_duration": 1.5
            },
            "combination_threshold": 2,
            "critical_duration": 3.0
        }
    
    @staticmethod
    def get_sensitive_config() -> Dict[str, Any]:
        """Cấu hình nhạy cảm hơn (phát hiện sớm hơn)."""
        config = FatigueDetectionConfig.get_default_config()
        config["ear_config"]["drowsy_duration"] = 1.0
        config["mar_config"]["yawn_duration"] = 0.8
        config["head_pose_config"]["drowsy_duration"] = 1.0
        config["combination_threshold"] = 1
        config["critical_duration"] = 2.0
        return config
    
    @staticmethod
    def get_conservative_config() -> Dict[str, Any]:
        """Cấu hình bảo thủ hơn (ít false positive)."""
        config = FatigueDetectionConfig.get_default_config()
        config["ear_config"]["drowsy_duration"] = 2.5
        config["mar_config"]["yawn_duration"] = 2.0
        config["head_pose_config"]["drowsy_duration"] = 2.5
        config["combination_threshold"] = 3
        config["critical_duration"] = 5.0
        return config


if __name__ == "__main__":
    # Test với dữ liệu mẫu
    config = FatigueDetectionConfig.get_default_config()
    detector = RuleBasedFatigueDetector(**config)
    
    # Mock features
    mock_features = {
        "left_eye": [(33, 160, 0.0), (160, 158, 0.0), (158, 133, 0.0), (133, 153, 0.0), (153, 144, 0.0), (144, 33, 0.0)],
        "right_eye": [(362, 385, 0.0), (385, 387, 0.0), (387, 263, 0.0), (263, 373, 0.0), (373, 380, 0.0), (380, 362, 0.0)],
        "mouth": [(61, 84, 0.0), (13, 82, 0.0), (14, 82, 0.0), (291, 84, 0.0), (17, 86, 0.0), (18, 86, 0.0)],
        "nose": [(320, 240, 0.0)],
        "face_outline": [(300, 400, 0.0), (340, 400, 0.0), (320, 420, 0.0), (320, 450, 0.0)]
    }
    
    # Test detection
    result = detector.process_frame(mock_features, (480, 640))
    
    print(f"Alert Level: {result['alert_level'].value}")
    print(f"Fatigue State: {result['fatigue_state'].value}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Alert Conditions: {result['alert_conditions']}")
    
    # Test summary
    summary = detector.get_detection_summary()
    print(f"\nSession Summary: {summary['latest_state']}")
