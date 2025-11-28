"""
detector_factory.py
------------------
Factory pattern for creating different types of fatigue detectors
Extracted from rule_based.py for better code organization
"""

from typing import Optional, Any, TYPE_CHECKING
from .detection_config import FatigueDetectionConfig

if TYPE_CHECKING:
    from .rule_based import RuleBasedFatigueDetector


class DetectorFactory:
    """Factory for creating different types of fatigue detectors."""
    
    @staticmethod
    def create_optimized_detector(lighting: str = "normal", 
                                camera_quality: str = "medium") -> 'RuleBasedFatigueDetector':
        """
        Create RuleBasedFatigueDetector with optimized engine.
        
        Args:
            lighting: Lighting conditions (low/normal/bright)
            camera_quality: Camera quality (low/medium/high)
            
        Returns:
            RuleBasedFatigueDetector with optimized engine
        """
        from .rule_based import RuleBasedFatigueDetector
        
        # Optimized integration removed - use enhanced detection instead
        config = FatigueDetectionConfig.get_default_config()
        
        # Create enhanced detector instead of optimized
        detector = RuleBasedFatigueDetector(
            use_enhanced_detection=True,
            use_optimized_engine=False,
            **config
        )
        
        return detector
    
    @staticmethod
    def create_enhanced_detector(lighting: str = "normal", 
                               camera_quality: str = "medium",
                               sensitivity: str = "default") -> 'RuleBasedFatigueDetector':
        """
        Create RuleBasedFatigueDetector with enhanced detection and quality awareness.
        
        Args:
            lighting: Lighting conditions (low/normal/bright)
            camera_quality: Camera quality (low/medium/high)
            sensitivity: Sensitivity level (sensitive/default/conservative)
            
        Returns:
            RuleBasedFatigueDetector with enhanced capabilities
        """
        from .rule_based import RuleBasedFatigueDetector
        
        # Get base config based on sensitivity
        if sensitivity == "sensitive":
            config = FatigueDetectionConfig.get_sensitive_config()
        elif sensitivity == "conservative":
            config = FatigueDetectionConfig.get_conservative_config()
        else:
            config = FatigueDetectionConfig.get_default_config()
        
        # Create enhanced detector
        detector = RuleBasedFatigueDetector(
            use_enhanced_detection=True,
            quality_aware=True,
            **config
        )
        
        return detector
    
    @staticmethod
    def create_full_featured_detector(lighting: str = "normal", 
                                    camera_quality: str = "medium",
                                    sensitivity: str = "default") -> 'RuleBasedFatigueDetector':
        """
        Create RuleBasedFatigueDetector with all enhanced features.
        
        Args:
            lighting: Lighting conditions
            camera_quality: Camera quality
            sensitivity: Sensitivity level
            
        Returns:
            Fully-featured RuleBasedFatigueDetector
        """
        from .rule_based import RuleBasedFatigueDetector
        
        # Get sensitivity-based config
        if sensitivity == "sensitive":
            config = FatigueDetectionConfig.get_sensitive_config()
        elif sensitivity == "conservative":
            config = FatigueDetectionConfig.get_conservative_config()
        else:
            config = FatigueDetectionConfig.get_default_config()
        
        # Create detector with all features enabled
        detector = RuleBasedFatigueDetector(
            use_enhanced_detection=True,
            use_optimized_engine=False,  # Enhanced detection is preferred
            quality_aware=True,
            **config
        )
        
        return detector