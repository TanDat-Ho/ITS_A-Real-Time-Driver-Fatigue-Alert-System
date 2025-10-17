import cv2
import time
import threading
import queue
from typing import Optional, Dict, Any
from dataclasses import dataclass
import numpy as np

# Internal imports
from .config import (
    get_fatigue_config, get_alert_color, get_recommendation,
    CAMERA_CONFIG, MEDIAPIPE_CONFIG, DISPLAY_CONFIG, COLORS
)
from ..input_layer.camera_handler import CameraHandler
from ..processing_layer.detect_landmark.landmark import FaceLandmarkDetector
from ..processing_layer.vision_processor.rule_based import RuleBasedFatigueDetector


@dataclass
class PerformanceMetrics:
    """Performance monitoring data structure"""
    capture_fps: float = 0.0
    processing_fps: float = 0.0
    display_fps: float = 0.0
    avg_processing_time: float = 0.0
    dropped_frames: int = 0
    total_frames: int = 0
    faces_detected: int = 0
    alerts_triggered: int = 0


class OptimizedFatigueDetectionPipeline:
    """
    Clean, optimized multi-threaded fatigue detection pipeline
    
    Architecture:
    - Capture Thread: Camera input with smart frame dropping
    - Processing Thread: Face detection + fatigue analysis
    - Display Thread: UI rendering + user interaction (main thread)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # Core configuration
        self.config = config or get_fatigue_config()
        
        # Components
        self.camera = None
        self.landmark_detector = None
        self.fatigue_detector = None
        
        # Threading control
        self.is_running = False
        self.frame_queue = queue.Queue(maxsize=8)
        self.result_queue = queue.Queue(maxsize=3)
        
        # Performance monitoring
        self.metrics = PerformanceMetrics()
        self._processing_times = []
        
        # Latest results for display
        self.latest_frame = None
        self.latest_result = None
    
    def initialize(self) -> bool:
        """Initialize all components"""
        try:
            self.camera = CameraHandler(**CAMERA_CONFIG)
            self.landmark_detector = FaceLandmarkDetector(**MEDIAPIPE_CONFIG)
            self.fatigue_detector = RuleBasedFatigueDetector(**self.config)
            print("✅ Components initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    def _capture_thread(self):
        """Dedicated capture thread with performance monitoring"""
        self.camera.start()
        time.sleep(1.0)  # Camera stabilization
        
        frame_count = 0
        last_time = time.time()
        
        while self.is_running:
            frame = self.camera.read_frame()
            if frame is None:
                continue
            
            # FPS calculation
            frame_count += 1
            current_time = time.time()
            if current_time - last_time >= 1.0:
                self.metrics.capture_fps = frame_count / (current_time - last_time)
                frame_count = 0
                last_time = current_time
            
            # Smart frame dropping - keep queue lean
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()  # Drop oldest
                    self.metrics.dropped_frames += 1
                except queue.Empty:
                    pass
            
            self.frame_queue.put(frame)
            time.sleep(0.005)  # Max 200 FPS capture rate
    
    def _processing_thread(self):
        """Dedicated processing thread with performance tracking"""
        processing_count = 0
        last_time = time.time()
        
        while self.is_running:
            try:
                frame = self.frame_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            
            # Process frame with timing
            start_time = time.time()
            result = self._process_single_frame(frame)
            process_time = time.time() - start_time
            
            # Performance tracking
            self._processing_times.append(process_time)
            if len(self._processing_times) > 50:  # Keep last 50 samples
                self._processing_times.pop(0)
            
            self.metrics.avg_processing_time = np.mean(self._processing_times)
            
            # FPS calculation
            processing_count += 1
            current_time = time.time()
            if current_time - last_time >= 1.0:
                self.metrics.processing_fps = processing_count / (current_time - last_time)
                processing_count = 0
                last_time = current_time
            
            # Store latest result
            if result:
                annotated, fatigue_result = result
                self.latest_frame = annotated
                self.latest_result = fatigue_result
                
                # Add to result queue for display
                if not self.result_queue.full():
                    self.result_queue.put(result)
    
    def _process_single_frame(self, frame: np.ndarray):
        """Process a single frame - core detection logic"""
        if frame is None:
            return None
        
        self.metrics.total_frames += 1
        
        # Face landmark detection
        landmarks, annotated = self.landmark_detector.detect(frame, draw=False)
        if not landmarks:
            return annotated, None
        
        self.metrics.faces_detected += 1
        
        # Extract facial features
        features = self.landmark_detector.extract_important_points(landmarks)
        if not features:
            return annotated, None
        
        # Draw debug overlay
        annotated = self.landmark_detector.draw_debug_overlay(annotated, features)
        
        # Fatigue analysis
        try:
            fatigue_result = self.fatigue_detector.process_frame(features, frame.shape)
            
            # Update alert counter
            if fatigue_result and fatigue_result["alert_level"].value in ["HIGH", "CRITICAL"]:
                self.metrics.alerts_triggered += 1
                self._handle_alert(fatigue_result["alert_level"].value)
            
            return annotated, fatigue_result
            
        except Exception as e:
            print(f"⚠️ Processing error: {e}")
            return annotated, None
    
    def _handle_alert(self, alert_level: str):
        """Handle critical alerts"""
        if alert_level == "CRITICAL":
            print("🆘 CRITICAL: Stop vehicle immediately!")
        elif alert_level == "HIGH":
            print("🚨 HIGH ALERT: Take a break soon!")
    
    def _draw_ui(self, frame: np.ndarray, fatigue_result: Optional[Dict]) -> np.ndarray:
        """Clean, comprehensive UI with performance overlay"""
        if frame is None:
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        h, w = frame.shape[:2]
        
        # === Main Status Area (Top Left) ===
        y = 25
        cv2.putText(frame, f"🚀 OPTIMIZED PIPELINE", (10, y), 
                   DISPLAY_CONFIG["font"], 0.7, (0, 255, 0), 2)
        y += 30
        
        if fatigue_result:
            alert = fatigue_result["alert_level"].value
            color = get_alert_color(alert)
            cv2.putText(frame, f"Status: {alert}", (10, y), 
                       DISPLAY_CONFIG["font"], 0.8, color, 2)
            y += 25
            
            conf = fatigue_result["confidence"]
            cv2.putText(frame, f"Confidence: {conf:.2f}", (10, y), 
                       DISPLAY_CONFIG["font"], 0.6, color, 1)
            y += 25
            
            # Detection metrics
            for key, label in [("ear", "EAR"), ("mar", "MAR"), ("head_pose", "Pitch")]:
                val = fatigue_result.get(key)
                if val:
                    state_key = f"{key.split('_')[0]}_state"
                    state = fatigue_result.get(state_key)
                    if state:
                        display_val = val.get(f"{key}_value", val.get("pitch", 0))
                        cv2.putText(frame, f"{label}: {display_val:.3f} ({state.value})",
                                   (10, y), DISPLAY_CONFIG["font"], 0.5, COLORS["TEXT_NORMAL"], 1)
                        y += 18
        else:
            cv2.putText(frame, "No face detected", (10, y), 
                       DISPLAY_CONFIG["font"], 0.7, COLORS["TEXT_WARNING"], 2)
        
        # === Performance Metrics (Bottom Left) ===
        self._draw_performance_overlay(frame)
        
        # === Statistics (Top Right) ===
        stats_x = w - 200
        cv2.putText(frame, f"Faces: {self.metrics.faces_detected}/{self.metrics.total_frames}", 
                   (stats_x, 30), DISPLAY_CONFIG["font"], 0.5, COLORS["TEXT_NORMAL"], 1)
        cv2.putText(frame, f"Alerts: {self.metrics.alerts_triggered}", 
                   (stats_x, 50), DISPLAY_CONFIG["font"], 0.5, COLORS["TEXT_NORMAL"], 1)
        
        # === Recommendations (Bottom Center) ===
        if fatigue_result:
            rec = get_recommendation(fatigue_result["alert_level"].value)
            if fatigue_result["alert_level"].value in ["HIGH", "CRITICAL"]:
                # Blinking warning
                if int(time.time() * 3) % 2:
                    cv2.rectangle(frame, (0, h-70), (w, h), get_alert_color(fatigue_result["alert_level"].value), -1)
                    cv2.putText(frame, rec, (10, h-25), DISPLAY_CONFIG["font"], 0.8, (255, 255, 255), 2)
            else:
                cv2.putText(frame, rec, (10, h-25), DISPLAY_CONFIG["font"], 0.6, 
                           get_alert_color(fatigue_result["alert_level"].value), 1)
        
        return frame
    
    def _draw_performance_overlay(self, frame: np.ndarray):
        """Draw performance metrics overlay"""
        h = frame.shape[0]
        y_start = h - 140
        
        # Performance background
        cv2.rectangle(frame, (5, y_start - 5), (350, h - 75), (0, 0, 0), -1)
        cv2.rectangle(frame, (5, y_start - 5), (350, h - 75), COLORS["TEXT_NORMAL"], 1)
        
        # Metrics with color coding
        metrics_data = [
            (f"📹 Capture: {self.metrics.capture_fps:.1f} FPS", self._get_fps_color(self.metrics.capture_fps)),
            (f"🧠 Process: {self.metrics.processing_fps:.1f} FPS", self._get_fps_color(self.metrics.processing_fps)),
            (f"⏱️  Avg Time: {self.metrics.avg_processing_time*1000:.1f}ms", self._get_time_color(self.metrics.avg_processing_time)),
            (f"📦 Dropped: {self.metrics.dropped_frames}", self._get_dropped_color(self.metrics.dropped_frames))
        ]
        
        for i, (text, color) in enumerate(metrics_data):
            cv2.putText(frame, text, (10, y_start + i * 15), 
                       DISPLAY_CONFIG["font"], 0.45, color, 1)
    
    def _get_fps_color(self, fps):
        """Color coding for FPS values"""
        if fps >= 25: return (0, 255, 0)      # Green
        elif fps >= 15: return (0, 255, 255)  # Yellow  
        else: return (0, 0, 255)              # Red
    
    def _get_time_color(self, time_ms):
        """Color coding for processing time"""
        time_ms *= 1000
        if time_ms <= 30: return (0, 255, 0)      # Green
        elif time_ms <= 50: return (0, 255, 255)  # Yellow
        else: return (0, 0, 255)                  # Red
    
    def _get_dropped_color(self, dropped):
        """Color coding for dropped frames"""
        if dropped == 0: return (0, 255, 0)       # Green
        elif dropped < 10: return (0, 255, 255)   # Yellow
        else: return (0, 0, 255)                  # Red
    
    def run(self):
        """Main execution - start all threads and handle display"""
        if not self.initialize():
            return
        
        print("🚀 Starting Optimized Multi-threaded Pipeline")
        print("   📹 Capture Thread: Starting...")
        print("   🧠 Processing Thread: Starting...")
        print("   🖥️  Display Thread: Main")
        print("   Controls: 'q'=quit, 'r'=reset, 's'=snapshot, 'p'=stats")
        
        self.is_running = True
        
        # Start worker threads
        capture_thread = threading.Thread(target=self._capture_thread, daemon=True)
        processing_thread = threading.Thread(target=self._processing_thread, daemon=True)
        
        capture_thread.start()
        processing_thread.start()
        
        # Main display loop
        display_count = 0
        last_display_time = time.time()
        
        try:
            while self.is_running:
                # Get latest processed frame
                try:
                    if not self.result_queue.empty():
                        self.latest_frame, self.latest_result = self.result_queue.get_nowait()
                except queue.Empty:
                    pass
                
                # Always display something
                if self.latest_frame is not None:
                    display_frame = self._draw_ui(self.latest_frame, self.latest_result)
                    cv2.imshow("Optimized Fatigue Detection", display_frame)
                    display_count += 1
                
                # Calculate display FPS
                current_time = time.time()
                if current_time - last_display_time >= 1.0:
                    self.metrics.display_fps = display_count / (current_time - last_display_time)
                    display_count = 0
                    last_display_time = current_time
                
                # Handle user input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    self._reset_system()
                elif key == ord('s'):
                    self._save_snapshot()
                elif key == ord('p'):
                    self._print_detailed_stats()
        
        except KeyboardInterrupt:
            print("\n⌨️ Interrupted by user")
        finally:
            self._cleanup()
    
    def _reset_system(self):
        """Reset all system states"""
        print("🔄 Resetting system...")
        if self.fatigue_detector:
            self.fatigue_detector.reset_session()
        self.metrics.alerts_triggered = 0
        self.metrics.dropped_frames = 0
        self._processing_times.clear()
    
    def _save_snapshot(self):
        """Save current frame"""
        if self.latest_frame is not None:
            timestamp = int(time.time())
            filename = f"fatigue_snapshot_{timestamp}.jpg"
            cv2.imwrite(filename, self.latest_frame)
            print(f"📸 Saved: {filename}")
        else:
            print("❌ No frame to save")
    
    def _print_detailed_stats(self):
        """Print comprehensive performance statistics"""
        print("\n" + "="*50)
        print("📊 DETAILED PERFORMANCE STATISTICS")
        print("="*50)
        print(f"📹 Capture FPS:     {self.metrics.capture_fps:.1f}")
        print(f"🧠 Processing FPS:  {self.metrics.processing_fps:.1f}")
        print(f"🖥️  Display FPS:     {self.metrics.display_fps:.1f}")
        print(f"⏱️  Avg Proc Time:   {self.metrics.avg_processing_time*1000:.1f}ms")
        print(f"📦 Dropped Frames:  {self.metrics.dropped_frames}")
        print(f"🎯 Total Frames:    {self.metrics.total_frames}")
        print(f"👤 Faces Detected:  {self.metrics.faces_detected}")
        print(f"🚨 Alerts Triggered: {self.metrics.alerts_triggered}")
        if self.metrics.total_frames > 0:
            detection_rate = (self.metrics.faces_detected / self.metrics.total_frames) * 100
            print(f"🎯 Detection Rate:  {detection_rate:.1f}%")
        print("="*50 + "\n")
    
    def _cleanup(self):
        """Clean resource cleanup"""
        print("🧹 Cleaning up resources...")
        self.is_running = False
        
        if self.camera:
            self.camera.release()
        if self.landmark_detector:
            self.landmark_detector.release()
        
        cv2.destroyAllWindows()
        print("✅ Cleanup complete")


def create_pipeline(config: Optional[Dict[str, Any]] = None) -> OptimizedFatigueDetectionPipeline:
    """Factory function for creating optimized pipeline"""
    return OptimizedFatigueDetectionPipeline(config)


if __name__ == "__main__":
    print("🚀 Starting Clean Optimized Pipeline...")
    pipeline = create_pipeline()
    pipeline.run()
