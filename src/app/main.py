import cv2
import time
import threading
import queue
from typing import Optional, Dict, Any
from dataclasses import dataclass
import numpy as np
import logging

# Internal imports
from .config import (
    get_fatigue_config, get_alert_color, get_recommendation,
    CAMERA_CONFIG, MEDIAPIPE_CONFIG, DISPLAY_CONFIG, COLORS
)
from ..input_layer.camera_handler import CameraHandler
from ..processing_layer.detect_landmark.landmark import FaceLandmarkDetector
from ..processing_layer.vision_processor.rule_based import RuleBasedFatigueDetector
from ..output_layer.alert_module import audio_manager, play_fatigue_alert
from ..output_layer.alert_history import log_alert_to_history, get_alert_stats_for_gui

# Enhanced input components (optional - disabled for performance)
# from ..input_layer.input_validator import IntegratedInputValidator, PerformanceMonitor
# from ..input_layer.optimized_input_config import OptimizedInputConfig

# Setup logger
logger = logging.getLogger(__name__)

# Constants
class PipelineConstants:
    """Constants for pipeline configuration"""
    MAX_FRAME_QUEUE_SIZE = 8
    MAX_RESULT_QUEUE_SIZE = 3
    CAMERA_STABILIZATION_TIME = 0.1  # Reduced from 1.0s to 0.1s for faster startup
    MAX_CAPTURE_FPS = 60   # Max 60 FPS capture rate (optimal for 30 FPS target)
    FRAME_DROP_SLEEP = 0.005
    PROCESSING_TIMEOUT = 0.1
    GUI_UPDATE_SLEEP = 0.01
    PERFORMANCE_SAMPLE_SIZE = 50
    
    # Performance thresholds
    GOOD_FPS_THRESHOLD = 25
    WARNING_FPS_THRESHOLD = 15
    GOOD_PROCESSING_TIME = 30  # ms
    WARNING_PROCESSING_TIME = 50  # ms
    LOW_DROPPED_FRAMES = 10


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
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, gui_mode: bool = False, enhanced: bool = False, detection_engine: Optional[Any] = None):
        # Core configuration
        self.config = config or get_fatigue_config()
        self.gui_mode = gui_mode  # Flag to disable OpenCV windows in GUI mode
        self.enhanced = enhanced  # Flag for enhanced input features
        self.detection_engine = detection_engine  # Optimized detection engine
        
        # Enhanced components (disabled for performance optimization)
        self.input_validator = None
        self.performance_monitor = None
        self.optimized_config = None
        self.quality_manager = None
        
        # Force disable enhanced features for best performance (29.8 FPS)
        self.enhanced = False
        logger.info("Performance mode: Enhanced features disabled for optimal camera performance")
        
        # Components
        self.camera = None
        self.landmark_detector = None
        self.fatigue_detector = None
        
        # Threading control
        self.is_running = False
        self.frame_queue = queue.Queue(maxsize=PipelineConstants.MAX_FRAME_QUEUE_SIZE)
        self.result_queue = queue.Queue(maxsize=PipelineConstants.MAX_RESULT_QUEUE_SIZE)
        
        # Performance monitoring
        self.metrics = PerformanceMetrics()
        
        # GUI communication
        self.gui_callback = None
        self._processing_times = []
        
        # Latest results for display
        self.latest_frame = None
        self.latest_result = None
        
        # GUI callback for status updates
        self.gui_status_callback = None
        
        # Cleanup flag to prevent double cleanup
        self._cleanup_done = False
    
    def initialize(self) -> bool:
        """Initialize all components"""
        try:
            # Use optimized basic config for best performance
            camera_config = CAMERA_CONFIG
            mp_config = MEDIAPIPE_CONFIG
            logger.info(f"Using optimized configuration: {camera_config['target_size']} @ {camera_config['fps_limit']}fps")
            
            self.camera = CameraHandler(**camera_config)
            
            # Start camera
            if not self.camera.start():
                raise RuntimeError("Failed to start camera")
                
            self.landmark_detector = FaceLandmarkDetector(**mp_config)
            self.fatigue_detector = self._create_fatigue_detector()
            
            # Validation disabled for optimal performance
            
            return True
        except Exception as e:
            from ..output_layer.logger import fatigue_logger
            fatigue_logger.logger.error(f"Initialization failed: {e}")
            if not self.gui_mode:
                print(f"❌ Initialization failed - check log file for details")
            return False
    
    def _create_fatigue_detector(self) -> RuleBasedFatigueDetector:
        """Create fatigue detector with appropriate configuration"""
        ear_config, mar_config = self._get_detection_configs()
        
        # Use basic detection until enhanced detection is fixed
        return RuleBasedFatigueDetector(
            ear_config=ear_config, 
            mar_config=mar_config,
            use_enhanced_detection=False,  # Temporarily disable enhanced detection
            use_optimized_engine=False
        )
    
    def _get_detection_configs(self) -> tuple:
        """Get EAR and MAR configurations based on current config"""
        if isinstance(self.config, str):
            return self._get_string_configs()
        elif isinstance(self.config, dict):
            return self._get_dict_configs()
        else:
            return self._get_default_configs()
    
    def _get_string_configs(self) -> tuple:
        """Get configs for string-based configuration"""
        config_map = {
            "high": (
                {"blink_threshold": 0.25, "drowsy_threshold": 0.25},
                {"yawn_threshold": 0.7}
            ),
            "low": (
                {"blink_threshold": 0.2, "drowsy_threshold": 0.2},
                {"yawn_threshold": 0.8}
            )
        }
        return config_map.get(self.config, self._get_default_configs())
    
    def _get_dict_configs(self) -> tuple:
        """Get configs for dict-based configuration"""
        ear_config = {
            "blink_threshold": self.config.get("ear_threshold", 0.22),
            "drowsy_threshold": self.config.get("ear_threshold", 0.22)
        }
        mar_config = {
            "yawn_threshold": self.config.get("mar_threshold", 0.75)
        }
        return ear_config, mar_config
    
    def _get_default_configs(self) -> tuple:
        """Get default configurations"""
        ear_config = {"blink_threshold": 0.22, "drowsy_threshold": 0.22}
        mar_config = {"yawn_threshold": 0.75}
        return ear_config, mar_config
    
    def _capture_thread(self):
        """Dedicated capture thread with performance monitoring"""
        # Camera already started in initialize() - no need to start again
        time.sleep(PipelineConstants.CAMERA_STABILIZATION_TIME)
        
        frame_count = 0
        last_time = time.time()
        
        while self.is_running:
            frame_data = self.camera.get_frame()
            if frame_data is None:
                continue
            frame = frame_data['frame']
            
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
            time.sleep(PipelineConstants.FRAME_DROP_SLEEP)
    
    def _processing_thread(self):
        """Dedicated processing thread with performance tracking"""
        processing_count = 0
        last_time = time.time()
        
        while self.is_running:
            try:
                frame = self.frame_queue.get(timeout=PipelineConstants.PROCESSING_TIMEOUT)
            except queue.Empty:
                continue
            
            # Process frame with timing
            start_time = time.time()
            result = self._process_single_frame(frame)
            process_time = time.time() - start_time
            
            # Performance tracking
            self._processing_times.append(process_time)
            if len(self._processing_times) > PipelineConstants.PERFORMANCE_SAMPLE_SIZE:
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
        """Process a single frame - core detection logic with enhanced validation"""
        if frame is None:
            return None
        
        self.metrics.total_frames += 1
        
        # Enhanced input validation if enabled
        quality_metrics = None
        if self.enhanced and self.input_validator:
            # Validate frame quality
            frame_validation = self.input_validator.frame_validator.validate_frame(frame)
            if not frame_validation.valid:
                logger.debug(f"Frame quality insufficient: {frame_validation.errors}")
                return frame, None  # Return original frame instead of None
                
            # Add performance metrics
            if self.performance_monitor:
                frame_quality = frame_validation.confidence
                processing_start = time.time()
            
            # Update quality manager if available
            if self.quality_manager:
                quality_metrics = self.quality_manager.update_quality_metrics(
                    frame_validation=frame_validation
                )
        
        # Face landmark detection
        landmarks, annotated, detection_info = self.landmark_detector.detect(frame, draw=False)
        if not landmarks:
            return annotated, None
        
        # Enhanced landmark validation if enabled
        if self.enhanced and self.input_validator:
            landmark_validation = self.input_validator.landmark_validator.validate_landmarks(
                landmarks, frame.shape
            )
            if not landmark_validation.valid:
                logger.debug(f"Landmark quality insufficient: {landmark_validation.warnings}")
                # Still continue processing but log the issue
            
            # Update quality manager with landmark info
            if self.quality_manager and quality_metrics:
                landmark_result = {
                    "valid": landmark_validation.valid,
                    "landmark_count": len(landmarks),
                    "processing_time": time.time() - processing_start if 'processing_start' in locals() else 0.0,
                    "stability_score": landmark_validation.confidence
                }
                quality_metrics = self.quality_manager.update_quality_metrics(
                    frame_validation=frame_validation,
                    landmark_result=landmark_result
                )
        
        self.metrics.faces_detected += 1
        
        # Extract facial features
        features = self.landmark_detector.extract_important_points(landmarks)
        if not features:
            return annotated, None
        
        # Debug overlay disabled for clean video output
        
        # Fatigue analysis
        try:
            # Pass quality metrics to enhanced fatigue detector
            if self.enhanced and quality_metrics:
                fatigue_result = self.fatigue_detector.process_frame(
                    features=features, 
                    frame_shape=frame.shape,
                    frame_validation=frame_validation if 'frame_validation' in locals() else None,
                    landmark_result=landmark_result if 'landmark_result' in locals() else None
                )
            else:
                fatigue_result = self.fatigue_detector.process_frame(features, frame.shape)
            
            # Update alert counter for all non-NONE alerts
            if fatigue_result and fatigue_result["alert_level"].value != "NONE":
                alert_level = fatigue_result["alert_level"].value
                self.metrics.alerts_triggered += 1
                self._handle_alert(alert_level)
            
            # Enhanced performance monitoring
            if self.enhanced and self.performance_monitor:
                processing_time = time.time() - processing_start
                landmark_count = len(landmarks)
                self.performance_monitor.add_metrics(frame_quality, landmark_count, processing_time)
            
            return annotated, fatigue_result
            
        except Exception as e:
            from ..output_layer.logger import fatigue_logger
            fatigue_logger.logger.error(f"Processing error: {e}")
            return annotated, None
    
    def _handle_alert(self, alert_level: str):
        """Handle critical alerts - log to history and play audio"""
        from ..output_layer.logger import fatigue_logger
        

        
        alert_details = {
            "level": alert_level,
            "timestamp": time.time()
        }
        
        # Log to file logger (traditional logging)
        fatigue_logger.log_alert(alert_level, alert_details)
        
        # Log to alert history manager (new system)
        confidence = getattr(self.latest_result, 'confidence', 0.8) if self.latest_result else 0.8
        ear_value = getattr(self.latest_result, 'ear', None) if self.latest_result else None
        mar_value = getattr(self.latest_result, 'mar', None) if self.latest_result else None
        head_pose = getattr(self.latest_result, 'head_pose_score', None) if self.latest_result else None
        
        log_alert_to_history(
            alert_level=alert_level,
            confidence=confidence,
            ear_value=ear_value,
            mar_value=mar_value,
            head_pose=head_pose
        )
        
        # Play audio alert
        play_fatigue_alert(alert_level)
        
        # Send alert to GUI if in GUI mode
        if self.gui_mode and hasattr(self, 'gui_callback') and self.gui_callback:
            alert_message = self._format_alert_message(alert_level, confidence, ear_value, mar_value, head_pose)
            alert_type = self._get_alert_display_type(alert_level)
            self.gui_callback('alert', alert_message, alert_type)
        

    
    def _format_alert_message(self, alert_level, confidence, ear_value, mar_value, head_pose):
        """Format alert message for GUI display"""
        alert_icons = {
            "NONE": "✅", "LOW": "⚠️", "MEDIUM": "🚨", 
            "HIGH": "🔴", "CRITICAL": "🆘"
        }
        
        icon = alert_icons.get(alert_level, "⚠️")
        message = f"{icon} {alert_level} Alert (Conf: {confidence:.2f})"
        
        # Add detection details
        details = []
        if ear_value is not None:
            details.append(f"EAR: {ear_value:.3f}")
        if mar_value is not None:
            details.append(f"MAR: {mar_value:.3f}")
        if head_pose is not None:
            details.append(f"Head: {head_pose:.1f}°")
            
        if details:
            message += f" | {' | '.join(details)}"
            
        return message
    
    def _get_alert_display_type(self, alert_level):
        """Get display type for GUI alert color coding"""
        if alert_level in ["CRITICAL", "HIGH"]:
            return "critical"
        elif alert_level in ["MEDIUM", "LOW"]:
            return "warning"
        else:
            return "info"
    
    def set_gui_callback(self, callback):
        """Set callback function to communicate with GUI"""
        self.gui_callback = callback
    
    def _draw_ui(self, frame: np.ndarray, fatigue_result: Optional[Dict]) -> np.ndarray:
        """Clean, comprehensive UI with performance overlay - works for both CLI and GUI"""
        if frame is None:
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        h, w = frame.shape[:2]
        
        # === Main Status Area (Top Left) ===
        y = 25
        status_text = "🎥 LIVE DETECTION" if self.gui_mode else "🚀 OPTIMIZED PIPELINE"
        cv2.putText(frame, status_text, (10, y), 
                   DISPLAY_CONFIG["font"], 0.6, (0, 255, 0), 2)
        y += 25
        
        if fatigue_result:
            alert = fatigue_result["alert_level"].value
            color = get_alert_color(alert)
            
            # Alert level with emoji
            alert_icons = {
                "NONE": "✅", "LOW": "⚠️", "MEDIUM": "🚨", 
                "HIGH": "🔴", "CRITICAL": "🆘"
            }
            alert_text = f"{alert_icons.get(alert, '⚠️')} {alert}"
            cv2.putText(frame, alert_text, (10, y), 
                       DISPLAY_CONFIG["font"], 0.7, color, 2)
            y += 23
            
            # Show confidence only if not NONE
            if alert != "NONE":
                conf = fatigue_result["confidence"]
                cv2.putText(frame, f"Confidence: {conf:.2f}", (10, y), 
                           DISPLAY_CONFIG["font"], 0.5, color, 1)
                y += 20
            
            # Detection metrics with visual indicators
            metric_icons = {"ear": "👁️", "mar": "👄", "head_pose": "🗣️"}
            metric_labels = {"ear": "EAR", "mar": "MAR", "head_pose": "HEAD"}
            
            for key, label in [("ear", "EAR"), ("mar", "MAR"), ("head_pose", "HEAD")]:
                val = fatigue_result.get(key if key != "head_pose" else "head_pose")
                if val:
                    state_key = f"{key.split('_')[0]}_state"
                    state = fatigue_result.get(state_key)
                    if state:
                        display_val = val.get(f"{key}_value", val.get("pitch", 0))
                        icon = metric_icons.get(key, "📊")
                        
                        # Color code by state
                        state_colors = {
                            "NORMAL": (0, 255, 0),    # Green
                            "WARNING": (0, 255, 255), # Yellow  
                            "DROWSY": (0, 0, 255),    # Red
                            "YAWNING": (255, 0, 255)  # Magenta
                        }
                        metric_color = state_colors.get(state.value, COLORS["TEXT_NORMAL"])
                        
                        cv2.putText(frame, f"{icon} {label}: {display_val:.2f}",
                                   (10, y), DISPLAY_CONFIG["font"], 0.45, metric_color, 1)
                        y += 16
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
        """Draw performance metrics overlay - simplified for GUI mode"""
        h, w = frame.shape[:2]
        
        if self.gui_mode:
            # Compact version for GUI - top right corner
            y_pos = 25
            x_pos = w - 150
            
            # Just show FPS in compact form
            fps_text = f"📊 {self.metrics.processing_fps:.1f} FPS"
            cv2.putText(frame, fps_text, (x_pos, y_pos), 
                       DISPLAY_CONFIG["font"], 0.5, self._get_fps_color(self.metrics.processing_fps), 1)
            
            # Show dropped frames if any
            if self.metrics.dropped_frames > 0:
                cv2.putText(frame, f"📦 {self.metrics.dropped_frames} dropped", (x_pos, y_pos + 20), 
                           DISPLAY_CONFIG["font"], 0.4, (0, 0, 255), 1)
        else:
            # Full version for CLI mode
            y_start = h - 120
            
            # Performance background
            cv2.rectangle(frame, (5, y_start - 5), (320, h - 55), (0, 0, 0), -1)
            cv2.rectangle(frame, (5, y_start - 5), (320, h - 55), COLORS["TEXT_NORMAL"], 1)
            
            # Metrics with color coding
            metrics_data = [
                (f"📹 Capture: {self.metrics.capture_fps:.1f} FPS", self._get_fps_color(self.metrics.capture_fps)),
                (f"🧠 Process: {self.metrics.processing_fps:.1f} FPS", self._get_fps_color(self.metrics.processing_fps)),
                (f"⏱️  Time: {self.metrics.avg_processing_time*1000:.1f}ms", self._get_time_color(self.metrics.avg_processing_time)),
                (f"📦 Dropped: {self.metrics.dropped_frames}", self._get_dropped_color(self.metrics.dropped_frames))
            ]
            
            for i, (text, color) in enumerate(metrics_data):
                cv2.putText(frame, text, (10, y_start + i * 14), 
                           DISPLAY_CONFIG["font"], 0.4, color, 1)
    
    def _get_fps_color(self, fps):
        """Color coding for FPS values"""
        if fps >= PipelineConstants.GOOD_FPS_THRESHOLD: 
            return (0, 255, 0)      # Green
        elif fps >= PipelineConstants.WARNING_FPS_THRESHOLD: 
            return (0, 255, 255)    # Yellow  
        else: 
            return (0, 0, 255)      # Red
    
    def _get_time_color(self, time_ms):
        """Color coding for processing time"""
        time_ms *= 1000
        if time_ms <= PipelineConstants.GOOD_PROCESSING_TIME: 
            return (0, 255, 0)      # Green
        elif time_ms <= PipelineConstants.WARNING_PROCESSING_TIME: 
            return (0, 255, 255)    # Yellow
        else: 
            return (0, 0, 255)      # Red
    
    def _get_dropped_color(self, dropped):
        """Color coding for dropped frames"""
        if dropped == 0: 
            return (0, 255, 0)       # Green
        elif dropped < PipelineConstants.LOW_DROPPED_FRAMES: 
            return (0, 255, 255)     # Yellow
        else: 
            return (0, 0, 255)       # Red
    
    def run(self):
        """Main execution - start all threads and handle display"""
        if not self.initialize():
            return
        
        # Enhanced startup messages with camera status
        if self.gui_mode:
            # More detailed messages for GUI callback
            self._update_gui_status("🔧 Initializing camera...")
            time.sleep(0.5)  # Allow GUI to update
            self._update_gui_status("📹 Camera: Ready")
            self._update_gui_status("🧠 AI Engine: Ready")
            if self.enhanced:
                self._update_gui_status("🚀 Enhanced mode: Active")
            self._update_gui_status("🎥 Detection starting...")
        else:
            # Console output with enhanced status
            if self.enhanced:
                print("🚀 Starting Enhanced Detection System...")
                if self.optimized_config:
                    cam_config = self.optimized_config["camera"]
                    print(f"🎯 Hardware-adaptive: {cam_config['target_size']} @ {cam_config['fps_limit']}fps")
                print("✅ Input validation: Enabled")
                print("📊 Performance monitoring: Enabled")
            else:
                print("🚀 Starting Detection System...")
            print("📊 Logs: log/fatigue_detection_YYYY-MM-DD.log")
        
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
                
                # Display handling - always render UI overlay for camera feed
                if self.latest_frame is not None:
                    # Always draw UI overlay (needed for both CLI and GUI camera feed)
                    display_frame = self._draw_ui(self.latest_frame, self.latest_result)
                    
                    if not self.gui_mode:
                        # CLI mode: Show OpenCV window
                        cv2.imshow("Optimized Fatigue Detection", display_frame)
                    else:
                        # GUI mode: Update processed frame for GUI display
                        self.latest_frame = display_frame  # GUI will use this processed frame
                        
                        # Update GUI status if callback available
                        if self.latest_result and hasattr(self, 'gui_status_callback') and self.gui_status_callback:
                            alert_level = self.latest_result.get('alert_level')
                            if alert_level and hasattr(alert_level, 'value'):
                                alert_val = alert_level.value
                                if alert_val != 'NONE':
                                    self.gui_status_callback('alert', f"🚨 {alert_val} Alert")
                                else:
                                    self.gui_status_callback('status', f"👁️ Monitoring... FPS: {self.metrics.processing_fps:.1f}")
                    
                    display_count += 1
                
                # Calculate display FPS
                current_time = time.time()
                if current_time - last_display_time >= 1.0:
                    self.metrics.display_fps = display_count / (current_time - last_display_time)
                    display_count = 0
                    last_display_time = current_time
                
                # Handle user input (skip in GUI mode)
                if not self.gui_mode:
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('r'):
                        self._reset_system()
                    elif key == ord('s'):
                        self._save_snapshot()
                    elif key == ord('p'):
                        self._print_detailed_stats()
                else:
                    # In GUI mode, just wait a bit to prevent high CPU usage
                    time.sleep(PipelineConstants.GUI_UPDATE_SLEEP)
        
        except KeyboardInterrupt:
            print("\n⌨️ Interrupted by user")
        finally:
            self._cleanup()
    
    def _reset_system(self):
        """Reset all system states"""
        if self.fatigue_detector:
            self.fatigue_detector.reset_session()
        self.metrics.alerts_triggered = 0
        self.metrics.dropped_frames = 0
        self._processing_times.clear()
        if not self.gui_mode:
            print("🔄 System reset")
    
    def _save_snapshot(self):
        """Save current frame"""
        if self.latest_frame is not None:
            timestamp = int(time.time())
            filename = f"fatigue_snapshot_{timestamp}.jpg"
            cv2.imwrite(filename, self.latest_frame)
            if not self.gui_mode:
                print(f"📸 Saved: {filename}")
        else:
            if not self.gui_mode:
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
    
    def stop(self):
        """Public method to stop the pipeline"""
        if hasattr(self, '_cleanup_done') and self._cleanup_done:
            return  # Already stopped
            
        print("⏹️ Stopping pipeline...")
        self.is_running = False
        self._cleanup()
    
    def _cleanup(self):
        """Clean resource cleanup"""
        if hasattr(self, '_cleanup_done') and self._cleanup_done:
            return  # Already cleaned up
            
        try:
            from ..output_layer.logger import fatigue_logger
            
            self.is_running = False
            
            # Log session summary
            summary = {
                "total_frames": self.metrics.total_frames,
                "faces_detected": self.metrics.faces_detected, 
                "alerts_triggered": self.metrics.alerts_triggered,
                "avg_fps": f"{self.metrics.processing_fps:.1f}"
            }
            fatigue_logger.log_session_end(summary)
            
            # Safe cleanup with error handling
            if self.camera:
                try:
                    self.camera.release()
                except Exception as e:
                    print(f"Warning: Camera cleanup error: {e}")
                finally:
                    self.camera = None
                    
            if self.landmark_detector:
                try:
                    self.landmark_detector.release()
                except Exception as e:
                    print(f"Warning: Landmark detector cleanup error: {e}")
                finally:
                    self.landmark_detector = None
            
            # Cleanup audio system
            try:
                audio_manager.cleanup()
            except Exception as e:
                print(f"Warning: Audio cleanup error: {e}")
            
            # Close OpenCV windows
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
                
                if not self.gui_mode:
                    print("✅ Session ended - Check log file for details")
            
        except Exception as e:
            print(f"Warning: Cleanup error: {e}")
        finally:
            self._cleanup_done = True


    
    def set_gui_status_callback(self, callback):
        """Set callback function for GUI status updates"""
        self.gui_status_callback = callback
    
    def _update_gui_status(self, message):
        """Update GUI status if callback is available"""
        if hasattr(self, 'gui_status_callback') and self.gui_status_callback:
            self.gui_status_callback('status', message)
        else:
            print(message)
        
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get real-time alert statistics for GUI display"""
        return get_alert_stats_for_gui()
    
    def export_alert_history(self, format: str = 'json') -> str:
        """Export alert history to file"""
        from ..output_layer.alert_history import alert_history
        return alert_history.export_session_data(format)
    
    def clear_alert_history(self):
        """Clear current alert history"""
        from ..output_layer.alert_history import alert_history
        alert_history.clear_session()


def create_pipeline(config: Optional[Dict[str, Any]] = None, gui_mode: bool = False, enhanced: bool = False, detection_engine: Optional[Any] = None) -> OptimizedFatigueDetectionPipeline:
    """Factory function for creating optimized pipeline with optional detection engine"""
    return OptimizedFatigueDetectionPipeline(config, gui_mode, enhanced, detection_engine)


if __name__ == "__main__":
    print("🚀 Starting Clean Optimized Pipeline...")
    pipeline = create_pipeline()
    pipeline.run()
