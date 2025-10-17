"""
main.py
-----------------
Main pipeline for driver fatigue detection system

Functions:
- Orchestrate entire pipeline from camera → processing → display
- Integrate landmark detection, rule-based analysis
- Display real-time results with English UI
- Logging and data storage
"""

import cv2
import time
import logging
import threading
from typing import Optional, Dict, Any
import numpy as np

# Import internal modules
from .config import (
    get_fatigue_config, get_alert_color, get_recommendation, get_display_text,
    CAMERA_CONFIG, MEDIAPIPE_CONFIG, DISPLAY_CONFIG, COLORS, MESSAGES
)

# Import processing layers
from ..input_layer.camera_handler import CameraHandler
from ..processing_layer.detect_landmark.landmark import FaceLandmarkDetector
from ..processing_layer.vision_processor.rule_based import RuleBasedFatigueDetector, FatigueDetectionConfig


class FatigueDetectionPipeline:
    """
    Main pipeline for fatigue detection system
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize pipeline"""
        self.setup_logging()
        self.logger = logging.getLogger("FatigueDetectionPipeline")
        
        # Load config
        self.config = config or get_fatigue_config()
        
        # Components
        self.camera = None
        self.landmark_detector = None
        self.fatigue_detector = None
        
        # State
        self.is_running = False
        self.frame_count = 0
        self.start_time = time.time()
        
        # Statistics
        self.stats = {
            "total_frames": 0,
            "faces_detected": 0,
            "alerts_triggered": 0,
            "last_alert_time": None
        }
        
        self.logger.info("🎯 Initializing fatigue detection system")
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("log/fatigue_detection.log", encoding='utf-8')
            ]
        )
    
    def initialize_components(self):
        """Initialize components"""
        try:
            # Camera
            self.logger.info("📹 Initializing camera...")
            self.camera = CameraHandler(**CAMERA_CONFIG)
            
            # Landmark detector
            self.logger.info("🎭 Initializing landmark detector...")
            self.landmark_detector = FaceLandmarkDetector(**MEDIAPIPE_CONFIG)
            
            # Fatigue detector
            self.logger.info("🧠 Initializing fatigue detector...")
            config = get_fatigue_config()
            self.fatigue_detector = RuleBasedFatigueDetector(**config)
            
            self.logger.info("✅ Successfully initialized all components")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Initialization error: {e}")
            return False
    
    def process_frame(self, frame: np.ndarray) -> tuple:
        """
        Xử lý một frame
        
        Returns:
            tuple: (annotated_frame, fatigue_result)
        """
        if frame is None:
            return None, None
        
        self.frame_count += 1
        self.stats["total_frames"] += 1
        
        # 1. Phát hiện landmarks
        landmarks, annotated = self.landmark_detector.detect(frame, draw=False)
        
        # 2. Nếu có khuôn mặt, tiến hành phân tích
        fatigue_result = None
        if landmarks:
            self.stats["faces_detected"] += 1
            
            # Trích xuất đặc trưng
            features = self.landmark_detector.extract_important_points(landmarks)
            
            if features:
                # Vẽ debug overlay
                annotated = self.landmark_detector.draw_debug_overlay(annotated, features)
                
                # Phân tích mệt mỏi
                fatigue_result = self.fatigue_detector.process_frame(features, frame.shape)
                
                # Cập nhật thống kê
                if fatigue_result["alert_level"].value in ["HIGH", "CRITICAL"]:
                    self.stats["alerts_triggered"] += 1
                    self.stats["last_alert_time"] = time.time()
        
        return annotated, fatigue_result
    
    def draw_ui(self, frame: np.ndarray, fatigue_result: Optional[Dict]) -> np.ndarray:
        """
        Vẽ giao diện người dùng trên frame
        """
        if frame is None:
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Tính FPS
        current_time = time.time()
        fps = self.frame_count / (current_time - self.start_time) if current_time > self.start_time else 0
        
        # Background overlay cho thông tin
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (400, 200), COLORS["BACKGROUND"], -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        y_offset = 30
        
        # FPS và frame count
        cv2.putText(frame, f"FPS: {fps:.1f}", 
                   (10, y_offset), DISPLAY_CONFIG["font"], 0.6, COLORS["TEXT_NORMAL"], 1)
        cv2.putText(frame, f"Frame: {self.frame_count}", 
                   (150, y_offset), DISPLAY_CONFIG["font"], 0.6, COLORS["TEXT_NORMAL"], 1)
        y_offset += 25
        
        # Thông tin phát hiện mệt mỏi
        if fatigue_result:
            alert_level = fatigue_result["alert_level"].value
            fatigue_state = fatigue_result["fatigue_state"].value
            confidence = fatigue_result["confidence"]
            
            # Màu sắc theo mức độ
            color = get_alert_color(alert_level)
            
            # Main status
            cv2.putText(frame, f"Status: {alert_level}", 
                       (10, y_offset), DISPLAY_CONFIG["font"], 0.7, color, 2)
            y_offset += 30
            
            # Độ tin cậy
            cv2.putText(frame, f"Do tin cay: {confidence:.2f}", 
                       (10, y_offset), DISPLAY_CONFIG["font"], 0.6, color, 2)
            y_offset += 25
            
            # Chi tiết các chỉ số
            if fatigue_result["ear"]:
                ear_val = fatigue_result["ear"]["ear_value"]
                ear_state = fatigue_result["eye_state"].value  # Sử dụng state mới
                cv2.putText(frame, f"EAR: {ear_val:.3f} ({ear_state})", 
                           (10, y_offset), DISPLAY_CONFIG["font"], 0.5, COLORS["TEXT_NORMAL"], 1)
                y_offset += 20
            
            if fatigue_result["mar"]:
                mar_val = fatigue_result["mar"]["mar_value"]
                mar_state = fatigue_result["mouth_state"].value  # Sử dụng state mới
                cv2.putText(frame, f"MAR: {mar_val:.3f} ({mar_state})", 
                           (10, y_offset), DISPLAY_CONFIG["font"], 0.5, COLORS["TEXT_NORMAL"], 1)
                y_offset += 20
            
            if fatigue_result["head_pose"]:
                pitch = fatigue_result["head_pose"]["pitch"]
                pose_state = fatigue_result["head_state"].value  # Sử dụng state mới
                cv2.putText(frame, f"Pitch: {pitch:.1f}° ({pose_state})", 
                           (10, y_offset), DISPLAY_CONFIG["font"], 0.5, COLORS["TEXT_NORMAL"], 1)
                y_offset += 20
            
            # Khuyến nghị
            recommendation = get_recommendation(alert_level)
            if alert_level in ["HIGH", "CRITICAL"]:
                # Cảnh báo nháy
                blink = int(time.time() * 3) % 2
                if blink:
                    cv2.rectangle(frame, (0, frame.shape[0]-80), (frame.shape[1], frame.shape[0]), color, -1)
                    cv2.putText(frame, recommendation, 
                               (10, frame.shape[0]-30), DISPLAY_CONFIG["font"], 0.8, (255, 255, 255), 2)
            else:
                cv2.putText(frame, recommendation, 
                           (10, frame.shape[0]-30), DISPLAY_CONFIG["font"], 0.6, color, 1)
        else:
            # Không phát hiện khuôn mặt
            cv2.putText(frame, get_display_text("no_face"), 
                       (10, y_offset), DISPLAY_CONFIG["font"], 0.7, COLORS["TEXT_WARNING"], 2)
        
        # Thống kê ở góc phải
        stats_x = frame.shape[1] - 200
        cv2.putText(frame, f"Khuon mat: {self.stats['faces_detected']}/{self.stats['total_frames']}", 
                   (stats_x, 30), DISPLAY_CONFIG["font"], 0.5, COLORS["TEXT_NORMAL"], 1)
        cv2.putText(frame, f"Canh bao: {self.stats['alerts_triggered']}", 
                   (stats_x, 50), DISPLAY_CONFIG["font"], 0.5, COLORS["TEXT_NORMAL"], 1)
        
        return frame
    
    def run(self):
        """Chạy pipeline chính"""
        if not self.initialize_components():
            return False
        
        self.logger.info("🚀 Bắt đầu pipeline phát hiện mệt mỏi")
        
        try:
            # Khởi động camera
            self.camera.start()
            time.sleep(1.0)  # Chờ camera ổn định
            
            self.is_running = True
            self.start_time = time.time()
            
            self.logger.info("✅ Hệ thống đã sẵn sàng - Nhấn 'q' để thoát, 'r' để reset")
            
            while self.is_running:
                # Đọc frame
                frame = self.camera.read_frame()
                
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                # Xử lý frame
                annotated, fatigue_result = self.process_frame(frame)
                
                # Vẽ UI
                display_frame = self.draw_ui(annotated, fatigue_result)
                
                # Hiển thị
                cv2.imshow(DISPLAY_CONFIG["window_name"], display_frame)
                
                # Xử lý input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.logger.info("🛑 Người dùng yêu cầu thoát")
                    break
                elif key == ord('r'):
                    self.logger.info("🔄 Reset session")
                    self.fatigue_detector.reset_session()
                    self.stats["alerts_triggered"] = 0
                elif key == ord('s'):
                    # Lưu ảnh
                    timestamp = int(time.time())
                    filename = f"snapshot_{timestamp}.jpg"
                    cv2.imwrite(filename, display_frame)
                    self.logger.info(f"📸 Đã lưu ảnh: {filename}")
                
                # Log important alerts
                if fatigue_result and fatigue_result["alert_level"].value == "CRITICAL":
                    self.logger.warning("🆘 CRITICAL ALERT: Severe fatigue detected!")
                elif fatigue_result and fatigue_result["alert_level"].value == "HIGH":
                    self.logger.warning("🚨 WARNING: Fatigue signs detected!")
        
        except KeyboardInterrupt:
            self.logger.info("⌨️  Dừng bởi người dùng (Ctrl+C)")
        except Exception as e:
            self.logger.error(f"❌ Lỗi trong quá trình chạy: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Dọn dẹp tài nguyên"""
        self.logger.info("🧹 Đang dọn dẹp tài nguyên...")
        
        self.is_running = False
        
        # Dừng camera
        if self.camera:
            self.camera.release()
        
        # Dừng landmark detector
        if self.landmark_detector:
            self.landmark_detector.release()
        
        # Đóng cửa sổ
        cv2.destroyAllWindows()
        
        # In thống kê cuối
        if self.fatigue_detector:
            summary = self.fatigue_detector.get_detection_summary()
            self.logger.info(f"📊 Thống kê phiên làm việc:")
            self.logger.info(f"   - Tổng frame: {self.stats['total_frames']}")
            self.logger.info(f"   - Phát hiện khuôn mặt: {self.stats['faces_detected']}")
            self.logger.info(f"   - Cảnh báo: {self.stats['alerts_triggered']}")
            self.logger.info(f"   - Trạng thái cuối: {summary.get('latest_state', 'UNKNOWN')}")
        
        self.logger.info("✅ Dọn dẹp hoàn tất")

    def get_current_stats(self) -> Dict[str, Any]:
        """Lấy thống kê hiện tại"""
        return {
            "uptime": time.time() - self.start_time,
            "fps": self.frame_count / (time.time() - self.start_time) if time.time() > self.start_time else 0,
            **self.stats
        }


def create_pipeline(config: Optional[Dict[str, Any]] = None) -> FatigueDetectionPipeline:
    """Factory function để tạo pipeline"""
    return FatigueDetectionPipeline(config)


if __name__ == "__main__":
    # Test pipeline
    print("🧪 Test chạy pipeline...")
    pipeline = create_pipeline()
    try:
        pipeline.run()
    except KeyboardInterrupt:
        print("\n⌨️  Test dừng bởi người dùng")
    except Exception as e:
        print(f"❌ Lỗi test: {e}")
    finally:
        print("🏁 Test hoàn tất")
    pipeline = create_pipeline()
    pipeline.run()
