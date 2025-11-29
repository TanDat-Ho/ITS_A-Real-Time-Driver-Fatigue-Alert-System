"""
adaptive_timing.py
-----------------
Adaptive timing system for personalized fatigue detection thresholds
"""

import time
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """User profile for adaptive thresholds"""
    avg_ear_baseline: float = 0.30
    avg_mar_baseline: float = 0.45
    blink_frequency: float = 0.3  # blinks per second
    sensitivity_level: str = "medium"  # low, medium, high
    driving_hours_today: float = 0.0
    time_since_last_break: float = 0.0

class AdaptiveTimingManager:
    """Manages adaptive timing for personalized detection"""
    
    def __init__(self):
        self.user_profile = UserProfile()
        self.recent_ear_values = deque(maxlen=300)  # 10 seconds at 30 FPS
        self.recent_mar_values = deque(maxlen=300)
        self.recent_blinks = deque(maxlen=1800)     # 60 seconds at 30 FPS
        self.session_start_time = time.time()
        
    def update_baselines(self, ear: float, mar: float, is_blink: bool):
        """Update user baselines based on recent behavior"""
        current_time = time.time()
        
        # Update recent values
        self.recent_ear_values.append(ear)
        self.recent_mar_values.append(mar)
        
        if is_blink:
            self.recent_blinks.append(current_time)
        
        # Update baselines every 30 seconds
        if len(self.recent_ear_values) >= 900:  # 30 seconds
            self.user_profile.avg_ear_baseline = sum(self.recent_ear_values) / len(self.recent_ear_values)
            self.user_profile.avg_mar_baseline = sum(self.recent_mar_values) / len(self.recent_mar_values)
            
            # Calculate blink frequency
            recent_blinks = [t for t in self.recent_blinks if current_time - t <= 60]
            self.user_profile.blink_frequency = len(recent_blinks) / 60.0
            
    def get_adaptive_thresholds(self) -> Dict[str, float]:
        """Get adaptive thresholds based on user profile"""
        driving_time = (time.time() - self.session_start_time) / 3600  # hours
        
        # Fatigue factor increases with driving time
        fatigue_factor = min(1.2, 1.0 + (driving_time * 0.05))
        
        # Sensitivity adjustments
        sensitivity_multiplier = {
            "low": 0.9,
            "medium": 1.0,
            "high": 1.1
        }.get(self.user_profile.sensitivity_level, 1.0)
        
        # Adaptive thresholds
        ear_drowsy = (self.user_profile.avg_ear_baseline * 0.7) * fatigue_factor * sensitivity_multiplier
        mar_yawn = (self.user_profile.avg_mar_baseline * 1.4) * fatigue_factor * sensitivity_multiplier
        
        return {
            "ear_drowsy_threshold": max(0.15, min(0.30, ear_drowsy)),
            "mar_yawn_threshold": max(0.55, min(0.80, mar_yawn)),
            "fatigue_factor": fatigue_factor,
            "sensitivity_multiplier": sensitivity_multiplier
        }
    
    def should_increase_sensitivity(self) -> bool:
        """Determine if sensitivity should be increased based on context"""
        driving_time = (time.time() - self.session_start_time) / 3600
        
        # Increase sensitivity after 2+ hours of driving
        if driving_time > 2.0:
            return True
            
        # Increase sensitivity if blink frequency is decreasing
        if self.user_profile.blink_frequency < 0.15:  # Less than 0.15 blinks/second
            return True
            
        return False
    
    def get_recommendation_priority(self) -> str:
        """Get recommendation priority based on adaptive analysis"""
        driving_time = (time.time() - self.session_start_time) / 3600
        
        if driving_time > 4.0:
            return "MANDATORY_BREAK"
        elif driving_time > 2.0:
            return "SUGGESTED_BREAK"
        elif self.user_profile.blink_frequency < 0.1:
            return "ATTENTION_REQUIRED"
        else:
            return "NORMAL"