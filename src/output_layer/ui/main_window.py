"""
Main GUI application for Driver Fatigue Detection System v2.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import cv2
from PIL import Image, ImageTk
import numpy as np
import os
import time
from typing import Optional, Dict, Any

from ...app.main import create_pipeline
from .welcome_screen import AnimatedWelcomeScreen

def silent_print(*args, **kwargs):
    """Print only if not in GUI mode"""
    if os.environ.get('GUI_MODE') != '1':
        print(*args, **kwargs)

# Global root window to prevent multiple Tk instances
_global_root = None
_root_created = False

def get_root():
    """Get or create the global root window"""
    global _global_root, _root_created
    if not _root_created:
        _global_root = tk.Tk()
        _root_created = True
    return _global_root


class FatigueDetectionGUI:
    """Main GUI for Driver Fatigue Detection System"""
    
    # Class variable to track instances
    _instance = None
    _instance_created = False
    
    def __new__(cls, config: Optional[Dict[str, Any]] = None):
        """Ensure only one instance can be created"""
        if cls._instance_created:
            print("⚠️ GUI instance already exists! Returning existing instance.")
            return cls._instance
        
        instance = super().__new__(cls)
        cls._instance = instance
        cls._instance_created = True
        return instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # Skip initialization if already initialized
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.config = config
        self.pipeline = None
        self.root = None
        self.video_label = None
        self.running = False
        self.update_thread = None
        
        # GUI State
        self.welcome_screen = None
        self.main_frame = None
        self.welcome_frame = None
        
        # Performance metrics
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        
        # Alert counters
        self.alert_counts = {
            'LOW': 0,
            'MEDIUM': 0, 
            'HIGH': 0,
            'CRITICAL': 0
        }
        
    def create_gui(self):
        """Create the main GUI window"""
        # Check if GUI already exists
        if self.root is not None:
            print("⚠️ GUI already created!")
            return
            
        # Use global root to prevent multiple Tk instances
        self.root = get_root()
        self.root.title("🚗 Driver Fatigue Detection System v2.0")
        self.root.geometry("1200x900")
        self.root.configure(bg='#1a1a2e')
        
        # Configure close behavior
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Configure style
        self._configure_style()
        
        # Show welcome screen first
        self._show_welcome_screen()
        
        print("🖥️ GUI created successfully")
        
    def _configure_style(self):
        """Configure the visual style"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Header.TLabel', 
                       background='#1a1a2e',
                       foreground='white', 
                       font=('Arial', 16, 'bold'))
        
        style.configure('Info.TLabel',
                       background='#1a1a2e',
                       foreground='#cccccc',
                       font=('Arial', 10))
        
    def _show_welcome_screen(self):
        """Show the welcome screen"""
        # Create welcome frame
        self.welcome_frame = tk.Frame(self.root, bg='#1a1a2e')
        self.welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create welcome screen
        self.welcome_screen = AnimatedWelcomeScreen(self.welcome_frame, self._start_main_app)
        
    def _start_main_app(self, selected_config):
        """Start main application from welcome screen"""
        print(f"🚀 Starting main application with config: {selected_config}")
        
        # Store selected config
        self.config = selected_config
        
        # Hide welcome screen
        if self.welcome_frame:
            self.welcome_frame.destroy()
            
        # Show main interface
        self._create_main_interface()
        
        # Auto-start detection after interface is ready
        self.root.after(1000, self._auto_start_detection)  # Delay 1 second to ensure UI is ready
        
    def _auto_start_detection(self):
        """Automatically start detection after main interface is loaded"""
        try:
            print("🎥 Auto-starting camera detection...")
            self.start_detection()
        except Exception as e:
            print(f"❌ Failed to auto-start detection: {e}")
            # Show error but don't crash the app
            messagebox.showwarning("Auto-start Failed", 
                                 f"Could not automatically start detection.\n"
                                 f"Please click START manually.\n\n"
                                 f"Error: {str(e)}")
        
    def _create_main_interface(self):
        """Create the main detection interface"""
        # Main container
        self.main_frame = tk.Frame(self.root, bg='#2b2b2b')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        self._create_header(self.main_frame)
        
        # Content area
        content_frame = tk.Frame(self.main_frame, bg='#2b2b2b')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Left panel (video)
        self._create_video_panel(content_frame)
        
        # Right panel (controls and stats)
        self._create_control_panel(content_frame)
        
        print("✅ Main interface created")
        
    def _create_header(self, parent):
        """Create header section"""
        header_frame = tk.Frame(parent, bg='#1a1a1a', height=80, relief=tk.RAISED, bd=2)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(header_frame,
                              text="🚗 Driver Fatigue Detection System",
                              bg='#1a1a1a',
                              fg='white', 
                              font=('Arial', 20, 'bold'))
        title_label.pack(expand=True)
        
        # Subtitle
        subtitle_label = tk.Label(header_frame,
                                 text="Real-time monitoring and alert system",
                                 bg='#1a1a1a',
                                 fg='#cccccc',
                                 font=('Arial', 11))
        subtitle_label.pack()
        
    def _create_video_panel(self, parent):
        """Create video display panel"""
        # Video frame
        video_frame = tk.LabelFrame(parent,
                                   text="📹 Live Camera Feed",
                                   bg='#3a3a3a',
                                   fg='white',
                                   font=('Arial', 12, 'bold'),
                                   relief=tk.GROOVE,
                                   bd=2)
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Video display area
        self.video_label = tk.Label(video_frame,
                                   text="📹 CAMERA STARTING...\n\nPlease wait while we initialize detection",
                                   bg='black',
                                   fg='white',
                                   font=('Arial', 14),
                                   justify=tk.CENTER)
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def _create_control_panel(self, parent):
        """Create control panel"""
        # Control frame
        control_frame = tk.Frame(parent, bg='#3a3a3a', width=300, relief=tk.GROOVE, bd=2)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)
        control_frame.pack_propagate(False)
        
        # Controls section
        self._create_controls_section(control_frame)
        
        # Statistics section
        self._create_statistics_section(control_frame)
        
        # Alert messages section
        self._create_alert_messages_section(control_frame)
        
        # Performance section
        self._create_performance_section(control_frame)
        
    def _create_controls_section(self, parent):
        """Create control buttons section"""
        controls_frame = tk.LabelFrame(parent,
                                      text="🎮 System Controls",
                                      bg='#3a3a3a',
                                      fg='white',
                                      font=('Arial', 12, 'bold'),
                                      relief=tk.GROOVE,
                                      bd=2)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Button container
        btn_frame = tk.Frame(controls_frame, bg='#3a3a3a')
        btn_frame.pack(fill=tk.X, padx=10, pady=15)
        
        # Main control buttons
        self.start_btn = tk.Button(btn_frame,
                                  text="🚀 START DETECTION",
                                  command=self.start_detection,
                                  bg='#28a745',
                                  fg='white',
                                  font=('Arial', 11, 'bold'),
                                  height=2,
                                  relief=tk.RAISED,
                                  bd=3)
        self.start_btn.pack(fill=tk.X, pady=(0, 5))
        
        self.stop_btn = tk.Button(btn_frame,
                                 text="⏹️ STOP DETECTION",
                                 command=self.stop_detection,
                                 bg='#dc3545',
                                 fg='white',
                                 font=('Arial', 11, 'bold'),
                                 height=2,
                                 relief=tk.RAISED,
                                 bd=3,
                                 state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=5)
        
        # Secondary buttons
        save_btn = tk.Button(btn_frame,
                            text="📸 Save Screenshot",
                            command=self.save_screenshot,
                            bg='#007bff',
                            fg='white',
                            font=('Arial', 10),
                            relief=tk.RAISED,
                            bd=2)
        save_btn.pack(fill=tk.X, pady=(5, 0))
        
        # Test alert button (for development)
        test_alert_btn = tk.Button(btn_frame,
                                  text="🧪 Test Alert",
                                  command=self._test_alert_counter,
                                  bg='#ffc107',
                                  fg='black',
                                  font=('Arial', 10),
                                  relief=tk.RAISED,
                                  bd=2)
        test_alert_btn.pack(fill=tk.X, pady=(5, 0))
        
        # Back to welcome button
        back_btn = tk.Button(btn_frame,
                            text="🏠 Back to Welcome",
                            command=self._back_to_welcome,
                            bg='#6c757d',
                            fg='white',
                            font=('Arial', 10),
                            relief=tk.RAISED,
                            bd=2)
        back_btn.pack(fill=tk.X, pady=(5, 0))
        
    def _create_statistics_section(self, parent):
        """Create statistics section"""
        stats_frame = tk.LabelFrame(parent,
                                   text="📊 Alert Statistics",
                                   bg='#3a3a3a',
                                   fg='white',
                                   font=('Arial', 12, 'bold'),
                                   relief=tk.GROOVE,
                                   bd=2)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Stats content
        stats_content = tk.Frame(stats_frame, bg='#3a3a3a')
        stats_content.pack(fill=tk.X, padx=10, pady=10)
        
        # Alert level counters
        self.alert_labels = {}
        alert_colors = {
            'LOW': '#17a2b8',
            'MEDIUM': '#ffc107', 
            'HIGH': '#fd7e14',
            'CRITICAL': '#dc3545'
        }
        
        for i, (level, color) in enumerate(alert_colors.items()):
            row_frame = tk.Frame(stats_content, bg='#3a3a3a')
            row_frame.pack(fill=tk.X, pady=2)
            
            # Level icon and name
            level_icons = {'LOW': '📝', 'MEDIUM': '⚠️', 'HIGH': '🚨', 'CRITICAL': '🆘'}
            icon_label = tk.Label(row_frame,
                                 text=f"{level_icons[level]} {level}:",
                                 bg='#3a3a3a',
                                 fg='white',
                                 font=('Arial', 10),
                                 width=12,
                                 anchor='w')
            icon_label.pack(side=tk.LEFT)
            
            # Count
            count_label = tk.Label(row_frame,
                                  text="0",
                                  bg='#3a3a3a',
                                  fg=color,
                                  font=('Arial', 10, 'bold'),
                                  anchor='e')
            count_label.pack(side=tk.RIGHT)
            
            self.alert_labels[level] = count_label
    
    def _create_alert_messages_section(self, parent):
        """Create alert messages display section"""
        alert_frame = tk.LabelFrame(parent,
                                   text="📢 Current Alerts",
                                   bg='#3a3a3a',
                                   fg='white',
                                   font=('Arial', 12, 'bold'),
                                   relief=tk.GROOVE,
                                   bd=2)
        alert_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Alert content with scrollable text
        alert_content = tk.Frame(alert_frame, bg='#3a3a3a')
        alert_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add scrollbar first
        scrollbar = tk.Scrollbar(alert_content)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Current alert text display
        self.current_alert_text = tk.Text(alert_content,
                                         height=4,
                                         bg='#2c2c2c',
                                         fg='white',
                                         font=('Courier', 9),
                                         wrap=tk.WORD,
                                         state=tk.DISABLED,
                                         relief=tk.SUNKEN,
                                         bd=1,
                                         yscrollcommand=scrollbar.set)
        self.current_alert_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Connect scrollbar
        scrollbar.config(command=self.current_alert_text.yview)
        
        # Initialize with welcome message
        self._update_alert_message("🟢 System ready - No alerts", "info")
            
    def _create_performance_section(self, parent):
        """Create performance monitoring section"""
        perf_frame = tk.LabelFrame(parent,
                                  text="⚡ Performance",
                                  bg='#3a3a3a',
                                  fg='white',
                                  font=('Arial', 12, 'bold'),
                                  relief=tk.GROOVE,
                                  bd=2)
        perf_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Performance content
        perf_content = tk.Frame(perf_frame, bg='#3a3a3a')
        perf_content.pack(fill=tk.X, padx=10, pady=10)
        
        # FPS display
        fps_frame = tk.Frame(perf_content, bg='#3a3a3a')
        fps_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(fps_frame,
                text="📈 FPS:",
                bg='#3a3a3a',
                fg='white',
                font=('Arial', 10),
                anchor='w').pack(side=tk.LEFT)
        
        self.fps_label = tk.Label(fps_frame,
                                 text="0.0",
                                 bg='#3a3a3a',
                                 fg='#28a745',
                                 font=('Arial', 10, 'bold'),
                                 anchor='e')
        self.fps_label.pack(side=tk.RIGHT)
        
        # Status display
        status_frame = tk.Frame(perf_content, bg='#3a3a3a')
        status_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(status_frame,
                text="🔄 Status:",
                bg='#3a3a3a',
                fg='white',
                font=('Arial', 10),
                anchor='w').pack(side=tk.LEFT)
        
        self.status_label = tk.Label(status_frame,
                                    text="READY",
                                    bg='#3a3a3a',
                                    fg='#17a2b8',
                                    font=('Arial', 10, 'bold'),
                                    anchor='e')
        self.status_label.pack(side=tk.RIGHT)
        
    def _back_to_welcome(self):
        """Return to welcome screen"""
        # Stop detection if running
        if self.running:
            self.stop_detection()
            
        # Destroy main interface
        if self.main_frame:
            self.main_frame.destroy()
            
        # Show welcome screen again
        self._show_welcome_screen()
        
        print("🏠 Returned to welcome screen")
        
    def start_detection(self):
        """Start fatigue detection"""
        if self.running:
            return
            
        try:
            # Ensure we're not in a broken state from previous stop
            if self.pipeline:
                self.pipeline = None
                
            # Reset counters
            self.alert_counts = {level: 0 for level in self.alert_counts}
            self._update_alert_display()
            
            # Create fresh pipeline with GUI mode enabled
            silent_print("🔄 Creating new detection pipeline...")
            self.pipeline = create_pipeline(self.config, gui_mode=True)
            
            if not self.pipeline:
                raise Exception("Failed to create detection pipeline")
            
            # Set GUI callback for alert messages
            self.pipeline.set_gui_callback(self._handle_pipeline_callback)
            
            # Show system ready message
            self._update_alert_message("🚀 Detection system starting up...", "info")
            
            self.running = True
            
            # Start pipeline thread
            pipeline_thread = threading.Thread(target=self._run_pipeline, daemon=True)
            pipeline_thread.start()
            
            # Start display update thread
            self.update_thread = threading.Thread(target=self._update_display, daemon=True)
            self.update_thread.start()
            
            # Start alert monitoring thread
            self.alert_monitor_thread = threading.Thread(target=self._monitor_alert_history, daemon=True)
            self.alert_monitor_thread.start()
            
            # Update UI
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_label.config(text="RUNNING", fg='#28a745')
            self.video_label.config(text="🔄 Initializing camera...\nPlease wait")
            
            # Show success message after a short delay
            self.root.after(1000, lambda: self._update_alert_message(
                "✅ Detection pipeline active - Monitoring for fatigue", "success"))
            
            silent_print("🚀 Detection started successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start detection:\n\n{str(e)}")
            silent_print(f"❌ Start error: {e}")
            # Reset state on error
            self.running = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_label.config(text="ERROR", fg='#dc3545')
            
    def _run_pipeline(self):
        """Run the detection pipeline"""
        try:
            if self.pipeline:
                self.pipeline.run()
            else:
                print("❌ No pipeline to run")
                self.running = False
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            self.running = False
            # Reset UI state on pipeline error
            self.root.after(0, self._reset_ui_on_error)
            
    def _reset_ui_on_error(self):
        """Reset UI state when pipeline fails"""
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="ERROR", fg='#dc3545')
        self.video_label.configure(
            image="",
            text="❌ PIPELINE ERROR\n\nCheck console for details\nTry restarting detection"
        )
            
    def _update_display(self):
        """Update display with latest data"""
        while self.running:
            try:
                # Update video feed
                if self.pipeline and hasattr(self.pipeline, 'latest_frame'):
                    frame = self.pipeline.latest_frame
                    if frame is not None:
                        self._update_video_display(frame)
                        self._update_fps()
                
                time.sleep(0.1)  # 10 FPS update rate
                
            except Exception as e:
                print(f"⚠️ Display update error: {e}")
                time.sleep(0.5)
                
    def _update_video_display(self, frame):
        """Update video display"""
        try:
            # Calculate display size
            height, width = frame.shape[:2]
            max_width = 800
            max_height = 600
            
            scale = min(max_width/width, max_height/height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Resize and convert
            frame_resized = cv2.resize(frame, (new_width, new_height))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            
            # Create PhotoImage
            image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(image=image)
            
            # Update display
            self.video_label.configure(image=photo, text="")
            self.video_label.image = photo
            
        except Exception as e:
            print(f"⚠️ Video display error: {e}")
            
    def _update_fps(self):
        """Update FPS counter"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.fps_start_time)
            self.fps_label.config(text=f"{self.current_fps:.1f}")
            
            self.fps_counter = 0
            self.fps_start_time = current_time
            
    def _update_alert_display(self):
        """Update alert count display"""
        for level, count in self.alert_counts.items():
            if level in self.alert_labels:
                self.alert_labels[level].config(text=str(count))
    
    def _update_alert_message(self, message, alert_type="info"):
        """Update the alert message display
        Args:
            message: The alert message to display
            alert_type: Type of alert (info, warning, critical)
        """
        if not hasattr(self, 'current_alert_text'):
            return
            
        # Color coding for different alert types
        colors = {
            'info': '#17a2b8',      # Blue
            'warning': '#ffc107',   # Yellow  
            'critical': '#dc3545',  # Red
            'success': '#28a745'    # Green
        }
        
        color = colors.get(alert_type, '#ffffff')
        
        # Enable text widget for editing
        self.current_alert_text.config(state=tk.NORMAL)
        
        # Clear and add new message with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Keep only last 10 messages to prevent overflow
        current_content = self.current_alert_text.get("1.0", tk.END)
        lines = current_content.strip().split('\n')
        if len(lines) >= 10:
            # Remove oldest lines
            lines = lines[-(9):]  # Keep 9 lines + 1 new = 10 total
            self.current_alert_text.delete("1.0", tk.END)
            for line in lines:
                if line.strip():
                    self.current_alert_text.insert(tk.END, line + '\n')
        
        # Add new message
        self.current_alert_text.insert(tk.END, formatted_message)
        
        # Configure color for the new line
        line_start = f"{int(self.current_alert_text.index(tk.END).split('.')[0]) - 1}.0"
        line_end = f"{int(self.current_alert_text.index(tk.END).split('.')[0]) - 1}.end"
        
        # Create tag for this message type if not exists
        tag_name = f"alert_{alert_type}"
        self.current_alert_text.tag_configure(tag_name, foreground=color)
        self.current_alert_text.tag_add(tag_name, line_start, line_end)
        
        # Auto-scroll to bottom
        self.current_alert_text.see(tk.END)
        
        # Disable editing
        self.current_alert_text.config(state=tk.DISABLED)
    
    def _handle_pipeline_callback(self, callback_type, *args):
        """Handle callbacks from the detection pipeline"""
        if callback_type == 'alert' and len(args) >= 2:
            message = args[0]
            alert_type = args[1]
            
            # Update alert message display
            self._update_alert_message(message, alert_type)
            
            # Update alert counter based on alert level in message
            message_upper = message.upper()
            
            if 'CRITICAL' in message_upper:
                self.alert_counts['CRITICAL'] += 1
            elif 'HIGH' in message_upper:
                self.alert_counts['HIGH'] += 1
            elif 'MEDIUM' in message_upper:
                self.alert_counts['MEDIUM'] += 1
            elif 'LOW' in message_upper:
                self.alert_counts['LOW'] += 1
                
            # Update display
            self._update_alert_display()
    
    def _test_alert_counter(self):
        """Test alert counter functionality"""
        import random
        alert_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        level = random.choice(alert_levels)
        
        test_message = f"🧪 {level} Test Alert (Conf: 0.{random.randint(70,95)})"
        alert_type = 'warning' if level in ['LOW', 'MEDIUM'] else 'critical'
        
        self._handle_pipeline_callback('alert', test_message, alert_type)
    
    def _monitor_alert_history(self):
        """Monitor alert history to update counters even if GUI callback fails"""
        from ..alert_history import get_alert_stats_for_gui
        
        last_counts = {level: 0 for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']}
        
        while self.running:
            try:
                # Get latest alert statistics
                stats = get_alert_stats_for_gui()
                current_counts = {
                    'LOW': stats.get('low_alerts', 0),
                    'MEDIUM': stats.get('medium_alerts', 0),
                    'HIGH': stats.get('high_alerts', 0),
                    'CRITICAL': stats.get('critical_alerts', 0)
                }
                
                # Check if counts increased
                for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
                    if current_counts[level] > last_counts[level]:
                        # New alerts detected in history
                        new_alerts = current_counts[level] - last_counts[level]
                        
                        print(f"📈 HISTORY ALERT DETECTED: {level} (+{new_alerts}), Total: {current_counts[level]}")  # Debug
                        
                        # Update local counter to match history
                        self.alert_counts[level] = current_counts[level]
                        
                        # Show message for new alerts
                        if new_alerts > 0:
                            self._update_alert_message(
                                f"📊 {level} Alert detected ({new_alerts} new)", 
                                'warning' if level in ['LOW', 'MEDIUM'] else 'critical'
                            )
                
                # Update display
                self._update_alert_display()
                last_counts = current_counts.copy()
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                silent_print(f"Alert monitoring error: {e}")
                time.sleep(5)
                
    def stop_detection(self):
        """Stop fatigue detection - only stop pipeline, keep GUI running"""
        if not self.running:
            return
            
        silent_print("⏹️ Stopping detection...")
        self._update_alert_message("⏹️ Stopping detection pipeline...", "info")
        self.running = False
        
        # Stop pipeline safely without killing the whole program
        try:
            if self.pipeline:
                # Just set flag to stop, don't call full cleanup
                self.pipeline.is_running = False
                
                # Safe cleanup of components
                if hasattr(self.pipeline, 'camera') and self.pipeline.camera:
                    try:
                        self.pipeline.camera.release()
                    except Exception as e:
                        print(f"Warning: Camera cleanup error: {e}")
                
                # Don't call pipeline.stop() as it might crash the GUI
                self.pipeline = None
                
        except Exception as e:
            print(f"Warning: Pipeline stop error: {e}")
            
        # Update UI
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="STOPPED", fg='#dc3545')
        
        # Reset video display
        self.video_label.configure(
            image="",
            text="📹 DETECTION STOPPED\n\nPress START to begin again"
        )
        
        # Show stopped message
        self._update_alert_message("⏹️ Detection stopped - System ready for restart", "info")
        
        silent_print("✅ Detection stopped - GUI remains active")
        
    def save_screenshot(self):
        """Save current frame as screenshot"""
        try:
            if self.pipeline and hasattr(self.pipeline, 'latest_frame'):
                frame = self.pipeline.latest_frame
                if frame is not None:
                    import os
                    os.makedirs('output/screenshots', exist_ok=True)
                    filename = f"output/screenshots/screenshot_{int(time.time())}.jpg"
                    cv2.imwrite(filename, frame)
                    messagebox.showinfo("Screenshot Saved", f"Screenshot saved as {filename}")
                    print(f"📸 Screenshot saved: {filename}")
                else:
                    messagebox.showwarning("No Frame", "No frame available to save")
            else:
                messagebox.showwarning("Not Running", "Detection is not running")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save screenshot:\n{str(e)}")
            print(f"❌ Screenshot error: {e}")
            
    def _on_close(self):
        """Handle window close event - safe cleanup"""
        try:
            # Stop detection safely (same as stop button)
            if self.running:
                self.stop_detection()
                
            # Don't call pipeline.stop() - just set to None
            if self.pipeline:
                self.pipeline = None
                
            # Close GUI window
            if self.root:
                self.root.destroy()
                self.root = None
            
            # Reset class variables
            FatigueDetectionGUI._instance = None
            FatigueDetectionGUI._instance_created = False
            
        except Exception as e:
            print(f"Warning during close: {e}")
            # Force close anyway - but don't crash
            try:
                if self.root:
                    self.root.quit()
            except:
                pass
            finally:
                FatigueDetectionGUI._instance = None
                FatigueDetectionGUI._instance_created = False

    def run(self):
        """Start the GUI application"""
        try:
            # Ensure only one instance
            if hasattr(self, 'root') and self.root and self.root.winfo_exists():
                self.root.lift()  # Bring existing window to front
                return
                
            self.create_gui()
            print("🚀 Starting GUI main loop...")
            self.root.mainloop()
        except Exception as e:
            print(f"❌ GUI error: {e}")
            messagebox.showerror("GUI Error", f"An error occurred:\n\n{str(e)}")
        finally:
            # Always reset on exit
            FatigueDetectionGUI._instance = None
            FatigueDetectionGUI._instance_created = False


def launch_gui(config: Optional[Dict[str, Any]] = None):
    """Launch the fatigue detection GUI"""
    try:
        # Check if already running
        if (FatigueDetectionGUI._instance_created and 
            FatigueDetectionGUI._instance is not None and
            hasattr(FatigueDetectionGUI._instance, 'root') and
            FatigueDetectionGUI._instance.root and
            FatigueDetectionGUI._instance.root.winfo_exists()):
            print("⚠️ GUI is already running! Bringing to front...")
            FatigueDetectionGUI._instance.root.lift()
            FatigueDetectionGUI._instance.root.focus_force()
            return
            
        gui = FatigueDetectionGUI(config)
        gui.run()
    except Exception as e:
        print(f"❌ Failed to launch GUI: {e}")
        # Reset on error
        FatigueDetectionGUI._instance = None
        FatigueDetectionGUI._instance_created = False


if __name__ == "__main__":
    # Test the GUI - commented to prevent multiple instances
    # launch_gui()
    pass
