"""
StealthMaster AI v3.0 - Adaptive Scheduler
Intelligent scheduling based on ticket drop patterns and platform behavior
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, time as datetime_time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque, defaultdict
import numpy as np
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ActivityLevel(Enum):
    """Platform activity levels"""
    DEAD = "dead"  # No activity for extended period
    LOW = "low"  # Minimal activity
    NORMAL = "normal"  # Regular activity
    HIGH = "high"  # Increased activity
    CRITICAL = "critical"  # Ticket drops detected


@dataclass
class PlatformPattern:
    """Learned patterns for a specific platform"""
    platform: str
    
    # Time-based patterns
    peak_hours: List[int] = field(default_factory=list)  # Hours of day with high activity
    peak_days: List[int] = field(default_factory=list)  # Days of week (0=Monday)
    
    # Drop patterns
    drop_intervals: deque = field(default_factory=lambda: deque(maxlen=100))
    average_drop_interval: float = 0.0
    last_drop_time: Optional[datetime] = None
    
    # Activity tracking
    activity_history: deque = field(default_factory=lambda: deque(maxlen=1000))
    current_activity_level: ActivityLevel = ActivityLevel.NORMAL
    
    # Success metrics
    check_success_rate: float = 0.0
    total_checks: int = 0
    successful_checks: int = 0
    
    def update_drop_time(self, timestamp: datetime):
        """Update drop pattern with new ticket availability"""
        if self.last_drop_time:
            interval = (timestamp - self.last_drop_time).total_seconds()
            self.drop_intervals.append(interval)
            self.average_drop_interval = np.mean(list(self.drop_intervals))
            
        self.last_drop_time = timestamp
        
        # Update peak hours
        hour = timestamp.hour
        if hour not in self.peak_hours:
            self.peak_hours.append(hour)
            
        # Update peak days
        day = timestamp.weekday()
        if day not in self.peak_days:
            self.peak_days.append(day)
            
    def predict_next_drop(self) -> Optional[datetime]:
        """Predict when next ticket drop might occur"""
        if not self.last_drop_time or len(self.drop_intervals) < 5:
            return None
            
        # Use exponential weighted average for prediction
        weights = np.exp(np.linspace(-1, 0, len(self.drop_intervals)))
        weights /= weights.sum()
        
        weighted_avg = np.average(list(self.drop_intervals), weights=weights)
        
        # Add some randomness (±20%)
        variance = weighted_avg * 0.2
        predicted_interval = weighted_avg + np.random.uniform(-variance, variance)
        
        return self.last_drop_time + timedelta(seconds=predicted_interval)


class AdaptiveScheduler:
    """
    Intelligent scheduler that learns from patterns and adapts monitoring frequency
    Minimizes unnecessary requests while maintaining quick response to ticket drops
    """
    
    def __init__(self):
        # Platform patterns
        self.patterns: Dict[str, PlatformPattern] = {}
        
        # Configuration
        self.base_intervals = {
            ActivityLevel.DEAD: 300,  # 5 minutes
            ActivityLevel.LOW: 120,  # 2 minutes
            ActivityLevel.NORMAL: 60,  # 1 minute
            ActivityLevel.HIGH: 30,  # 30 seconds
            ActivityLevel.CRITICAL: 10  # 10 seconds (only during drops)
        }
        
        # Global patterns
        self.global_quiet_hours = [(0, 6)]  # 12 AM - 6 AM
        self.global_peak_hours = [(10, 12), (14, 16), (19, 21)]  # Common drop times
        
        # Burst mode control
        self.burst_mode_duration = 300  # 5 minutes of intense monitoring after detection
        self.burst_mode_active: Dict[str, datetime] = {}
        
        # Learning parameters
        self.learning_rate = 0.1
        self.pattern_confidence_threshold = 0.7
        
        # Performance tracking
        self.request_savings = 0
        self.total_scheduled = 0
        
        logger.info("Adaptive scheduler initialized")
        
    def get_platform_pattern(self, platform: str) -> PlatformPattern:
        """Get or create pattern for platform"""
        if platform not in self.patterns:
            self.patterns[platform] = PlatformPattern(platform=platform)
        return self.patterns[platform]
        
    def calculate_next_check_interval(
        self, 
        platform: str, 
        priority: str = "NORMAL",
        last_activity: Optional[datetime] = None
    ) -> float:
        """
        Calculate optimal interval until next check
        
        Returns:
            Interval in seconds
        """
        pattern = self.get_platform_pattern(platform)
        current_time = datetime.now()
        
        # Check if in burst mode
        if platform in self.burst_mode_active:
            burst_start = self.burst_mode_active[platform]
            if (current_time - burst_start).total_seconds() < self.burst_mode_duration:
                return self.base_intervals[ActivityLevel.CRITICAL]
            else:
                del self.burst_mode_active[platform]
                
        # Determine current activity level
        activity_level = self._determine_activity_level(pattern, current_time)
        
        # Get base interval
        base_interval = self.base_intervals[activity_level]
        
        # Apply time-based modifiers
        interval = self._apply_time_modifiers(base_interval, pattern, current_time)
        
        # Apply priority modifiers
        if priority == "CRITICAL":
            interval *= 0.5
        elif priority == "LOW":
            interval *= 2.0
            
        # Apply pattern-based predictions
        interval = self._apply_predictive_modifiers(interval, pattern, current_time)
        
        # Ensure reasonable bounds
        interval = max(10, min(600, interval))  # 10 seconds to 10 minutes
        
        # Track savings
        self.total_scheduled += 1
        default_interval = 30  # What the old system would use
        self.request_savings += max(0, interval - default_interval) / default_interval
        
        logger.debug(f"Calculated interval for {platform}: {interval}s (activity: {activity_level.value})")
        
        return interval
        
    def _determine_activity_level(self, pattern: PlatformPattern, current_time: datetime) -> ActivityLevel:
        """Determine current activity level based on patterns"""
        
        # Check recent activity
        recent_window = 3600  # 1 hour
        recent_activities = [
            activity for activity in pattern.activity_history
            if (current_time - activity['timestamp']).total_seconds() < recent_window
        ]
        
        if not recent_activities:
            # No recent activity
            hours_since_last = float('inf')
            if pattern.last_drop_time:
                hours_since_last = (current_time - pattern.last_drop_time).total_seconds() / 3600
                
            if hours_since_last > 24:
                return ActivityLevel.DEAD
            elif hours_since_last > 6:
                return ActivityLevel.LOW
            else:
                return ActivityLevel.NORMAL
                
        # Calculate activity score
        success_count = sum(1 for a in recent_activities if a['success'])
        activity_score = success_count / len(recent_activities)
        
        # Determine level based on score
        if activity_score > 0.5:
            return ActivityLevel.HIGH
        elif activity_score > 0.1:
            return ActivityLevel.NORMAL
        else:
            return ActivityLevel.LOW
            
    def _apply_time_modifiers(self, base_interval: float, pattern: PlatformPattern, current_time: datetime) -> float:
        """Apply time-based modifiers to interval"""
        
        current_hour = current_time.hour
        current_day = current_time.weekday()
        
        # Check if in quiet hours
        for start, end in self.global_quiet_hours:
            if start <= current_hour < end:
                return base_interval * 3.0  # Much slower during quiet hours
                
        # Check if in peak hours
        for start, end in self.global_peak_hours:
            if start <= current_hour < end:
                base_interval *= 0.7  # Faster during peak hours
                
        # Platform-specific peak times
        if current_hour in pattern.peak_hours:
            base_interval *= 0.5  # Even faster during platform peaks
            
        if current_day in pattern.peak_days:
            base_interval *= 0.8
            
        return base_interval
        
    def _apply_predictive_modifiers(self, interval: float, pattern: PlatformPattern, current_time: datetime) -> float:
        """Apply predictive modifiers based on learned patterns"""
        
        # Check if we're approaching predicted drop time
        predicted_drop = pattern.predict_next_drop()
        if predicted_drop:
            time_until_drop = (predicted_drop - current_time).total_seconds()
            
            if 0 < time_until_drop < 600:  # Within 10 minutes
                # Exponentially decrease interval as we approach
                modifier = np.exp(-time_until_drop / 300)  # e^(-t/5min)
                interval *= (1 - modifier * 0.8)  # Up to 80% reduction
                
        return interval
        
    def record_check_result(
        self, 
        platform: str, 
        success: bool, 
        tickets_found: int = 0,
        response_time: float = 0
    ):
        """Record the result of a platform check"""
        pattern = self.get_platform_pattern(platform)
        current_time = datetime.now()
        
        # Update activity history
        pattern.activity_history.append({
            'timestamp': current_time,
            'success': success,
            'tickets_found': tickets_found,
            'response_time': response_time
        })
        
        # Update success metrics
        pattern.total_checks += 1
        if success:
            pattern.successful_checks += 1
        pattern.check_success_rate = pattern.successful_checks / pattern.total_checks
        
        # If tickets found, update drop patterns
        if tickets_found > 0:
            pattern.update_drop_time(current_time)
            # Activate burst mode
            self.burst_mode_active[platform] = current_time
            logger.info(f"🎯 Tickets detected on {platform}! Activating burst mode")
            
    def should_check_now(self, platform: str, last_check_time: Optional[datetime] = None) -> bool:
        """Determine if we should check the platform now"""
        
        if not last_check_time:
            return True
            
        pattern = self.get_platform_pattern(platform)
        current_time = datetime.now()
        
        # Always check if in burst mode
        if platform in self.burst_mode_active:
            return True
            
        # Check if approaching predicted drop
        predicted_drop = pattern.predict_next_drop()
        if predicted_drop:
            time_until_drop = (predicted_drop - current_time).total_seconds()
            if 0 < time_until_drop < 300:  # Within 5 minutes
                return True
                
        # Otherwise use standard interval
        time_since_last = (current_time - last_check_time).total_seconds()
        interval = self.calculate_next_check_interval(platform)
        
        return time_since_last >= interval
        
    def get_sleep_mode_duration(self) -> Optional[float]:
        """Calculate if system should enter sleep mode"""
        current_time = datetime.now()
        current_hour = current_time.hour
        
        # Check if in quiet hours
        for start, end in self.global_quiet_hours:
            if start <= current_hour < end:
                # Calculate time until quiet hours end
                wake_time = current_time.replace(hour=end, minute=0, second=0)
                if wake_time < current_time:
                    wake_time += timedelta(days=1)
                    
                sleep_duration = (wake_time - current_time).total_seconds()
                
                # Only sleep if no recent activity
                all_patterns = list(self.patterns.values())
                recent_activity = any(
                    p.last_drop_time and (current_time - p.last_drop_time).total_seconds() < 3600
                    for p in all_patterns
                )
                
                if not recent_activity:
                    return sleep_duration
                    
        return None
        
    def get_platform_recommendations(self, platform: str) -> Dict[str, Any]:
        """Get scheduling recommendations for a platform"""
        pattern = self.get_platform_pattern(platform)
        
        recommendations = {
            'current_activity': pattern.current_activity_level.value,
            'recommended_interval': self.calculate_next_check_interval(platform),
            'peak_hours': pattern.peak_hours,
            'peak_days': pattern.peak_days,
            'success_rate': pattern.check_success_rate,
            'last_drop': pattern.last_drop_time.isoformat() if pattern.last_drop_time else None,
            'predicted_next_drop': pattern.predict_next_drop().isoformat() if pattern.predict_next_drop() else None
        }
        
        return recommendations
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        total_patterns = len(self.patterns)
        active_platforms = sum(1 for p in self.patterns.values() if p.current_activity_level != ActivityLevel.DEAD)
        
        # Calculate request savings percentage
        savings_percentage = (self.request_savings / max(1, self.total_scheduled)) * 100
        
        return {
            'total_platforms': total_patterns,
            'active_platforms': active_platforms,
            'burst_mode_active': list(self.burst_mode_active.keys()),
            'request_savings_percent': savings_percentage,
            'total_checks_scheduled': self.total_scheduled,
            'patterns_learned': {
                platform: {
                    'drops_recorded': len(pattern.drop_intervals),
                    'average_interval_hours': pattern.average_drop_interval / 3600 if pattern.average_drop_interval else 0,
                    'confidence': min(len(pattern.drop_intervals) / 10, 1.0)  # Confidence based on data
                }
                for platform, pattern in self.patterns.items()
            }
        }
        
    def export_patterns(self, filepath: str):
        """Export learned patterns to file"""
        export_data = {}
        
        for platform, pattern in self.patterns.items():
            export_data[platform] = {
                'peak_hours': pattern.peak_hours,
                'peak_days': pattern.peak_days,
                'average_drop_interval': pattern.average_drop_interval,
                'last_drop_time': pattern.last_drop_time.isoformat() if pattern.last_drop_time else None,
                'drop_intervals': list(pattern.drop_intervals),
                'success_rate': pattern.check_success_rate
            }
            
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        logger.info(f"Exported patterns to {filepath}")
        
    def import_patterns(self, filepath: str):
        """Import previously learned patterns"""
        try:
            with open(filepath, 'r') as f:
                import_data = json.load(f)
                
            for platform, data in import_data.items():
                pattern = self.get_platform_pattern(platform)
                pattern.peak_hours = data.get('peak_hours', [])
                pattern.peak_days = data.get('peak_days', [])
                pattern.average_drop_interval = data.get('average_drop_interval', 0)
                
                if data.get('last_drop_time'):
                    pattern.last_drop_time = datetime.fromisoformat(data['last_drop_time'])
                    
                # Rebuild drop intervals
                for interval in data.get('drop_intervals', []):
                    pattern.drop_intervals.append(interval)
                    
            logger.info(f"Imported patterns from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to import patterns: {e}")
            

class MultiAccountCoordinator:
    """
    Coordinates multiple accounts to avoid detection
    Ensures accounts don't all check at the same time
    """
    
    def __init__(self, num_accounts: int):
        self.num_accounts = num_accounts
        self.account_schedules: Dict[str, datetime] = {}
        self.minimum_spacing = 5.0  # Minimum seconds between account checks
        
    def get_account_delay(self, account_id: str, base_interval: float) -> float:
        """Get delay for specific account to avoid clustering"""
        
        # Distribute accounts evenly across the interval
        account_index = hash(account_id) % self.num_accounts
        
        # Calculate offset within interval
        offset_fraction = account_index / max(1, self.num_accounts - 1)
        delay = offset_fraction * min(base_interval * 0.5, 30)  # Max 30 second spread
        
        # Add jitter
        jitter = np.random.uniform(-2, 2)
        delay += jitter
        
        return max(0, delay)
        
    def should_account_check(self, account_id: str) -> bool:
        """Determine if account should check now based on coordination"""
        
        current_time = datetime.now()
        
        # Check last check time
        if account_id in self.account_schedules:
            last_check = self.account_schedules[account_id]
            if (current_time - last_check).total_seconds() < self.minimum_spacing:
                return False
                
        # Check if other accounts checked recently
        recent_checks = sum(
            1 for last_time in self.account_schedules.values()
            if (current_time - last_time).total_seconds() < self.minimum_spacing
        )
        
        # Limit concurrent checks
        if recent_checks >= max(1, self.num_accounts // 3):
            return False
            
        return True
        
    def record_account_check(self, account_id: str):
        """Record that account performed a check"""
        self.account_schedules[account_id] = datetime.now()