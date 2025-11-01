#!/usr/bin/env python3
"""
gui_launcher.py

GUI Launcher for Driver Fatigue Detection System
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

def check_dependencies():
    """Check if all required dependencies are installed"""
    missing_packages = []
    
    try:
        import cv2
    except ImportError:
        missing_packages.append("opencv-python")
    
    try:
        import mediapipe
    except ImportError:
        missing_packages.append("mediapipe")
    
    try:
        import numpy
    except ImportError:
        missing_packages.append("numpy")
    
    try:
        import PIL
    except ImportError:
        missing_packages.append("Pillow")
    
    try:
        import tkinter
    except ImportError:
        missing_packages.append("tkinter (should be built-in)")
    
    if missing_packages:
        print("❌ Missing required packages:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\n📦 Install missing packages:")
        if "tkinter" not in missing_packages[0]:
            print(f"   pip install {' '.join([p for p in missing_packages if 'tkinter' not in p])}")
        return False
    
    return True

def main():
    """Main entry point"""
    print("🚗 Driver Fatigue Detection System - GUI Mode")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        input("\nPress Enter to exit...")
        return 1
    
    try:
        # Import and run GUI
        from src.output_layer.ui.main_window import FatigueDetectionGUI
        
        print("✅ All dependencies found")
        print("🚀 Starting GUI application...")
        
        app = FatigueDetectionGUI()
        app.run()
        
        return 0
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔧 Make sure you're running from the project root directory")
        input("\nPress Enter to exit...")
        return 1
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        input("\nPress Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())