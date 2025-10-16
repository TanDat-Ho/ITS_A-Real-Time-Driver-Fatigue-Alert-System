"""
run.py
-----------------
Main entry point for def print_banner():



Usage:
    python run.py                    # Run with default configuration
    python run.py --config sensitive # Run with sensitive configuration
    python run.py --help            # Show help
"""

"""Print startup banner"""
banner = """
===============================================================
                                                               
   🚗 DRIVER FATIGUE DETECTION SYSTEM                         
      Real-time Driver Fatigue Detection System               
                                                               
   📊 Technology: Computer Vision + Machine Learning          
   🎯 Features: EAR + MAR + Head Pose Analysis               
   🔬 Framework: OpenCV + MediaPipe                           
                                                               
===============================================================
    """
print(banner)



import os
import sys
import argparse
import logging
from pathlib import Path

# Thêm project root vào Python path
PROJECT_ROOT = Path(__file__).parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import components
try:
    from src.app.main import create_pipeline
    from src.app.config import (
        get_fatigue_config, validate_config, 
        EAR_CONFIG, MAR_CONFIG, HEAD_POSE_CONFIG,
        get_display_text
    )
    from src.processing_layer.vision_processor.rule_based import FatigueDetectionConfig
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("🔧 Make sure you're running from the project root directory")
    sys.exit(1)


def setup_directories():
    """Create necessary directories"""
    directories = [
        "log",
        "assets/sounds", 
        "assets/icon",
        "output/snapshots"
    ]
    
    for directory in directories:
        dir_path = PROJECT_ROOT / directory
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Created necessary directories in: {PROJECT_ROOT}")


def print_banner():
    """In banner khởi động"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🚗 HỆ THỐNG PHÁT HIỆN MỆT MỎI LÁI XE                       ║
║      Real-time Driver Fatigue Detection System                ║
║                                                               ║
║   📊 Công nghệ: Computer Vision + Machine Learning            ║
║   🎯 Chức năng: EAR + MAR + Head Pose Analysis               ║
║   🔬 Framework: OpenCV + MediaPipe                           ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_config_info(config_type: str = "default"):
    """Print configuration information"""
    print(f"\n📋 Current configuration: {config_type.upper()}")
    print("─" * 50)
    
    if config_type == "default":
        config = FatigueDetectionConfig.get_default_config()
    elif config_type == "sensitive":
        config = FatigueDetectionConfig.get_sensitive_config()
    elif config_type == "conservative":
        config = FatigueDetectionConfig.get_conservative_config()
    else:
        config = get_fatigue_config()
    
    print(f"👁️  EAR - Drowsy threshold: {config['ear_config']['drowsy_threshold']}")
    print(f"    Duration: {config['ear_config']['drowsy_duration']}s")
    
    print(f"👄 MAR - Yawn threshold: {config['mar_config']['yawn_threshold']}")
    print(f"    Duration: {config['mar_config']['yawn_duration']}s")
    
    print(f"🗣️  HEAD - Tilt threshold: {config['head_pose_config']['drowsy_threshold']}°")
    print(f"    Duration: {config['head_pose_config']['drowsy_duration']}s")
    
    print(f"⚡ Combination threshold: {config['combination_threshold']}/3 conditions")
    print(f"🚨 Critical duration: {config['critical_duration']}s")


def print_instructions():
    """Print usage instructions"""
    instructions = """
🎮 USAGE INSTRUCTIONS:
─────────────────────
⌨️  Keyboard shortcuts:
   • 'q' or 'Q'    → Exit program
   • 'r' or 'R'    → Reset session (clear statistics)
   • 's' or 'S'    → Take screenshot
   • 'Ctrl+C'      → Force quit

📊 Display information:
   • Top left: FPS, Frame count, status
   • Top right: Detection statistics
   • Bottom: Recommendations and warnings

🎨 Warning colors:
   • 🟢 GREEN     → Normal (safe)
   • 🟡 YELLOW    → Low warning
   • 🟠 ORANGE    → Medium warning
   • 🔴 RED       → Danger (need rest)
   • 🟣 PURPLE    → Critical (stop immediately)

💡 NOTE: Ensure adequate lighting and camera can see face clearly
    """
    print(instructions)


def run_system(config_type: str = "default", debug: bool = False):
    """
    Run the system with specified configuration
    
    Args:
        config_type: Configuration type (default/sensitive/conservative)
        debug: Debug mode
    """
    try:
        # Validate configuration
        validate_config()
        print("✅ Configuration is valid")
        
        # Create and run pipeline
        print("🚀 Starting system...")
        
        # Override configuration if needed
        if config_type != "default":
            print(f"🔧 Applying configuration: {config_type}")
            # Update global config
            global EAR_CONFIG, MAR_CONFIG, HEAD_POSE_CONFIG
            if config_type == "sensitive":
                config = FatigueDetectionConfig.get_sensitive_config()
            elif config_type == "conservative":
                config = FatigueDetectionConfig.get_conservative_config()
            
            EAR_CONFIG.update(config.get("ear_config", {}))
            MAR_CONFIG.update(config.get("mar_config", {}))
            HEAD_POSE_CONFIG.update(config.get("head_pose_config", {}))
        
        # Create pipeline
        pipeline = create_pipeline()
        
        # Set debug mode
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            print("🔍 Debug mode enabled")
        
        # Run
        pipeline.run()
        
        print("👋 System stopped. Thank you for using!")
        
    except KeyboardInterrupt:
        print("\n⌨️  User stopped the program")
    except Exception as e:
        print(f"❌ Error: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="🚗 Driver Fatigue Detection System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  python run.py                      # Run with default configuration
  python run.py --config sensitive   # Run with sensitive configuration (early detection)
  python run.py --config conservative # Run with conservative configuration (fewer alerts)
  python run.py --debug              # Run with debug mode
        """
    )
    
    parser.add_argument(
        "--config", "-c",
        choices=["default", "sensitive", "conservative"],
        default="default",
        help="Configuration type to use (default: default)"
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--info", "-i",
        action="store_true",
        help="Show configuration information only"
    )
    
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Create necessary directories only"
    )
    
    args = parser.parse_args()
    
    # Setup directories
    setup_directories()
    
    if args.setup:
        print("✅ Successfully created necessary directories")
        return 0
    
    # Print banner
    print_banner()
    
    # Print config info
    print_config_info(args.config)
    
    if args.info:
        print_instructions()
        return 0
    
    # Print instructions
    print_instructions()
    
    # Wait for user confirmation
    try:
        input("\n🎯 Press Enter to start or Ctrl+C to exit...")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    
    # Run system
    return run_system(args.config, args.debug)


if __name__ == "__main__":
    sys.exit(main())
