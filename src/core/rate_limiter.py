"""
Intelligent Rate Limiter with Anti-Detection
Prevents aggressive scraping patterns that trigger bot detection
"""

import asyncio
import time
import random
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    # Base intervals (in seconds)
    min_interval: float = 30.0
    max_interval: float = 120.0
    
    # Burst mode settings
    burst_min_interval: float = 15.0
    burst_max_requests: int = 5
    burst_cooldown: float = 300.0  # 5 minutes
    
    # Anti-detection settings
    randomization_factor: float = 0.3  # 30% randomization
    backoff_multiplier: float = 2.0
    max_backoff: float = 300.0  # 5 minutes
    
    # Pattern breaking
    occasional_long_pause: float = 0.1  # 10% chance
    long_pause_duration: float = 180.0  # 3 minutes
    
    # Per-platform settings
    platform_multipliers: Dict[str, float] = field(default_factory=lambda: {
        'ticketmaster': 1.5,  # More sensitive to bot detection
        'fansale': 1.2,
        'vivaticket': 1.0
    })


class IntelligentRateLimiter:
    """Smart rate limiter that mimics human behavior"""
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        
        # Request history
        self.request_history: Dict[str, deque] = {}
        
        # Backoff state
        self.backoff_until: Dict[str, datetime] = {}
        self.consecutive_errors: Dict[str, int] = {}
        
        # Burst mode tracking
        self.burst_mode_active: Dict[str, bool] = {}
        self.burst_requests_made: Dict[str, int] = {}
        self.burst_started_at: Dict[str, Optional[datetime]] = {}
        
        # Detection events
        self.detection_events: deque = deque(maxlen=100)
        
    def get_wait_time(self, platform: str, priority: str = "NORMAL") -> float:
        """Calculate intelligent wait time before next request"""
        
        # Check if in backoff
        if platform in self.backoff_until:
            if datetime.now() < self.backoff_until[platform]:
                remaining = (self.backoff_until[platform] - datetime.now()).total_seconds()
                logger.warning(f"Platform {platform} in backoff for {remaining:.1f}s")
                return remaining
            else:
                # Backoff expired
                del self.backoff_until[platform]
                self.consecutive_errors[platform] = 0
        
        # Get platform multiplier
        multiplier = self.config.platform_multipliers.get(platform, 1.0)
        
        # Base interval calculation
        if self._should_burst(platform, priority):
            base_interval = self.config.burst_min_interval
            self.burst_requests_made[platform] = self.burst_requests_made.get(platform, 0) + 1
        else:
            base_interval = self._calculate_adaptive_interval(platform)
        
        # Apply platform multiplier
        interval = base_interval * multiplier
        
        # Add randomization to avoid patterns
        randomization = interval * self.config.randomization_factor
        interval += random.uniform(-randomization, randomization)
        
        # Occasionally add long pause
        if random.random() < self.config.occasional_long_pause:
            logger.info(f"Adding occasional long pause for {platform}")
            interval += self.config.long_pause_duration
        
        # Ensure minimum interval
        interval = max(interval, self.config.burst_min_interval)
        
        logger.debug(f"Rate limit for {platform}: {interval:.1f}s")
        return interval
    
    def _should_burst(self, platform: str, priority: str) -> bool:
        """Determine if burst mode should be active"""
        if priority != "CRITICAL":
            return False
            
        # Check burst cooldown
        if platform in self.burst_started_at:
            burst_start = self.burst_started_at[platform]
            if burst_start and (datetime.now() - burst_start).total_seconds() > self.config.burst_cooldown:
                # Reset burst mode
                self.burst_mode_active[platform] = False
                self.burst_requests_made[platform] = 0
                self.burst_started_at[platform] = None
        
        # Check if we can burst
        requests_made = self.burst_requests_made.get(platform, 0)
        if requests_made < self.config.burst_max_requests:
            if not self.burst_mode_active.get(platform, False):
                self.burst_mode_active[platform] = True
                self.burst_started_at[platform] = datetime.now()
                logger.info(f"Activating burst mode for {platform}")
            return True
            
        return False
    
    def _calculate_adaptive_interval(self, platform: str) -> float:
        """Calculate adaptive interval based on recent activity"""
        # Get recent request history
        history = self.request_history.get(platform, deque(maxlen=50))
        
        if len(history) < 2:
            return self.config.min_interval
        
        # Calculate recent request rate
        recent_requests = list(history)[-10:]  # Last 10 requests
        if len(recent_requests) >= 2:
            time_span = (recent_requests[-1] - recent_requests[0]).total_seconds()
            if time_span > 0:
                request_rate = len(recent_requests) / time_span
                
                # If request rate is too high, increase interval
                if request_rate > 0.1:  # More than 1 request per 10 seconds
                    return min(self.config.max_interval, self.config.min_interval * 2)
        
        # Check for recent detection events
        recent_detections = sum(
            1 for event in self.detection_events 
            if event['platform'] == platform and 
            (datetime.now() - event['timestamp']).total_seconds() < 3600
        )
        
        if recent_detections > 0:
            # Increase interval based on detection events
            return min(
                self.config.max_interval,
                self.config.min_interval * (1 + recent_detections * 0.5)
            )
        
        return self.config.min_interval
    
    def record_request(self, platform: str, success: bool = True) -> None:
        """Record a request for rate limiting analysis"""
        # Initialize history if needed
        if platform not in self.request_history:
            self.request_history[platform] = deque(maxlen=50)
        
        self.request_history[platform].append(datetime.now())
        
        if not success:
            self.consecutive_errors[platform] = self.consecutive_errors.get(platform, 0) + 1
            
            # Implement exponential backoff on errors
            if self.consecutive_errors[platform] >= 3:
                backoff_time = min(
                    self.config.max_backoff,
                    self.config.min_interval * (self.config.backoff_multiplier ** self.consecutive_errors[platform])
                )
                self.backoff_until[platform] = datetime.now() + timedelta(seconds=backoff_time)
                logger.warning(f"Platform {platform} entering backoff for {backoff_time:.1f}s")
        else:
            # Reset error count on success
            self.consecutive_errors[platform] = 0
    
    def record_detection(self, platform: str, detection_type: str) -> None:
        """Record a bot detection event"""
        event = {
            'platform': platform,
            'type': detection_type,
            'timestamp': datetime.now()
        }
        self.detection_events.append(event)
        
        # Immediate backoff on detection
        backoff_time = self.config.max_backoff
        self.backoff_until[platform] = datetime.now() + timedelta(seconds=backoff_time)
        logger.error(f"Bot detection on {platform}! Backing off for {backoff_time}s")
        
        # Reset burst mode
        self.burst_mode_active[platform] = False
        self.burst_requests_made[platform] = 0
        self.burst_started_at[platform] = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        stats = {}
        
        for platform in self.request_history:
            history = self.request_history[platform]
            if history:
                recent = list(history)[-10:]
                if len(recent) >= 2:
                    avg_interval = (recent[-1] - recent[0]).total_seconds() / (len(recent) - 1)
                else:
                    avg_interval = 0
                    
                stats[platform] = {
                    'total_requests': len(history),
                    'recent_avg_interval': avg_interval,
                    'consecutive_errors': self.consecutive_errors.get(platform, 0),
                    'in_backoff': platform in self.backoff_until,
                    'burst_active': self.burst_mode_active.get(platform, False),
                    'detection_events': sum(1 for e in self.detection_events if e['platform'] == platform)
                }
        
        return stats
    
    async def wait_if_needed(self, platform: str, priority: str = "NORMAL") -> None:
        """Async wait based on rate limiting"""
        wait_time = self.get_wait_time(platform, priority)
        if wait_time > 0:
            logger.info(f"Rate limiting {platform}: waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)


# Singleton instance
_rate_limiter: Optional[IntelligentRateLimiter] = None


def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> IntelligentRateLimiter:
    """Get or create rate limiter singleton"""
    global _rate_limiter
    
    if _rate_limiter is None:
        _rate_limiter = IntelligentRateLimiter(config)
    
    return _rate_limiter