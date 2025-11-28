"""
quality_manager.py
-----------------
Quality management integration between enhanced input layer and detection rules.
Provides centralized quality assessment and adaptive configuration.
"""

import numpy as np
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Container for input quality metrics"""
    face_size_category: str = "optimal"
    face_size_confidence: float = 1.0
    roi_quality: float = 1.0
    roi_stability: float = 1.0
    landmark_quality: float = 1.0
    frame_brightness: float = 128.0
    frame_contrast: float = 50.0
    frame_blur_score: float = 100.0
    motion_blur_score: float = 0.0
    processing_time: float = 0.0
    timestamp: float = 0.0

class QualityManager:
    """
    Centralized quality management for enhanced input-detection integration
    """
    
    def __init__(self, history_size: int = 20):
        self.history_size = history_size
        self.quality_history = deque(maxlen=history_size)
        self.adaptive_thresholds = self._init_adaptive_thresholds()
        self.performance_monitor = {
            "frame_count": 0,
            "detection_success_rate": 0.0,
            "avg_processing_time": 0.0,
            "quality_trends": {
                "roi_quality": deque(maxlen=10),
                "landmark_quality": deque(maxlen=10),
                "frame_quality": deque(maxlen=10)
            }
        }
    
    def _init_adaptive_thresholds(self) -> Dict[str, Any]:
        """Initialize adaptive thresholds"""
        return {
            "ear": {
                "base_blink_threshold": 0.25,
                "base_drowsy_threshold": 0.22,
                "quality_adjustment_range": (0.8, 1.2)
            },
            "mar": {
                "base_yawn_threshold": 0.65,
                "base_speaking_threshold": 0.35,
                "quality_adjustment_range": (0.8, 1.2)
            },
            "head_pose": {
                "base_normal_threshold": 12.0,
                "base_drowsy_threshold": 18.0,
                "quality_adjustment_range": (0.7, 1.3)
            }
        }
    
    def update_quality_metrics(self, 
                              roi_result: Optional[Dict] = None,
                              face_validation: Optional[Dict] = None,
                              frame_validation: Optional[Dict] = None,
                              landmark_result: Optional[Dict] = None) -> QualityMetrics:
        """
        Update and aggregate quality metrics from all input sources
        """
        metrics = QualityMetrics(timestamp=time.time())
        
        # Face size and validation metrics
        if face_validation:
            if hasattr(face_validation, 'metrics'):
                face_metrics = face_validation.metrics
                metrics.face_size_category = face_metrics.get("size_category", "optimal")
                metrics.face_size_confidence = face_validation.confidence
            else:
                face_metrics = face_validation if isinstance(face_validation, dict) else {}
                metrics.face_size_category = face_metrics.get("size_category", "optimal")
                metrics.face_size_confidence = face_metrics.get("confidence", 1.0)
        
        # ROI quality metrics
        if roi_result:
            metrics.roi_quality = self._calculate_roi_quality(roi_result)
            metrics.roi_stability = self._calculate_roi_stability(roi_result)
        
        # Frame quality metrics
        if frame_validation:
            if hasattr(frame_validation, 'metrics'):
                frame_metrics = frame_validation.metrics
            else:
                frame_metrics = frame_validation if isinstance(frame_validation, dict) else {}
            metrics.frame_brightness = frame_metrics.get("brightness", 128.0)
            metrics.frame_contrast = frame_metrics.get("contrast", 50.0)
            metrics.frame_blur_score = frame_metrics.get("blur_score", 100.0)
            metrics.motion_blur_score = frame_metrics.get("motion_score", 0.0)
        
        # Landmark quality metrics
        if landmark_result:
            metrics.landmark_quality = self._calculate_landmark_quality(landmark_result)
            metrics.processing_time = landmark_result.get("processing_time", 0.0)
        
        # Store in history
        self.quality_history.append(metrics)
        self._update_performance_monitor(metrics)
        
        return metrics
    
    def get_adaptive_thresholds(self, metrics: QualityMetrics) -> Dict[str, Dict[str, float]]:
        """
        Calculate adaptive thresholds based on current quality metrics
        """
        thresholds = {}
        
        # Calculate overall quality factor
        overall_quality = self._calculate_overall_quality(metrics)
        
        # Face size adjustment factor
        face_size_factor = self._get_face_size_adjustment(metrics.face_size_category)
        
        # ROI stability factor
        roi_factor = max(0.8, min(1.2, metrics.roi_quality * metrics.roi_stability))
        
        # Frame quality factor
        frame_factor = self._get_frame_quality_factor(metrics)
        
        # Combined adjustment factor
        combined_factor = (face_size_factor + roi_factor + frame_factor) / 3.0
        
        # Apply to each detection method
        for method, config in self.adaptive_thresholds.items():
            thresholds[method] = {}
            min_adj, max_adj = config["quality_adjustment_range"]
            adjustment = max(min_adj, min(max_adj, combined_factor))
            
            for threshold_name, base_value in config.items():
                if threshold_name.startswith("base_"):
                    threshold_key = threshold_name.replace("base_", "")
                    thresholds[method][threshold_key] = base_value * adjustment
        
        return thresholds
    
    def get_detection_configuration(self, metrics: QualityMetrics) -> Dict[str, Any]:
        """
        Get complete detection configuration based on quality metrics
        """
        adaptive_thresholds = self.get_adaptive_thresholds(metrics)
        
        config = {
            "thresholds": adaptive_thresholds,
            "quality_metrics": {
                "overall_quality": self._calculate_overall_quality(metrics),
                "face_size_category": metrics.face_size_category,
                "roi_quality": metrics.roi_quality,
                "landmark_quality": metrics.landmark_quality,
                "frame_quality_score": self._get_frame_quality_score(metrics)
            },
            "processing_flags": {
                "enable_temporal_smoothing": metrics.roi_stability > 0.7,
                "use_strict_validation": metrics.landmark_quality < 0.6,
                "apply_noise_reduction": metrics.frame_blur_score < 60,
                "enable_quality_feedback": True
            },
            "confidence_adjustments": {
                "face_size_confidence": metrics.face_size_confidence,
                "roi_confidence": min(1.0, metrics.roi_quality * 1.2),
                "landmark_confidence": metrics.landmark_quality,
                "frame_confidence": max(0.3, self._get_frame_quality_score(metrics))
            }
        }
        
        return config
    
    def assess_detection_reliability(self, detection_result: Dict, metrics: QualityMetrics) -> Dict[str, Any]:
        """
        Assess reliability of detection results based on quality metrics
        """
        reliability = {
            "overall_reliability": 0.0,
            "component_reliability": {},
            "quality_warnings": [],
            "recommendations": []
        }
        
        # Assess each component
        component_scores = []
        
        # EAR reliability
        if "ear_analysis" in detection_result and detection_result["ear_analysis"].get("valid"):
            ear_reliability = self._assess_ear_reliability(detection_result["ear_analysis"], metrics)
            reliability["component_reliability"]["ear"] = ear_reliability
            component_scores.append(ear_reliability)
        
        # MAR reliability
        if "mar_analysis" in detection_result and detection_result["mar_analysis"].get("valid"):
            mar_reliability = self._assess_mar_reliability(detection_result["mar_analysis"], metrics)
            reliability["component_reliability"]["mar"] = mar_reliability
            component_scores.append(mar_reliability)
        
        # Head pose reliability
        if "head_pose_analysis" in detection_result and detection_result["head_pose_analysis"].get("valid"):
            pose_reliability = self._assess_head_pose_reliability(detection_result["head_pose_analysis"], metrics)
            reliability["component_reliability"]["head_pose"] = pose_reliability
            component_scores.append(pose_reliability)
        
        # Overall reliability
        reliability["overall_reliability"] = np.mean(component_scores) if component_scores else 0.0
        
        # Quality warnings
        reliability["quality_warnings"] = self._generate_quality_warnings(metrics)
        
        # Recommendations
        reliability["recommendations"] = self._generate_recommendations(metrics, reliability)
        
        return reliability
    
    def _calculate_roi_quality(self, roi_result: Dict) -> float:
        """Calculate ROI quality score"""
        if not roi_result.get("used_roi", False):
            return 0.8  # Default score when no ROI
        
        roi_coords = roi_result.get("roi_coordinates")
        if not roi_coords:
            return 0.8
        
        x, y, w, h = roi_coords
        
        # Quality based on ROI size and aspect ratio
        area = w * h
        aspect_ratio = w / h if h > 0 else 1.0
        
        # Prefer reasonable ROI sizes
        if 40000 <= area <= 160000:  # 200x200 to 400x400
            size_score = 1.0
        elif 25000 <= area <= 225000:  # Acceptable range
            size_score = 0.8
        else:
            size_score = 0.6
        
        # Prefer square-ish aspect ratios for faces
        if 0.8 <= aspect_ratio <= 1.2:
            aspect_score = 1.0
        else:
            aspect_score = 0.7
        
        return (size_score + aspect_score) / 2.0
    
    def _calculate_roi_stability(self, roi_result: Dict) -> float:
        """Calculate ROI stability over time"""
        if len(self.quality_history) < 3:
            return 1.0
        
        # Look at ROI coordinates over recent history
        recent_rois = []
        for metrics in list(self.quality_history)[-3:]:
            # This would need to be stored in metrics, simplified here
            recent_rois.append(1.0)  # Placeholder
        
        return np.mean(recent_rois)
    
    def _calculate_landmark_quality(self, landmark_result: Dict) -> float:
        """Calculate landmark detection quality"""
        base_quality = 0.5
        
        if not landmark_result.get("valid", False):
            return 0.3
        
        landmark_count = landmark_result.get("landmark_count", 0)
        if landmark_count >= 468:  # Full MediaPipe landmarks
            base_quality = 0.95
        elif landmark_count >= 200:
            base_quality = 0.8
        elif landmark_count >= 100:
            base_quality = 0.6
        
        # Processing time factor
        processing_time = landmark_result.get("processing_time", 0.05)
        if processing_time < 0.03:
            time_factor = 1.1
        elif processing_time > 0.1:
            time_factor = 0.9
        else:
            time_factor = 1.0
        
        # Stability score if available
        stability_score = landmark_result.get("stability_score", 1.0)
        
        return min(1.0, base_quality * time_factor * stability_score)
    
    def _calculate_overall_quality(self, metrics: QualityMetrics) -> float:
        """Calculate overall input quality score"""
        face_quality = metrics.face_size_confidence
        roi_quality = metrics.roi_quality * metrics.roi_stability
        landmark_quality = metrics.landmark_quality
        frame_quality = self._get_frame_quality_score(metrics)
        
        # Weighted average
        weights = [0.25, 0.25, 0.3, 0.2]  # landmark quality weighted higher
        qualities = [face_quality, roi_quality, landmark_quality, frame_quality]
        
        return np.average(qualities, weights=weights)
    
    def _get_face_size_adjustment(self, face_size_category: str) -> float:
        """Get threshold adjustment factor based on face size"""
        adjustments = {
            "too_small": 0.85,
            "acceptable_small": 0.92,
            "optimal": 1.0,
            "acceptable_large": 1.08,
            "too_large": 1.15
        }
        return adjustments.get(face_size_category, 1.0)
    
    def _get_frame_quality_factor(self, metrics: QualityMetrics) -> float:
        """Calculate frame quality adjustment factor"""
        brightness_factor = 1.0
        if metrics.frame_brightness < 60 or metrics.frame_brightness > 200:
            brightness_factor = 0.85
        elif metrics.frame_brightness < 80 or metrics.frame_brightness > 180:
            brightness_factor = 0.95
        
        contrast_factor = 1.0 if metrics.frame_contrast > 30 else 0.8
        blur_factor = 1.0 if metrics.frame_blur_score > 70 else 0.85
        motion_factor = 1.0 if metrics.motion_blur_score < 20 else 0.9
        
        return brightness_factor * contrast_factor * blur_factor * motion_factor
    
    def _get_frame_quality_score(self, metrics: QualityMetrics) -> float:
        """Get overall frame quality score (0-1)"""
        brightness_score = 1.0
        if 80 <= metrics.frame_brightness <= 180:
            brightness_score = 1.0
        elif 60 <= metrics.frame_brightness <= 220:
            brightness_score = 0.8
        else:
            brightness_score = 0.6
        
        contrast_score = min(1.0, metrics.frame_contrast / 50.0)
        blur_score = min(1.0, metrics.frame_blur_score / 100.0)
        motion_score = max(0.3, 1.0 - metrics.motion_blur_score / 50.0)
        
        return np.mean([brightness_score, contrast_score, blur_score, motion_score])
    
    def _assess_ear_reliability(self, ear_result: Dict, metrics: QualityMetrics) -> float:
        """Assess EAR detection reliability"""
        base_reliability = 0.7
        
        # EAR value reasonableness
        ear_value = ear_result.get("ear_value", 0.25)
        if 0.1 <= ear_value <= 0.4:
            value_score = 1.0
        else:
            value_score = 0.6
        
        # Quality factors
        quality_score = (metrics.roi_quality + metrics.landmark_quality) / 2.0
        
        return min(1.0, base_reliability * value_score * quality_score)
    
    def _assess_mar_reliability(self, mar_result: Dict, metrics: QualityMetrics) -> float:
        """Assess MAR detection reliability"""
        base_reliability = 0.65
        
        # MAR value reasonableness
        mar_value = mar_result.get("mar_value", 0.3)
        if 0.1 <= mar_value <= 1.0:
            value_score = 1.0
        else:
            value_score = 0.5
        
        # Quality factors
        quality_score = (metrics.roi_quality + metrics.landmark_quality) / 2.0
        
        return min(1.0, base_reliability * value_score * quality_score)
    
    def _assess_head_pose_reliability(self, pose_result: Dict, metrics: QualityMetrics) -> float:
        """Assess head pose detection reliability"""
        base_reliability = 0.6
        
        # Angle reasonableness
        pitch = abs(pose_result.get("pitch", 0))
        if pitch < 35:
            angle_score = 1.0
        elif pitch < 50:
            angle_score = 0.7
        else:
            angle_score = 0.4
        
        # Quality factors  
        quality_score = (metrics.landmark_quality + metrics.roi_stability) / 2.0
        
        return min(1.0, base_reliability * angle_score * quality_score)
    
    def _generate_quality_warnings(self, metrics: QualityMetrics) -> List[str]:
        """Generate quality-based warnings"""
        warnings = []
        
        if metrics.face_size_category in ["too_small", "too_large"]:
            warnings.append(f"Suboptimal face size: {metrics.face_size_category}")
        
        if metrics.roi_quality < 0.7:
            warnings.append("ROI detection quality is low")
        
        if metrics.landmark_quality < 0.6:
            warnings.append("Landmark detection quality is poor")
        
        if metrics.frame_brightness < 60:
            warnings.append("Frame is too dark")
        elif metrics.frame_brightness > 220:
            warnings.append("Frame is too bright")
        
        if metrics.frame_contrast < 25:
            warnings.append("Frame contrast is too low")
        
        if metrics.frame_blur_score < 50:
            warnings.append("Frame is blurry")
        
        if metrics.motion_blur_score > 30:
            warnings.append("Motion blur detected")
        
        return warnings
    
    def _generate_recommendations(self, metrics: QualityMetrics, reliability: Dict) -> List[str]:
        """Generate recommendations for improving detection quality"""
        recommendations = []
        
        overall_reliability = reliability["overall_reliability"]
        
        if overall_reliability < 0.6:
            recommendations.append("Consider improving lighting conditions")
            
        if metrics.face_size_category == "too_small":
            recommendations.append("Move closer to camera")
        elif metrics.face_size_category == "too_large":
            recommendations.append("Move away from camera")
        
        if metrics.roi_stability < 0.7:
            recommendations.append("Keep head position stable")
        
        if metrics.frame_blur_score < 60:
            recommendations.append("Ensure camera is in focus")
        
        if metrics.motion_blur_score > 25:
            recommendations.append("Reduce head movement")
        
        if not recommendations:
            recommendations.append("Detection quality is good")
        
        return recommendations
    
    def _update_performance_monitor(self, metrics: QualityMetrics):
        """Update performance monitoring metrics"""
        self.performance_monitor["frame_count"] += 1
        
        # Update quality trends
        self.performance_monitor["quality_trends"]["roi_quality"].append(metrics.roi_quality)
        self.performance_monitor["quality_trends"]["landmark_quality"].append(metrics.landmark_quality)
        frame_quality = self._get_frame_quality_score(metrics)
        self.performance_monitor["quality_trends"]["frame_quality"].append(frame_quality)
        
        # Update averages
        if self.performance_monitor["quality_trends"]["roi_quality"]:
            avg_processing = np.mean([m.processing_time for m in self.quality_history if m.processing_time > 0])
            self.performance_monitor["avg_processing_time"] = avg_processing
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get quality assessment summary"""
        if not self.quality_history:
            return {"message": "No quality data available"}
        
        recent_metrics = list(self.quality_history)[-5:]
        
        return {
            "current_quality": {
                "overall": self._calculate_overall_quality(self.quality_history[-1]) if self.quality_history else 0.0,
                "face_size": self.quality_history[-1].face_size_category if self.quality_history else "unknown",
                "roi_quality": self.quality_history[-1].roi_quality if self.quality_history else 0.0,
                "landmark_quality": self.quality_history[-1].landmark_quality if self.quality_history else 0.0
            },
            "quality_trends": {
                "roi_stability": np.std([m.roi_quality for m in recent_metrics]),
                "landmark_consistency": np.std([m.landmark_quality for m in recent_metrics]),
                "frame_quality_trend": np.mean([self._get_frame_quality_score(m) for m in recent_metrics])
            },
            "performance": self.performance_monitor,
            "recent_warnings": self._generate_quality_warnings(self.quality_history[-1]) if self.quality_history else []
        }

