"""
src/output_layer/logger.py

Centralized logging system for fatigue detection
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any

class FatigueLogger:
    """Centralized logger for fatigue detection system"""
    
    def __init__(self, log_dir: str = "log", log_level: str = "INFO"):
        self.log_dir = log_dir
        self.setup_logger(log_level)
        
    def setup_logger(self, log_level: str):
        """Setup file-based logging with minimal console output"""
        
        # Create log directory
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"fatigue_detection_{timestamp}.log")
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                # File handler - detailed logging
                logging.FileHandler(log_file, encoding='utf-8'),
                # Console handler - minimal output
                logging.StreamHandler()
            ]
        )
        
        # Set console handler to WARNING level only
        console_handler = logging.getLogger().handlers[-1]
        console_handler.setLevel(logging.WARNING)
        
        self.logger = logging.getLogger("FatigueDetection")
        
    def log_alert(self, alert_level: str, details: Dict[str, Any]):
        """Log fatigue alerts"""
        message = f"ALERT [{alert_level}]: {details}"
        
        if alert_level in ["HIGH", "CRITICAL"]:
            self.logger.warning(message)  # Show in console
        else:
            self.logger.info(message)     # File only
            
    def log_performance(self, metrics: Dict[str, float]):
        """Log performance metrics"""
        self.logger.info(f"PERFORMANCE: {metrics}")
        
    def log_session_start(self):
        """Log session start"""
        self.logger.info("=" * 50)
        self.logger.info("FATIGUE DETECTION SESSION STARTED")
        self.logger.info("=" * 50)
        
    def log_session_end(self, summary: Dict[str, Any]):
        """Log session end with summary"""
        self.logger.info("=" * 50)
        self.logger.info("FATIGUE DETECTION SESSION ENDED")
        self.logger.info(f"SUMMARY: {summary}")
        self.logger.info("=" * 50)

# Global logger instance
fatigue_logger = FatigueLogger()
