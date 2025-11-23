"""
optimized_input_config.py
-----------------
Optimized configuration for drowsy detection input layer.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OptimizedInputConfig:
    """Optimized configuration for drowsy detection input"""
    
    # Base camera configuration optimized for face detection
    BASE_CAMERA_CONFIG = {
        "src": 0,
        "queue_size": 5,
        "target_size": (640, 480),
        "color": "rgb",
        "normalize": False,
        "fps_limit": 25.0,
        "auto_reconnect": True,
        "validate_quality": True,
        "exposure": None,
        "brightness": None,
        "contrast": None,
    }
    
    # MediaPipe Face Mesh configuration optimized for real-time
    BASE_MEDIAPIPE_CONFIG = {
        "static_mode": False,
        "max_faces": 1,
        "refine_landmarks": True,
        "min_detection_confidence": 0.7,
        "min_tracking_confidence": 0.7
    }
    
    @classmethod
    def get_camera_config(cls) -> Dict[str, Any]:
        """Get optimized camera configuration"""
        return cls.BASE_CAMERA_CONFIG.copy()
    
    @classmethod
    def get_mediapipe_config(cls) -> Dict[str, Any]:
        """Get optimized MediaPipe configuration"""
        return cls.BASE_MEDIAPIPE_CONFIG.copy()
    
    @classmethod
    def get_hardware_info(cls) -> Dict[str, Any]:
        """Get current hardware information"""
        try:
            import psutil
            return {
                "cpu_cores": psutil.cpu_count(logical=False),
                "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
                "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 1)
            }
        except Exception as e:
            logger.warning(f"Could not get hardware info: {e}")
            return {
                "cpu_cores": 4,
                "memory_gb": 8.0,
                "memory_available_gb": 4.0
            }
    
    @classmethod
    def adapt_for_hardware(cls, hardware_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Adapt configuration based on hardware capabilities"""
        if hardware_info is None:
            hardware_info = cls.get_hardware_info()
        
        config = {
            "camera": cls.get_camera_config(),
            "mediapipe": cls.get_mediapipe_config()
        }
        
        cpu_cores = hardware_info.get("cpu_cores", 4)
        memory_available = hardware_info.get("memory_available_gb", 4.0)
        
        # Adapt based on CPU performance
        if cpu_cores < 4:
            config["camera"]["target_size"] = (480, 360)
            config["camera"]["fps_limit"] = 20.0
            config["camera"]["queue_size"] = 3
            config["mediapipe"]["refine_landmarks"] = False
            config["mediapipe"]["min_detection_confidence"] = 0.6
            logger.info("Applied low-end CPU optimizations")
            
        elif cpu_cores >= 8:
            config["camera"]["target_size"] = (640, 480)
            config["camera"]["fps_limit"] = 30.0
            config["camera"]["queue_size"] = 8
            config["mediapipe"]["refine_landmarks"] = True
            logger.info("Applied high-end CPU optimizations")
        
        # Adapt based on available memory
        if memory_available < 2.0:
            config["camera"]["queue_size"] = min(config["camera"]["queue_size"], 3)
            config["camera"]["target_size"] = (480, 360)
            logger.info("Applied low memory optimizations")
            
        elif memory_available >= 8.0:
            config["camera"]["queue_size"] = 10
            logger.info("Applied high memory optimizations")
        
        return config