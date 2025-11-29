"""
Main GUI application for Driver Fatigue Detection System v2.0
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import cv2
from PIL import Image, ImageTk
import numpy as np
import os
import time
import json
import csv
from datetime import datetime
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
        self.root.title("🚗 AI Driver Safety Monitor v2.0")
        self.root.geometry("1400x1000")  # Larger for better UX
        self.root.configure(bg='#0d1117')  # Modern dark theme
        self.root.minsize(1200, 800)  # Prevent too small windows
        
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
        """Create modern video display panel with enhanced UX"""
        # Video frame with gradient-like styling
        video_frame = tk.Frame(parent, bg='#1e1e1e', relief=tk.FLAT, bd=0)
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        # Header with status indicator
        header_frame = tk.Frame(video_frame, bg='#1e1e1e', height=40)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        header_frame.pack_propagate(False)
        
        # Status indicator
        self.status_indicator = tk.Label(header_frame,
                                        text="🟢 CAMERA READY",
                                        bg='#1e1e1e',
                                        fg='#00ff88',
                                        font=('Segoe UI', 11, 'bold'))
        self.status_indicator.pack(side=tk.LEFT, pady=8)
        
        # Video container with rounded corners effect
        video_container = tk.Frame(video_frame, bg='#0d1117', relief=tk.RAISED, bd=2)
        video_container.pack(fill=tk.BOTH, expand=True)
        
        # Video display area with modern styling
        self.video_label = tk.Label(video_container,
                                   text="🎯 AI VISION SYSTEM\n\n✨ Position your face centrally\n📐 Maintain 60-80cm distance\n🔆 Ensure optimal lighting\n\n🚀 Ready for Detection",
                                   bg='#0d1117',
                                   fg='#58a6ff',
                                   font=('Segoe UI', 13),
                                   justify=tk.CENTER)
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
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
        
        # Data Management Section
        data_frame = tk.LabelFrame(controls_frame, 
                                  text="📊 DATA MANAGEMENT",
                                  bg='#21262d',
                                  fg='#f0f6fc',
                                  font=('Segoe UI', 11, 'bold'),
                                  relief=tk.GROOVE,
                                  bd=2)
        data_frame.pack(fill=tk.X, pady=15)
        
        data_buttons = tk.Frame(data_frame, bg='#21262d')
        data_buttons.pack(fill=tk.X, padx=10, pady=10)
        
        # Row 1: View and Export
        row1 = tk.Frame(data_buttons, bg='#21262d')
        row1.pack(fill=tk.X, pady=(0, 5))
        
        tk.Button(row1,
                 text="📋 View Logs",
                 command=self._show_log_viewer,
                 bg='#0969da',
                 fg='white',
                 font=('Segoe UI', 9),
                 relief=tk.FLAT,
                 padx=15,
                 pady=6).pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        tk.Button(row1,
                 text="📊 Báo cáo Excel",
                 command=self._export_session_data,
                 bg='#238636',
                 fg='white',
                 font=('Segoe UI', 9),
                 relief=tk.FLAT,
                 padx=15,
                 pady=6).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Row 2: Clear and Screenshot
        row2 = tk.Frame(data_buttons, bg='#21262d')
        row2.pack(fill=tk.X)
        
        tk.Button(row2,
                 text="🗑️ Clear Session",
                 command=self._clear_session_data,
                 bg='#da3633',
                 fg='white',
                 font=('Segoe UI', 9),
                 relief=tk.FLAT,
                 padx=15,
                 pady=6).pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        tk.Button(row2,
                 text="📸 Screenshot",
                 command=self.save_screenshot,
                 bg='#8b5cf6',
                 fg='white',
                 font=('Segoe UI', 9),
                 relief=tk.FLAT,
                 padx=15,
                 pady=6).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
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
        """Create modern statistics section with visual metrics"""
        stats_frame = tk.Frame(parent, bg='#21262d', relief=tk.FLAT, bd=0)
        stats_frame.pack(fill=tk.X, padx=10, pady=15)
        
        # Header with icon
        header_frame = tk.Frame(stats_frame, bg='#21262d')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame,
                text="📊 ALERT ANALYTICS",
                bg='#21262d',
                fg='#f0f6fc',
                font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
        
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
        """Create modern alert display with dynamic status indicators"""
        alert_frame = tk.Frame(parent, bg='#161b22', relief=tk.FLAT, bd=0)
        alert_frame.pack(fill=tk.X, padx=10, pady=15)
        
        # Dynamic status header
        header_frame = tk.Frame(alert_frame, bg='#161b22')
        header_frame.pack(fill=tk.X, pady=(0, 12))
        
        tk.Label(header_frame,
                text="🛡️ SAFETY STATUS",
                bg='#161b22',
                fg='#f0f6fc',
                font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
        
        # Current alert status (large display)
        self.current_status_frame = tk.Frame(alert_frame, bg='#2c2c2c', relief=tk.SUNKEN, bd=2)
        self.current_status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.current_status_label = tk.Label(self.current_status_frame,
                                           text="🟢 ALERT STATUS: SAFE",
                                           bg='#2c2c2c',
                                           fg='#28a745',
                                           font=('Arial', 11, 'bold'),
                                           pady=8)
        self.current_status_label.pack()
        
        # Alert history (smaller scrollable area)
        history_label = tk.Label(alert_frame,
                                text="📝 Alert History:",
                                bg='#3a3a3a',
                                fg='#cccccc',
                                font=('Arial', 9))
        history_label.pack(anchor='w', padx=5, pady=(5,0))
        
        alert_content = tk.Frame(alert_frame, bg='#3a3a3a')
        alert_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar first
        scrollbar = tk.Scrollbar(alert_content)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Alert history text display (smaller)
        self.current_alert_text = tk.Text(alert_content,
                                         height=3,
                                         bg='#1a1a1a',
                                         fg='#cccccc',
                                         font=('Courier', 8),
                                         wrap=tk.WORD,
                                         state=tk.DISABLED,
                                         relief=tk.SUNKEN,
                                         bd=1,
                                         yscrollcommand=scrollbar.set)
        self.current_alert_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Connect scrollbar
        scrollbar.config(command=self.current_alert_text.yview)
        
        # Initialize with welcome message
        self._update_alert_message("System initialized - Ready for monitoring", "info")
            
    def _create_performance_section(self, parent):
        """Create modern performance monitoring with visual indicators"""
        perf_frame = tk.Frame(parent, bg='#1c2128', relief=tk.FLAT, bd=0)
        perf_frame.pack(fill=tk.X, padx=10, pady=15)
        
        # Header with performance icon
        header_frame = tk.Frame(perf_frame, bg='#1c2128')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame,
                text="⚡ SYSTEM PERFORMANCE",
                bg='#1c2128',
                fg='#f0f6fc',
                font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
        
        # Performance content with modern styling
        perf_content = tk.Frame(perf_frame, bg='#1c2128')
        perf_content.pack(fill=tk.X, padx=15, pady=12)
        
        # FPS indicator with performance bar
        fps_container = tk.Frame(perf_content, bg='#1c2128')
        fps_container.pack(fill=tk.X, pady=8)
        
        fps_header = tk.Frame(fps_container, bg='#1c2128')
        fps_header.pack(fill=tk.X)
        
        tk.Label(fps_header,
                text="📋 PROCESSING SPEED",
                bg='#1c2128',
                fg='#f0f6fc',
                font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        
        # Modern FPS display
        fps_display = tk.Frame(fps_container, bg='#0969da', relief=tk.FLAT, bd=0, height=25)
        fps_display.pack(fill=tk.X, pady=(5, 0))
        fps_display.pack_propagate(False)
        
        self.fps_label = tk.Label(fps_display,
                                 text="0.0 FPS",
                                 bg='#0969da',
                                 fg='white',
                                 font=('Segoe UI', 10, 'bold'))
        self.fps_label.pack(expand=True)
        
        # Modern metrics grid
        metrics_container = tk.Frame(perf_content, bg='#1c2128')
        metrics_container.pack(fill=tk.X, pady=10)
        
        # EAR Metric with visual indicator
        ear_frame = tk.Frame(metrics_container, bg='#238636', relief=tk.FLAT, bd=1)
        ear_frame.pack(fill=tk.X, pady=3, ipady=5)
        
        tk.Label(ear_frame,
                text="👁️ EYE RATIO",
                bg='#238636',
                fg='white',
                font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=8)
        
        self.ear_value_label = tk.Label(ear_frame,
                                       text="--",
                                       bg='#238636',
                                       fg='#17a2b8',
                                       font=('Arial', 9, 'bold'),
                                       anchor='e')
        self.ear_value_label.pack(side=tk.RIGHT)
        
        # MAR value display  
        mar_frame = tk.Frame(perf_content, bg='#3a3a3a')
        mar_frame.pack(fill=tk.X, pady=1)
        
        tk.Label(mar_frame,
                text="👄 MAR:",
                bg='#3a3a3a',
                fg='white',
                font=('Arial', 9),
                anchor='w').pack(side=tk.LEFT)
        
        self.mar_value_label = tk.Label(mar_frame,
                                       text="--",
                                       bg='#3a3a3a',
                                       fg='#17a2b8',
                                       font=('Arial', 9, 'bold'),
                                       anchor='e')
        self.mar_value_label.pack(side=tk.RIGHT)
        
        # Status display with visual indicator
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
        
        # Add detection quality indicator
        quality_frame = tk.Frame(perf_content, bg='#3a3a3a')
        quality_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(quality_frame,
                text="🎯 Detection:",
                bg='#3a3a3a',
                fg='white',
                font=('Arial', 10),
                anchor='w').pack(side=tk.LEFT)
        
        self.detection_quality_label = tk.Label(quality_frame,
                                               text="WAITING",
                                               bg='#3a3a3a',
                                               fg='#ffc107',
                                               font=('Arial', 10, 'bold'),
                                               anchor='e')
        self.detection_quality_label.pack(side=tk.RIGHT)
        
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
            self.status_label.config(text="STARTING", fg='#ffc107')
            self.detection_quality_label.config(text="INITIALIZING", fg='#ffc107')
            self.video_label.config(text="🔄 STARTING CAMERA...\n\n📹 Connecting to camera\n⚙️ Loading AI models\n🎯 Preparing detection")
            
            # Update status progressively
            self.root.after(1000, self._update_startup_progress)
            self.root.after(2000, lambda: self.status_label.config(text="RUNNING", fg='#28a745'))
            self.root.after(3000, lambda: self._update_alert_message(
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
        
        # Reset detection quality
        if hasattr(self, 'detection_quality_label'):
            self.detection_quality_label.config(text="ERROR", fg='#dc3545')
        
        # Reset main status
        if hasattr(self, 'current_status_label'):
            self.current_status_label.config(text="❌ SYSTEM ERROR", fg='#dc3545')
            
        self.video_label.configure(
            image="",
            text="❌ DETECTION ERROR\n\n🔧 Check camera connection\n💻 Check console for details\n🔄 Try restarting detection\n📞 Contact support if issue persists"
        )
            
    def _update_display(self):
        """Update display with latest data"""
        while self.running:
            try:
                # Update video feed and detection data
                if self.pipeline and hasattr(self.pipeline, 'latest_frame'):
                    frame = self.pipeline.latest_frame
                    if frame is not None:
                        self._update_video_display(frame)
                        self._update_fps()
                        
                        # Try to get detection data if available
                        if hasattr(self.pipeline, 'latest_detection_result'):
                            detection_result = self.pipeline.latest_detection_result
                            if detection_result:
                                self._extract_and_update_detection_values(detection_result)
                
                time.sleep(0.1)  # 10 FPS update rate
                
            except Exception as e:
                print(f"⚠️ Display update error: {e}")
                time.sleep(0.5)
                
    def _extract_and_update_detection_values(self, detection_result):
        """Extract and update detection values from pipeline result"""
        try:
            if isinstance(detection_result, dict):
                # Extract EAR value
                ear_data = detection_result.get('ear')
                ear_value = None
                if ear_data and isinstance(ear_data, dict):
                    ear_value = ear_data.get('ear')
                    
                # Extract MAR value
                mar_data = detection_result.get('mar')
                mar_value = None 
                if mar_data and isinstance(mar_data, dict):
                    mar_value = mar_data.get('mar')
                    
                # Extract alert level
                alert_level_enum = detection_result.get('alert_level')
                alert_level = "SAFE"
                if alert_level_enum:
                    level_str = str(alert_level_enum).split('.')[-1]  # Get enum name
                    if level_str == 'CRITICAL':
                        alert_level = "DANGER"
                    elif level_str == 'HIGH':
                        alert_level = "WARNING"
                    elif level_str in ['MEDIUM', 'LOW']:
                        alert_level = "CAUTION"
                        
                # Update display
                self._update_detection_values(ear_value, mar_value, None, alert_level)
                
        except Exception as e:
            # Silent fail - don't spam console
            pass
                
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
        """Update FPS counter with color coding"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.fps_start_time)
            
            # Color code FPS based on performance
            if self.current_fps >= 25:
                fps_color = '#28a745'  # Green - excellent
            elif self.current_fps >= 15:
                fps_color = '#ffc107'  # Yellow - acceptable 
            else:
                fps_color = '#dc3545'  # Red - poor
                
            self.fps_label.config(text=f"{self.current_fps:.1f}", fg=fps_color)
            
            self.fps_counter = 0
            self.fps_start_time = current_time
            
    def _update_startup_progress(self):
        """Update startup progress messages"""
        if hasattr(self, 'detection_quality_label'):
            self.detection_quality_label.config(text="LOADING", fg='#17a2b8')
            self.video_label.config(text="🎥 CAMERA ACTIVE\n\n👤 Please position your face\n📏 Maintain 60-80cm distance\n✅ System is learning...")
            
    def _update_detection_values(self, ear_value=None, mar_value=None, head_angle=None, alert_level="SAFE"):
        """Update real-time detection values with modern visual feedback"""
        try:
            # EAR with dynamic status indicators
            if hasattr(self, 'ear_value_label') and ear_value is not None:
                if ear_value > 0.25:  # Safe
                    bg_color, text_color = '#238636', 'white'  # Green
                    status = "👁️ ALERT"
                elif ear_value > 0.22:  # Caution
                    bg_color, text_color = '#bf8700', 'white'  # Yellow
                    status = "⚠️ TIRED"
                else:  # Drowsy
                    bg_color, text_color = '#da3633', 'white'  # Red
                    status = "😴 DROWSY"
                
                # Update parent frame background for visual impact
                if hasattr(self.ear_value_label, 'master'):
                    self.ear_value_label.master.config(bg=bg_color)
                self.ear_value_label.config(text=f"{ear_value:.3f} | {status}", 
                                           bg=bg_color, fg=text_color, font=('Segoe UI', 9, 'bold'))
            
            # MAR with status descriptions
            if hasattr(self, 'mar_value_label') and mar_value is not None:
                if mar_value < 0.6:  # Normal
                    bg_color, text_color = '#238636', 'white'  # Green
                    status = "😐 NORMAL"
                elif mar_value < 0.7:  # Wide
                    bg_color, text_color = '#bf8700', 'white'  # Yellow
                    status = "😯 WIDE"
                else:  # Yawning
                    bg_color, text_color = '#fd7e14', 'white'  # Orange
                    status = "🥱 YAWN"
                
                if hasattr(self.mar_value_label, 'master'):
                    self.mar_value_label.master.config(bg=bg_color)
                self.mar_value_label.config(text=f"{mar_value:.3f} | {status}", 
                                           bg=bg_color, fg=text_color, font=('Segoe UI', 9, 'bold'))
            
            # Head angle with directional indicators  
            if hasattr(self, 'head_angle_label') and head_angle is not None:
                if abs(head_angle) < 15:  # Normal
                    bg_color, text_color = '#238636', 'white'  # Green
                    status = "📐 UPRIGHT"
                elif abs(head_angle) < 25:  # Tilted
                    bg_color, text_color = '#bf8700', 'white'  # Yellow
                    status = "📐 TILTED"
                else:  # Very tilted/drowsy
                    bg_color, text_color = '#da3633', 'white'  # Red  
                    status = "💤 NODDING"
                
                direction = "➡️" if head_angle > 0 else "⬅️" if head_angle < 0 else "⬆️"
                if hasattr(self.head_angle_label, 'master'):
                    self.head_angle_label.master.config(bg=bg_color)
                self.head_angle_label.config(text=f"{head_angle:.1f}° {direction} | {status}", 
                                           bg=bg_color, fg=text_color, font=('Segoe UI', 9, 'bold'))
                
        except Exception as e:
            silent_print(f"Error updating detection values: {e}")
            
        # Update detection quality status
        if hasattr(self, 'detection_quality_label'):
            quality_colors = {
                'SAFE': '#28a745',
                'CAUTION': '#ffc107', 
                'WARNING': '#fd7e14',
                'DANGER': '#dc3545'
            }
            color = quality_colors.get(alert_level, '#17a2b8')
            self.detection_quality_label.config(text=alert_level, fg=color)
            
        # Update main status display
        if hasattr(self, 'current_status_label'):
            status_messages = {
                'SAFE': '🟢 ALERT STATUS: SAFE - DRIVING OK',
                'CAUTION': '🟡 ALERT STATUS: CAUTION - STAY FOCUSED', 
                'WARNING': '🟠 ALERT STATUS: WARNING - TAKE BREAK SOON',
                'DANGER': '🔴 ALERT STATUS: DANGER - PULL OVER NOW'
            }
            status_colors = {
                'SAFE': '#28a745',
                'CAUTION': '#ffc107',
                'WARNING': '#fd7e14', 
                'DANGER': '#dc3545'
            }
            
            message = status_messages.get(alert_level, '🔵 ALERT STATUS: MONITORING')
            color = status_colors.get(alert_level, '#17a2b8')
            
            self.current_status_label.config(text=message, fg=color)
            
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
            
            alert_level = "SAFE"
            if 'CRITICAL' in message_upper:
                self.alert_counts['CRITICAL'] += 1
                alert_level = "DANGER"
            elif 'HIGH' in message_upper:
                self.alert_counts['HIGH'] += 1
                alert_level = "WARNING"
            elif 'MEDIUM' in message_upper:
                self.alert_counts['MEDIUM'] += 1
                alert_level = "CAUTION"
            elif 'LOW' in message_upper:
                self.alert_counts['LOW'] += 1
                alert_level = "CAUTION"
                
            # Update display with new alert level
            self._update_alert_display()
            
        elif callback_type == 'detection_data' and len(args) >= 1:
            # Handle real-time detection data
            detection_data = args[0]
            ear_value = detection_data.get('ear_value')
            mar_value = detection_data.get('mar_value')
            alert_level = detection_data.get('alert_level', 'SAFE')
            
            # Update real-time values
            self._update_detection_values(ear_value, mar_value, None, alert_level)
    
    def _show_log_viewer(self):
        """Show log viewer window with recent logs and alert history"""
        try:
            # Create log viewer window
            log_window = tk.Toplevel(self.root)
            log_window.title("📋 System Logs & Alert History")
            log_window.geometry("900x700")
            log_window.configure(bg='#0d1117')
            
            # Create notebook for different log types
            notebook = ttk.Notebook(log_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Alert History Tab
            alert_frame = tk.Frame(notebook, bg='#161b22')
            notebook.add(alert_frame, text="🚨 Alert History")
            
            # Alert history content
            alert_text = scrolledtext.ScrolledText(alert_frame,
                                                  bg='#0d1117',
                                                  fg='#f0f6fc',
                                                  font=('Courier New', 10),
                                                  height=25,
                                                  wrap=tk.WORD)
            alert_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Load alert history
            try:
                from ..alert_history import get_alert_stats_for_gui, alert_history
                
                # Get recent alerts
                recent_alerts = alert_history.get_recent_alerts(50)
                
                if recent_alerts:
                    alert_text.insert(tk.END, f"📊 RECENT ALERT HISTORY ({len(recent_alerts)} alerts)\n")
                    alert_text.insert(tk.END, "=" * 60 + "\n\n")
                    
                    for alert in reversed(recent_alerts):  # Most recent first
                        timestamp = datetime.fromtimestamp(alert.timestamp).strftime("%H:%M:%S")
                        level_icon = {
                            'CRITICAL': '🆘',
                            'HIGH': '🔴', 
                            'MEDIUM': '🟡',
                            'LOW': '🟢'
                        }.get(alert.alert_level, '⚪')
                        
                        alert_text.insert(tk.END, f"{level_icon} [{timestamp}] {alert.alert_level}\n")
                        alert_text.insert(tk.END, f"   Confidence: {alert.confidence:.2f}\n")
                        
                        if alert.ear_value:
                            alert_text.insert(tk.END, f"   EAR: {alert.ear_value:.3f}\n")
                        if alert.mar_value:
                            alert_text.insert(tk.END, f"   MAR: {alert.mar_value:.3f}\n")
                        if alert.head_pose:
                            alert_text.insert(tk.END, f"   Head: {alert.head_pose:.1f}°\n")
                        
                        alert_text.insert(tk.END, "\n")
                else:
                    alert_text.insert(tk.END, "📜 No alert history available yet.\n")
                    
            except Exception as e:
                alert_text.insert(tk.END, f"⚠️ Error loading alert history: {e}\n")
            
            # System Logs Tab
            log_frame = tk.Frame(notebook, bg='#161b22')
            notebook.add(log_frame, text="📄 System Logs")
            
            log_text = scrolledtext.ScrolledText(log_frame,
                                               bg='#0d1117',
                                               fg='#f0f6fc',
                                               font=('Courier New', 10),
                                               height=25,
                                               wrap=tk.WORD)
            log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Load system logs
            try:
                log_dir = "log"
                today = datetime.now().strftime("%Y-%m-%d")
                log_file = os.path.join(log_dir, f"fatigue_detection_{today}.log")
                
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        # Get last 100 lines
                        lines = f.readlines()
                        recent_lines = lines[-100:] if len(lines) > 100 else lines
                        
                    log_text.insert(tk.END, f"📋 SYSTEM LOG - {today}\n")
                    log_text.insert(tk.END, "=" * 60 + "\n\n")
                    
                    for line in recent_lines:
                        # Color code log levels
                        if "ERROR" in line:
                            log_text.insert(tk.END, line, "error")
                        elif "WARNING" in line:
                            log_text.insert(tk.END, line, "warning") 
                        elif "ALERT" in line:
                            log_text.insert(tk.END, line, "alert")
                        else:
                            log_text.insert(tk.END, line)
                else:
                    log_text.insert(tk.END, f"📜 No log file found: {log_file}\n")
                    
            except Exception as e:
                log_text.insert(tk.END, f"⚠️ Error loading system logs: {e}\n")
            
            # Configure text colors
            log_text.tag_config("error", foreground="#ff6b6b")
            log_text.tag_config("warning", foreground="#ffd93d")
            log_text.tag_config("alert", foreground="#6bcf7f")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open log viewer:\n{str(e)}")
    
    def _export_session_data(self):
        """Export current session data to Excel file"""
        try:
            # Confirm export action
            result = messagebox.askyesno(
                "Export Session Data", 
                "Xuất dữ liệu phiên làm việc ra file Excel?\n\nFile sẽ chứa:\n• Thời gian cảnh báo\n• Mức độ nguy hiểm\n• Các thông số kỹ thuật\n• Thống kê tổng quan"
            )
            
            if not result:
                return
            
            # File save dialog for Excel
            default_name = f"BaoCao_PhatHien_MeTai_{datetime.now().strftime('%d%m%Y_%H%M')}.xlsx"
            filepath = filedialog.asksaveasfilename(
                title="Lưu Báo Cáo Excel",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=default_name
            )
            
            if not filepath:
                return
            
            # Create Excel file with readable format
            try:
                import pandas as pd
                from ..alert_history import alert_history, get_alert_stats_for_gui
                
                # Get session data
                recent_alerts = alert_history.get_recent_alerts(200)  # Get more alerts for report
                stats = get_alert_stats_for_gui()
                
                if not recent_alerts:
                    messagebox.showwarning("Không có dữ liệu", "Chưa có dữ liệu cảnh báo để xuất!")
                    return
                
                # Prepare data for Excel
                excel_data = []
                for alert in recent_alerts:
                    # Convert timestamp to readable format
                    alert_time = datetime.fromtimestamp(alert.timestamp)
                    
                    # Map alert level to Vietnamese
                    level_map = {
                        'LOW': 'Thấp',
                        'MEDIUM': 'Trung bình', 
                        'HIGH': 'Cao',
                        'CRITICAL': 'Rất nguy hiểm'
                    }
                    
                    # Status based on alert level
                    status_map = {
                        'LOW': 'Bình thường',
                        'MEDIUM': 'Chú ý',
                        'HIGH': 'Cảnh báo', 
                        'CRITICAL': 'Nguy hiểm'
                    }
                    
                    excel_data.append({
                        'Thời gian': alert_time.strftime('%d/%m/%Y %H:%M:%S'),
                        'Ngày': alert_time.strftime('%d/%m/%Y'),
                        'Giờ': alert_time.strftime('%H:%M:%S'),
                        'Mức độ': level_map.get(alert.alert_level, alert.alert_level),
                        'Trạng thái': status_map.get(alert.alert_level, 'Không xác định'),
                        'Độ tin cậy (%)': f"{alert.confidence*100:.1f}%",
                        'Mắt đóng/mở': f"{alert.ear_value:.3f}" if alert.ear_value else "N/A",
                        'Miệng há': f"{alert.mar_value:.3f}" if alert.mar_value else "N/A", 
                        'Góc đầu (độ)': f"{alert.head_pose:.1f}°" if alert.head_pose else "N/A",
                    })
                
                # Create DataFrame
                df = pd.DataFrame(excel_data)
                
                # Create summary statistics
                summary_data = {
                    'Thống kê': ['Tổng số cảnh báo', 'Mức thấp', 'Mức trung bình', 'Mức cao', 'Rất nguy hiểm', 
                               'Thời gian bắt đầu', 'Thời gian kết thúc', 'Tổng thời gian'],
                    'Giá trị': [
                        stats.get('total_alerts', 0),
                        stats.get('low_alerts', 0),
                        stats.get('medium_alerts', 0), 
                        stats.get('high_alerts', 0),
                        stats.get('critical_alerts', 0),
                        datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                        datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                        f"{len(recent_alerts)} phút" if recent_alerts else "0 phút"
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                
                # Write to Excel with multiple sheets
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    # Main data sheet
                    df.to_excel(writer, sheet_name='Chi tiết cảnh báo', index=False)
                    
                    # Summary sheet  
                    summary_df.to_excel(writer, sheet_name='Tổng quan', index=False)
                    
                    # Get workbook and worksheets for formatting
                    workbook = writer.book
                    
                    # Format main sheet
                    if 'Chi tiết cảnh báo' in workbook.sheetnames:
                        worksheet = workbook['Chi tiết cảnh báo']
                        
                        # Auto-adjust column widths
                        for column in worksheet.columns:
                            max_length = 0
                            column_letter = column[0].column_letter
                            for cell in column:
                                if cell.value:
                                    max_length = max(max_length, len(str(cell.value)))
                            adjusted_width = min(max_length + 2, 20)
                            worksheet.column_dimensions[column_letter].width = adjusted_width
                    
                    # Format summary sheet
                    if 'Tổng quan' in workbook.sheetnames:
                        summary_sheet = workbook['Tổng quan'] 
                        for column in summary_sheet.columns:
                            max_length = 0
                            column_letter = column[0].column_letter
                            for cell in column:
                                if cell.value:
                                    max_length = max(max_length, len(str(cell.value)))
                            adjusted_width = min(max_length + 2, 30)
                            summary_sheet.column_dimensions[column_letter].width = adjusted_width
                
                # Show success message
                result = messagebox.askyesno(
                    "Xuất dữ liệu thành công!",
                    f"Báo cáo Excel đã được tạo thành công!\n\n"
                    f"📄 File: {os.path.basename(filepath)}\n"
                    f"📁 Vị trí: {os.path.dirname(filepath)}\n"
                    f"📊 Số cảnh báo: {len(recent_alerts)}\n\n"
                    f"Mở thư mục chứa file?"
                )
                
                if result:
                    import subprocess
                    import platform
                    
                    if platform.system() == 'Windows':
                        subprocess.run(['explorer', '/select,', filepath])
                    elif platform.system() == 'Darwin':  # macOS
                        subprocess.run(['open', '-R', filepath])
                    else:  # Linux
                        subprocess.run(['xdg-open', os.path.dirname(filepath)])
                        
                print(f"📊 Báo cáo Excel đã xuất: {filepath}")
                
            except ImportError:
                messagebox.showerror("Lỗi", "Cần cài đặt thư viện pandas và openpyxl để xuất Excel!\n\nChạy: pip install pandas openpyxl")
            except Exception as e:
                messagebox.showerror("Lỗi xuất dữ liệu", f"Không thể tạo báo cáo Excel:\n{str(e)}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Export failed:\n{str(e)}")
    
    def _clear_session_data(self):
        """Clear current session data after confirmation"""
        try:
            # Get current session stats for confirmation
            from ..alert_history import alert_history, get_alert_stats_for_gui
            
            stats = get_alert_stats_for_gui()
            total_alerts = stats.get('total_alerts', 0)
            
            # Confirmation dialog with session info
            result = messagebox.askyesnocancel(
                "Clear Session Data",
                f"Are you sure you want to clear the current session?\n\n"
                f"📊 Current Session Stats:\n"
                f"  • Total Alerts: {total_alerts}\n"
                f"  • Critical: {stats.get('critical_alerts', 0)}\n"
                f"  • High: {stats.get('high_alerts', 0)}\n"
                f"  • Medium: {stats.get('medium_alerts', 0)}\n"
                f"  • Low: {stats.get('low_alerts', 0)}\n\n"
                f"This action cannot be undone!\n\n"
                f"Export data first? (Yes = Export then clear, No = Clear only, Cancel = Cancel)"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - Export first
                self._export_session_data()
                # Ask again after export
                if not messagebox.askyesno("Confirm Clear", "Proceed with clearing session data?"):
                    return
            
            # Clear the session
            alert_history.clear_session()
            
            # Reset UI counters
            self.alert_counts = {
                'LOW': 0,
                'MEDIUM': 0,
                'HIGH': 0,
                'CRITICAL': 0
            }
            self._update_alert_display()
            
            # Update alert message
            self._update_alert_message("Session data cleared - Starting fresh session", "info")
            
            messagebox.showinfo("Session Cleared", "Session data has been cleared successfully!")
            print("🗑️ Session data cleared")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear session data:\n{str(e)}")
    
    def _show_log_viewer(self):
        """Show log viewer window with recent logs and alert history"""
        try:
            # Create log viewer window
            log_window = tk.Toplevel(self.root)
            log_window.title("📋 System Logs & Alert History")
            log_window.geometry("900x700")
            log_window.configure(bg='#0d1117')
            
            # Create notebook for different log types
            notebook = ttk.Notebook(log_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Alert History Tab
            alert_frame = tk.Frame(notebook, bg='#161b22')
            notebook.add(alert_frame, text="🚨 Alert History")
            
            # Alert history content
            alert_text = scrolledtext.ScrolledText(alert_frame,
                                                  bg='#0d1117',
                                                  fg='#f0f6fc',
                                                  font=('Courier New', 10),
                                                  height=25,
                                                  wrap=tk.WORD)
            alert_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Load alert history
            try:
                from ..alert_history import get_alert_stats_for_gui, alert_history
                
                # Get recent alerts
                recent_alerts = alert_history.get_recent_alerts(50)
                
                if recent_alerts:
                    alert_text.insert(tk.END, f"📊 RECENT ALERT HISTORY ({len(recent_alerts)} alerts)\n")
                    alert_text.insert(tk.END, "=" * 60 + "\n\n")
                    
                    for alert in reversed(recent_alerts):  # Most recent first
                        timestamp = datetime.fromtimestamp(alert.timestamp).strftime("%H:%M:%S")
                        level_icon = {
                            'CRITICAL': '🆘',
                            'HIGH': '🔴', 
                            'MEDIUM': '🟡',
                            'LOW': '🟢'
                        }.get(alert.alert_level, '⚪')
                        
                        alert_text.insert(tk.END, f"{level_icon} [{timestamp}] {alert.alert_level}\n")
                        alert_text.insert(tk.END, f"   Confidence: {alert.confidence:.2f}\n")
                        
                        if alert.ear_value:
                            alert_text.insert(tk.END, f"   EAR: {alert.ear_value:.3f}\n")
                        if alert.mar_value:
                            alert_text.insert(tk.END, f"   MAR: {alert.mar_value:.3f}\n")
                        if alert.head_pose:
                            alert_text.insert(tk.END, f"   Head: {alert.head_pose:.1f}°\n")
                        
                        alert_text.insert(tk.END, "\n")
                else:
                    alert_text.insert(tk.END, "📜 No alert history available yet.\n")
                    
            except Exception as e:
                alert_text.insert(tk.END, f"⚠️ Error loading alert history: {e}\n")
            
            # System Logs Tab
            log_frame = tk.Frame(notebook, bg='#161b22')
            notebook.add(log_frame, text="📄 System Logs")
            
            log_text = scrolledtext.ScrolledText(log_frame,
                                               bg='#0d1117',
                                               fg='#f0f6fc',
                                               font=('Courier New', 10),
                                               height=25,
                                               wrap=tk.WORD)
            log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Load system logs
            try:
                log_dir = "log"
                today = datetime.now().strftime("%Y-%m-%d")
                log_file = os.path.join(log_dir, f"fatigue_detection_{today}.log")
                
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        # Get last 100 lines
                        lines = f.readlines()
                        recent_lines = lines[-100:] if len(lines) > 100 else lines
                        
                    log_text.insert(tk.END, f"📋 SYSTEM LOG - {today}\n")
                    log_text.insert(tk.END, "=" * 60 + "\n\n")
                    
                    for line in recent_lines:
                        # Color code log levels
                        if "ERROR" in line:
                            log_text.insert(tk.END, line, "error")
                        elif "WARNING" in line:
                            log_text.insert(tk.END, line, "warning") 
                        elif "ALERT" in line:
                            log_text.insert(tk.END, line, "alert")
                        else:
                            log_text.insert(tk.END, line)
                else:
                    log_text.insert(tk.END, f"📜 No log file found: {log_file}\n")
                    
            except Exception as e:
                log_text.insert(tk.END, f"⚠️ Error loading system logs: {e}\n")
            
            # Configure text colors
            log_text.tag_config("error", foreground="#ff6b6b")
            log_text.tag_config("warning", foreground="#ffd93d")
            log_text.tag_config("alert", foreground="#6bcf7f")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open log viewer:\n{str(e)}")
    
    def _clear_session_data(self):
        """Clear current session data after confirmation"""
        try:
            # Get current session stats for confirmation
            from ..alert_history import alert_history, get_alert_stats_for_gui
            
            stats = get_alert_stats_for_gui()
            total_alerts = stats.get('total_alerts', 0)
            
            # Confirmation dialog with session info
            result = messagebox.askyesnocancel(
                "Clear Session Data",
                f"Are you sure you want to clear the current session?\n\n"
                f"📊 Current Session Stats:\n"
                f"  • Total Alerts: {total_alerts}\n"
                f"  • Critical: {stats.get('critical_alerts', 0)}\n"
                f"  • High: {stats.get('high_alerts', 0)}\n"
                f"  • Medium: {stats.get('medium_alerts', 0)}\n"
                f"  • Low: {stats.get('low_alerts', 0)}\n\n"
                f"This action cannot be undone!\n\n"
                f"Export data first? (Yes = Export then clear, No = Clear only, Cancel = Cancel)"
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - Export first
                self._export_session_data()
                # Ask again after export
                if not messagebox.askyesno("Confirm Clear", "Proceed with clearing session data?"):
                    return
            
            # Clear the session
            alert_history.clear_session()
            
            # Reset UI counters
            self.alert_counts = {
                'LOW': 0,
                'MEDIUM': 0,
                'HIGH': 0,
                'CRITICAL': 0
            }
            self._update_alert_display()
            
            # Update alert message
            self._update_alert_message("Session data cleared - Starting fresh session", "info")
            
            messagebox.showinfo("Session Cleared", "Session data has been cleared successfully!")
            print("🗑️ Session data cleared")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear session data:\n{str(e)}")
    
    def _test_alert_counter(self):
        """Test alert counter functionality"""
        import random
        alert_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        level = random.choice(alert_levels)
        
        test_message = f"🧪 {level} Test Alert (Conf: 0.{random.randint(70,95)})"
        alert_type = 'warning' if level in ['LOW', 'MEDIUM'] else 'critical'
        
        self._handle_pipeline_callback('alert', test_message, alert_type)
    
    def _take_screenshot(self):
        """Take screenshot of current detection display"""
        try:
            if not hasattr(self, 'current_image') or self.current_image is None:
                messagebox.showwarning("No Image", "No current image to screenshot")
                return
            
            # Create output directory if it doesn't exist
            output_dir = "output/screenshots"
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"detection_screenshot_{timestamp}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            # Save current image from camera display
            cv2.imwrite(filepath, self.current_image)
            
            # Show success message
            result = messagebox.askyesno(
                "Screenshot Saved",
                f"Screenshot saved successfully!\n\nFile: {filename}\nLocation: {output_dir}\n\nOpen folder?"
            )
            
            if result:
                # Open file explorer to screenshots folder
                import subprocess
                import platform
                
                if platform.system() == 'Windows':
                    subprocess.run(['explorer', os.path.abspath(output_dir)])
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', os.path.abspath(output_dir)])
                else:  # Linux
                    subprocess.run(['xdg-open', os.path.abspath(output_dir)])
            
            print(f"📸 Screenshot saved: {filepath}")
            
        except Exception as e:
            messagebox.showerror("Screenshot Error", f"Failed to save screenshot:\n{str(e)}")
    
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
        
        # Reset video display with better instructions
        self.video_label.configure(
            image="",
            text="📹 DETECTION STOPPED\n\n🔄 Press START to begin monitoring\n👤 Ensure good lighting and clear face view\n📏 Position camera at eye level"
        )
        
        # Reset detection values
        if hasattr(self, 'ear_value_label'):
            self.ear_value_label.config(text="--", fg='#cccccc')
        if hasattr(self, 'mar_value_label'):
            self.mar_value_label.config(text="--", fg='#cccccc')
        if hasattr(self, 'detection_quality_label'):
            self.detection_quality_label.config(text="STOPPED", fg='#dc3545')
        if hasattr(self, 'current_status_label'):
            self.current_status_label.config(text="🔴 SYSTEM STOPPED", fg='#dc3545')
        
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
