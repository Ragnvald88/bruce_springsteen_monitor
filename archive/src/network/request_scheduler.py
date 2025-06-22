"""
Request Scheduler for Rate Limit Management
Intelligent scheduling to avoid detection with single proxy
"""

import time
from collections import defaultdict, deque
from typing import Dict, Optional
import asyncio

from ..utils.logging import get_logger

logger = get_logger(__name__)


class RequestScheduler:
    """Intelligent request scheduling to avoid rate limits"""
    
    def __init__(self):
        self.request_times = defaultdict(deque)
        self.rate_limits = {
            'fansale': {'requests': 30, 'window': 60},
            'ticketmaster': {'requests': 20, 'window': 60},
            'vivaticket': {'requests': 40, 'window': 60}
        }
        
        # Track consecutive requests to same platform
        self.consecutive_counts = defaultdict(int)
        self.last_platform = None
        
    async def can_request(self, platform: str) -> bool:
        """Check if we can make a request without hitting rate limits"""
        now = time.time()
        times = self.request_times[platform]
        limit = self.rate_limits.get(platform, {'requests': 30, 'window': 60})
        
        # Remove old requests outside window
        while times and times[0] < now - limit['window']:
            times.popleft()
        
        # Check rate limit
        if len(times) >= limit['requests']:
            wait_time = limit['window'] - (now - times[0])
            logger.warning(f"Rate limit approaching for {platform}, wait {wait_time:.1f}s")
            return False
        
        return True
    
    async def wait_if_needed(self, platform: str) -> float:
        """Wait if necessary to avoid rate limits, return wait time"""
        if not await self.can_request(platform):
            now = time.time()
            times = self.request_times[platform]
            limit = self.rate_limits[platform]
            
            # Calculate wait time
            wait_time = limit['window'] - (now - times[0]) + 1
            
            logger.info(f"Rate limit reached for {platform}, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
            
            return wait_time
        
        # Add jitter to avoid patterns
        if self.last_platform == platform:
            self.consecutive_counts[platform] += 1
            
            # Add progressive delay for consecutive requests
            if self.consecutive_counts[platform] > 5:
                jitter = min(5, self.consecutive_counts[platform] * 0.5)
                await asyncio.sleep(jitter)
                return jitter
        else:
            self.consecutive_counts[platform] = 1
            self.last_platform = platform
        
        return 0
    
    def record_request(self, platform: str):
        """Record that a request was made"""
        self.request_times[platform].append(time.time())
        
        # Log rate limit status
        times = self.request_times[platform]
        limit = self.rate_limits[platform]
        usage_percent = (len(times) / limit['requests']) * 100
        
        if usage_percent > 80:
            logger.warning(f"{platform} rate limit usage: {usage_percent:.0f}%")
    
    def get_optimal_interval(self, platform: str, base_interval: float) -> float:
        """Calculate optimal request interval based on current usage"""
        times = self.request_times[platform]
        limit = self.rate_limits[platform]
        
        if not times:
            return base_interval
        
        # Calculate current request rate
        usage_percent = (len(times) / limit['requests']) * 100
        
        # Adjust interval based on usage
        if usage_percent > 90:
            # Critical - slow down significantly
            return base_interval * 3
        elif usage_percent > 70:
            # High usage - moderate slowdown
            return base_interval * 2
        elif usage_percent > 50:
            # Medium usage - slight slowdown
            return base_interval * 1.5
        else:
            # Low usage - normal speed
            return base_interval
    
    def get_status(self) -> Dict[str, Dict[str, any]]:
        """Get current rate limit status for all platforms"""
        status = {}
        now = time.time()
        
        for platform, limit in self.rate_limits.items():
            times = self.request_times[platform]
            
            # Clean old entries
            while times and times[0] < now - limit['window']:
                times.popleft()
            
            status[platform] = {
                'current_requests': len(times),
                'max_requests': limit['requests'],
                'window_seconds': limit['window'],
                'usage_percent': (len(times) / limit['requests']) * 100,
                'consecutive_count': self.consecutive_counts.get(platform, 0)
            }
        
        return status


# Global instance
request_scheduler = RequestScheduler()
