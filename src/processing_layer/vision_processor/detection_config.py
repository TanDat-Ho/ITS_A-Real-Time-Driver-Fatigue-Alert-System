"""
detection_config.py
------------------
Configuration management for fatigue detection system
Extracted from rule_based.py for better code organization
"""

from typing import Dict, Any
from .detection_enums import AlertLevel, FatigueState, EyeState, MouthState, HeadState


class FatigueDetectionConfig:
    """Configuration management for FatigueDetector."""
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default configuration with optimized values."""
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
        """Sensitive configuration with optimized values."""
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
        """Conservative configuration with optimized values."""
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


class RecommendationManager:
    """Manages recommendations and mappings between states."""
    
    @staticmethod
    def determine_fatigue_state(alert_level: AlertLevel) -> FatigueState:
        """Map alert level to fatigue state."""
        mapping = {
            AlertLevel.NONE: FatigueState.AWAKE,
            AlertLevel.LOW: FatigueState.SLIGHTLY_TIRED,
            AlertLevel.MEDIUM: FatigueState.MODERATELY_TIRED,
            AlertLevel.HIGH: FatigueState.SEVERELY_TIRED,
            AlertLevel.CRITICAL: FatigueState.DANGEROUSLY_DROWSY
        }
        return mapping.get(alert_level, FatigueState.AWAKE)
    
    @staticmethod
    def get_recommendation(alert_level: AlertLevel, fatigue_state: FatigueState) -> str:
        """Get recommendation based on current state."""
        recommendations = {
            AlertLevel.NONE: "Driving safely - Stay focused on the road",
            AlertLevel.LOW: "⚠️ Early fatigue signs - Open windows, adjust posture", 
            AlertLevel.MEDIUM: "🚨 Moderate fatigue - Find rest stop within 30 minutes",
            AlertLevel.HIGH: "🛑 DANGER: Pull over safely and rest for 15-20 minutes",
            AlertLevel.CRITICAL: "🚨 CRITICAL: STOP DRIVING NOW - Find safe place immediately"
        }
        return recommendations.get(alert_level, "Continue driving safely")
    
    @staticmethod
    def calculate_confidence(eye_state: EyeState, 
                           mouth_state: MouthState, 
                           head_state: HeadState, 
                           alert_level: AlertLevel) -> float:
        """Calculate confidence score based on individual states and alert level."""
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