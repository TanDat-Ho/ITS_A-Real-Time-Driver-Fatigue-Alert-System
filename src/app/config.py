"""
config.py
-----------------
Configuration of thresholds and parameters for fatigue detection system
"""

# ===== EAR (Eye Aspect Ratio) CONFIGURATION =====
EAR_CONFIG = {
    "blink_threshold": 0.25,      # EAR threshold to detect blink
    "blink_frames": 3,            # Consecutive frames to confirm blink
    "drowsy_threshold": 0.25,     # EAR threshold to detect drowsiness
    "drowsy_duration": 1.5        # Duration (seconds) to confirm drowsiness
}

# ===== MAR (Mouth Aspect Ratio) CONFIGURATION =====
MAR_CONFIG = {
    "yawn_threshold": 0.6,        # MAR threshold to detect yawn
    "yawn_duration": 1.2,         # Duration (seconds) to confirm prolonged yawn
    "speaking_threshold": 0.4     # MAR threshold to distinguish speaking/silence
}

# ===== HEAD POSE CONFIGURATION =====
HEAD_POSE_CONFIG = {
    "normal_threshold": 12.0,     # Normal pitch angle (degrees)
    "drowsy_threshold": 20.0,     # Drowsy pitch angle (degrees)
    "drowsy_duration": 2.0        # Duration to maintain for drowsiness confirmation (seconds)
}

# ===== RULE-BASED CONFIGURATION =====
RULE_BASED_CONFIG = {
    "combination_threshold": 2,   # Minimum conditions for high warning
    "critical_duration": 3.0      # Duration to maintain for CRITICAL state
}

# ===== CAMERA CONFIGURATION =====
CAMERA_CONFIG = {
    "src": 0,                  # Camera index (0 = default camera)
    "target_size": (640, 480),    # Frame size
    "fps_limit": 30,              # FPS limit
    "color": "bgr",               # Color format (bgr or rgb)
    "normalize": False,           # Normalize pixel values
    # Optimal camera properties for drowsiness detection
    "brightness": 80,             # Optimized brightness for 130-140 range
    "contrast": 40,              # User recommended contrast
    "exposure": -8,              # Reduced exposure for optimal brightness
    "auto_exposure": 0.25,       # Auto exposure enabled
    "auto_wb": 1,                # Auto white balance
    "queue_size": 1,             # Minimal buffer for lowest latency
    "auto_reconnect": True,      # Auto reconnect on failure
    "validate_quality": False    # Disable for performance
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
