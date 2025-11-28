"""
quality_manager.py
-----------------
Cleaned quality management integration between enhanced input layer and detection rules.
Provides centralized quality assessment and adaptive configuration.
"""

import time
import numpy as np
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
            if isinstance(face_validation, dict):
                metrics.face_size_category = face_validation.get("size_category", "optimal")
                metrics.face_size_confidence = face_validation.get("confidence", 1.0)
            else:
                # Handle ValidationResult objects
                metrics.face_size_category = getattr(face_validation, 'metrics', {}).get("size_category", "optimal")
                metrics.face_size_confidence = getattr(face_validation, 'confidence', 1.0)
        
        # ROI quality metrics
        if roi_result:
            metrics.roi_quality = self._calculate_roi_quality(roi_result)
            metrics.roi_stability = self._calculate_roi_stability(roi_result)
        
        # Frame quality metrics
        if frame_validation:
            if isinstance(frame_validation, dict) and "metrics" in frame_validation:
                frame_metrics = frame_validation["metrics"]
                metrics.frame_brightness = frame_metrics.get("brightness", 128.0)
                metrics.frame_contrast = frame_metrics.get("contrast", 50.0)
                metrics.frame_blur_score = frame_metrics.get("blur_score", 100.0)
                metrics.motion_blur_score = frame_metrics.get("motion_score", 0.0)
            else:
                # Handle ValidationResult objects
                frame_metrics = getattr(frame_validation, 'metrics', {})
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
            method_thresholds = {}
            for threshold_name, base_value in config.items():
                if threshold_name == "quality_adjustment_range":
                    continue
                min_adj, max_adj = config["quality_adjustment_range"]
                adjustment = max(min_adj, min(max_adj, combined_factor))
                method_thresholds[threshold_name] = base_value * adjustment
            thresholds[method] = method_thresholds
        
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
            return 1.0  # Full frame processing
        
        roi_coords = roi_result.get("roi_coordinates")
        if not roi_coords:
            return 0.8
        
        x, y, w, h = roi_coords
        
        # Quality based on ROI size and aspect ratio
        area = w * h
        aspect_ratio = w / h if h > 0 else 1.0
        
        # Prefer reasonable ROI sizes (face regions)
        if 40000 <= area <= 160000:
            size_score = 1.0
        elif 25000 <= area <= 225000:
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
            return 1.0  # Not enough history
        
        # Look at ROI coordinates over recent history
        recent_rois = []
        for metrics in list(self.quality_history)[-3:]:
            if hasattr(metrics, 'roi_quality') and metrics.roi_quality > 0:
                recent_rois.append(metrics.roi_quality)
        
        if len(recent_rois) < 2:
            return 1.0
        
        # Calculate stability as inverse of variation
        stability = 1.0 - min(0.5, np.std(recent_rois))
        return max(0.5, stability)
    
    def _calculate_landmark_quality(self, landmark_result: Dict) -> float:
        """Calculate landmark detection quality"""
        base_quality = 0.5
        
        if not landmark_result.get("valid", False):
            return base_quality
        
        landmark_count = landmark_result.get("landmark_count", 0)
        if landmark_count >= 468:
            count_quality = 1.0
        elif landmark_count >= 400:
            count_quality = 0.9
        elif landmark_count >= 300:
            count_quality = 0.7
        else:
            count_quality = 0.4
        
        # Processing time factor (prefer faster processing)
        processing_time = landmark_result.get("processing_time", 0.05)
        if processing_time <= 0.03:
            time_quality = 1.0
        elif processing_time <= 0.05:
            time_quality = 0.9
        elif processing_time <= 0.1:
            time_quality = 0.7
        else:
            time_quality = 0.5
        
        return (count_quality + time_quality) / 2.0
    
    def _calculate_overall_quality(self, metrics: QualityMetrics) -> float:
        """Calculate overall quality score"""
        factors = [
            metrics.face_size_confidence,
            metrics.roi_quality,
            metrics.landmark_quality,
            self._get_frame_quality_score(metrics)
        ]
        return np.mean(factors)
    
    def _get_face_size_adjustment(self, face_size_category: str) -> float:
        """Get adjustment factor based on face size category"""
        adjustments = {
            "optimal": 1.0,
            "good": 0.95,
            "acceptable": 0.9,
            "small": 0.8,
            "large": 1.1,
            "too_small": 0.7,
            "too_large": 1.2
        }
        return adjustments.get(face_size_category, 1.0)
    
    def _get_frame_quality_factor(self, metrics: QualityMetrics) -> float:
        """Calculate frame quality adjustment factor"""
        brightness_factor = 1.0
        if metrics.frame_brightness < 60 or metrics.frame_brightness > 200:
            brightness_factor = 0.8
        elif metrics.frame_brightness < 80 or metrics.frame_brightness > 180:
            brightness_factor = 0.9
        
        contrast_factor = 1.0
        if metrics.frame_contrast < 30:
            contrast_factor = 0.7
        elif metrics.frame_contrast < 40:
            contrast_factor = 0.85
        
        blur_factor = 1.0
        if metrics.frame_blur_score < 60:
            blur_factor = 0.6
        elif metrics.frame_blur_score < 100:
            blur_factor = 0.8
        
        return (brightness_factor + contrast_factor + blur_factor) / 3.0
    
    def _get_frame_quality_score(self, metrics: QualityMetrics) -> float:
        """Get normalized frame quality score"""
        brightness_score = 1.0
        if 60 <= metrics.frame_brightness <= 200:
            brightness_score = 1.0
        elif 40 <= metrics.frame_brightness <= 220:
            brightness_score = 0.8
        else:
            brightness_score = 0.5
        
        contrast_score = min(1.0, metrics.frame_contrast / 50.0)
        blur_score = min(1.0, metrics.frame_blur_score / 100.0)
        motion_penalty = max(0.5, 1.0 - metrics.motion_blur_score / 50.0)
        
        return (brightness_score + contrast_score + blur_score) * motion_penalty / 3.0
    
    def _assess_ear_reliability(self, ear_result: Dict, metrics: QualityMetrics) -> float:
        """Assess EAR detection reliability"""
        base_reliability = 0.7
        
        # Factor in frame quality
        frame_quality = self._get_frame_quality_score(metrics)
        reliability = base_reliability * (0.5 + 0.5 * frame_quality)
        
        # Factor in landmark quality
        reliability *= (0.6 + 0.4 * metrics.landmark_quality)
        
        # Factor in face size
        if metrics.face_size_category in ["optimal", "good"]:
            reliability *= 1.0
        elif metrics.face_size_category in ["acceptable"]:
            reliability *= 0.9
        else:
            reliability *= 0.7
        
        return min(1.0, reliability)
    
    def _assess_mar_reliability(self, mar_result: Dict, metrics: QualityMetrics) -> float:
        """Assess MAR detection reliability"""
        base_reliability = 0.8
        
        # MAR is generally more robust than EAR
        frame_quality = self._get_frame_quality_score(metrics)
        reliability = base_reliability * (0.6 + 0.4 * frame_quality)
        
        # Factor in landmark quality
        reliability *= (0.7 + 0.3 * metrics.landmark_quality)
        
        # Factor in motion blur (affects mouth region detection)
        motion_penalty = max(0.8, 1.0 - metrics.motion_blur_score / 40.0)
        reliability *= motion_penalty
        
        return min(1.0, reliability)
    
    def _assess_head_pose_reliability(self, pose_result: Dict, metrics: QualityMetrics) -> float:
        """Assess head pose detection reliability"""
        base_reliability = 0.75
        
        # Head pose is sensitive to landmark quality
        reliability = base_reliability * metrics.landmark_quality
        
        # Factor in ROI stability
        reliability *= (0.7 + 0.3 * metrics.roi_stability)
        
        # Factor in face size
        if metrics.face_size_category in ["optimal", "good"]:
            reliability *= 1.0
        elif metrics.face_size_category == "acceptable":
            reliability *= 0.85
        else:
            reliability *= 0.6
        
        return min(1.0, reliability)
    
    def _generate_quality_warnings(self, metrics: QualityMetrics) -> List[str]:
        """Generate quality warnings based on metrics"""
        warnings = []
        
        if metrics.frame_brightness < 60:
            warnings.append("Poor lighting conditions detected")
        elif metrics.frame_brightness > 200:
            warnings.append("Overexposed frame detected")
        
        if metrics.frame_contrast < 30:
            warnings.append("Low contrast may affect detection")
        
        if metrics.frame_blur_score < 80:
            warnings.append("Frame blur may reduce accuracy")
        
        if metrics.motion_blur_score > 25:
            warnings.append("Motion blur detected")
        
        if metrics.landmark_quality < 0.7:
            warnings.append("Landmark detection quality is low")
        
        if metrics.roi_stability < 0.6:
            warnings.append("Unstable face tracking")
        
        if metrics.face_size_category in ["small", "too_small"]:
            warnings.append("Face size may be too small for accurate detection")
        elif metrics.face_size_category in ["large", "too_large"]:
            warnings.append("Face size may cause processing issues")
        
        return warnings
    
    def _generate_recommendations(self, metrics: QualityMetrics, reliability: Dict) -> List[str]:
        """Generate recommendations based on quality and reliability"""
        recommendations = []
        
        if metrics.frame_brightness < 60:
            recommendations.append("Improve lighting conditions")
        elif metrics.frame_brightness > 200:
            recommendations.append("Reduce lighting or adjust camera exposure")
        
        if metrics.frame_blur_score < 80:
            recommendations.append("Ensure camera is stable and in focus")
        
        if metrics.motion_blur_score > 25:
            recommendations.append("Reduce camera or subject movement")
        
        if metrics.landmark_quality < 0.7:
            recommendations.append("Check face visibility and camera angle")
        
        if reliability["overall_reliability"] < 0.6:
            recommendations.append("Consider recalibrating detection thresholds")
        
        if metrics.face_size_category in ["small", "too_small"]:
            recommendations.append("Move closer to camera or adjust camera position")
        elif metrics.face_size_category in ["large", "too_large"]:
            recommendations.append("Move further from camera")
        
        return recommendations
    
    def _update_performance_monitor(self, metrics: QualityMetrics):
        """Update performance monitoring metrics"""
        self.performance_monitor["frame_count"] += 1
        
        # Update quality trends
        overall_quality = self._calculate_overall_quality(metrics)
        self.performance_monitor["quality_trends"]["frame_quality"].append(overall_quality)
        self.performance_monitor["quality_trends"]["roi_quality"].append(metrics.roi_quality)
        self.performance_monitor["quality_trends"]["landmark_quality"].append(metrics.landmark_quality)
        
        # Update average processing time
        if metrics.processing_time > 0:
            current_avg = self.performance_monitor["avg_processing_time"]
            frame_count = self.performance_monitor["frame_count"]
            self.performance_monitor["avg_processing_time"] = (
                (current_avg * (frame_count - 1) + metrics.processing_time) / frame_count
            )
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get comprehensive quality summary"""
        if not self.quality_history:
            return {"status": "no_data"}
        
        latest_metrics = self.quality_history[-1]
        
        # Calculate recent averages
        recent_metrics = list(self.quality_history)[-5:]  # Last 5 frames
        
        summary = {
            "current_quality": {
                "overall": self._calculate_overall_quality(latest_metrics),
                "frame": self._get_frame_quality_score(latest_metrics),
                "landmarks": latest_metrics.landmark_quality,
                "roi": latest_metrics.roi_quality,
                "stability": latest_metrics.roi_stability
            },
            "recent_averages": {
                "frame_brightness": np.mean([m.frame_brightness for m in recent_metrics]),
                "frame_contrast": np.mean([m.frame_contrast for m in recent_metrics]),
                "blur_score": np.mean([m.frame_blur_score for m in recent_metrics]),
                "landmark_quality": np.mean([m.landmark_quality for m in recent_metrics])
            },
            "performance": self.performance_monitor.copy(),
            "warnings": self._generate_quality_warnings(latest_metrics),
            "recommendations": self._generate_recommendations(latest_metrics, {"overall_reliability": self._calculate_overall_quality(latest_metrics)})
        }
        
        return summary

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
    print(f"EAR blink threshold: {thresholds['ear']['base_blink_threshold']:.3f}")
    print(f"MAR yawn threshold: {thresholds['mar']['base_yawn_threshold']:.3f}")
    print(f"Head pose drowsy threshold: {thresholds['head_pose']['base_drowsy_threshold']:.1f}")
    
    # Get quality summary
    summary = manager.get_quality_summary()
    print(f"Overall quality: {summary['current_quality']['overall']:.2f}")
    
    print("✅ Quality Manager test completed!")