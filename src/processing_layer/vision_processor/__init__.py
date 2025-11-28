"""
vision_processor package
-----------------------
Refactored fatigue detection components for better maintainability

Components:
- rule_based.py: Main RuleBasedFatigueDetector class
- detection_enums.py: All enum definitions (AlertLevel, FatigueState, etc.)
- detection_config.py: Configuration and recommendation management
- state_analyzers.py: State analysis functions
- detector_factory.py: Factory pattern for creating detectors
"""

# Import main classes for easy access
from .rule_based import RuleBasedFatigueDetector
from .detection_enums import AlertLevel, FatigueState, EyeState, MouthState, HeadState
from .detection_config import FatigueDetectionConfig, RecommendationManager
from .state_analyzers import StateAnalyzer
from .detector_factory import DetectorFactory

# Export commonly used components
__all__ = [
    # Main detector class
    'RuleBasedFatigueDetector',
    
    # Enums
    'AlertLevel',
    'FatigueState', 
    'EyeState',
    'MouthState',
    'HeadState',
    
    # Configuration and management
    'FatigueDetectionConfig',
    'RecommendationManager',
    'StateAnalyzer',
    'DetectorFactory'
]