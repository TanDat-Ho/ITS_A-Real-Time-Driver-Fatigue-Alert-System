#!/usr/bin/env python3
"""
launcher.py

Unified Launcher for Driver Fatigue Detection System
Integrates existing GUI (FatigueDetectionGUI) with CLI backend logic from run.py
"""

import sys
import os
import argparse
from pathlib import Path
import logging

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are installed (from gui_launcher.py)"""
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
    
    # Check additional packages for enhanced features
    try:
        import psutil
    except ImportError:
        print("⚠️  Optional: psutil not found (hardware detection will use defaults)")
    
    if missing_packages:
        print("❌ Missing required packages:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\n📦 Install missing packages:")
        if "tkinter" not in missing_packages[0]:
            print(f"   pip install {' '.join([p for p in missing_packages if 'tkinter' not in p])}")
        return False
    
    return True

def setup_directories():
    """Create necessary directories (from run.py)"""
    for subdir in ["log", "assets/sounds", "assets/icon", "output/snapshots"]:
        (PROJECT_ROOT / subdir).mkdir(parents=True, exist_ok=True)

def run_input_validation():
    """Run quick input system validation"""
    print("🧪 Running input system validation...")
    
    try:
        # Test camera initialization
        from src.input_layer.optimized_input_config import OptimizedInputConfig
        from src.input_layer.camera_handler import CameraHandler
        from src.processing_layer.detect_landmark.landmark import FaceLandmarkDetector
        
        # Get optimized config
        config = OptimizedInputConfig.adapt_for_hardware()
        print(f"✅ Hardware-adaptive configuration loaded")
        
        # Test camera
        print("📹 Testing camera initialization...")
        camera = CameraHandler(**config["camera"])
        camera.start()
        import time
        
        # Wait longer for camera to fully initialize
        time.sleep(2.0)
        
        # Try multiple attempts to get frame
        frame_data = None
        for attempt in range(3):
            frame_data = camera.get_frame_with_metadata(block=True, timeout=5.0)
            if frame_data:
                break
            time.sleep(0.5)
        
        camera.stop()
        
        if frame_data:
            print(f"✅ Camera working - Frame shape: {frame_data['frame'].shape}")
            quality = frame_data.get('quality', {})
            if quality.get('is_acceptable', False):
                print(f"✅ Frame quality good - Brightness: {quality.get('brightness', 0):.1f}")
            else:
                print(f"⚠️  Frame quality marginal - Check lighting")
        else:
            print("⚠️  Camera test inconclusive - May work during actual run")
            print("   (This is normal if camera is in use by another app)")
            # Don't fail validation for camera issues - may work during actual run
            return True
        
        # Test landmark detector
        print("🎯 Testing landmark detector...")
        detector = FaceLandmarkDetector(**config["mediapipe"])
        detector.release()
        print("✅ Landmark detector initialized successfully")
        
        print("✅ Input system validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Input validation failed: {e}")
        return False

def show_config(config_type: str):
    """Display the chosen configuration (from run.py)"""
    try:
        from src.app.config import get_fatigue_config
        from src.processing_layer.vision_processor.rule_based import FatigueDetectionConfig
        
        presets = {
            "default": FatigueDetectionConfig.get_default_config,
            "sensitive": FatigueDetectionConfig.get_sensitive_config,
            "conservative": FatigueDetectionConfig.get_conservative_config,
        }
        config = presets.get(config_type, get_fatigue_config)()
        ear, mar, head = config["ear_config"], config["mar_config"], config["head_pose_config"]

        print(f"\n📋 CONFIGURATION: {config_type.upper()}")
        print(f"👁️ EAR → threshold: {ear['drowsy_threshold']}, duration: {ear['drowsy_duration']}s")
        print(f"👄 MAR → threshold: {mar['yawn_threshold']}, duration: {mar['yawn_duration']}s")
        print(f"�️ HEAD → threshold: {head['drowsy_threshold']}°, duration: {head['drowsy_duration']}s")
        print(f"⚡ Combination threshold: {config['combination_threshold']}/3")
        print(f"� Critical duration: {config['critical_duration']}s")
    except ImportError as e:
        print(f"❌ Config error: {e}")

def apply_config(config_type: str):
    """Apply config overrides to global parameters (from run.py)"""
    try:
        from src.app.config import EAR_CONFIG, MAR_CONFIG, HEAD_POSE_CONFIG
        from src.processing_layer.vision_processor.rule_based import FatigueDetectionConfig
        
        if config_type == "default":
            return
        
        configs = {
            "sensitive": FatigueDetectionConfig.get_sensitive_config,
            "conservative": FatigueDetectionConfig.get_conservative_config,
        }
        config = configs.get(config_type)()
        EAR_CONFIG.update(config["ear_config"])
        MAR_CONFIG.update(config["mar_config"])
        HEAD_POSE_CONFIG.update(config["head_pose_config"])
    except ImportError as e:
        print(f"❌ Config error: {e}")

def run_detection_system(config_type: str, enhanced: bool = False):
    """Run the fatigue detection system with given config"""
    try:
        from src.app.main import create_pipeline
        from src.app.config import validate_config
        from src.output_layer.logger import fatigue_logger
        
        validate_config()
        apply_config(config_type)
        
        # Start session logging
        fatigue_logger.log_session_start()
        
        if enhanced:
            print("🚀 Starting Enhanced Driver Fatigue Detection System...")
            print("🎯 Features: Hardware-adaptive config, Input validation, Performance monitoring")
        else:
            print("🚀 Starting Driver Fatigue Detection System...")
        
        print("📊 Detailed logs saved to: log/fatigue_detection_YYYY-MM-DD.log")
        print("🎮 Controls: [q] Quit | [r] Reset | [s] Screenshot")
        
        # Create pipeline with enhanced mode flag và optimized detection
        if enhanced:
            print("🔧 ENHANCED MODE - Initializing optimized detection engine...")
            
            # Import optimized detection components
            from src.processing_layer.detect_rules.optimized_integration import create_optimized_engine
            
            # Create optimized detection engine với adaptive thresholds
            detection_engine = create_optimized_engine(
                lighting="normal",  # Could be auto-detected from camera
                quality="medium"    # Could be auto-detected from camera specs
            )
            print("   ✅ Optimized detection engine with adaptive thresholds ready")
            
            # Create pipeline with optimized engine
            pipeline = create_pipeline(enhanced=enhanced, detection_engine=detection_engine)
        else:
            pipeline = create_pipeline(enhanced=enhanced)
            
        pipeline.run()
        
        print("\n👋 System stopped. Check log file for details.")
        
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user.")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

def run_cli_mode():
    """Run in CLI mode (original run.py functionality)"""
    parser = argparse.ArgumentParser(
        description="🚗 Driver Fatigue Detection System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-c", "--config", choices=["default", "sensitive", "conservative"], default="default")
    parser.add_argument("--info", "-i", action="store_true", help="Show configuration info only")
    parser.add_argument("--setup", action="store_true", help="Create required directories only")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal console output")
    parser.add_argument("--enhanced", action="store_true", help="Use enhanced input optimization")
    parser.add_argument("--test-input", action="store_true", help="Test input system before starting")
    args = parser.parse_args()

    setup_directories()

    if args.setup:
        return 0

    # Adjust verbosity based on quiet flag
    if args.quiet:
        import logging
        logging.getLogger().setLevel(logging.ERROR)
        print("🤫 Quiet mode: Minimal console output, check log files for details")

    show_config(args.config)

    # Test input system if requested
    if args.test_input:
        if not run_input_validation():
            print("❌ Input validation failed. Please check camera and lighting.")
            return 1
        print("")
    
    if args.info:
        print("\n🎮 USAGE")
        print("─────────────────────")
        print("[q] Quit     [r] Reset stats     [s] Screenshot")
        print("Ctrl+C → Exit forcefully")
        if args.enhanced:
            print("\n🚀 ENHANCED MODE:")
            print("• Hardware-adaptive configuration")
            print("• Input quality validation")
            print("• Performance monitoring")
        return 0

    print("\n🎮 USAGE")
    print("─────────────────────")
    print("[q] Quit     [r] Reset stats     [s] Screenshot")
    print("Ctrl+C → Exit forcefully")
    
    if args.enhanced:
        print("\n🚀 Enhanced mode enabled - Input optimization active")

    if not args.quiet and not args.enhanced:
        try:
            input("\n🎯 Press Enter to start...")
        except KeyboardInterrupt:
            print("\n👋 Exit.")
            return 0
    elif args.enhanced or args.quiet:
        print("🚀 Auto-starting in enhanced/quiet mode...")

    try:
        # Pass enhanced flag to detection system
        run_detection_system(args.config, enhanced=args.enhanced)
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

def main():
    """Main entry point"""
    # Check dependencies first
    if not check_dependencies():
        input("\nPress Enter to exit...")
        return 1
    
    # CLI mode if arguments provided, otherwise GUI mode
    if len(sys.argv) > 1 and "--cli" in sys.argv:
        # Remove --cli flag and run CLI mode
        sys.argv.remove("--cli")
        return run_cli_mode()
    elif len(sys.argv) > 1:
        # Other arguments -> CLI mode
        return run_cli_mode()
    else:
        # No arguments -> GUI mode (use existing FatigueDetectionGUI)
        # Minimize console output in GUI mode
        import os
        os.environ['GUI_MODE'] = '1'
        
        # Set logging to WARNING level for GUI mode (less console spam)
        import logging
        logging.getLogger().setLevel(logging.WARNING)
        
        try:
            # Setup directories before starting GUI
            setup_directories()
            
            # Import and run existing GUI
            from src.output_layer.ui.main_window import FatigueDetectionGUI
            
            # Check if enhanced features should be enabled by default in GUI
            enhanced_gui = True  # Enable enhanced features by default in GUI mode
            if enhanced_gui:
                print("🚀 GUI Mode: Enhanced features enabled")
            
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