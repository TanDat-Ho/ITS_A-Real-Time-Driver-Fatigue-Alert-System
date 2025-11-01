"""Simple Welcome Screen without auto-advance"""

import tkinter as tk
from tkinter import ttk
from typing import Callable


class SimpleWelcomeScreen:
    """Simple welcome screen that waits for user input"""
    
    def __init__(self, parent_frame: tk.Frame, start_callback: Callable):
        self.parent_frame = parent_frame
        self.start_callback = start_callback
        self.config_var = tk.StringVar(value="default")
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup simple welcome screen UI"""
        # Main container
        main_container = tk.Frame(self.parent_frame, bg='#1a1a2e')
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_container,
            text="DRIVER FATIGUE DETECTION SYSTEM",
            font=("Arial", 28, "bold"),
            fg='#00d4ff',
            bg='#1a1a2e'
        )
        title_label.pack(pady=(100, 20))
        
        # Subtitle
        subtitle_label = tk.Label(
            main_container,
            text="AI-Powered Real-time Drowsiness Detection",
            font=("Arial", 16),
            fg='#a0a0ff',
            bg='#1a1a2e'
        )
        subtitle_label.pack(pady=(0, 50))
        
        # Configuration frame
        config_frame = tk.LabelFrame(
            main_container,
            text="Configuration",
            font=("Arial", 14, "bold"),
            fg='white',
            bg='#2a2a3e',
            bd=2,
            relief=tk.GROOVE
        )
        config_frame.pack(pady=20, padx=100, fill=tk.X)
        
        # Sensitivity options
        tk.Label(
            config_frame,
            text="Detection Sensitivity:",
            font=("Arial", 12),
            fg='white',
            bg='#2a2a3e'
        ).pack(pady=(10, 5))
        
        sensitivity_frame = tk.Frame(config_frame, bg='#2a2a3e')
        sensitivity_frame.pack(pady=10)
        
        options = [
            ("High Sensitivity", "high"),
            ("Default", "default"), 
            ("Low Sensitivity", "low")
        ]
        
        for text, value in options:
            rb = tk.Radiobutton(
                sensitivity_frame,
                text=text,
                variable=self.config_var,
                value=value,
                font=("Arial", 11),
                fg='white',
                bg='#2a2a3e',
                selectcolor='#1a1a2e',
                activebackground='#3a3a4e',
                activeforeground='white'
            )
            rb.pack(anchor='w', padx=20, pady=2)
            
        # Start button
        start_button = tk.Button(
            main_container,
            text="START DETECTION",
            command=self.on_start_clicked,
            bg='#28a745',
            fg='white',
            font=('Arial', 16, 'bold'),
            height=2,
            width=20,
            relief=tk.RAISED,
            bd=3
        )
        start_button.pack(pady=50)
        
        # Instructions
        instructions = tk.Label(
            main_container,
            text="Select your preferred sensitivity level and click START DETECTION",
            font=("Arial", 11),
            fg='#888888',
            bg='#1a1a2e'
        )
        instructions.pack(pady=(0, 50))
        
    def on_start_clicked(self):
        """Handle start button click"""
        selected_config = self.config_var.get()
        print(f"User selected config: {selected_config}")
        self.start_callback(selected_config)