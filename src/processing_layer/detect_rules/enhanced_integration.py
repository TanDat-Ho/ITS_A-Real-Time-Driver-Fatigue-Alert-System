"""
enhanced_integration.py
----------------------
Enhanced integration layer between optimized input and detection rules.
Provides quality-aware detection with adaptive thresholds.
"""

import numpy as np
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import deque

# Import existing detection rules
from .ear import calculate_ear_both_eyes, analyze_ear_state
from .mar import calculate_mar, analyze_mar_state  
from .head_pose import calculate_head_pose, analyze_head_pose_state

logger = logging.getLogger(__name__)

class EnhancedDetectionWrapper:
    """
    Wrapper class that enhances existing detection rules with input quality awareness
    """
    
    def __init__(self):
        self.quality_history = deque(maxlen=10)
        self.detection_history = deque(maxlen=30)
        
    def analyze_ear_enhanced(self, left_eye: List[Tuple], right_eye: List[Tuple],
                           face_size_category: str = "optimal", 
                           roi_quality: float = 1.0,
                           frame_quality: Dict = None) -> Dict[str, Any]:
        """
        Enhanced EAR analysis with quality-based adjustments
        """
        if len(left_eye) != 6 or len(right_eye) != 6:
            return {"valid": False, "reason": "insufficient_eye_landmarks"}
        
        try:
            # Calculate base EAR
            ear_value = calculate_ear_both_eyes(left_eye, right_eye)
            
            # Determine quality adjustments
            face_size_factor = self._get_face_size_factor(face_size_category)
            roi_quality_factor = max(0.9, min(1.1, roi_quality))
            frame_quality_factor = self._get_frame_quality_factor(frame_quality)
            
            # Enhanced analysis with quality factors
            enhanced_result = analyze_ear_state(
                ear_value,
                blink_threshold=0.25 * face_size_factor * roi_quality_factor,
                drowsy_threshold=0.22 * face_size_factor * roi_quality_factor,
                blink_frames=2,
                drowsy_duration=1.2
            )
            
            # Add quality metrics
            enhanced_result.update({
                "quality_adjustments": {
                    "face_size_factor": face_size_factor,
                    "roi_quality_factor": roi_quality_factor, 
                    "frame_quality_factor": frame_quality_factor
                },
                "adjusted_thresholds": {
                    "blink": 0.25 * face_size_factor * roi_quality_factor,
                    "drowsy": 0.22 * face_size_factor * roi_quality_factor
                },
                "confidence": self._calculate_ear_confidence(enhanced_result, face_size_factor, roi_quality_factor),
                "valid": True
            })
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Enhanced EAR analysis error: {e}")
            return {"valid": False, "error": str(e)}
    
    def analyze_mar_enhanced(self, mouth_landmarks: List[Tuple],
                           face_size_category: str = "optimal",
                           roi_quality: float = 1.0,
                           mouth_landmark_quality: float = 1.0) -> Dict[str, Any]:
        """
        Enhanced MAR analysis with quality-based adjustments
        """
        if len(mouth_landmarks) < 6:
            return {"valid": False, "reason": "insufficient_mouth_landmarks"}
        
        try:
            # Calculate base MAR
            mar_value = calculate_mar(mouth_landmarks[:6])
            
            # Quality adjustments
            face_size_factor = self._get_face_size_factor(face_size_category)
            roi_quality_factor = max(0.9, min(1.1, roi_quality))
            mouth_quality_factor = max(0.6, min(1.0, mouth_landmark_quality))
            
            # Enhanced analysis
            enhanced_result = analyze_mar_state(
                mar_value,
                yawn_threshold=0.65 * face_size_factor * roi_quality_factor,
                yawn_duration=1.0,
                speaking_threshold=0.35 * face_size_factor
            )
            
            # Add quality-based enhancements
            enhanced_result.update({
                "quality_adjustments": {
                    "face_size_factor": face_size_factor,
                    "roi_quality_factor": roi_quality_factor,
                    "mouth_quality_factor": mouth_quality_factor
                },
                "adjusted_thresholds": {
                    "yawn": 0.65 * face_size_factor * roi_quality_factor,
                    "speaking": 0.35 * face_size_factor
                },
                "confidence": self._calculate_mar_confidence(enhanced_result, mouth_quality_factor),
                "is_likely_speaking": self._detect_speaking_pattern(mar_value, enhanced_result),
                "valid": True
            })
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Enhanced MAR analysis error: {e}")
            return {"valid": False, "error": str(e)}
    
    def analyze_head_pose_enhanced(self, features: Dict[str, List], frame_shape: Tuple,
                                 landmark_quality: float = 1.0,
                                 roi_stability: float = 1.0,
                                 face_size_category: str = "optimal") -> Dict[str, Any]:
        """
        Enhanced head pose analysis with quality considerations
        """
        try:
            # Calculate base head pose
            pose_data = calculate_head_pose(features, frame_shape)
            
            if pose_data is None:
                return {"valid": False, "reason": "head_pose_calculation_failed"}
            
            # Quality adjustments
            face_size_factor = self._get_face_size_factor(face_size_category)
            quality_factor = landmark_quality * roi_stability
            
            # Enhanced analysis with quality factors
            enhanced_result = analyze_head_pose_state(
                pose_data,
                normal_threshold=12.0 / max(0.8, quality_factor),  # Stricter when quality is low
                drowsy_threshold=18.0 / max(0.8, quality_factor),
                drowsy_duration=1.3
            )
            
            # Add quality enhancements
            enhanced_result.update({
                "quality_adjustments": {
                    "face_size_factor": face_size_factor,
                    "landmark_quality": landmark_quality,
                    "roi_stability": roi_stability,
                    "overall_quality": quality_factor
                },
                "adjusted_thresholds": {
                    "normal": 12.0 / max(0.8, quality_factor),
                    "drowsy": 18.0 / max(0.8, quality_factor)
                },
                "confidence": self._calculate_head_pose_confidence(enhanced_result, quality_factor),
                "multi_angle_score": self._calculate_multi_angle_score(pose_data),
                "valid": True
            })
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Enhanced head pose analysis error: {e}")
            return {"valid": False, "error": str(e)}
    
    def process_complete_detection(self, features: Dict[str, List], frame_shape: Tuple,
                                 input_quality_metrics: Dict = None) -> Dict[str, Any]:
        """
        Complete enhanced detection pipeline
        """
        if not features:
            return {"valid": False, "reason": "no_features_provided"}
        
        # Extract quality metrics
        face_size_category = input_quality_metrics.get("face_size_category", "optimal") if input_quality_metrics else "optimal"
        roi_quality = input_quality_metrics.get("roi_quality", 1.0) if input_quality_metrics else 1.0
        landmark_quality = input_quality_metrics.get("landmark_quality", 1.0) if input_quality_metrics else 1.0
        roi_stability = input_quality_metrics.get("roi_stability", 1.0) if input_quality_metrics else 1.0
        frame_quality = input_quality_metrics.get("frame_quality") if input_quality_metrics else None
        
        results = {
            "timestamp": time.time(),
            "input_quality": input_quality_metrics or {},
            "ear_analysis": None,
            "mar_analysis": None,
            "head_pose_analysis": None,
            "combined_analysis": None,
            "valid": False
        }
        
        # EAR Analysis
        if "left_eye" in features and "right_eye" in features:
            results["ear_analysis"] = self.analyze_ear_enhanced(
                features["left_eye"], features["right_eye"],
                face_size_category, roi_quality, frame_quality
            )
        
        # MAR Analysis
        if "mouth" in features:
            mouth_quality = self._estimate_mouth_landmark_quality(features["mouth"])
            results["mar_analysis"] = self.analyze_mar_enhanced(
                features["mouth"], face_size_category, roi_quality, mouth_quality
            )
        
        # Head Pose Analysis
        results["head_pose_analysis"] = self.analyze_head_pose_enhanced(
            features, frame_shape, landmark_quality, roi_stability, face_size_category
        )
        
        # Combined Analysis
        results["combined_analysis"] = self._analyze_combined_state_enhanced(results)
        results["valid"] = any([
            results.get("ear_analysis", {}).get("valid", False),
            results.get("mar_analysis", {}).get("valid", False),
            results.get("head_pose_analysis", {}).get("valid", False)
        ])
        
        # Store in history
        self.detection_history.append(results)
        
        return results
    
    def _get_face_size_factor(self, face_size_category: str) -> float:
        """Get adjustment factor based on face size"""
        factors = {
            "too_small": 0.85,      # More sensitive thresholds for small faces
            "acceptable_small": 0.92,
            "optimal": 1.0,
            "acceptable_large": 1.08,
            "too_large": 1.15,      # Less sensitive thresholds for large faces
        }
        return factors.get(face_size_category, 1.0)
    
    def _get_frame_quality_factor(self, frame_quality: Dict) -> float:
        """Get adjustment factor based on frame quality"""
        if not frame_quality:
            return 1.0
        
        brightness = frame_quality.get("brightness", 128)
        contrast = frame_quality.get("contrast", 50)
        blur_score = frame_quality.get("blur_score", 100)
        
        # Adjust based on quality metrics
        brightness_factor = 1.0
        if brightness < 60 or brightness > 200:
            brightness_factor = 0.9
        
        contrast_factor = 1.0 if contrast > 30 else 0.85
        
        blur_factor = 1.0 if blur_score > 80 else 0.8
        
        return brightness_factor * contrast_factor * blur_factor
    
    def _calculate_ear_confidence(self, ear_result: Dict, face_size_factor: float, roi_quality_factor: float) -> float:
        """Calculate confidence score for EAR detection"""
        base_confidence = 0.8
        
        # Adjust based on EAR value reasonableness
        ear_value = ear_result.get("ear_value", 0.25)
        if 0.15 <= ear_value <= 0.35:
            base_confidence += 0.15
        elif ear_value < 0.1 or ear_value > 0.4:
            base_confidence -= 0.2
        
        # Quality adjustments
        quality_confidence = (face_size_factor + roi_quality_factor) / 2.0 - 0.5
        
        return max(0.2, min(1.0, base_confidence + quality_confidence))
    
    def _calculate_mar_confidence(self, mar_result: Dict, mouth_quality_factor: float) -> float:
        """Calculate confidence score for MAR detection"""
        base_confidence = 0.75
        
        # Adjust based on MAR value reasonableness
        mar_value = mar_result.get("mar_value", 0.3)
        if 0.2 <= mar_value <= 0.8:
            base_confidence += 0.1
        elif mar_value > 1.0:
            base_confidence -= 0.3
        
        # Mouth landmark quality adjustment
        base_confidence += (mouth_quality_factor - 0.8) * 0.5
        
        return max(0.2, min(1.0, base_confidence))
    
    def _calculate_head_pose_confidence(self, head_pose_result: Dict, quality_factor: float) -> float:
        """Calculate confidence score for head pose detection"""
        base_confidence = 0.7
        
        # Adjust based on angle reasonableness
        pitch = abs(head_pose_result.get("pitch", 0))
        if pitch < 30:  # Reasonable head angles
            base_confidence += 0.2
        elif pitch > 45:  # Extreme angles might be errors
            base_confidence -= 0.3
        
        # Quality factor adjustment
        base_confidence += (quality_factor - 0.8) * 0.4
        
        return max(0.2, min(1.0, base_confidence))
    
    def _detect_speaking_pattern(self, mar_value: float, mar_result: Dict) -> bool:
        """Detect if mouth movement indicates speaking rather than yawning"""
        # Speaking typically has moderate MAR values with variation
        speaking_threshold = mar_result.get("adjusted_thresholds", {}).get("speaking", 0.35)
        yawn_threshold = mar_result.get("adjusted_thresholds", {}).get("yawn", 0.65)
        
        # Check if in speaking range
        if speaking_threshold <= mar_value < yawn_threshold * 0.8:
            # Additional checks could include temporal patterns
            return True
        
        return False
    
    def _estimate_mouth_landmark_quality(self, mouth_landmarks: List[Tuple]) -> float:
        """Estimate quality of mouth landmarks"""
        if len(mouth_landmarks) < 6:
            return 0.5
        
        # Check landmark spread and consistency
        points = np.array([(p[0], p[1]) for p in mouth_landmarks[:6]])
        
        # Calculate mouth width and height
        width = np.max(points[:, 0]) - np.min(points[:, 0])
        height = np.max(points[:, 1]) - np.min(points[:, 1])
        
        # Quality based on reasonable proportions
        if width < 10 or height < 3:  # Too small
            return 0.6
        elif width > 100 or height > 50:  # Too large
            return 0.7
        else:
            return 0.9
    
    def _calculate_multi_angle_score(self, pose_data: Dict) -> float:
        """Calculate score based on multiple head pose angles"""
        pitch = abs(pose_data.get("pitch", 0))
        yaw = abs(pose_data.get("yaw", 0))
        roll = abs(pose_data.get("roll", 0))
        
        # Combine angles with weights
        combined_score = (pitch * 1.0 + yaw * 0.7 + roll * 0.5) / 2.2
        
        # Normalize to 0-1 range (0 = normal pose, 1 = extreme pose)
        return min(1.0, combined_score / 30.0)
    
    def _analyze_combined_state_enhanced(self, results: Dict) -> Dict[str, Any]:
        """Enhanced combined state analysis"""
        combined = {
            "state": "normal",
            "confidence": 0.0,
            "alert_level": 0,
            "contributing_factors": []
        }
        
        # Collect valid analysis results
        analyses = []
        if results.get("ear_analysis", {}).get("valid"):
            analyses.append(("ear", results["ear_analysis"]))
        if results.get("mar_analysis", {}).get("valid"):
            analyses.append(("mar", results["mar_analysis"]))
        if results.get("head_pose_analysis", {}).get("valid"):
            analyses.append(("head_pose", results["head_pose_analysis"]))
        
        if not analyses:
            return combined
        
        # Calculate combined confidence and state
        total_confidence = 0.0
        alert_indicators = []
        
        for analysis_type, analysis in analyses:
            confidence = analysis.get("confidence", 0.5)
            total_confidence += confidence
            
            # Check for drowsiness indicators
            if analysis_type == "ear":
                if analysis.get("is_below_drowsy_threshold") and analysis.get("is_drowsy_duration"):
                    alert_indicators.append(("eyes_closed", confidence))
                    combined["contributing_factors"].append("prolonged_eye_closure")
            
            elif analysis_type == "mar":
                if analysis.get("is_above_yawn_threshold") and analysis.get("is_yawn_duration"):
                    alert_indicators.append(("yawning", confidence))
                    combined["contributing_factors"].append("prolonged_yawning")
            
            elif analysis_type == "head_pose":
                if analysis.get("is_head_down") and analysis.get("is_drowsy_duration"):
                    alert_indicators.append(("head_down", confidence))
                    combined["contributing_factors"].append("head_nodding")
        
        # Calculate overall confidence
        combined["confidence"] = total_confidence / len(analyses) if analyses else 0.0
        
        # Determine alert level
        if len(alert_indicators) >= 2:
            combined["state"] = "severe_drowsiness"
            combined["alert_level"] = 3
        elif len(alert_indicators) == 1:
            _, indicator_confidence = alert_indicators[0]
            if indicator_confidence > 0.8:
                combined["state"] = "moderate_drowsiness" 
                combined["alert_level"] = 2
            else:
                combined["state"] = "mild_drowsiness"
                combined["alert_level"] = 1
        
        return combined
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.detection_history:
            return {"message": "No detection history available"}
        
        recent_detections = list(self.detection_history)[-10:]
        
        return {
            "total_detections": len(self.detection_history),
            "recent_avg_confidence": np.mean([d.get("combined_analysis", {}).get("confidence", 0) for d in recent_detections]),
            "recent_alert_rate": sum(1 for d in recent_detections if d.get("combined_analysis", {}).get("alert_level", 0) > 0) / len(recent_detections),
            "component_success_rates": {
                "ear": sum(1 for d in recent_detections if d.get("ear_analysis", {}).get("valid", False)) / len(recent_detections),
                "mar": sum(1 for d in recent_detections if d.get("mar_analysis", {}).get("valid", False)) / len(recent_detections),
                "head_pose": sum(1 for d in recent_detections if d.get("head_pose_analysis", {}).get("valid", False)) / len(recent_detections)
            }
        }

