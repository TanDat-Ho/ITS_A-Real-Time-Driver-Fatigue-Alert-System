"""
src/output_layer/logger.py

Centralized logging system for fatigue detection
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler

# Constants for logging configuration
class LoggerConstants:
    """Constants for logging system"""
    DEFAULT_LOG_DIR = "log"
    DEFAULT_LOG_LEVEL = "INFO"
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class FatigueLogger:
    """Centralized logger for fatigue detection system"""
    
    def __init__(self, 
                 log_dir: str = LoggerConstants.DEFAULT_LOG_DIR, 
                 log_level: str = LoggerConstants.DEFAULT_LOG_LEVEL,
                 max_log_size: int = LoggerConstants.MAX_LOG_SIZE,
                 backup_count: int = LoggerConstants.BACKUP_COUNT):
        self.log_dir = log_dir
        self.max_log_size = max_log_size
        self.backup_count = backup_count
        self.setup_logger(log_level)
        
    def setup_logger(self, log_level: str):
        """Setup file-based logging with minimal console output"""
        
        # Create log directory
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"fatigue_detection_{timestamp}.log")
        
        # Configure logging with rotation
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=self.max_log_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(
            LoggerConstants.LOG_FORMAT,
            LoggerConstants.DATE_FORMAT
        ))
        
        # Create console handler for warnings only
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(logging.Formatter(
            "%(levelname)s: %(message)s"
        ))
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            handlers=[file_handler, console_handler]
        )
        
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
