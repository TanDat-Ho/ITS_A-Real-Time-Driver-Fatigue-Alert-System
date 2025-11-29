#!/usr/bin/env python3
"""
Production Camera Solution - Performance optimized for drowsiness detection
Giải pháp camera tối ưu cho production, đảm bảo performance như hệ thống cũ
"""

import cv2
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SimpleCameraHandler:
    """
    Simple camera handler với performance cao
    Thay thế cho CameraHandler phức tạp khi cần performance tối đa
    """
    
    def __init__(self, src: int = 0, target_size: tuple = (640, 480), 
                 fps_limit: float = 30.0, **kwargs):
        self.src = src
        self.target_size = target_size
        self.fps_limit = fps_limit
        self.cap = None
        self.running = False
        self.last_frame_time = 0
        
        # Camera properties từ config đã tối ưu
        self.brightness = kwargs.get('brightness', 80)
        self.contrast = kwargs.get('contrast', 40) 
        self.exposure = kwargs.get('exposure', -8)
        self.auto_exposure = kwargs.get('auto_exposure', 0.25)
        self.auto_wb = kwargs.get('auto_wb', 1)
        
        # Performance settings
        self.frame_interval = 1.0 / fps_limit if fps_limit > 0 else 0
        
    def start(self) -> bool:
        """Start camera với config tối ưu"""
        
        try:
            logger.info(f"Starting SimpleCameraHandler with source {self.src}")
            
            # Open camera
            self.cap = cv2.VideoCapture(self.src)
            
            if not self.cap.isOpened():
                logger.error(f"Cannot open camera source {self.src}")
                return False
            
            # Apply optimal settings cho drowsiness detection
            if self.target_size:
                w, h = self.target_size
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
                logger.info(f"Camera resolution set to {w}x{h}")
            
            # Performance-critical settings
            self.cap.set(cv2.CAP_PROP_FPS, self.fps_limit)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal latency
            
            # Optimal quality settings cho face detection
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.brightness)
            self.cap.set(cv2.CAP_PROP_CONTRAST, self.contrast)
            self.cap.set(cv2.CAP_PROP_EXPOSURE, self.exposure)
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, self.auto_exposure)
            self.cap.set(cv2.CAP_PROP_AUTO_WB, self.auto_wb)
            
            # Test frame read để đảm bảo hoạt động
            ret, test_frame = self.cap.read()
            if ret and test_frame is not None:
                self.running = True
                logger.info(f"SimpleCameraHandler started successfully - frame shape: {test_frame.shape}")
                return True
            else:
                logger.error("Cannot read test frame from camera")
                self.cap.release()
                return False
                
        except Exception as e:
            logger.exception(f"Error starting SimpleCameraHandler: {e}")
            if self.cap:
                self.cap.release()
            return False
    
    def get_frame(self, block: bool = False, timeout: float = 0.01) -> Optional[Dict]:
        """
        Get frame với performance cao
        Compatible với CameraHandler interface
        """
        
        if not self.running or not self.cap or not self.cap.isOpened():
            return None
            
        # Respect FPS limit
        now = time.time()
        if self.frame_interval > 0:
            time_since_last = now - self.last_frame_time
            if time_since_last < self.frame_interval:
                time.sleep(self.frame_interval - time_since_last)
                now = time.time()
        
        try:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.last_frame_time = now
                return {
                    "frame": frame,
                    "ts": now,
                    "meta": {
                        "source": "simple_camera",
                        "fps": self.fps_limit,
                        "shape": frame.shape
                    }
                }
        except Exception as e:
            logger.warning(f"Frame read error: {e}")
        
        return None
    
    def stop(self):
        """Stop camera và cleanup resources"""
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
            logger.info("SimpleCameraHandler stopped")