# Convenience functions for backward compatibility
def create_enhanced_detector() -> EnhancedDetectionWrapper:
    """Create an enhanced detection wrapper instance"""
    return EnhancedDetectionWrapper()

# Global instance for simple usage
_enhanced_detector = None

def get_enhanced_detector() -> EnhancedDetectionWrapper:
    """Get global enhanced detector instance"""
    global _enhanced_detector
    if _enhanced_detector is None:
        _enhanced_detector = EnhancedDetectionWrapper()
    return _enhanced_detector

if __name__ == "__main__":
    # Test enhanced integration
    print("Testing Enhanced Detection Integration...")
    
    detector = create_enhanced_detector()
    
    # Mock features for testing
    mock_features = {
        "left_eye": [(100, 100, 0.1)] * 6,
        "right_eye": [(150, 100, 0.1)] * 6,
        "mouth": [(125, 150, 0.1)] * 6,
        "nose": [(125, 125, 0.1)],
        "face_outline": [(75, 75, 0.1), (175, 75, 0.1), (175, 175, 0.1), (75, 175, 0.1)]
    }
    
    # Mock quality metrics
    quality_metrics = {
        "face_size_category": "optimal",
        "roi_quality": 0.95,
        "landmark_quality": 0.9,
        "roi_stability": 0.8,
        "frame_quality": {"brightness": 120, "contrast": 45, "blur_score": 85}
    }
    
    result = detector.process_complete_detection(
        mock_features, 
        (480, 640),
        quality_metrics
    )
    
    print(f"Detection result: {result['combined_analysis']['state']}")
    print(f"Overall confidence: {result['combined_analysis']['confidence']:.2f}")
    print(f"Alert level: {result['combined_analysis']['alert_level']}")
    print(f"Contributing factors: {result['combined_analysis']['contributing_factors']}")
    
    print("✅ Enhanced integration test completed!")