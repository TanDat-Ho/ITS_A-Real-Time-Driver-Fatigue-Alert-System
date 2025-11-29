"""
optimized_input_config.py
-----------------
Cleaned optimized configuration for drowsy detection input layer.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OptimizedInputConfig:
    """Optimized configuration for drowsy detection input"""
    
    # Optimal configuration for drowsiness detection (30 FPS standard)
    BASE_CAMERA_CONFIG = {
        "src": 0,
        "queue_size": 1,           # Minimal buffer for lowest latency
        "target_size": (640, 480), # High quality capture
        "processing_size": (320, 240), # Resize for processing speed
        "color": "bgr",            # Standard color format
        "normalize": False,
        "fps_limit": 30.0,         # Smooth 30 FPS for real-time
        "auto_reconnect": True,
        "validate_quality": False, # Disable for performance
        # Optimized camera properties
        "brightness": 80,          # Optimal brightness for 130-140 range
        "contrast": 40,            # User recommended contrast
        "exposure": -8,            # Reduced exposure for optimal brightness
        "auto_exposure": 0.25,     # Auto exposure enabled
        "auto_wb": 1,              # Auto white balance
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
        """Get comprehensive hardware information including GPU"""
        hardware_info = {
            "cpu_cores": 4,
            "memory_gb": 8.0,
            "memory_available_gb": 4.0,
            "gpu_available": False,
            "gpu_count": 0,
            "gpu_memory_mb": 0
        }
        
        try:
            import psutil
            hardware_info.update({
                "cpu_cores": psutil.cpu_count(logical=False),
                "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
                "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 1)
            })
        except Exception as e:
            logger.warning(f"Could not get CPU/memory info: {e}")
            
        # GPU detection
        try:
            import cv2
            gpu_count = cv2.cuda.getCudaEnabledDeviceCount()
            if gpu_count > 0:
                hardware_info["gpu_available"] = True
                hardware_info["gpu_count"] = gpu_count
                logger.info(f"Detected {gpu_count} CUDA-enabled GPU(s)")
        except Exception as e:
            logger.debug(f"GPU detection failed: {e}")
            
        return hardware_info
    
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
        
        # Adapt based on CPU performance (30 FPS standard with processing resize)
        if cpu_cores < 4:
            config["camera"]["target_size"] = (480, 360)    # Reduced capture for low-end
            config["camera"]["processing_size"] = (240, 180) # Smaller processing
            config["camera"]["fps_limit"] = 25.0
            config["camera"]["queue_size"] = 1
            config["mediapipe"]["refine_landmarks"] = False
            config["mediapipe"]["min_detection_confidence"] = 0.6
            logger.info("Applied low-end CPU optimizations")
            
        elif cpu_cores >= 8:
            config["camera"]["target_size"] = (640, 480)    # Full quality
            config["camera"]["processing_size"] = (320, 240) # Standard processing
            config["camera"]["fps_limit"] = 30.0            # Full 30 FPS
            config["camera"]["queue_size"] = 2
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
            
        # GPU optimizations
        gpu_available = hardware_info.get("gpu_available", False)
        config["gpu"] = {
            "enabled": gpu_available,
            "acceleration": gpu_available,
            "preprocessing": gpu_available
        }
        
        if gpu_available:
            # Enhanced settings for GPU systems (full 30 FPS capability)
            config["camera"]["target_size"] = (640, 480)     # High quality capture
            config["camera"]["processing_size"] = (320, 240)  # GPU can handle resize
            config["camera"]["fps_limit"] = 30.0            # Full 30 FPS with GPU
            config["camera"]["queue_size"] = 2
            config["mediapipe"]["refine_landmarks"] = True
            logger.info("Applied GPU acceleration optimizations (30 FPS)")
        
        return config
    
    @classmethod 
    def get_environment_adaptive_config(cls, lighting_condition: str = "auto") -> Dict[str, Any]:
        """Get environment-adaptive configuration"""
        base_config = cls.adapt_for_hardware()
        
        # Lighting-based adaptations
        if lighting_condition == "bright":
            base_config["camera"]["brightness"] = -10  # Reduce brightness
            base_config["camera"]["exposure"] = -2     # Reduce exposure
            base_config["mediapipe"]["min_detection_confidence"] = 0.6
            logger.info("Applied bright environment optimizations")
            
        elif lighting_condition == "dark":
            base_config["camera"]["brightness"] = 10   # Increase brightness
            base_config["camera"]["exposure"] = 1      # Increase exposure
            base_config["mediapipe"]["min_detection_confidence"] = 0.8
            logger.info("Applied dark environment optimizations")
            
        elif lighting_condition == "auto":
            # Let adaptive systems handle automatically
            base_config["adaptive"] = {
                "auto_brightness": True,
                "auto_exposure": True,
                "dynamic_thresholds": True
            }
            logger.info("Applied automatic environment adaptation")
            
        return base_config


# Convenience function for external usage
def get_optimized_config() -> Dict[str, Any]:
    """Get optimized configuration with hardware adaptation"""
    return OptimizedInputConfig.adapt_for_hardware()