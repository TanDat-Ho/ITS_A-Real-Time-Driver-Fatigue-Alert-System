# Minimal quality manager stub for backward compatibility
"""
Quality Manager stub - provides minimal interface for existing code
"""

class QualityMetrics:
    """Simple quality metrics class"""
    def __init__(self):
        self.frame_quality = 1.0
        self.face_confidence = 1.0
        self.landmark_quality = 1.0
        self.blur_score = 0.0
        self.brightness_score = 1.0
        self.contrast_score = 1.0
        
    def to_dict(self):
        return {
            'frame_quality': self.frame_quality,
            'face_confidence': self.face_confidence,
            'landmark_quality': self.landmark_quality,
            'blur_score': self.blur_score,
            'brightness_score': self.brightness_score,
            'contrast_score': self.contrast_score
        }

class QualityManager:
    """Minimal quality manager - always returns good quality metrics"""
    
    def __init__(self):
        self.frame_count = 0
        
    def update_quality_metrics(self, frame=None, face_region=None, landmarks=None, face_validation=None):
        """Return default good quality metrics"""
        self.frame_count += 1
        return QualityMetrics()
        
    def get_quality_summary(self):
        """Return summary of quality metrics"""
        return {
            'total_frames': self.frame_count,
            'average_quality': 1.0,
            'quality_trend': 'stable'
        }
        
    def is_quality_acceptable(self, metrics=None):
        """Always return True for minimal implementation"""
        return True