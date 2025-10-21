import sys
import argparse
from pathlib import Path

# Thêm project root vào Python path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Import component
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
    for subdir in ["log", "assets/sounds", "assets/icon", "output/snapshots"]:
        (PROJECT_ROOT / subdir).mkdir(parents=True, exist_ok=True)
    print("✅ Directories verified.")

def show_config(config_type: str):
    """Display the chosen configuration."""
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
    print(f"🗣️ HEAD → threshold: {head['drowsy_threshold']}°, duration: {head['drowsy_duration']}s")
    print(f"⚡ Combination threshold: {config['combination_threshold']}/3")
    print(f"🚨 Critical duration: {config['critical_duration']}s")

def show_instructions():
    """Quick usage instructions."""
    print("""
🎮 USAGE
─────────────────────
[q] Quit     [r] Reset stats     [s] Screenshot
Ctrl+C → Exit forcefully
""")
    
def apply_config(config_type: str):
    """Apply config overrides to global parameters."""
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

def run_system(config_type: str):
    """Run the optimized fatigue detection system."""
    try:
        validate_config()
        apply_config(config_type)
        
        print("🚀 Starting OPTIMIZED multi-threaded fatigue detection system...")
        pipeline = create_pipeline()
        pipeline.run()
            
        print("👋 System stopped. Goodbye!")
    except KeyboardInterrupt:
        print("\n🛑 User terminated program.")
    except Exception as e:
        print(f"❌ Runtime error: {e}")
        return 1
    return 0

def main():
    parser = argparse.ArgumentParser(
        description="🚗 Driver Fatigue Detection System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-c", "--config", choices=["default", "sensitive", "conservative"], default="default")
    parser.add_argument("--info", "-i", action="store_true", help="Show configuration info only")
    parser.add_argument("--setup", action="store_true", help="Create required directories only")
    args = parser.parse_args()

    setup_directories()

    if args.setup:
        return 0

    show_config(args.config)

    if args.info:
        show_instructions()
        return 0

    show_instructions()

    try:
        input("\n🎯 Press Enter to start...")
    except KeyboardInterrupt:
        print("\n👋 Exit.")
        return 0

    return run_system(args.config)



if __name__ == "__main__":
    sys.exit(main())
