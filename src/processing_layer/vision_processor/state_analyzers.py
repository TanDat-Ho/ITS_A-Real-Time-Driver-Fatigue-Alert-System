"""
state_analyzers.py
-----------------
State analysis functions for fatigue detection
Extracted from rule_based.py for better code organization
"""

from typing import Optional, Dict, List
from .detection_enums import AlertLevel, EyeState, MouthState, HeadState


class StateAnalyzer:
    """Analyzes individual states from detection data."""
    
    @staticmethod
    def analyze_eye_state(ear_data: Optional[Dict]) -> EyeState:
        """
        Determine eye state from EAR numerical data.
        
        Args:
            ear_data: Numerical data from EAR calculation
            
        Returns:
            EyeState: Current eye state
        """
        if not ear_data:
            return EyeState.OPEN
            
        if ear_data.get("is_drowsy_duration", False):
            return EyeState.DROWSY
        elif ear_data.get("is_below_threshold", False):
            return EyeState.CLOSING
        elif ear_data.get("consecutive_frames", 0) > 0:
            return EyeState.BLINKING
        else:
            return EyeState.OPEN
    
    @staticmethod
    def analyze_mouth_state(mar_data: Optional[Dict]) -> MouthState:
        """
        Determine mouth state from MAR numerical data.
        
        Args:
            mar_data: Numerical data from MAR calculation
            
        Returns:
            MouthState: Current mouth state
        """
        if not mar_data:
            return MouthState.CLOSED
            
        if mar_data.get("is_yawn_duration", False):
            return MouthState.YAWNING
        elif mar_data.get("is_above_yawn_threshold", False):
            return MouthState.WIDE_OPEN
        elif mar_data.get("is_above_speaking_threshold", False):
            return MouthState.SPEAKING
        else:
            return MouthState.CLOSED
    
    @staticmethod
    def analyze_head_state(head_data: Optional[Dict]) -> HeadState:
        """
        Determine head state from head pose numerical data.
        
        Args:
            head_data: Numerical data from head pose calculation
            
        Returns:
            HeadState: Current head state
        """
        if not head_data:
            return HeadState.NORMAL
            
        if head_data.get("is_drowsy_duration", False):
            return HeadState.HEAD_DOWN_DROWSY
        elif head_data.get("is_above_drowsy_threshold", False):
            return HeadState.TILTED
        elif head_data.get("is_above_normal_threshold", False):
            return HeadState.SLIGHTLY_TILTED
        else:
            return HeadState.NORMAL

    @staticmethod
    def determine_alert_level(eye_state: EyeState, 
                            mouth_state: MouthState, 
                            head_state: HeadState,
                            combination_threshold: int = 2) -> AlertLevel:
        """
        Determine overall alert level based on individual states.
        
        Args:
            eye_state: Current eye state
            mouth_state: Current mouth state  
            head_state: Current head state
            combination_threshold: Minimum conditions for HIGH alert
            
        Returns:
            AlertLevel: Overall alert level
        """
        high_risk_conditions = 0
        medium_risk_conditions = 0
        
        # Count high risk conditions
        if eye_state == EyeState.DROWSY:
            high_risk_conditions += 1
        elif eye_state in [EyeState.CLOSING]:
            medium_risk_conditions += 1
            
        if mouth_state == MouthState.YAWNING:
            high_risk_conditions += 1
        elif mouth_state == MouthState.WIDE_OPEN:
            medium_risk_conditions += 1
            
        if head_state == HeadState.HEAD_DOWN_DROWSY:
            high_risk_conditions += 1
        elif head_state == HeadState.TILTED:
            medium_risk_conditions += 1
        
        # Determine alert level based on rule combinations
        if high_risk_conditions >= combination_threshold:
            return AlertLevel.HIGH
        elif high_risk_conditions >= 1 or medium_risk_conditions >= 2:
            return AlertLevel.MEDIUM
        elif medium_risk_conditions >= 1:
            return AlertLevel.LOW
        else:
            return AlertLevel.NONE

    @staticmethod
    def build_alert_conditions(eye_state: EyeState, 
                             mouth_state: MouthState, 
                             head_state: HeadState) -> List[str]:
        """
        Build alert conditions list based on current states.
        
        Args:
            eye_state: Current eye state
            mouth_state: Current mouth state
            head_state: Current head state
            
        Returns:
            List of alert condition descriptions
        """
        alert_conditions = []
        
        if eye_state == EyeState.DROWSY:
            alert_conditions.append("😴 Prolonged eye closure (>1.2s) - Microsleep risk")
        if mouth_state == MouthState.YAWNING:
            alert_conditions.append("😪 Excessive yawning - Oxygen deficiency sign")
        if head_state == HeadState.HEAD_DOWN_DROWSY:
            alert_conditions.append("😵 Head nodding - Loss of muscle control")
        
        return alert_conditions