"""
Performance-Optimized Camera Configuration
Config tối ưu hóa để khôi phục camera performance như ban đầu
"""

# CAMERA CONFIG - PERFORMANCE OPTIMIZED 
# Giảm complexity, tăng performance như hệ thống cũ
MINIMAL_CAMERA_CONFIG = {
    # Core settings - giống hệ thống cũ
    "src": 0,
    "target_size": (640, 480),  # Optimal resolution
    "color": "bgr",
    "normalize": False,         # Skip processing để tăng speed
    
    # Performance-critical settings
    "queue_size": 1,            # GIẢM từ 10 xuống 1 - critical fix!
    "fps_limit": 30.0,          # Reasonable limit
    "validate_quality": False,   # TẮT validation - major performance gain
    
    # Reliability
    "auto_reconnect": True,
    
    # Optimal camera properties (từ hệ thống cũ tốt)
    "brightness": 80,
    "contrast": 40,
    "exposure": -8,
    "auto_exposure": 0.25,
    "auto_wb": 1,
}

# Simplified input config - loại bỏ complexity
OPTIMIZED_INPUT_CONFIG = {
    "CAMERA": MINIMAL_CAMERA_CONFIG,
    
    # Simplified capture settings  
    "MAX_CAPTURE_FPS": 60,      # GIẢM từ 200 xuống 60
    "CAPTURE_TIMEOUT": 1.0,     # Quick timeout
    
    # Minimal validation
    "VALIDATION_ENABLED": False,  # TẮT validation hoàn toàn
    "QUALITY_CHECK": False,       # TẮT quality check
    
    # Simple processing
    "ENHANCED_MODE": False,       # Use basic mode only
}

def get_performance_camera_config():
    """Get performance-optimized camera config"""
    return MINIMAL_CAMERA_CONFIG.copy()

def get_simple_camera_setup():
    """Setup camera với config đơn giản như hệ thống cũ"""
    
    config = {
        "src": 0,
        "queue_size": 1,              # Critical: minimal queue
        "target_size": (640, 480),
        "color": "bgr", 
        "normalize": False,           # No processing
        "fps_limit": 30.0,
        "auto_reconnect": True,
        "validate_quality": False,    # Critical: no validation
        
        # Camera properties
        "brightness": 80,
        "contrast": 40, 
        "exposure": -8,
        "auto_exposure": 0.25,
        "auto_wb": 1,
    }
    
    return config

# Export chính
__all__ = [
    'MINIMAL_CAMERA_CONFIG',
    'OPTIMIZED_INPUT_CONFIG', 
    'get_performance_camera_config',
    'get_simple_camera_setup'
]