"""
config.py
-----------------
Configuration of thresholds and parameters for fatigue detection system
"""

# ===== EAR (Eye Aspect Ratio) CONFIGURATION =====
EAR_CONFIG = {
    "blink_threshold": 0.25,      # Balanced blink detection
    "blink_frames": 3,            # Conservative blink confirmation
    "drowsy_threshold": 0.22,     # More practical drowsiness threshold
    "drowsy_duration": 2.0        # Longer confirmation to avoid false positives
}

# ===== MAR (Mouth Aspect Ratio) CONFIGURATION =====
MAR_CONFIG = {
    "yawn_threshold": 0.7,        # Higher threshold to avoid false positives
    "yawn_duration": 1.5,         # Longer duration for genuine yawn confirmation
    "speaking_threshold": 0.5     # Clear separation from normal speaking
}

# ===== HEAD POSE CONFIGURATION =====
HEAD_POSE_CONFIG = {
    "normal_threshold": 15.0,     # Allow normal head movement
    "drowsy_threshold": 25.0,     # More conservative drowsy detection
    "drowsy_duration": 2.5        # Longer confirmation for genuine drowsiness
}

# ===== RULE-BASED CONFIGURATION =====
RULE_BASED_CONFIG = {
    "combination_threshold": 2,   # Require 2 indicators for reliable detection
    "critical_duration": 4.0      # Conservative escalation to CRITICAL
}

# ===== CAMERA CONFIGURATION =====
CAMERA_CONFIG = {
    "src": 0,                     # Camera index (0 = default camera)
    "target_size": None,          # Let camera use default size for fastest startup
    "fps_limit": 30,              # FPS limit
    "color": "bgr",               # Color format (bgr or rgb)
    "normalize": False,           # Normalize pixel values
    # Minimal settings for fastest startup
    "brightness": None,           # Skip brightness adjustment 
    "contrast": None,             # Skip contrast adjustment
    "exposure": None,             # Skip exposure adjustment
    "auto_exposure": None,        # Skip auto exposure
    "auto_wb": None,              # Skip white balance
    "queue_size": 1,              # Minimal buffer for lowest latency
    "auto_reconnect": True,       # Auto reconnect on failure
    "validate_quality": False     # Disable for performance
}

# ===== MEDIAPIPE CONFIGURATION =====
MEDIAPIPE_CONFIG = {
    "static_mode": False,
    "max_faces": 1,
    "refine_landmarks": True,
    "min_detection_confidence": 0.5,
    "min_tracking_confidence": 0.5
}

# ===== DISPLAY COLORS =====
COLORS = {
    # Colors for feature regions
    "left_eye": (0, 255, 0),      # Green - Left eye
    "right_eye": (0, 255, 255),   # Yellow - Right eye
    "mouth": (0, 0, 255),         # Red - Mouth
    "nose": (255, 0, 0),          # Blue - Nose
    "face_outline": (255, 255, 0), # Cyan - Face outline
    
    # Colors by warning level
    "NONE": (0, 255, 0),          # Green
    "LOW": (0, 255, 255),         # Yellow
    "MEDIUM": (0, 165, 255),      # Orange
    "HIGH": (0, 0, 255),          # Red
    "CRITICAL": (255, 0, 255),    # Magenta
    
    # Text and UI colors
    "TEXT_NORMAL": (255, 255, 255),   # White
    "TEXT_WARNING": (0, 255, 255),    # Yellow
    "TEXT_HIGH": (0, 0, 255),         # Red
    "BACKGROUND": (50, 50, 50)        # Dark gray
}

# ===== DISPLAY CONFIGURATION =====
DISPLAY_CONFIG = {
    "window_name": "🚗 Driver Fatigue Detection System",
    "show_fps": True,
    "show_landmarks": True,
    "show_metrics": True,
    "font": 0,  # cv2.FONT_HERSHEY_SIMPLEX
    "font_scale": 0.7,
    "thickness": 2,
    "line_spacing": 30
}

# ===== ENGLISH MESSAGES =====
MESSAGES = {
    "starting": "🎯 Starting system...",
    "camera_ready": "📹 Camera is ready",
    "no_face": "😴 No face detected",
    "face_detected": "😊 Face detected",
    "processing": "⚡ Processing...",
    "alert_drowsy": "🚨 WARNING: Drowsiness detected!",
    "alert_yawn": "🥱 WARNING: Yawn detected!",
    "alert_head_down": "💤 WARNING: Prolonged head down!",
    "critical_alert": "🆘 DANGER: Stop vehicle immediately!",
    "recommendations": {
        "NONE": "✅ Continue driving safely",
        "LOW": "⚠️ Pay attention",
        "MEDIUM": "🛑 Consider taking a break soon",
        "HIGH": "🚨 Need to rest immediately",
        "CRITICAL": "🆘 STOP VEHICLE NOW - Find safe place to rest"
    }
}

# ===== LOGGING CONFIGURATION =====
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    "handlers": {
        "console": True,
        "file": True,
        "file_path": "log/fatigue_detection.log"
    }
}

# ===== AUDIO CONFIGURATION (Optional) =====
AUDIO_CONFIG = {
    "enabled": True,
    "alert_sound": "assets/sounds/alert_beep.mp3",
    "critical_sound": "assets/sounds/critical_alarm.mp3",
    "volume": 0.8
}

# ===== FUNCTION HELPERS =====
def get_fatigue_config():
    """Get complete configuration for FatigueDetector"""
    return {
        "ear_config": EAR_CONFIG,
        "mar_config": MAR_CONFIG,
        "head_pose_config": HEAD_POSE_CONFIG,
        **RULE_BASED_CONFIG
    }

def get_alert_color(alert_level: str) -> tuple:
    """Get color corresponding to alert level"""
    return COLORS.get(alert_level, COLORS["NONE"])

def get_recommendation(alert_level: str) -> str:
    """Get recommendation corresponding to alert level"""
    return MESSAGES["recommendations"].get(alert_level, "Continue driving safely")

def get_display_text(key: str) -> str:
    """Get display text in English"""
    return MESSAGES.get(key, key)

# ===== VALIDATION =====
def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check EAR
    if EAR_CONFIG["blink_threshold"] <= 0 or EAR_CONFIG["blink_threshold"] >= 1:
        errors.append("EAR blink_threshold must be in range (0, 1)")
    
    # Check MAR
    if MAR_CONFIG["yawn_threshold"] <= 0:
        errors.append("MAR yawn_threshold must be > 0")
    
    # Check Head Pose
    if HEAD_POSE_CONFIG["normal_threshold"] >= HEAD_POSE_CONFIG["drowsy_threshold"]:
        errors.append("Head Pose normal_threshold must be < drowsy_threshold")
    
    if errors:
        raise ValueError(f"Configuration errors: {'; '.join(errors)}")
    
    return True

if __name__ == "__main__":
    # Test configuration
    try:
        validate_config()
        print("✅ Configuration is valid!")
        
        # Print main configuration
        config = get_fatigue_config()
        print(f"📋 Fatigue detection configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")
            
    except ValueError as e:
        print(f"❌ {e}")
