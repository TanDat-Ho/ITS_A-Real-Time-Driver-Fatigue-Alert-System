"""
Integration Module cho Optimized Detection System
Tích hợp tất cả optimized detection rules với thresholds mới
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import time

from .ear import calculate_ear, analyze_ear_state
from .mar import calculate_mar, analyze_mar_state  
from .head_pose import calculate_head_pose, analyze_head_pose_state
from .optimized_thresholds import OptimizedThresholds, get_ear_thresholds, get_mar_thresholds, get_head_pose_thresholds

class OptimizedDetectionEngine:
    """
    Engine tích hợp tất cả detection rules với thresholds tối ưu
    """
    
    def __init__(self, lighting_condition: str = "normal", camera_quality: str = "medium"):
        """
        Initialize detection engine với adaptive thresholds
        
        Args:
            lighting_condition: low, normal, bright
            camera_quality: low, medium, high
        """
        self.lighting_condition = lighting_condition
        self.camera_quality = camera_quality
        
        # Load adaptive thresholds
        self.thresholds = OptimizedThresholds.get_adaptive_thresholds(
            lighting_condition, camera_quality
        )
        
        # State tracking
        self.detection_history = []
        self.last_alert_time = 0
        self.frame_count = 0
        
        print(f"🔧 OptimizedDetectionEngine initialized")
        print(f"   Lighting: {lighting_condition}, Camera: {camera_quality}")
        print(f"   EAR blink threshold: {self.thresholds['ear']['blink_threshold']}")
        print(f"   MAR yawn threshold: {self.thresholds['mar']['yawn_threshold']}")
        print(f"   Head pose drowsy threshold: {self.thresholds['head_pose']['drowsy_threshold']}")
    
    def process_frame(self, landmarks: Dict[str, List], frame_shape: Tuple[int, int]) -> Dict[str, Any]:
        """
        Process một frame với optimized detection
        
        Args:
            landmarks: Dict chứa landmarks từ MediaPipe
            frame_shape: (height, width) của frame
            
        Returns:
            Dict chứa kết quả detection và analysis
        """
        self.frame_count += 1
        current_time = time.time()
        
        results = {
            "frame_count": self.frame_count,
            "timestamp": current_time,
            "ear_analysis": None,
            "mar_analysis": None, 
            "head_pose_analysis": None,
            "combined_state": "normal",
            "confidence": 0.0,
            "should_alert": False
        }
        
        try:
            # EAR Analysis với optimized thresholds
            if "left_eye" in landmarks and "right_eye" in landmarks:
                left_eye = landmarks["left_eye"]
                right_eye = landmarks["right_eye"]
                
                if len(left_eye) >= 6 and len(right_eye) >= 6:
                    # Calculate EAR
                    left_ear = calculate_ear(left_eye)
                    right_ear = calculate_ear(right_eye)
                    avg_ear = (left_ear + right_ear) / 2.0
                    
                    # Analyze với optimized thresholds
                    ear_thresholds = self.thresholds["ear"]
                    results["ear_analysis"] = analyze_ear_state(
                        avg_ear,
                        blink_threshold=ear_thresholds["blink_threshold"],
                        blink_frames=ear_thresholds["blink_frames"],
                        drowsy_threshold=ear_thresholds["drowsy_threshold"],
                        drowsy_duration=ear_thresholds["drowsy_duration"]
                    )
            
            # MAR Analysis với optimized thresholds  
            if "mouth" in landmarks:
                mouth_landmarks = landmarks["mouth"]
                if len(mouth_landmarks) >= 20:  # MediaPipe mouth có 20 points
                    # Extract key mouth points for MAR calculation
                    # Points theo MediaPipe mouth landmarks mapping
                    mouth_points = [
                        mouth_landmarks[0],   # left_corner  
                        mouth_landmarks[3],   # top_left
                        mouth_landmarks[9],   # top_right
                        mouth_landmarks[6],   # right_corner
                        mouth_landmarks[15],  # bottom_right
                        mouth_landmarks[12]   # bottom_left
                    ]
                    
                    # Calculate MAR
                    mar_value = calculate_mar(mouth_points)
                    
                    # Analyze với optimized thresholds
                    mar_thresholds = self.thresholds["mar"]
                    results["mar_analysis"] = analyze_mar_state(
                        mar_value,
                        yawn_threshold=mar_thresholds["yawn_threshold"],
                        yawn_duration=mar_thresholds["yawn_duration"],
                        speaking_threshold=mar_thresholds["speaking_threshold"]
                    )
            
            # Head Pose Analysis với optimized thresholds
            if all(key in landmarks for key in ["nose", "face_outline"]):
                # Construct features dict cho head pose
                features = {
                    "nose": landmarks["nose"][:1],  # Chỉ lấy nose tip
                    "face_outline": landmarks["face_outline"],
                    "left_eye": landmarks.get("left_eye", [])[:6],
                    "right_eye": landmarks.get("right_eye", [])[:6], 
                    "mouth": landmarks.get("mouth", [])[:6]
                }
                
                # Calculate head pose
                head_pose = calculate_head_pose(features, frame_shape)
                
                if head_pose:
                    # Analyze với optimized thresholds
                    hp_thresholds = self.thresholds["head_pose"]
                    results["head_pose_analysis"] = analyze_head_pose_state(
                        head_pose,
                        normal_threshold=hp_thresholds["normal_threshold"],
                        drowsy_threshold=hp_thresholds["drowsy_threshold"],
                        drowsy_duration=hp_thresholds["drowsy_duration"]
                    )
            
            # Combined Analysis
            combined_result = self._analyze_combined_state(results)
            results.update(combined_result)
            
            # Update detection history
            self.detection_history.append({
                "timestamp": current_time,
                "state": results["combined_state"],
                "confidence": results["confidence"]
            })
            
            # Giữ chỉ 30 frames gần nhất
            if len(self.detection_history) > 30:
                self.detection_history.pop(0)
                
        except Exception as e:
            print(f"❌ Error in optimized detection: {e}")
            results["error"] = str(e)
        
        return results
    
    def _analyze_combined_state(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phân tích trạng thái tổng hợp từ tất cả detection methods
        
        Args:
            results: Dict chứa kết quả từ các detection methods
            
        Returns:
            Dict chứa combined state analysis
        """
        combined_thresholds = self.thresholds["combined"]
        severity_levels = combined_thresholds["severity_levels"]
        
        # Tính confidence score từ các indicators
        confidence_scores = []
        state_indicators = []
        
        # EAR contribution
        if results["ear_analysis"]:
            ear_analysis = results["ear_analysis"]
            if ear_analysis.get("is_drowsy", False):
                confidence_scores.append(0.8)  # High confidence for EAR drowsiness
                state_indicators.append("ear_drowsy")
            elif ear_analysis.get("is_blinking", False):
                confidence_scores.append(0.3)  # Lower confidence for normal blinking
                state_indicators.append("ear_blink")
        
        # MAR contribution  
        if results["mar_analysis"]:
            mar_analysis = results["mar_analysis"]
            if mar_analysis.get("is_yawning", False):
                confidence_scores.append(0.7)  # High confidence for yawning
                state_indicators.append("mar_yawn")
            elif mar_analysis.get("is_speaking", False):
                confidence_scores.append(0.2)  # Low confidence for speaking
                state_indicators.append("mar_speak")
        
        # Head Pose contribution
        if results["head_pose_analysis"]:
            hp_analysis = results["head_pose_analysis"]
            if hp_analysis.get("is_drowsy", False):
                confidence_scores.append(0.9)  # Very high confidence for head pose
                state_indicators.append("head_drowsy")
            elif hp_analysis.get("angle") and hp_analysis["angle"] > self.thresholds["head_pose"]["normal_threshold"]:
                confidence_scores.append(0.4)  # Moderate confidence for head movement
                state_indicators.append("head_movement")
        
        # Calculate overall confidence
        overall_confidence = max(confidence_scores) if confidence_scores else 0.0
        
        # Determine combined state
        combined_state = "normal"
        should_alert = False
        
        if overall_confidence >= severity_levels["severe"]:
            combined_state = "severe_drowsiness"
            should_alert = True
        elif overall_confidence >= severity_levels["moderate"]:
            combined_state = "moderate_drowsiness" 
            should_alert = True
        elif overall_confidence >= severity_levels["mild"]:
            combined_state = "mild_drowsiness"
        
        # Check alert cooldown
        current_time = time.time()
        if should_alert and (current_time - self.last_alert_time) < combined_thresholds["alert_cooldown"]:
            should_alert = False  # In cooldown period
        
        if should_alert:
            self.last_alert_time = current_time
        
        return {
            "combined_state": combined_state,
            "confidence": overall_confidence,
            "should_alert": should_alert,
            "state_indicators": state_indicators,
            "confidence_scores": confidence_scores
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Lấy thống kê detection trong session hiện tại
        
        Returns:
            Dict chứa thống kê
        """
        if not self.detection_history:
            return {"no_data": True}
        
        recent_states = [h["state"] for h in self.detection_history[-10:]]  # 10 frames gần nhất
        recent_confidences = [h["confidence"] for h in self.detection_history[-10:]]
        
        return {
            "total_frames": self.frame_count,
            "recent_avg_confidence": np.mean(recent_confidences) if recent_confidences else 0.0,
            "recent_max_confidence": max(recent_confidences) if recent_confidences else 0.0,
            "recent_states": recent_states,
            "drowsy_frame_ratio": len([s for s in recent_states if "drowsy" in s]) / len(recent_states),
            "lighting_condition": self.lighting_condition,
            "camera_quality": self.camera_quality,
            "active_thresholds": {
                "ear_blink": self.thresholds["ear"]["blink_threshold"],
                "mar_yawn": self.thresholds["mar"]["yawn_threshold"], 
                "head_pose_drowsy": self.thresholds["head_pose"]["drowsy_threshold"]
            }
        }

# Quick access function
def create_optimized_engine(lighting: str = "normal", quality: str = "medium") -> OptimizedDetectionEngine:
    """
    Quick factory function để tạo optimized detection engine
    
    Args:
        lighting: Lighting condition
        quality: Camera quality
        
    Returns:
        OptimizedDetectionEngine instance
    """
    return OptimizedDetectionEngine(lighting, quality)

if __name__ == "__main__":
    # Test optimized detection engine
    print("=== TESTING OPTIMIZED DETECTION ENGINE ===")
    
    # Create engine
    engine = create_optimized_engine("normal", "medium")
    
    # Test with mock landmarks
    mock_landmarks = {
        "left_eye": [(100, 100, 0)] * 6,
        "right_eye": [(200, 100, 0)] * 6,
        "mouth": [(150, 150, 0)] * 20,
        "nose": [(150, 120, 0)],
        "face_outline": [(50, 50, 0), (250, 50, 0), (250, 250, 0), (50, 250, 0)]
    }
    
    # Process frame
    result = engine.process_frame(mock_landmarks, (480, 640))
    print(f"Detection result: {result['combined_state']}")
    print(f"Confidence: {result['confidence']:.2f}")
    
    # Get statistics
    stats = engine.get_statistics()
    print(f"Statistics: {stats}")
    
    print("✅ OPTIMIZED DETECTION ENGINE TEST COMPLETE!")