"""
src/output_layer/ui/welcome_screen.py

Welcome screen với animation và hiệu ứng đẹp
"""

import tkinter as tk
from tkinter import ttk
import math
import time
from typing import Callable

class AnimatedWelcomeScreen:
    """Welcome screen với animation"""
    
    def __init__(self, parent_frame: tk.Frame, start_callback: Callable):
        self.parent_frame = parent_frame
        self.start_callback = start_callback
        
        # Animation variables
        self.animation_running = True
        self.pulse_offset = 0
        
        self.setup_ui()
        self.start_animations()
        
    def update_canvas_scroll_region(self):
        """Update canvas scroll region"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def on_canvas_configure(self, event):
        """Handle canvas resize to center content"""
        canvas_width = event.width
        frame_width = self.scrollable_frame.winfo_reqwidth()
        
        # Center the frame horizontally
        x_position = max(0, (canvas_width - frame_width) // 2)
        self.canvas.coords(self.canvas_window, x_position, 0)
        
    def setup_ui(self):
        """Setup welcome screen UI"""
        # Main container with scrollable canvas
        self.canvas = tk.Canvas(self.parent_frame, bg='#1a1a2e', highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.parent_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='#1a1a2e')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.update_canvas_scroll_region()
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="n")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Bind canvas resize to center content
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Use scrollable frame as container
        self.container = self.scrollable_frame
        
        # Header section
        header_frame = tk.Frame(self.container, bg='#1a1a2e')
        header_frame.pack(expand=True, pady=(20, 10))
        
        # Animated title
        self.title_label = tk.Label(
            header_frame,
            text="🚗 DRIVER FATIGUE DETECTION",
            font=("Arial", 32, "bold"),
            fg='#00d4ff',
            bg='#1a1a2e'
        )
        self.title_label.pack(anchor="center")
        
        # Subtitle with gradient effect
        self.subtitle_label = tk.Label(
            header_frame,
            text="AI-Powered Real-time Drowsiness Detection System",
            font=("Arial", 16),
            fg='#a0a0ff',
            bg='#1a1a2e'
        )
        self.subtitle_label.pack(pady=10, anchor="center")
        
        # Features section
        features_frame = tk.Frame(self.container, bg='#1a1a2e')
        features_frame.pack(expand=True, pady=15)
        
        features_title = tk.Label(
            features_frame,
            text="🔬 ADVANCED DETECTION FEATURES",
            font=("Arial", 18, "bold"),
            fg='#ffffff',
            bg='#1a1a2e'
        )
        features_title.pack(pady=10, anchor="center")
        
        # Feature cards
        cards_frame = tk.Frame(features_frame, bg='#1a1a2e')
        cards_frame.pack(anchor="center")
        
        self.create_feature_cards(cards_frame)
        
        # Configuration section
        config_frame = tk.Frame(self.container, bg='#1a1a2e')
        config_frame.pack(expand=True, pady=20)
        
        tk.Label(
            config_frame,
            text="⚙️ DETECTION SENSITIVITY",
            font=("Arial", 16, "bold"),
            fg='#ffffff',
            bg='#1a1a2e'
        ).pack(pady=10, anchor="center")
        
        self.sensitivity_var = tk.StringVar(value="default")
        self.create_sensitivity_selector(config_frame)
        
        # Start section
        start_frame = tk.Frame(self.container, bg='#1a1a2e')
        start_frame.pack(expand=True, pady=30)
        
        # Animated start button - Make it more prominent
        self.start_button = tk.Button(
            start_frame,
            text="🚀 START DETECTION",
            font=("Arial", 24, "bold"),
            fg='#ffffff',
            bg='#ff6600',
            activebackground='#ff8800',
            activeforeground='#ffffff',
            width=20,
            height=3,
            relief=tk.RAISED,
            borderwidth=5,
            command=self.on_start_clicked
        )
        self.start_button.pack(pady=20, anchor="center")
        
        # Status
        self.status_label = tk.Label(
            start_frame,
            text="📹 Ensure camera is connected • 🎧 Enable audio alerts",
            font=("Arial", 12),
            fg='#ffff88',
            bg='#1a1a2e'
        )
        self.status_label.pack(pady=15, anchor="center")
        
    def create_feature_cards(self, parent):
        """Create feature cards with icons"""
        features = [
            ("👁️", "EAR Detection", "Eye Aspect Ratio\nMicrosleep Detection"),
            ("👄", "MAR Analysis", "Mouth Aspect Ratio\nYawn Detection"), 
            ("🗣️", "Head Pose", "Head Position\nNodding Detection"),
            ("🚨", "Multi-Alert", "Progressive Warning\nCritical Alerts")
        ]
        
        for i, (icon, title, desc) in enumerate(features):
            card = tk.Frame(parent, bg='#16213e', relief=tk.RAISED, borderwidth=2)
            card.grid(row=0, column=i, padx=15, pady=10, sticky='nsew')
            
            # Icon
            tk.Label(
                card,
                text=icon,
                font=("Arial", 24),
                bg='#16213e',
                fg='#00d4ff'
            ).pack(pady=5)
            
            # Title
            tk.Label(
                card,
                text=title,
                font=("Arial", 12, "bold"),
                bg='#16213e',
                fg='#ffffff'
            ).pack()
            
            # Description
            tk.Label(
                card,
                text=desc,
                font=("Arial", 9),
                bg='#16213e',
                fg='#cccccc',
                justify=tk.CENTER
            ).pack(pady=5)
            
    def create_sensitivity_selector(self, parent):
        """Create animated sensitivity selector"""
        selector_frame = tk.Frame(parent, bg='#1a1a2e')
        selector_frame.pack(pady=15, anchor="center")
        
        options = [
            ("default", "🎯 Default", "Balanced detection"),
            ("sensitive", "🔍 High Sensitivity", "More alerts, fewer missed events"),
            ("conservative", "🛡️ Conservative", "Fewer false alarms")
        ]
        
        for value, text, desc in options:
            option_frame = tk.Frame(selector_frame, bg='#1a1a2e')
            option_frame.pack(side=tk.LEFT, padx=20)
            
            rb = tk.Radiobutton(
                option_frame,
                text=text,
                variable=self.sensitivity_var,
                value=value,
                font=("Arial", 12, "bold"),
                fg='#ffffff',
                bg='#1a1a2e',
                selectcolor='#00aa00',
                activebackground='#1a1a2e',
                activeforeground='#ffffff',
                indicatoron=False,
                width=15,
                pady=5
            )
            rb.pack()
            
            tk.Label(
                option_frame,
                text=desc,
                font=("Arial", 8),
                fg='#aaaaaa',
                bg='#1a1a2e'
            ).pack()
            
    def start_animations(self):
        """Start UI animations"""
        self.animate_title()
        self.animate_button()
        
    def animate_title(self):
        """Animate title with color cycling"""
        if not self.animation_running:
            return
            
        # Color cycling
        colors = ['#00d4ff', '#0099cc', '#006699', '#0099cc']
        color_index = int(time.time() * 2) % len(colors)
        self.title_label.config(fg=colors[color_index])
        
        # Schedule next frame
        self.container.after(500, self.animate_title)
        
    def animate_button(self):
        """Animate start button with pulsing effect"""
        if not self.animation_running:
            return
            
        self.pulse_offset += 0.2
        
        # Pulsing effect
        scale = 1 + 0.1 * math.sin(self.pulse_offset)
        if scale > 1.05:
            # Change button color during pulse
            colors = ['#00aa00', '#00cc00', '#00ee00']
            color_index = int(self.pulse_offset) % len(colors)
            self.start_button.config(bg=colors[color_index])
        else:
            self.start_button.config(bg='#00aa00')
            
        # Schedule next frame
        self.container.after(50, self.animate_button)
        
    def on_start_clicked(self):
        """Handle start button click"""
        self.animation_running = False
        self.start_button.config(
            state=tk.DISABLED,
            text="🔄 INITIALIZING...",
            bg='#666666'
        )
        
        # Get selected configuration
        config = self.sensitivity_var.get()
        
        # Call start callback
        self.start_callback(config)
        
    def destroy(self):
        """Clean up welcome screen"""
        self.animation_running = False
        self.canvas.destroy()
        self.scrollbar.destroy()