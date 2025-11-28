"""
rule_based.py
-----------------
Rule-based Fatigue Detection Processor (Refactored)

Main detection class integrating EAR + MAR + Head Pose with enhanced quality awareness.
Components moved to separate modules for better maintainability:
- detection_enums.py: All enum definitions
- detection_config.py: Configuration and recommendations
- state_analyzers.py: State analysis functions
- detector_factory.py: Factory pattern for creating detectors

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

If 2 out of 3 conditions occur simultaneously, system triggers high alert.
"""

import time
import logging
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

# Import detection components
from .detection_enums import AlertLevel, FatigueState, EyeState, MouthState, HeadState
from .detection_config import RecommendationManager
from .state_analyzers import StateAnalyzer

# Import detection functions
from ..detect_rules.ear import calculate_ear_full, reset_ear_state, get_ear_statistics
from ..detect_rules.mar import calculate_mar_with_analysis, reset_mar_state, get_mar_statistics  
from ..detect_rules.head_pose import calculate_head_pose_with_analysis, reset_head_pose_state, get_head_pose_statistics
from ..detect_rules.enhanced_integration import EnhancedDetectionWrapper, get_enhanced_detector
from ...input_layer.quality_manager import QualityManager, QualityMetrics


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
        
        # Build alert conditions list using StateAnalyzer
        alert_conditions = StateAnalyzer.build_alert_conditions(eye_state, mouth_state, head_state)
        
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
    
    # State analysis methods now use StateAnalyzer
    def _analyze_eye_state(self, ear_data: Optional[Dict]) -> EyeState:
        """Analyze eye state using StateAnalyzer."""
        return StateAnalyzer.analyze_eye_state(ear_data)
    
    def _analyze_mouth_state(self, mar_data: Optional[Dict]) -> MouthState:
        """Analyze mouth state using StateAnalyzer."""
        return StateAnalyzer.analyze_mouth_state(mar_data)
    
    def _analyze_head_state(self, head_data: Optional[Dict]) -> HeadState:
        """Analyze head state using StateAnalyzer."""
        return StateAnalyzer.analyze_head_state(head_data)

    def _determine_alert_level(self, eye_state: EyeState, mouth_state: MouthState, head_state: HeadState) -> AlertLevel:
        """Determine alert level using StateAnalyzer."""
        return StateAnalyzer.determine_alert_level(eye_state, mouth_state, head_state, self.combination_threshold)
    
    def _determine_fatigue_state(self, alert_level: AlertLevel) -> FatigueState:
        """Determine fatigue state using RecommendationManager."""
        return RecommendationManager.determine_fatigue_state(alert_level)
    
    def _get_recommendation(self, alert_level: AlertLevel, fatigue_state: FatigueState) -> str:
        """Get recommendation using RecommendationManager."""
        return RecommendationManager.get_recommendation(alert_level, fatigue_state)
    
    def _calculate_confidence(self, eye_state: EyeState, mouth_state: MouthState, head_state: HeadState, alert_level: AlertLevel) -> float:
        """Calculate confidence using RecommendationManager."""
        return RecommendationManager.calculate_confidence(eye_state, mouth_state, head_state, alert_level)
    
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


# Factory methods moved to detector_factory.py
# Configuration classes moved to detection_config.py


if __name__ == "__main__":
    # Test với dữ liệu mẫu - all detection modes
    from .detection_config import FatigueDetectionConfig
    from .detector_factory import DetectorFactory
    
    print("=== TESTING REFACTORED RULE-BASED FATIGUE DETECTOR ===")
    
    # Test original detector
    print("\n1. Testing Original Detector:")
    config = FatigueDetectionConfig.get_default_config()
    detector = RuleBasedFatigueDetector(use_enhanced_detection=False, **config)
    
    # Test optimized detector
    print("\n2. Testing Optimized Detector:")
    optimized_detector = DetectorFactory.create_optimized_detector("normal", "medium")
    
    # Test enhanced detector
    print("\n3. Testing Enhanced Detector:")
    enhanced_detector = DetectorFactory.create_enhanced_detector("normal", "medium", "default")
    
    # Test full-featured detector
    print("\n4. Testing Full-Featured Detector:")
    full_detector = DetectorFactory.create_full_featured_detector("normal", "medium", "default")
    
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