def create_optimized_camera(enhanced_fallback: bool = True) -> Optional[Any]:
    """
    Create camera với performance tối ưu
    
    Strategy:
    1. Try CameraHandler với minimal config (nếu enhanced_fallback=True)
    2. Fallback to SimpleCameraHandler
    3. Ensure 25-30 FPS performance
    
    Args:
        enhanced_fallback: Có thử CameraHandler trước không
    
    Returns:
        Camera instance hoặc None nếu fail
    """
    
    # Optimal config cho drowsiness detection
    optimal_config = {
        "src": 0,
        "target_size": (640, 480),
        "fps_limit": 30.0,
        "validate_quality": False,  # Critical: disable validation
        "queue_size": 1,           # Minimal queue
        "auto_reconnect": True,
        "brightness": 80,
        "contrast": 40,
        "exposure": -8,
        "auto_exposure": 0.25,
        "auto_wb": 1,
    }
    
    camera = None
    
    # Strategy 1: Try enhanced CameraHandler nếu được yêu cầu
    if enhanced_fallback:
        try:
            # Import locally to avoid issues
            import sys
            import os
            sys.path.append(os.path.dirname(__file__))
            
            from src.input_layer.camera_handler import CameraHandler
            logger.info("Attempting CameraHandler with optimal config...")
            
            camera = CameraHandler(**optimal_config)
            if camera.start():
                # Quick test để đảm bảo frames
                test_frame = camera.get_frame(timeout=1.0)
                if test_frame:
                    logger.info("✅ CameraHandler working successfully")
                    return camera
                else:
                    logger.warning("CameraHandler started but no frames - falling back")
                    camera.stop()
        except Exception as e:
            logger.warning(f"CameraHandler failed: {e}")
    
    # Strategy 2: Use SimpleCameraHandler (reliable performance)
    try:
        logger.info("Using SimpleCameraHandler for optimal performance...")
        camera = SimpleCameraHandler(**optimal_config)
        
        if camera.start():
            logger.info("✅ SimpleCameraHandler started successfully")
            return camera
        else:
            logger.error("SimpleCameraHandler failed to start")
            
    except Exception as e:
        logger.exception(f"SimpleCameraHandler error: {e}")
    
    logger.error("All camera strategies failed")
    return None

# Export cho sử dụng
__all__ = ['SimpleCameraHandler', 'create_optimized_camera']

if __name__ == "__main__":
    # Demo usage
    print("🎬 DEMO: Creating optimized camera...")
    
    # Enable logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create camera
    camera = create_optimized_camera(enhanced_fallback=False)  # Use simple only
    
    if camera:
        print("✅ Camera created successfully")
        
        # Test performance
        print("📊 Testing performance for 5 seconds...")
        start_time = time.time()
        frames = 0
        
        try:
            while time.time() - start_time < 5.0:
                frame_data = camera.get_frame()
                if frame_data:
                    frames += 1
                    if frames % 30 == 0:  # Show progress every 30 frames
                        elapsed = time.time() - start_time
                        current_fps = frames / elapsed
                        print(f"   Progress: {frames} frames, {current_fps:.1f} FPS")
                time.sleep(0.01)
                
            duration = time.time() - start_time
            fps = frames / duration if duration > 0 else 0
            
            print(f"\n📈 FINAL PERFORMANCE RESULTS:")
            print(f"   • Total frames: {frames}")
            print(f"   • Test duration: {duration:.1f}s")
            print(f"   • Average FPS: {fps:.1f}")
            print(f"   • Status: {'✅ EXCELLENT' if fps > 25 else '⚠️ NEEDS IMPROVEMENT'}")
            
            if fps > 25:
                print("\n🎉 SUCCESS: Camera performance restored to original levels!")
                print("✅ Ready for production use")
            else:
                print("\n⚠️ Performance below expected level")
                print("💡 Consider checking camera hardware or system resources")
            
        finally:
            camera.stop()
            print("🛑 Camera stopped")
    else:
        print("❌ Failed to create camera")
        print("💡 Check camera hardware and permissions")