# Global quality manager instance
_quality_manager = None

def get_quality_manager() -> QualityManager:
    """Get global quality manager instance"""
    global _quality_manager
    if _quality_manager is None:
        _quality_manager = QualityManager()
    return _quality_manager

if __name__ == "__main__":
    # Test quality manager
    print("Testing Quality Manager...")
    
    manager = QualityManager()
    
    # Test with sample metrics
    sample_face_validation = {
        "size_category": "optimal",
        "confidence": 0.85
    }
    
    sample_frame_validation = {
        "metrics": {
            "brightness": 140,
            "contrast": 45,
            "blur_score": 75,
            "motion_score": 15
        }
    }
    
    sample_landmark_result = {
        "valid": True,
        "landmark_count": 468,
        "processing_time": 0.025,
        "stability_score": 0.9
    }
    
    # Update quality metrics
    metrics = manager.update_quality_metrics(
        face_validation=sample_face_validation,
        frame_validation=sample_frame_validation,
        landmark_result=sample_landmark_result
    )
    
    # Get adaptive thresholds
    thresholds = manager.get_adaptive_thresholds(metrics)
    print(f"EAR blink threshold: {thresholds['ear']['blink_threshold']:.3f}")
    print(f"MAR yawn threshold: {thresholds['mar']['yawn_threshold']:.3f}")
    print(f"Head pose drowsy threshold: {thresholds['head_pose']['drowsy_threshold']:.1f}")
    
    # Get quality summary
    summary = manager.get_quality_summary()
    print(f"Overall quality: {summary['current_quality']['overall']:.2f}")
    
    print("✅ Quality Manager test completed!")