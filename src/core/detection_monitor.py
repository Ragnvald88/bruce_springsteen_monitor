# src/core/detection_monitor.py
"""
Advanced Detection Monitoring System
Tracks access patterns, login states, blocks, and stealth effectiveness
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Deque
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class DetectionEventType(Enum):
    """Types of detection events"""
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    CAPTCHA_TRIGGERED = "captcha_triggered"
    CAPTCHA_SOLVED = "captcha_solved"
    RATE_LIMITED = "rate_limited"
    IP_BLOCKED = "ip_blocked"
    FINGERPRINT_CHALLENGED = "fingerprint_challenged"
    SESSION_EXPIRED = "session_expired"
    STEALTH_CHECK_PASSED = "stealth_check_passed"
    STEALTH_CHECK_FAILED = "stealth_check_failed"
    BOT_DETECTED = "bot_detected"
    CLOUDFLARE_CHALLENGE = "cloudflare_challenge"
    QUEUE_ENTERED = "queue_entered"
    QUEUE_BYPASSED = "queue_bypassed"


@dataclass
class DetectionEvent:
    """Single detection event record"""
    timestamp: float
    event_type: DetectionEventType
    platform: str
    profile_id: str
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)
    fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "platform": self.platform,
            "profile_id": self.profile_id,
            "success": self.success,
            "details": self.details,
            "fingerprint": self.fingerprint,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat()
        }


@dataclass
class PlatformMetrics:
    """Metrics for a specific platform"""
    total_attempts: int = 0
    successful_access: int = 0
    blocked_access: int = 0
    login_attempts: int = 0
    successful_logins: int = 0
    failed_logins: int = 0
    captcha_encounters: int = 0
    captcha_solved: int = 0
    rate_limits_hit: int = 0
    ip_blocks: int = 0
    bot_detections: int = 0
    avg_response_time_ms: float = 0.0
    last_successful_access: Optional[float] = None
    last_block_time: Optional[float] = None
    current_streak: int = 0
    max_streak: int = 0
    
    def calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_access / self.total_attempts) * 100
    
    def calculate_block_rate(self) -> float:
        """Calculate block rate"""
        if self.total_attempts == 0:
            return 0.0
        return (self.blocked_access / self.total_attempts) * 100


class DetectionMonitor:
    """
    Central monitoring system for detection events
    Provides real-time and historical analysis
    """
    
    def __init__(self, log_dir: Path = None, max_events: int = 10000):
        self.log_dir = log_dir or Path("logs/detection_metrics")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage
        self.events: Deque[DetectionEvent] = deque(maxlen=max_events)
        self.platform_metrics: Dict[str, PlatformMetrics] = defaultdict(PlatformMetrics)
        self.profile_metrics: Dict[str, Dict[str, PlatformMetrics]] = defaultdict(
            lambda: defaultdict(PlatformMetrics)
        )
        
        # Real-time tracking
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.recent_blocks: Deque[DetectionEvent] = deque(maxlen=100)
        
        # Persistence
        self.last_save_time = time.time()
        self.save_interval = 60  # Save every minute
        
        # Load existing data
        self._load_metrics()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background monitoring tasks"""
        asyncio.create_task(self._periodic_save())
        asyncio.create_task(self._calculate_rolling_metrics())
    
    async def _periodic_save(self):
        """Periodically save metrics to disk"""
        while True:
            try:
                await asyncio.sleep(self.save_interval)
                self._save_metrics()
            except Exception as e:
                logger.error(f"Error in periodic save: {e}")
    
    async def _calculate_rolling_metrics(self):
        """Calculate rolling metrics every 30 seconds"""
        while True:
            try:
                await asyncio.sleep(30)
                self._update_rolling_metrics()
            except Exception as e:
                logger.error(f"Error calculating rolling metrics: {e}")
    
    def log_event(
        self,
        event_type: DetectionEventType,
        platform: str,
        profile_id: str,
        success: bool,
        details: Dict[str, Any] = None,
        fingerprint: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> DetectionEvent:
        """Log a detection event"""
        event = DetectionEvent(
            timestamp=time.time(),
            event_type=event_type,
            platform=platform,
            profile_id=profile_id,
            success=success,
            details=details or {},
            fingerprint=fingerprint,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Store event
        self.events.append(event)
        
        # Update metrics
        self._update_metrics(event)
        
        # Track blocks
        if event_type in [
            DetectionEventType.ACCESS_DENIED,
            DetectionEventType.IP_BLOCKED,
            DetectionEventType.BOT_DETECTED,
            DetectionEventType.RATE_LIMITED
        ]:
            self.recent_blocks.append(event)
            logger.warning(
                f"🚫 BLOCKED: {platform} - {event_type.value} - Profile: {profile_id}"
            )
        
        # Log success
        if success and event_type == DetectionEventType.ACCESS_GRANTED:
            logger.info(
                f"✅ ACCESS: {platform} - Profile: {profile_id} - "
                f"Streak: {self.platform_metrics[platform].current_streak}"
            )
        
        # Real-time notification for important events
        self._notify_event(event)
        
        return event
    
    def _update_metrics(self, event: DetectionEvent):
        """Update platform and profile metrics"""
        platform_metric = self.platform_metrics[event.platform]
        profile_metric = self.profile_metrics[event.profile_id][event.platform]
        
        # Update counters based on event type
        if event.event_type == DetectionEventType.ACCESS_GRANTED:
            platform_metric.successful_access += 1
            platform_metric.current_streak += 1
            platform_metric.max_streak = max(
                platform_metric.max_streak,
                platform_metric.current_streak
            )
            platform_metric.last_successful_access = event.timestamp
            
        elif event.event_type == DetectionEventType.ACCESS_DENIED:
            platform_metric.blocked_access += 1
            platform_metric.current_streak = 0
            platform_metric.last_block_time = event.timestamp
            
        elif event.event_type == DetectionEventType.LOGIN_SUCCESS:
            platform_metric.successful_logins += 1
            platform_metric.login_attempts += 1
            
        elif event.event_type == DetectionEventType.LOGIN_FAILED:
            platform_metric.failed_logins += 1
            platform_metric.login_attempts += 1
            
        elif event.event_type == DetectionEventType.CAPTCHA_TRIGGERED:
            platform_metric.captcha_encounters += 1
            
        elif event.event_type == DetectionEventType.CAPTCHA_SOLVED:
            platform_metric.captcha_solved += 1
            
        elif event.event_type == DetectionEventType.RATE_LIMITED:
            platform_metric.rate_limits_hit += 1
            platform_metric.current_streak = 0
            
        elif event.event_type == DetectionEventType.IP_BLOCKED:
            platform_metric.ip_blocks += 1
            platform_metric.current_streak = 0
            
        elif event.event_type == DetectionEventType.BOT_DETECTED:
            platform_metric.bot_detections += 1
            platform_metric.current_streak = 0
        
        # Always increment total attempts for access-related events
        if event.event_type in [
            DetectionEventType.ACCESS_GRANTED,
            DetectionEventType.ACCESS_DENIED
        ]:
            platform_metric.total_attempts += 1
        
        # Update response time if provided
        if "response_time_ms" in event.details:
            self._update_avg_response_time(
                platform_metric,
                event.details["response_time_ms"]
            )
    
    def _update_avg_response_time(self, metric: PlatformMetrics, new_time: float):
        """Update average response time"""
        if metric.avg_response_time_ms == 0:
            metric.avg_response_time_ms = new_time
        else:
            # Exponential moving average
            alpha = 0.1
            metric.avg_response_time_ms = (
                alpha * new_time + (1 - alpha) * metric.avg_response_time_ms
            )
    
    def get_platform_summary(self, platform: str) -> Dict[str, Any]:
        """Get comprehensive summary for a platform"""
        metric = self.platform_metrics[platform]
        
        # Calculate time-based metrics
        now = time.time()
        last_access_ago = None
        last_block_ago = None
        
        if metric.last_successful_access:
            last_access_ago = now - metric.last_successful_access
        
        if metric.last_block_time:
            last_block_ago = now - metric.last_block_time
        
        return {
            "platform": platform,
            "total_attempts": metric.total_attempts,
            "successful_access": metric.successful_access,
            "blocked_access": metric.blocked_access,
            "success_rate": metric.calculate_success_rate(),
            "block_rate": metric.calculate_block_rate(),
            "login_success_rate": (
                (metric.successful_logins / metric.login_attempts * 100)
                if metric.login_attempts > 0 else 0
            ),
            "captcha_solve_rate": (
                (metric.captcha_solved / metric.captcha_encounters * 100)
                if metric.captcha_encounters > 0 else 0
            ),
            "current_streak": metric.current_streak,
            "max_streak": metric.max_streak,
            "avg_response_time_ms": round(metric.avg_response_time_ms, 2),
            "last_successful_access": last_access_ago,
            "last_block": last_block_ago,
            "rate_limits_hit": metric.rate_limits_hit,
            "ip_blocks": metric.ip_blocks,
            "bot_detections": metric.bot_detections,
            "health_score": self._calculate_health_score(metric)
        }
    
    def _calculate_health_score(self, metric: PlatformMetrics) -> float:
        """Calculate platform health score (0-100)"""
        factors = []
        
        # Success rate (40% weight)
        success_rate = metric.calculate_success_rate()
        factors.append(success_rate * 0.4)
        
        # Current streak (20% weight)
        streak_score = min(metric.current_streak * 10, 100)
        factors.append(streak_score * 0.2)
        
        # No recent blocks (20% weight)
        if metric.last_block_time:
            time_since_block = time.time() - metric.last_block_time
            no_block_score = min(time_since_block / 3600 * 100, 100)  # 1 hour = 100%
        else:
            no_block_score = 100
        factors.append(no_block_score * 0.2)
        
        # Low bot detection (20% weight)
        if metric.total_attempts > 0:
            bot_detection_rate = (metric.bot_detections / metric.total_attempts) * 100
            bot_score = max(0, 100 - bot_detection_rate * 10)
        else:
            bot_score = 100
        factors.append(bot_score * 0.2)
        
        return round(sum(factors), 2)
    
    def get_recent_events(
        self,
        limit: int = 100,
        platform: str = None,
        event_type: DetectionEventType = None
    ) -> List[Dict[str, Any]]:
        """Get recent events with optional filtering"""
        events = list(self.events)
        
        # Apply filters
        if platform:
            events = [e for e in events if e.platform == platform]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Sort by timestamp descending and limit
        events.sort(key=lambda x: x.timestamp, reverse=True)
        events = events[:limit]
        
        return [e.to_dict() for e in events]
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        platforms_data = {}
        for platform in self.platform_metrics:
            platforms_data[platform] = self.get_platform_summary(platform)
        
        # Calculate global metrics
        total_attempts = sum(m.total_attempts for m in self.platform_metrics.values())
        total_success = sum(m.successful_access for m in self.platform_metrics.values())
        total_blocks = sum(m.blocked_access for m in self.platform_metrics.values())
        
        return {
            "timestamp": time.time(),
            "platforms": platforms_data,
            "global_metrics": {
                "total_attempts": total_attempts,
                "total_success": total_success,
                "total_blocks": total_blocks,
                "global_success_rate": (
                    (total_success / total_attempts * 100) if total_attempts > 0 else 0
                ),
                "active_sessions": len(self.active_sessions),
                "recent_blocks": [e.to_dict() for e in list(self.recent_blocks)[-10:]]
            },
            "recent_events": self.get_recent_events(limit=50),
            "alerts": self._get_active_alerts()
        }
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts based on current metrics"""
        alerts = []
        
        for platform, metric in self.platform_metrics.items():
            # High block rate alert
            if metric.calculate_block_rate() > 30:
                alerts.append({
                    "severity": "high",
                    "platform": platform,
                    "message": f"High block rate: {metric.calculate_block_rate():.1f}%",
                    "timestamp": time.time()
                })
            
            # Recent IP block alert
            if metric.last_block_time and (time.time() - metric.last_block_time) < 300:
                alerts.append({
                    "severity": "medium",
                    "platform": platform,
                    "message": "Recent block detected",
                    "timestamp": metric.last_block_time
                })
            
            # Low health score alert
            health_score = self._calculate_health_score(metric)
            if health_score < 50:
                alerts.append({
                    "severity": "medium",
                    "platform": platform,
                    "message": f"Low health score: {health_score:.1f}",
                    "timestamp": time.time()
                })
        
        return alerts
    
    def clear_metrics(self, platform: str = None):
        """Clear metrics for a specific platform or all"""
        if platform:
            if platform in self.platform_metrics:
                self.platform_metrics[platform] = PlatformMetrics()
                # Clear events for this platform
                self.events = deque(
                    (e for e in self.events if e.platform != platform),
                    maxlen=self.events.maxlen
                )
        else:
            # Clear all metrics
            self.platform_metrics.clear()
            self.profile_metrics.clear()
            self.events.clear()
            self.recent_blocks.clear()
        
        # Save cleared state
        self._save_metrics()
        logger.info(f"Metrics cleared for: {platform or 'all platforms'}")
    
    def _save_metrics(self):
        """Save metrics to disk"""
        try:
            # Save current metrics
            metrics_file = self.log_dir / "detection_metrics.json"
            with open(metrics_file, "w") as f:
                json.dump({
                    "last_updated": time.time(),
                    "platform_metrics": {
                        platform: asdict(metric)
                        for platform, metric in self.platform_metrics.items()
                    },
                    "recent_events": [e.to_dict() for e in list(self.events)[-1000:]]
                }, f, indent=2)
            
            # Save daily log
            today = datetime.now().strftime("%Y-%m-%d")
            daily_file = self.log_dir / f"detection_log_{today}.jsonl"
            
            # Append new events since last save
            new_events = [
                e for e in self.events
                if e.timestamp > self.last_save_time
            ]
            
            with open(daily_file, "a") as f:
                for event in new_events:
                    f.write(json.dumps(event.to_dict()) + "\n")
            
            self.last_save_time = time.time()
            
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def _load_metrics(self):
        """Load metrics from disk"""
        try:
            metrics_file = self.log_dir / "detection_metrics.json"
            if metrics_file.exists():
                with open(metrics_file, "r") as f:
                    data = json.load(f)
                
                # Restore platform metrics
                for platform, metric_data in data.get("platform_metrics", {}).items():
                    self.platform_metrics[platform] = PlatformMetrics(**metric_data)
                
                logger.info(f"Loaded metrics for {len(self.platform_metrics)} platforms")
        
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")
    
    def _update_rolling_metrics(self):
        """Update rolling time-window metrics"""
        # This would calculate metrics for different time windows
        # (last hour, last 24 hours, etc.)
        pass
    
    def _notify_event(self, event: DetectionEvent):
        """Send real-time notification for important events"""
        # This would integrate with the notification system
        # For now, just log important events
        if event.event_type in [
            DetectionEventType.IP_BLOCKED,
            DetectionEventType.BOT_DETECTED
        ]:
            logger.critical(
                f"🚨 CRITICAL: {event.event_type.value} on {event.platform} "
                f"(Profile: {event.profile_id})"
            )


# Global instance
_monitor_instance: Optional[DetectionMonitor] = None


def get_detection_monitor() -> DetectionMonitor:
    """Get or create the global detection monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = DetectionMonitor()
    return _monitor_instance