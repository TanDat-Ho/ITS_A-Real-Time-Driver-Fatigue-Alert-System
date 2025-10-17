"""
rule_based.py
-----------------
Rule-based Fatigue Detection Processor

Central state definition and decision making system integrating EAR + MAR + Head Pose:

Integration of three metrics (EAR + MAR + Head Pose):
┌─────────────────┬─────────────────────────┬──────────────────────────┐
│ Behavior        │ Combined Conditions     │ Detection                │
├─────────────────┼─────────────────────────┼──────────────────────────┤
│ Microsleep      │ EAR < 0.2 for ≥1.5s     │ Eyes closed for long     │
├─────────────────┼─────────────────────────┼──────────────────────────┤
│ Prolonged yawn  │ MAR > 0.6 for >1.2s     │ Fatigue                  │
├─────────────────┼─────────────────────────┼──────────────────────────┤
│ Head nodding    │ |pitch| ≤ 15° for>1.5s  │ Drowsy or lost focus     │
└─────────────────┴─────────────────────────┴──────────────────────────┘

If 2 out of 3 conditions occur simultaneously, system triggers high alert (sound/display/log).
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
    """Enum defining alert levels."""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FatigueState(Enum):
    """Enum defining fatigue states."""
    AWAKE = "AWAKE"
    SLIGHTLY_TIRED = "SLIGHTLY_TIRED"
    MODERATELY_TIRED = "MODERATELY_TIRED"
    SEVERELY_TIRED = "SEVERELY_TIRED"
    DANGEROUSLY_DROWSY = "DANGEROUSLY_DROWSY"


class EyeState(Enum):
    """Enum defining eye states."""
    OPEN = "OPEN"
    BLINKING = "BLINKING"
    CLOSING = "CLOSING"
    DROWSY = "DROWSY"


class MouthState(Enum):
    """Enum defining mouth states."""
    CLOSED = "CLOSED"
    SPEAKING = "SPEAKING"
    SLIGHTLY_OPEN = "SLIGHTLY_OPEN"
    WIDE_OPEN = "WIDE_OPEN"
    YAWNING = "YAWNING"


class HeadState(Enum):
    """Enum defining head pose states."""
    NORMAL = "NORMAL"
    SLIGHTLY_TILTED = "SLIGHTLY_TILTED"
    TILTED = "TILTED"
    HEAD_DOWN = "HEAD_DOWN"
    HEAD_DOWN_DROWSY = "HEAD_DOWN_DROWSY"


class RuleBasedFatigueDetector:
    """
    Main class for rule-based fatigue detection combining EAR, MAR, Head Pose.
    This class defines all states and decision logic.
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
        Combine results from 3 detectors to make final decision using state definitions.
        """
        # Analyze individual states using numerical data
        eye_state = self._analyze_eye_state(ear_result)
        mouth_state = self._analyze_mouth_state(mar_result)
        head_state = self._analyze_head_state(head_pose_result)
        
        # Determine alert level based on state combination
        alert_level = self._determine_alert_level(eye_state, mouth_state, head_state)
        
        # Handle critical duration escalation
        if alert_level == AlertLevel.HIGH:
            if self.high_alert_start_time is None:
                self.high_alert_start_time = timestamp
            
            # Check if should escalate to CRITICAL
            alert_duration = timestamp - self.high_alert_start_time
            if alert_duration >= self.critical_duration:
                alert_level = AlertLevel.CRITICAL
        else:
            self.high_alert_start_time = None
        
        # Determine fatigue state and recommendation
        fatigue_state = self._determine_fatigue_state(alert_level)
        recommendation = self._get_recommendation(alert_level, fatigue_state)
        
        # Build alert conditions list
        alert_conditions = []
        if eye_state == EyeState.DROWSY:
            alert_conditions.append("Eyes closed for extended period")
        if mouth_state == MouthState.YAWNING:
            alert_conditions.append("Yawning detected")
        if head_state == HeadState.HEAD_DOWN_DROWSY:
            alert_conditions.append("Head down for extended period")
        
        # Calculate confidence based on severity
        confidence = self._calculate_confidence(eye_state, mouth_state, head_state, alert_level)
        
        # Count total alerts
        if alert_level in [AlertLevel.HIGH, AlertLevel.CRITICAL]:
            self.total_alerts += 1
        
        # Log if there's an alert
        if alert_level != AlertLevel.NONE:
            self.logger.warning(f"Fatigue Alert: {alert_level.value} - {recommendation}")
        
        return {
            "timestamp": timestamp,
            "ear": ear_result,
            "mar": mar_result, 
            "head_pose": head_pose_result,
            "eye_state": eye_state,
            "mouth_state": mouth_state,
            "head_state": head_state,
            "alert_conditions": alert_conditions,
            "alert_level": alert_level,
            "fatigue_state": fatigue_state,
            "confidence": confidence,
            "recommendation": recommendation
        }
    
    def _calculate_confidence(self, eye_state: EyeState, mouth_state: MouthState, head_state: HeadState, alert_level: AlertLevel) -> float:
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
    
    def get_detection_summary(self, time_window: float = 60.0) -> Dict[str, Any]:
        """
        Get detection summary for recent time window.
        
        Args:
            time_window: Time window for calculation (seconds)
            
        Returns:
            Dict containing summary information
        """
        current_time = time.time()
        recent_detections = [
            d for d in self.detection_history 
            if current_time - d["timestamp"] <= time_window
        ]
        
        if not recent_detections:
            return {"status": "No recent data"}
        
        # Count alerts by level
        alert_counts = {level.value: 0 for level in AlertLevel}
        for detection in recent_detections:
            alert_counts[detection["alert_level"].value] += 1
        
        # Calculate average confidence
        avg_confidence = np.mean([d["confidence"] for d in recent_detections])
        
        # Get statistics from sub-detectors
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
        """Reset all session data."""
        reset_ear_state()
        reset_mar_state()
        reset_head_pose_state()
        self.high_alert_start_time = None
        self.detection_history = []
        self.total_alerts = 0
        self.logger.info("Fatigue detection session reset")
    
    def export_session_data(self) -> Dict[str, Any]:
        """Export all session data for analysis."""
        return {
            "detection_history": self.detection_history,
            "ear_statistics": get_ear_statistics(),
            "mar_statistics": get_mar_statistics(),
            "head_pose_statistics": get_head_pose_statistics(),
            "total_alerts": self.total_alerts,
            "session_summary": self.get_detection_summary()
        }
    
    def _analyze_eye_state(self, ear_data: Optional[Dict]) -> EyeState:
        """
        Determine eye state from EAR numerical data.
        
        Args:
            ear_data: Numerical data from EAR calculation
            
        Returns:
            EyeState: Current eye state
        """
        if not ear_data:
            return EyeState.OPEN
            
        if ear_data.get("is_drowsy_duration", False):
            return EyeState.DROWSY
        elif ear_data.get("is_below_threshold", False):
            return EyeState.CLOSING
        elif ear_data.get("consecutive_frames", 0) > 0:
            return EyeState.BLINKING
        else:
            return EyeState.OPEN
    
    def _analyze_mouth_state(self, mar_data: Optional[Dict]) -> MouthState:
        """
        Determine mouth state from MAR numerical data.
        
        Args:
            mar_data: Numerical data from MAR calculation
            
        Returns:
            MouthState: Current mouth state
        """
        if not mar_data:
            return MouthState.CLOSED
            
        if mar_data.get("is_yawn_duration", False):
            return MouthState.YAWNING
        elif mar_data.get("is_above_yawn_threshold", False):
            return MouthState.WIDE_OPEN
        elif mar_data.get("is_above_speaking_threshold", False):
            return MouthState.SPEAKING
        else:
            return MouthState.CLOSED
    
    def _analyze_head_state(self, head_data: Optional[Dict]) -> HeadState:
        """
        Determine head state from head pose numerical data.
        
        Args:
            head_data: Numerical data from head pose calculation
            
        Returns:
            HeadState: Current head state
        """
        if not head_data:
            return HeadState.NORMAL
            
        if head_data.get("is_drowsy_duration", False):
            return HeadState.HEAD_DOWN_DROWSY
        elif head_data.get("is_above_drowsy_threshold", False):
            return HeadState.TILTED
        elif head_data.get("is_above_normal_threshold", False):
            return HeadState.SLIGHTLY_TILTED
        else:
            return HeadState.NORMAL

    def _determine_alert_level(self, eye_state: EyeState, mouth_state: MouthState, head_state: HeadState) -> AlertLevel:
        """
        Determine overall alert level based on individual states.
        
        Args:
            eye_state: Current eye state
            mouth_state: Current mouth state  
            head_state: Current head state
            
        Returns:
            AlertLevel: Overall alert level
        """
        high_risk_conditions = 0
        medium_risk_conditions = 0
        
        # Count high risk conditions
        if eye_state == EyeState.DROWSY:
            high_risk_conditions += 1
        elif eye_state in [EyeState.CLOSING]:
            medium_risk_conditions += 1
            
        if mouth_state == MouthState.YAWNING:
            high_risk_conditions += 1
        elif mouth_state == MouthState.WIDE_OPEN:
            medium_risk_conditions += 1
            
        if head_state == HeadState.HEAD_DOWN_DROWSY:
            high_risk_conditions += 1
        elif head_state in [HeadState.TILTED, HeadState.HEAD_DOWN]:
            medium_risk_conditions += 1
        
        # Determine alert level based on rule combinations
        if high_risk_conditions >= self.combination_threshold:
            return AlertLevel.HIGH
        elif high_risk_conditions >= 1 or medium_risk_conditions >= 2:
            return AlertLevel.MEDIUM
        elif medium_risk_conditions >= 1:
            return AlertLevel.LOW
        else:
            return AlertLevel.NONE
    
    def _determine_fatigue_state(self, alert_level: AlertLevel) -> FatigueState:
        """
        Map alert level to fatigue state.
        
        Args:
            alert_level: Current alert level
            
        Returns:
            FatigueState: Corresponding fatigue state
        """
        mapping = {
            AlertLevel.NONE: FatigueState.AWAKE,
            AlertLevel.LOW: FatigueState.SLIGHTLY_TIRED,
            AlertLevel.MEDIUM: FatigueState.MODERATELY_TIRED,
            AlertLevel.HIGH: FatigueState.SEVERELY_TIRED,
            AlertLevel.CRITICAL: FatigueState.DANGEROUSLY_DROWSY
        }
        return mapping.get(alert_level, FatigueState.AWAKE)
    
    def _get_recommendation(self, alert_level: AlertLevel, fatigue_state: FatigueState) -> str:
        """
        Get recommendation based on current state.
        
        Args:
            alert_level: Current alert level
            fatigue_state: Current fatigue state
            
        Returns:
            str: Recommendation message
        """
        recommendations = {
            AlertLevel.NONE: "Continue driving safely",
            AlertLevel.LOW: "Slight fatigue detected - Stay alert", 
            AlertLevel.MEDIUM: "Moderate fatigue - Take a break soon",
            AlertLevel.HIGH: "High fatigue detected - Consider taking a break",
            AlertLevel.CRITICAL: "STOP DRIVING IMMEDIATELY - Find safe place to rest"
        }
        return recommendations.get(alert_level, "Continue driving safely")
    
    def _calculate_confidence(self, eye_state: EyeState, mouth_state: MouthState, head_state: HeadState, alert_level: AlertLevel) -> float:
        """
        Calculate confidence score based on individual states and alert level.
        
        Args:
            eye_state: Current eye state
            mouth_state: Current mouth state
            head_state: Current head state
            alert_level: Overall alert level
            
        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        base_confidence = {
            AlertLevel.NONE: 0.0,
            AlertLevel.LOW: 0.3,
            AlertLevel.MEDIUM: 0.6,
            AlertLevel.HIGH: 0.8,
            AlertLevel.CRITICAL: 1.0
        }
        
        confidence = base_confidence.get(alert_level, 0.0)
        
        # Boost confidence for severe individual states
        if eye_state == EyeState.DROWSY:
            confidence += 0.1
        if mouth_state == MouthState.YAWNING:
            confidence += 0.1
        if head_state == HeadState.HEAD_DOWN_DROWSY:
            confidence += 0.1
            
        return min(1.0, confidence)


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
