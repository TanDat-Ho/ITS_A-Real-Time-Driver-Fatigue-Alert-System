"""
detection_enums.py
-----------------
Enum definitions for fatigue detection system
Extracted from rule_based.py for better code organization
"""

from enum import Enum


class AlertLevel(Enum):
    """Enum defining alert levels."""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FatigueState(Enum):
    """Enum defining fatigue states with driving safety context."""
    AWAKE = "ALERT_DRIVING"  # Safe to continue driving
    SLIGHTLY_TIRED = "EARLY_FATIGUE"  # Monitor closely, maintain alertness
    MODERATELY_TIRED = "CAUTION_NEEDED"  # Plan for rest stop soon
    SEVERELY_TIRED = "UNSAFE_TO_DRIVE"  # Pull over safely
    DANGEROUSLY_DROWSY = "IMMEDIATE_STOP_REQUIRED"  # Emergency - stop now


class EyeState(Enum):
    """Enum defining eye states."""
    OPEN = "OPEN"
    BLINKING = "BLINKING"
    CLOSING = "CLOSING"
    DROWSY = "DROWSY"


class MouthState(Enum):
    """Enum defining mouth states."""
    CLOSED = "CLOSED"
    SPEAKING = "SPEAKING"
    SLIGHTLY_OPEN = "SLIGHTLY_OPEN"
    WIDE_OPEN = "WIDE_OPEN"
    YAWNING = "YAWNING"


class HeadState(Enum):
    """Enum defining head pose states."""
    NORMAL = "NORMAL"
    SLIGHTLY_TILTED = "SLIGHTLY_TILTED"
    TILTED = "TILTED"
    HEAD_DOWN = "HEAD_DOWN"
    HEAD_DOWN_DROWSY = "HEAD_DOWN_DROWSY"