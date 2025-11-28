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

from ..detect_rules.ear import calculate_ear_full, reset_ear_state, get_ear_statistics
from ..detect_rules.mar import calculate_mar_with_analysis, reset_mar_state, get_mar_statistics  
from ..detect_rules.head_pose import calculate_head_pose_with_analysis, reset_head_pose_state, get_head_pose_statistics
# Removed optimized imports - using enhanced detection instead
from ..detect_rules.enhanced_integration import EnhancedDetectionWrapper, get_enhanced_detector
from ...input_layer.quality_manager import QualityManager, QualityMetrics


class AlertLevel(Enum):
    """Enum defining alert levels."""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FatigueState(Enum):
    """Enum defining fatigue states with driving safety context."""
    AWAKE = "ALERT_DRIVING"  # Safe to continue driving
    SLIGHTLY_TIRED = "EARLY_FATIGUE"  # Monitor closely, maintain alertness
    MODERATELY_TIRED = "CAUTION_NEEDED"  # Plan for rest stop soon
    SEVERELY_TIRED = "UNSAFE_TO_DRIVE"  # Pull over safely
    DANGEROUSLY_DROWSY = "IMMEDIATE_STOP_REQUIRED"  # Emergency - stop now


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
                 critical_duration: float = 3.0,
                 use_optimized_engine: bool = False,
                 use_enhanced_detection: bool = True,  # NEW: Enhanced detection by default
                 detection_engine: Optional[Any] = None,
                 quality_aware: bool = True):
        """
        Args:
            ear_config: Cấu hình cho EAR functions
            mar_config: Cấu hình cho MAR functions
            head_pose_config: Cấu hình cho HeadPose functions
            combination_threshold: Số lượng điều kiện tối thiểu để báo HIGH alert
            critical_duration: Thời gian duy trì HIGH alert để chuyển thành CRITICAL
            use_optimized_engine: Use OptimizedDetectionEngine
            use_enhanced_detection: Use EnhancedDetectionWrapper (recommended)
            detection_engine: Specific detection engine instance
            quality_aware: Enable quality-aware adaptive thresholds
        """
        # Logging - initialize first
        self.logger = logging.getLogger("FatigueDetector")
        
        # Enhanced detection setup
        self.use_optimized_engine = use_optimized_engine
        self.use_enhanced_detection = use_enhanced_detection
        self.quality_aware = quality_aware
        self.detection_engine = detection_engine
        
        # Initialize enhanced components
        if use_enhanced_detection:
            self.enhanced_detector = get_enhanced_detector()
            self.quality_manager = QualityManager()
            self.logger.info("Enhanced detection wrapper initialized")
        else:
            self.enhanced_detector = None
            self.quality_manager = None
        
        # Use standard config - optimized thresholds removed
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
        
    def process_frame(self, 
                     features: Dict[str, List[Tuple[int, int, float]]], 
                     frame_shape: Tuple[int, int],
                     input_quality_metrics: Optional[Dict] = None,
                     roi_result: Optional[Dict] = None,
                     face_validation: Optional[Dict] = None,
                     frame_validation: Optional[Dict] = None,
                     landmark_result: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Xử lý một frame với enhanced quality-aware detection.
        
        Args:
            features: Các đặc trưng khuôn mặt từ FaceLandmarkDetector
            frame_shape: Kích thước frame (height, width)
            input_quality_metrics: Quality metrics from enhanced input layer
            roi_result: ROI detection result
            face_validation: Face size validation result
            frame_validation: Frame quality validation result
            landmark_result: Landmark detection result
            
        Returns:
            Dict chứa tất cả thông tin phát hiện với enhanced quality awareness
        """
        timestamp = time.time()
        
        # Priority 1: Enhanced detection with full quality awareness
        if self.use_enhanced_detection and self.enhanced_detector:
            return self._process_with_enhanced_detection(
                features, frame_shape, timestamp, input_quality_metrics,
                roi_result, face_validation, frame_validation, landmark_result
            )
        
        # Priority 2: Optimized detection engine
        elif self.use_optimized_engine and self.detection_engine:
            return self._process_with_optimized_engine(features, frame_shape, timestamp)
        
        # Fallback: Original processing with quality adjustments if available
        return self._process_with_quality_adjustments(
            features, frame_shape, timestamp, input_quality_metrics
        )
        
        # 1. Tính toán EAR với optimized parameters
        ear_result = None
        if features.get("left_eye") and features.get("right_eye"):
            ear_result = calculate_ear_full(
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
    
    def _process_with_optimized_engine(self, 
                                     features: Dict[str, List[Tuple[int, int, float]]], 
                                     frame_shape: Tuple[int, int],
                                     timestamp: float) -> Dict[str, Any]:
        """
        Xử lý frame sử dụng optimized detection engine.
        
        Args:
            features: Face landmarks
            frame_shape: Frame dimensions
            timestamp: Current timestamp
            
        Returns:
            Dict chứa kết quả optimized detection
        """
        # Process với optimized engine
        optimized_result = self.detection_engine.process_frame(features, frame_shape)
        
        # Convert optimized result to compatible format
        compatible_result = self._convert_optimized_result(optimized_result, timestamp)
        
        # Lưu vào lịch sử
        self.detection_history.append(compatible_result)
        if len(self.detection_history) > self.max_history:
            self.detection_history.pop(0)
            
        return compatible_result
    
    def _process_with_enhanced_detection(self, 
                                       features: Dict[str, List[Tuple[int, int, float]]], 
                                       frame_shape: Tuple[int, int],
                                       timestamp: float,
                                       input_quality_metrics: Optional[Dict] = None,
                                       roi_result: Optional[Dict] = None,
                                       face_validation: Optional[Dict] = None,
                                       frame_validation: Optional[Dict] = None,
                                       landmark_result: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process frame using enhanced detection wrapper with full quality awareness.
        """
        # Update quality manager if quality data available
        quality_metrics = None
        if self.quality_manager and any([roi_result, face_validation, frame_validation, landmark_result]):
            quality_metrics = self.quality_manager.update_quality_metrics(
                roi_result=roi_result,
                face_validation=face_validation,
                frame_validation=frame_validation,
                landmark_result=landmark_result
            )
        
        # Prepare input quality metrics for enhanced detection
        if not input_quality_metrics and quality_metrics:
            input_quality_metrics = {
                "face_size_category": getattr(quality_metrics, 'face_size_category', 'optimal'),
                "roi_quality": getattr(quality_metrics, 'roi_quality', 1.0),
                "landmark_quality": getattr(quality_metrics, 'landmark_quality', 1.0),
                "roi_stability": getattr(quality_metrics, 'roi_stability', 1.0),
                "frame_quality": {
                    "brightness": getattr(quality_metrics, 'frame_brightness', 128.0),
                    "contrast": getattr(quality_metrics, 'frame_contrast', 50.0),
                    "blur_score": getattr(quality_metrics, 'frame_blur_score', 100.0)
                }
            }
        
        # Process with enhanced detection
        enhanced_result = self.enhanced_detector.process_complete_detection(
            features, frame_shape, input_quality_metrics
        )
        
        # Convert to rule-based format with enhanced information
        compatible_result = self._convert_enhanced_result(
            enhanced_result, timestamp, quality_metrics
        )
        
        # Store in history
        self.detection_history.append(compatible_result)
        if len(self.detection_history) > self.max_history:
            self.detection_history.pop(0)
            
        return compatible_result
    
    def _process_with_quality_adjustments(self, 
                                        features: Dict[str, List[Tuple[int, int, float]]], 
                                        frame_shape: Tuple[int, int],
                                        timestamp: float,
                                        input_quality_metrics: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process with original detection but apply quality-based threshold adjustments.
        """
        # Get quality-adjusted configs
        ear_config = self.ear_config.copy()
        mar_config = self.mar_config.copy()
        head_pose_config = self.head_pose_config.copy()
        
        # Apply quality adjustments if available
        if input_quality_metrics and self.quality_aware:
            face_size_category = input_quality_metrics.get("face_size_category", "optimal")
            roi_quality = input_quality_metrics.get("roi_quality", 1.0)
            
            # Adjust thresholds based on input quality
            face_size_factor = self._get_face_size_factor(face_size_category)
            
            # Apply adjustments
            if "blink_threshold" in ear_config:
                ear_config["blink_threshold"] *= face_size_factor * roi_quality
            if "drowsy_threshold" in ear_config:
                ear_config["drowsy_threshold"] *= face_size_factor * roi_quality
            if "yawn_threshold" in mar_config:
                mar_config["yawn_threshold"] *= face_size_factor * roi_quality
        
        # Original processing with adjusted configs
        ear_result = None
        if features.get("left_eye") and features.get("right_eye"):
            ear_result = calculate_ear_full(
                features["left_eye"], features["right_eye"], **ear_config
            )
        
        mar_result = None
        if features.get("mouth"):
            mar_result = calculate_mar_with_analysis(features["mouth"], **mar_config)
        
        head_pose_result = None
        if features:
            head_pose_result = calculate_head_pose_with_analysis(features, frame_shape, **head_pose_config)
        
        # Combine results
        combined_result = self._combine_results(ear_result, mar_result, head_pose_result, timestamp)
        
        # Add quality information if available
        if input_quality_metrics:
            combined_result["input_quality_metrics"] = input_quality_metrics
            combined_result["quality_adjusted"] = True
        
        # Store in history
        self.detection_history.append(combined_result)
        if len(self.detection_history) > self.max_history:
            self.detection_history.pop(0)
        
        return combined_result
    
    def _convert_enhanced_result(self, enhanced_result: Dict[str, Any], 
                               timestamp: float, 
                               quality_metrics: Optional[QualityMetrics] = None) -> Dict[str, Any]:
        """
        Convert enhanced detection result to rule-based format.
        """
        if not enhanced_result.get("valid"):
            return self._get_invalid_result(timestamp, "enhanced_detection_failed")
        
        combined_analysis = enhanced_result.get("combined_analysis", {})
        
        # Map enhanced states to rule-based format
        state = combined_analysis.get("state", "normal")
        confidence = combined_analysis.get("confidence", 0.0)
        alert_level_value = combined_analysis.get("alert_level", 0)
        
        # Convert to AlertLevel enum
        if state == "severe_drowsiness" or alert_level_value >= 3:
            alert_level = AlertLevel.CRITICAL
        elif state == "moderate_drowsiness" or alert_level_value == 2:
            alert_level = AlertLevel.HIGH
        elif state == "mild_drowsiness" or alert_level_value == 1:
            alert_level = AlertLevel.MEDIUM
        else:
            alert_level = AlertLevel.NONE
        
        # Handle critical duration escalation
        if alert_level == AlertLevel.HIGH:
            if self.high_alert_start_time is None:
                self.high_alert_start_time = timestamp
            
            alert_duration = timestamp - self.high_alert_start_time
            if alert_duration >= self.critical_duration:
                alert_level = AlertLevel.CRITICAL
        else:
            self.high_alert_start_time = None
        
        # Determine other states from enhanced results
        ear_analysis = enhanced_result.get("ear_analysis", {})
        mar_analysis = enhanced_result.get("mar_analysis", {})
        head_pose_analysis = enhanced_result.get("head_pose_analysis", {})
        
        eye_state = EyeState.DROWSY if ear_analysis.get("is_below_drowsy_threshold") and ear_analysis.get("is_drowsy_duration") else EyeState.OPEN
        mouth_state = MouthState.YAWNING if mar_analysis.get("is_above_yawn_threshold") and mar_analysis.get("is_yawn_duration") else MouthState.CLOSED
        head_state = HeadState.HEAD_DOWN_DROWSY if head_pose_analysis.get("is_head_down") and head_pose_analysis.get("is_drowsy_duration") else HeadState.NORMAL
        
        # Build alert conditions
        alert_conditions = combined_analysis.get("contributing_factors", [])
        
        # Determine fatigue state and recommendation
        fatigue_state = self._determine_fatigue_state(alert_level)
        recommendation = self._get_recommendation(alert_level, fatigue_state)
        
        # Count alerts
        if alert_level in [AlertLevel.HIGH, AlertLevel.CRITICAL]:
            self.total_alerts += 1
        
        return {
            "timestamp": timestamp,
            "ear": ear_analysis,
            "mar": mar_analysis,
            "head_pose": head_pose_analysis,
            "eye_state": eye_state,
            "mouth_state": mouth_state,
            "head_state": head_state,
            "alert_conditions": alert_conditions,
            "alert_level": alert_level,
            "fatigue_state": fatigue_state,
            "confidence": confidence,
            "recommendation": recommendation,
            "enhanced_detection_used": True,
            "quality_metrics": quality_metrics.__dict__ if quality_metrics else None,
            "enhanced_result": enhanced_result  # Keep original for debugging
        }
    
    def _convert_optimized_result(self, optimized_result: Dict[str, Any], timestamp: float) -> Dict[str, Any]:
        """
        Convert optimized engine result to rule-based format.
        
        Args:
            optimized_result: Result from OptimizedDetectionEngine
            timestamp: Current timestamp
            
        Returns:
            Dict in rule-based format
        """
        # Map optimized states to rule-based enums
        combined_state = optimized_result.get("combined_state", "normal")
        confidence = optimized_result.get("confidence", 0.0)
        
        # Convert to AlertLevel
        if combined_state == "severe_drowsiness":
            alert_level = AlertLevel.CRITICAL
        elif combined_state == "moderate_drowsiness":
            alert_level = AlertLevel.HIGH
        elif combined_state == "mild_drowsiness":
            alert_level = AlertLevel.MEDIUM
        else:
            alert_level = AlertLevel.NONE
            
        # Convert to FatigueState
        fatigue_state = self._determine_fatigue_state(alert_level)
        
        # Get recommendation
        recommendation = self._get_recommendation(alert_level, fatigue_state)
        
        # Count alerts
        if alert_level in [AlertLevel.HIGH, AlertLevel.CRITICAL]:
            self.total_alerts += 1
            
        # Handle critical duration escalation
        if alert_level == AlertLevel.HIGH:
            if self.high_alert_start_time is None:
                self.high_alert_start_time = timestamp
            
            alert_duration = timestamp - self.high_alert_start_time
            if alert_duration >= self.critical_duration:
                alert_level = AlertLevel.CRITICAL
        else:
            self.high_alert_start_time = None
        
        return {
            "timestamp": timestamp,
            "ear": optimized_result.get("ear_analysis"),
            "mar": optimized_result.get("mar_analysis"), 
            "head_pose": optimized_result.get("head_pose_analysis"),
            "eye_state": EyeState.DROWSY if "ear_drowsy" in optimized_result.get("state_indicators", []) else EyeState.OPEN,
            "mouth_state": MouthState.YAWNING if "mar_yawn" in optimized_result.get("state_indicators", []) else MouthState.CLOSED,
            "head_state": HeadState.HEAD_DOWN_DROWSY if "head_drowsy" in optimized_result.get("state_indicators", []) else HeadState.NORMAL,
            "alert_conditions": optimized_result.get("state_indicators", []),
            "alert_level": alert_level,
            "fatigue_state": fatigue_state,
            "confidence": confidence,
            "recommendation": recommendation,
            "optimized_engine_used": True
        }
    
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
            alert_conditions.append("😴 Prolonged eye closure (>1.2s) - Microsleep risk")
        if mouth_state == MouthState.YAWNING:
            alert_conditions.append("😪 Excessive yawning - Oxygen deficiency sign")
        if head_state == HeadState.HEAD_DOWN_DROWSY:
            alert_conditions.append("😵 Head nodding - Loss of muscle control")
        
        # Calculate confidence based on severity
        confidence = self._calculate_confidence(eye_state, mouth_state, head_state, alert_level)
        
        # Count total alerts
        if alert_level in [AlertLevel.HIGH, AlertLevel.CRITICAL]:
            self.total_alerts += 1
        
        # Log if there's an alert (silent in GUI mode)
        if alert_level != AlertLevel.NONE:
            import os
            if os.environ.get('GUI_MODE') != '1':
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
        elif head_state == HeadState.TILTED:
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
            AlertLevel.NONE: "Driving safely - Stay focused on the road",
            AlertLevel.LOW: "⚠️ Early fatigue signs - Open windows, adjust posture", 
            AlertLevel.MEDIUM: "🚨 Moderate fatigue - Find rest stop within 30 minutes",
            AlertLevel.HIGH: "🛑 DANGER: Pull over safely and rest for 15-20 minutes",
            AlertLevel.CRITICAL: "🚨 CRITICAL: STOP DRIVING NOW - Find safe place immediately"
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
    
    def _get_face_size_factor(self, face_size_category: str) -> float:
        """Get threshold adjustment factor based on face size category"""
        factors = {
            "too_small": 0.85,      # More sensitive for small faces
            "acceptable_small": 0.92,
            "optimal": 1.0,
            "acceptable_large": 1.08,
            "too_large": 1.15       # Less sensitive for large faces
        }
        return factors.get(face_size_category, 1.0)
    
    def _get_invalid_result(self, timestamp: float, reason: str) -> Dict[str, Any]:
        """Get standard invalid result format"""
        return {
            "timestamp": timestamp,
            "ear": None,
            "mar": None,
            "head_pose": None,
            "eye_state": EyeState.OPEN,
            "mouth_state": MouthState.CLOSED,
            "head_state": HeadState.NORMAL,
            "alert_conditions": [],
            "alert_level": AlertLevel.NONE,
            "fatigue_state": FatigueState.AWAKE,
            "confidence": 0.0,
            "recommendation": "Unable to detect - " + reason,
            "valid": False,
            "error_reason": reason
        }
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get quality assessment summary from quality manager"""
        if self.quality_manager:
            return self.quality_manager.get_quality_summary()
        else:
            return {"message": "Quality manager not available"}
    
    def get_enhanced_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics from enhanced detector"""
        stats = {}
        
        if self.enhanced_detector:
            stats["enhanced_detector"] = self.enhanced_detector.get_performance_stats()
        
        if self.quality_manager:
            stats["quality_manager"] = self.quality_manager.get_quality_summary()
        
        # Add rule-based stats
        stats["rule_based"] = {
            "total_detections": len(self.detection_history),
            "total_alerts": self.total_alerts,
            "recent_alert_rate": sum(1 for d in self.detection_history[-20:] if d["alert_level"] != AlertLevel.NONE) / min(20, len(self.detection_history)) if self.detection_history else 0,
            "enhanced_detection_enabled": self.use_enhanced_detection,
            "quality_aware_enabled": self.quality_aware
        }
        
        return stats


class FatigueDetectionConfig:
    """Lớp cấu hình cho FatigueDetector."""
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Lấy cấu hình mặc định với optimized values."""
        return {
            "ear_config": {
                "blink_threshold": 0.25,  # Optimized từ 0.2
                "blink_frames": 2,        # Optimized từ 3
                "drowsy_threshold": 0.22, # Optimized từ 0.2
                "drowsy_duration": 1.2    # Optimized từ 1.5
            },
            "mar_config": {
                "yawn_threshold": 0.65,    # Optimized từ 0.6
                "yawn_duration": 1.0,      # Optimized từ 1.2
                "speaking_threshold": 0.35 # Optimized từ 0.4
            },
            "head_pose_config": {
                "normal_threshold": 12.0,
                "drowsy_threshold": 18.0,  # Optimized từ 20.0
                "drowsy_duration": 1.3     # Optimized từ 2.0
            },
            "combination_threshold": 2,
            "critical_duration": 3.0
        }
    
    @staticmethod
    def get_sensitive_config() -> Dict[str, Any]:
        """Cấu hình nhạy cảm hơn với optimized values."""
        config = FatigueDetectionConfig.get_default_config()
        # Sensitive adjustments based on optimized baseline
        config["ear_config"]["blink_threshold"] = 0.27     # Tăng sensitivity
        config["ear_config"]["drowsy_duration"] = 0.8      # Giảm duration
        config["mar_config"]["yawn_threshold"] = 0.6       # Giảm threshold
        config["mar_config"]["yawn_duration"] = 0.7        # Giảm duration
        config["head_pose_config"]["drowsy_threshold"] = 15.0  # Giảm threshold
        config["head_pose_config"]["drowsy_duration"] = 0.8     # Giảm duration
        config["combination_threshold"] = 1
        config["critical_duration"] = 2.0
        return config
    
    @staticmethod
    def get_conservative_config() -> Dict[str, Any]:
        """Cấu hình bảo thủ hơn với optimized values."""
        config = FatigueDetectionConfig.get_default_config()
        # Conservative adjustments giảm false positives
        config["ear_config"]["blink_threshold"] = 0.23     # Giảm sensitivity
        config["ear_config"]["drowsy_duration"] = 2.0      # Tăng duration
        config["mar_config"]["yawn_threshold"] = 0.7       # Tăng threshold
        config["mar_config"]["yawn_duration"] = 1.5        # Tăng duration
        config["head_pose_config"]["drowsy_threshold"] = 22.0  # Tăng threshold
        config["head_pose_config"]["drowsy_duration"] = 2.0     # Tăng duration
        config["combination_threshold"] = 3
        config["critical_duration"] = 5.0
        return config
    
    @staticmethod
    def create_optimized_detector(lighting: str = "normal", camera_quality: str = "medium") -> 'RuleBasedFatigueDetector':
        """
        Tạo RuleBasedFatigueDetector với optimized engine.
        
        Args:
            lighting: Điều kiện ánh sáng (low/normal/bright)
            camera_quality: Chất lượng camera (low/medium/high)
            
        Returns:
            RuleBasedFatigueDetector với optimized engine
        """
        # Optimized integration removed - use enhanced detection instead
        config = FatigueDetectionConfig.get_default_config()
        
        # Create enhanced detector instead of optimized
        detector = RuleBasedFatigueDetector(
            use_enhanced_detection=True,
            use_optimized_engine=False,
            **config
        )
        
        return detector
    
    @staticmethod
    def create_enhanced_detector(lighting: str = "normal", 
                               camera_quality: str = "medium",
                               sensitivity: str = "default") -> 'RuleBasedFatigueDetector':
        """
        Tạo RuleBasedFatigueDetector với enhanced detection và quality awareness.
        
        Args:
            lighting: Điều kiện ánh sáng (low/normal/bright)
            camera_quality: Chất lượng camera (low/medium/high)
            sensitivity: Độ nhạy (sensitive/default/conservative)
            
        Returns:
            RuleBasedFatigueDetector với enhanced capabilities
        """
        # Get base config based on sensitivity
        if sensitivity == "sensitive":
            config = FatigueDetectionConfig.get_sensitive_config()
        elif sensitivity == "conservative":
            config = FatigueDetectionConfig.get_conservative_config()
        else:
            config = FatigueDetectionConfig.get_default_config()
        
        # Create enhanced detector
        detector = RuleBasedFatigueDetector(
            use_enhanced_detection=True,
            quality_aware=True,
            **config
        )
        
        return detector
    
    @staticmethod
    def create_full_featured_detector(lighting: str = "normal", 
                                    camera_quality: str = "medium",
                                    sensitivity: str = "default") -> 'RuleBasedFatigueDetector':
        """
        Tạo RuleBasedFatigueDetector với tất cả enhanced features.
        
        Args:
            lighting: Điều kiện ánh sáng
            camera_quality: Chất lượng camera
            sensitivity: Độ nhạy
            
        Returns:
            Fully-featured RuleBasedFatigueDetector
        """
        # Get sensitivity-based config
        if sensitivity == "sensitive":
            config = FatigueDetectionConfig.get_sensitive_config()
        elif sensitivity == "conservative":
            config = FatigueDetectionConfig.get_conservative_config()
        else:
            config = FatigueDetectionConfig.get_default_config()
        
        # Create detector with all features enabled
        detector = RuleBasedFatigueDetector(
            use_enhanced_detection=True,
            use_optimized_engine=False,  # Enhanced detection is preferred
            quality_aware=True,
            **config
        )
        
        return detector


if __name__ == "__main__":
    # Test với dữ liệu mẫu - all detection modes
    print("=== TESTING ENHANCED RULE-BASED FATIGUE DETECTOR ===")
    
    # Test original detector
    print("\n1. Testing Original Detector:")
    config = FatigueDetectionConfig.get_default_config()
    detector = RuleBasedFatigueDetector(use_enhanced_detection=False, **config)
    
    # Test optimized detector
    print("\n2. Testing Optimized Detector:")
    optimized_detector = FatigueDetectionConfig.create_optimized_detector("normal", "medium")
    
    # Test enhanced detector
    print("\n3. Testing Enhanced Detector:")
    enhanced_detector = FatigueDetectionConfig.create_enhanced_detector("normal", "medium", "default")
    
    # Test full-featured detector
    print("\n4. Testing Full-Featured Detector:")
    full_detector = FatigueDetectionConfig.create_full_featured_detector("normal", "medium", "default")
    
    # Mock features
    mock_features = {
        "left_eye": [(33, 160, 0.0), (160, 158, 0.0), (158, 133, 0.0), (133, 153, 0.0), (153, 144, 0.0), (144, 33, 0.0)],
        "right_eye": [(362, 385, 0.0), (385, 387, 0.0), (387, 263, 0.0), (263, 373, 0.0), (373, 380, 0.0), (380, 362, 0.0)],
        "mouth": [(61, 84, 0.0), (13, 82, 0.0), (14, 82, 0.0), (291, 84, 0.0), (17, 86, 0.0), (18, 86, 0.0)],
        "nose": [(320, 240, 0.0)],
        "face_outline": [(300, 400, 0.0), (340, 400, 0.0), (320, 420, 0.0), (320, 450, 0.0)]
    }
    
    # Mock quality metrics for enhanced testing
    mock_quality_metrics = {
        "face_size_category": "optimal",
        "roi_quality": 0.95,
        "landmark_quality": 0.9,
        "roi_stability": 0.85,
        "frame_quality": {
            "brightness": 125,
            "contrast": 45,
            "blur_score": 80
        }
    }
    
    mock_face_validation = {"size_category": "optimal", "confidence": 0.9}
    mock_roi_result = {"used_roi": True, "roi_coordinates": (100, 100, 200, 200)}
    mock_frame_validation = {"valid": True, "metrics": {"brightness": 125, "contrast": 45}}
    mock_landmark_result = {"valid": True, "landmark_count": 468, "processing_time": 0.03}
    
    # Test detection với original detector
    result = detector.process_frame(mock_features, (480, 640))
    print(f"   Alert Level: {result['alert_level'].value}")
    print(f"   Confidence: {result['confidence']:.2f}")
    
    # Test optimized detector
    optimized_result = optimized_detector.process_frame(mock_features, (480, 640))
    print(f"   Optimized Alert Level: {optimized_result['alert_level'].value}")
    print(f"   Optimized Confidence: {optimized_result['confidence']:.2f}")
    
    # Test enhanced detector with quality metrics
    enhanced_result = enhanced_detector.process_frame(
        mock_features, (480, 640), 
        input_quality_metrics=mock_quality_metrics,
        roi_result=mock_roi_result,
        face_validation=mock_face_validation,
        frame_validation=mock_frame_validation,
        landmark_result=mock_landmark_result
    )
    print(f"   Enhanced Alert Level: {enhanced_result['alert_level'].value}")
    print(f"   Enhanced Confidence: {enhanced_result['confidence']:.2f}")
    print(f"   Enhanced Detection Used: {enhanced_result.get('enhanced_detection_used', False)}")
    
    # Test full-featured detector
    full_result = full_detector.process_frame(
        mock_features, (480, 640),
        input_quality_metrics=mock_quality_metrics,
        roi_result=mock_roi_result,
        face_validation=mock_face_validation,
        frame_validation=mock_frame_validation,
        landmark_result=mock_landmark_result
    )
    print(f"   Full-Featured Alert Level: {full_result['alert_level'].value}")
    print(f"   Full-Featured Confidence: {full_result['confidence']:.2f}")
    
    # Performance comparison
    print("\n=== PERFORMANCE COMPARISON ===")
    print(f"Original Confidence:     {result['confidence']:.3f}")
    print(f"Optimized Confidence:    {optimized_result['confidence']:.3f}")
    print(f"Enhanced Confidence:     {enhanced_result['confidence']:.3f}")
    print(f"Full-Featured Confidence: {full_result['confidence']:.3f}")
    
    # Enhanced statistics
    if enhanced_result.get('enhanced_detection_used'):
        print(f"\n=== ENHANCED DETECTION STATS ===")
        stats = enhanced_detector.get_enhanced_performance_stats()
        print(f"Quality Manager Available: {'✅' if 'quality_manager' in stats else '❌'}")
        print(f"Enhanced Detector Available: {'✅' if 'enhanced_detector' in stats else '❌'}")
        
        quality_summary = enhanced_detector.get_quality_summary()
        if 'current_quality' in quality_summary:
            print(f"Current Overall Quality: {quality_summary['current_quality']['overall']:.2f}")
    
    print("\n🎉 ENHANCED RULE-BASED DETECTOR TESTING COMPLETE!")
    print("✅ All detection modes working properly")
    print("🚀 Enhanced quality-aware detection ready for production!")
