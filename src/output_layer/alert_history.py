"""
src/output_layer/alert_history.py

Alert History Manager for real-time alert tracking and statistics
"""

from collections import deque
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import csv
import os
import threading
import time


@dataclass
class AlertRecord:
    """Data structure for individual alert record"""
    timestamp: float
    datetime_str: str
    alert_level: str
    confidence: float
    ear_value: Optional[float] = None
    mar_value: Optional[float] = None
    head_pose: Optional[float] = None
    session_id: Optional[str] = None
    duration_ms: Optional[int] = None


@dataclass
class SessionStats:
    """Session-level statistics"""
    session_start: float
    total_alerts: int = 0
    critical_alerts: int = 0
    high_alerts: int = 0
    medium_alerts: int = 0
    low_alerts: int = 0
    avg_confidence: float = 0.0
    max_consecutive_alerts: int = 0
    total_session_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AlertHistoryManager:
    """Manages alert history with circular buffer and statistics"""
    
    def __init__(self, max_alerts: int = 500):
        self.max_alerts = max_alerts
        self.alerts = deque(maxlen=max_alerts)
        self.session_stats = SessionStats(session_start=time.time())
        self.current_session_id = self._generate_session_id()
        self.consecutive_alerts = 0
        self.last_alert_time = 0
        self.lock = threading.RLock()
        
        # Alert level counters
        self.level_counters = {
            'CRITICAL': 0,
            'HIGH': 0, 
            'MEDIUM': 0,
            'LOW': 0
        }
        
        print(f"🗂️ Alert History Manager initialized (max: {max_alerts} alerts)")
        
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"session_{int(time.time())}"
        
    def add_alert(self, alert_level: str, confidence: float = 0.0, 
                  ear_value: Optional[float] = None, mar_value: Optional[float] = None,
                  head_pose: Optional[float] = None) -> AlertRecord:
        """Add new alert to history"""
        
        with self.lock:
            current_time = time.time()
            
            # Create alert record
            alert = AlertRecord(
                timestamp=current_time,
                datetime_str=datetime.fromtimestamp(current_time).strftime("%H:%M:%S.%f")[:-3],
                alert_level=alert_level.upper(),
                confidence=confidence,
                ear_value=ear_value,
                mar_value=mar_value,
                head_pose=head_pose,
                session_id=self.current_session_id,
                duration_ms=int((current_time - self.last_alert_time) * 1000) if self.last_alert_time > 0 else 0
            )
            
            # Add to circular buffer
            self.alerts.append(alert)
            
            # Update statistics
            self._update_statistics(alert, current_time)
            
            self.last_alert_time = current_time
            
            return alert
    
    def _update_statistics(self, alert: AlertRecord, current_time: float):
        """Update session statistics"""
        # Total alerts
        self.session_stats.total_alerts += 1
        
        # Level-specific counters
        level = alert.alert_level
        if level in self.level_counters:
            self.level_counters[level] += 1
            
        # Update session stats
        if level == 'CRITICAL':
            self.session_stats.critical_alerts += 1
        elif level == 'HIGH':
            self.session_stats.high_alerts += 1
        elif level == 'MEDIUM':
            self.session_stats.medium_alerts += 1
        elif level == 'LOW':
            self.session_stats.low_alerts += 1
            
        # Consecutive alerts tracking
        if current_time - self.last_alert_time < 5.0:  # Within 5 seconds
            self.consecutive_alerts += 1
        else:
            self.consecutive_alerts = 1
            
        self.session_stats.max_consecutive_alerts = max(
            self.session_stats.max_consecutive_alerts,
            self.consecutive_alerts
        )
        
        # Average confidence
        total_confidence = sum(a.confidence for a in self.alerts if a.confidence > 0)
        confidence_count = sum(1 for a in self.alerts if a.confidence > 0)
        self.session_stats.avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 0.0
        
        # Session time
        self.session_stats.total_session_time = current_time - self.session_stats.session_start
    
    def get_recent_alerts(self, count: int = 50) -> List[AlertRecord]:
        """Get most recent alerts"""
        with self.lock:
            return list(self.alerts)[-count:] if count < len(self.alerts) else list(self.alerts)
    
    def get_alerts_by_level(self, level: str) -> List[AlertRecord]:
        """Get alerts filtered by level"""
        with self.lock:
            return [alert for alert in self.alerts if alert.alert_level == level.upper()]
    
    def get_alerts_in_timeframe(self, minutes: int = 30) -> List[AlertRecord]:
        """Get alerts within specified timeframe"""
        with self.lock:
            cutoff_time = time.time() - (minutes * 60)
            return [alert for alert in self.alerts if alert.timestamp >= cutoff_time]
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        with self.lock:
            summary = {
                'session_id': self.current_session_id,
                'session_stats': self.session_stats.to_dict(),
                'level_breakdown': self.level_counters.copy(),
                'total_alerts_in_buffer': len(self.alerts),
                'recent_activity': self._get_recent_activity_summary(),
                'peak_periods': self._identify_peak_periods()
            }
            return summary
    
    def _get_recent_activity_summary(self) -> Dict[str, Any]:
        """Get summary of recent activity"""
        recent_alerts = self.get_alerts_in_timeframe(10)  # Last 10 minutes
        
        if not recent_alerts:
            return {'status': 'quiet', 'alerts_count': 0}
            
        levels = [a.alert_level for a in recent_alerts]
        most_common_level = max(set(levels), key=levels.count) if levels else 'NONE'
        
        return {
            'status': 'active' if len(recent_alerts) > 5 else 'moderate',
            'alerts_count': len(recent_alerts),
            'dominant_level': most_common_level,
            'avg_confidence': sum(a.confidence for a in recent_alerts) / len(recent_alerts) if recent_alerts else 0
        }
    
    def _identify_peak_periods(self) -> List[Dict[str, Any]]:
        """Identify periods of high alert activity"""
        with self.lock:
            if len(self.alerts) < 10:
                return []
                
            # Group alerts by 5-minute windows
            windows = {}
            for alert in self.alerts:
                window_key = int(alert.timestamp // 300) * 300  # 5-minute windows
                if window_key not in windows:
                    windows[window_key] = []
                windows[window_key].append(alert)
            
            # Find windows with high activity (>= 5 alerts)
            peak_periods = []
            for window_start, window_alerts in windows.items():
                if len(window_alerts) >= 5:
                    levels = [a.alert_level for a in window_alerts]
                    peak_periods.append({
                        'start_time': datetime.fromtimestamp(window_start).strftime("%H:%M:%S"),
                        'duration': '5 minutes',
                        'alert_count': len(window_alerts),
                        'dominant_level': max(set(levels), key=levels.count),
                        'severity_score': self._calculate_severity_score(window_alerts)
                    })
            
            return sorted(peak_periods, key=lambda x: x['severity_score'], reverse=True)[:5]
    
    def _calculate_severity_score(self, alerts: List[AlertRecord]) -> float:
        """Calculate severity score for a group of alerts"""
        level_weights = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
        total_score = sum(level_weights.get(a.alert_level, 0) for a in alerts)
        return total_score / len(alerts) if alerts else 0
    
    def export_session_data(self, format: str = 'json', filepath: Optional[str] = None) -> str:
        """Export current session data"""
        with self.lock:
            if not filepath:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                os.makedirs('output/alert_history', exist_ok=True)
                filepath = f'output/alert_history/session_{timestamp}.{format}'
            
            if format.lower() == 'json':
                return self._export_json(filepath)
            elif format.lower() == 'csv':
                return self._export_csv(filepath)
            else:
                raise ValueError(f"Unsupported format: {format}")
    
    def _export_json(self, filepath: str) -> str:
        """Export to JSON format"""
        export_data = {
            'session_summary': self.get_session_summary(),
            'all_alerts': [asdict(alert) for alert in self.alerts]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _export_csv(self, filepath: str) -> str:
        """Export to CSV format"""
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if not self.alerts:
                return filepath
                
            writer = csv.DictWriter(f, fieldnames=asdict(self.alerts[0]).keys())
            writer.writeheader()
            
            for alert in self.alerts:
                writer.writerow(asdict(alert))
        
        return filepath
    
    def get_realtime_stats_for_gui(self) -> Dict[str, Any]:
        """Get stats optimized for GUI display"""
        with self.lock:
            recent_alerts = self.get_recent_alerts(10)
            
            return {
                'total_alerts': self.session_stats.total_alerts,
                'recent_alerts': len(recent_alerts),
                'level_counts': self.level_counters.copy(),
                'session_duration': int(self.session_stats.total_session_time),
                'avg_confidence': round(self.session_stats.avg_confidence, 2),
                'consecutive_alerts': self.consecutive_alerts,
                'last_alert': recent_alerts[-1].datetime_str if recent_alerts else 'None',
                'activity_status': self._get_recent_activity_summary()['status']
            }
    
    def clear_session(self):
        """Clear current session and start fresh"""
        with self.lock:
            self.alerts.clear()
            self.session_stats = SessionStats(session_start=time.time())
            self.current_session_id = self._generate_session_id()
            self.consecutive_alerts = 0
            self.last_alert_time = 0
            self.level_counters = {k: 0 for k in self.level_counters}
            
        print(f"🔄 Alert history cleared - New session: {self.current_session_id}")


# Global alert history manager instance
alert_history = AlertHistoryManager()

def log_alert_to_history(alert_level: str, confidence: float = 0.0, **kwargs) -> AlertRecord:
    """Convenience function to log alert to history"""
    return alert_history.add_alert(alert_level, confidence, **kwargs)

def get_alert_stats_for_gui() -> Dict[str, Any]:
    """Convenience function for GUI stats"""
    return alert_history.get_realtime_stats_for_gui()

if __name__ == "__main__":
    # Test the alert history system
    manager = AlertHistoryManager(max_alerts=100)
    
    # Simulate some alerts
    import random
    levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    
    for i in range(20):
        level = random.choice(levels)
        confidence = random.uniform(0.5, 1.0)
        manager.add_alert(level, confidence)
        time.sleep(0.1)
    
    # Print summary
    summary = manager.get_session_summary()
    print("📊 Session Summary:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    # Export test
    export_path = manager.export_session_data('json')
    print(f"📁 Exported to: {export_path}")