# stealthmaster/network/rate_limiter.py
"""Intelligent rate limiting with adaptive patterns and human behavior simulation."""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from collections import deque, defaultdict
from dataclasses import dataclass, field
import math
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    FIXED = "fixed"              # Fixed delay between requests
    RANDOM = "random"            # Random delay within range
    EXPONENTIAL = "exponential"  # Exponential backoff
    ADAPTIVE = "adaptive"        # Learn from response patterns
    HUMAN = "human"              # Mimic human browsing patterns
    BURST = "burst"              # Allow bursts with cooldown


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    strategy: RateLimitStrategy = RateLimitStrategy.ADAPTIVE
    min_delay_ms: int = 500      # Minimum delay between requests
    max_delay_ms: int = 5000     # Maximum delay between requests
    burst_size: int = 5          # Max requests in burst
    burst_window_s: int = 10     # Burst window duration
    backoff_factor: float = 1.5  # Exponential backoff multiplier
    jitter_factor: float = 0.2   # Random jitter percentage
    human_variation: float = 0.3 # Human behavior variation


@dataclass
class DomainMetrics:
    """Metrics for a specific domain."""
    domain: str
    request_times: deque = field(default_factory=lambda: deque(maxlen=100))
    response_times: List[float] = field(default_factory=list)
    error_counts: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    success_count: int = 0
    last_request: Optional[datetime] = None
    current_delay_ms: float = 1000
    consecutive_errors: int = 0
    rate_limit_detected: bool = False
    optimal_delay_ms: Optional[float] = None


class IntelligentRateLimiter:
    """Advanced rate limiter with ML-inspired adaptive behavior."""
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize rate limiter."""
        self.config = config or RateLimitConfig()
        self._domain_metrics: Dict[str, DomainMetrics] = {}
        self._global_semaphore = asyncio.Semaphore(10)  # Global concurrent limit
        self._domain_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        
        # Human behavior patterns
        self._human_patterns = HumanBehaviorPatterns()
        
        # Adaptive learning parameters
        self._learning_rate = 0.1
        self._exploration_rate = 0.1
        
        # Pattern detection
        self._pattern_detector = PatternDetector()
    
    async def acquire(self, url: str) -> float:
        """
        Acquire permission to make a request.
        
        Args:
            url: Target URL
            
        Returns:
            Actual delay applied (ms)
        """
        domain = self._extract_domain(url)
        
        # Get or create domain metrics
        if domain not in self._domain_metrics:
            self._domain_metrics[domain] = DomainMetrics(domain=domain)
        
        metrics = self._domain_metrics[domain]
        
        # Wait for domain-specific lock
        async with self._domain_locks[domain]:
            # Calculate and apply delay
            delay_ms = self._calculate_delay(metrics)
            
            # Apply human-like variation if enabled
            if self.config.strategy == RateLimitStrategy.HUMAN:
                delay_ms = self._apply_human_variation(delay_ms, metrics)
            
            # Record request time
            metrics.request_times.append(datetime.now())
            metrics.last_request = datetime.now()
            
            # Apply delay
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000.0)
            
            # Global rate limit
            await self._global_semaphore.acquire()
            
            return delay_ms
    
    def release(self) -> None:
        """Release global semaphore."""
        self._global_semaphore.release()
    
    def record_response(
        self,
        url: str,
        status_code: int,
        response_time_ms: float
    ) -> None:
        """
        Record response metrics for learning.
        
        Args:
            url: Request URL
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
        """
        domain = self._extract_domain(url)
        
        if domain not in self._domain_metrics:
            return
        
        metrics = self._domain_metrics[domain]
        metrics.response_times.append(response_time_ms)
        
        # Keep only recent response times
        if len(metrics.response_times) > 100:
            metrics.response_times = metrics.response_times[-100:]
        
        # Update metrics based on response
        if status_code == 429:  # Rate limited
            metrics.rate_limit_detected = True
            metrics.consecutive_errors += 1
            self._handle_rate_limit(metrics)
        elif status_code >= 500:  # Server error
            metrics.error_counts[status_code] += 1
            metrics.consecutive_errors += 1
        elif 200 <= status_code < 300:  # Success
            metrics.success_count += 1
            metrics.consecutive_errors = 0
            self._optimize_delay(metrics, response_time_ms)
        else:  # Client error
            metrics.error_counts[status_code] += 1
        
        # Detect patterns
        self._pattern_detector.analyze(metrics)
    
    def _calculate_delay(self, metrics: DomainMetrics) -> float:
        """Calculate delay based on strategy and metrics."""
        strategy = self.config.strategy
        
        if strategy == RateLimitStrategy.FIXED:
            return self.config.min_delay_ms
        
        elif strategy == RateLimitStrategy.RANDOM:
            return random.uniform(
                self.config.min_delay_ms,
                self.config.max_delay_ms
            )
        
        elif strategy == RateLimitStrategy.EXPONENTIAL:
            if metrics.consecutive_errors > 0:
                delay = self.config.min_delay_ms * (
                    self.config.backoff_factor ** metrics.consecutive_errors
                )
                return min(delay, self.config.max_delay_ms)
            return self.config.min_delay_ms
        
        elif strategy == RateLimitStrategy.ADAPTIVE:
            return self._adaptive_delay(metrics)
        
        elif strategy == RateLimitStrategy.HUMAN:
            return self._human_delay(metrics)
        
        elif strategy == RateLimitStrategy.BURST:
            return self._burst_delay(metrics)
        
        return self.config.min_delay_ms
    
    def _adaptive_delay(self, metrics: DomainMetrics) -> float:
        """Calculate adaptive delay based on learned patterns."""
        # Start with current delay
        delay = metrics.current_delay_ms
        
        # If we have an optimal delay, use it with exploration
        if metrics.optimal_delay_ms and random.random() > self._exploration_rate:
            delay = metrics.optimal_delay_ms
        
        # Adjust based on recent errors
        if metrics.rate_limit_detected:
            # Significant increase for rate limits
            delay *= 2.0
            metrics.rate_limit_detected = False
        elif metrics.consecutive_errors > 0:
            # Gradual increase for errors
            delay *= (1 + 0.2 * metrics.consecutive_errors)
        
        # Add jitter
        jitter = delay * self.config.jitter_factor
        delay += random.uniform(-jitter, jitter)
        
        # Clamp to configured range
        delay = max(self.config.min_delay_ms, min(delay, self.config.max_delay_ms))
        
        # Update current delay
        metrics.current_delay_ms = delay
        
        return delay
    
    def _human_delay(self, metrics: DomainMetrics) -> float:
        """Calculate human-like delay patterns."""
        base_delay = self._human_patterns.get_next_delay(metrics)
        
        # Add natural variation
        variation = base_delay * self.config.human_variation
        delay = base_delay + random.uniform(-variation, variation)
        
        # Ensure minimum delay
        return max(self.config.min_delay_ms, delay)
    
    def _burst_delay(self, metrics: DomainMetrics) -> float:
        """Calculate delay for burst strategy."""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.config.burst_window_s)
        
        # Count recent requests
        recent_requests = sum(
            1 for t in metrics.request_times
            if t > window_start
        )
        
        if recent_requests < self.config.burst_size:
            # Still in burst, minimal delay
            return self.config.min_delay_ms
        else:
            # Burst exhausted, wait until window passes
            oldest_in_window = next(
                (t for t in metrics.request_times if t > window_start),
                None
            )
            
            if oldest_in_window:
                wait_time = (oldest_in_window + timedelta(seconds=self.config.burst_window_s) - now).total_seconds()
                return max(wait_time * 1000, self.config.min_delay_ms)
            
            return self.config.max_delay_ms
    
    def _apply_human_variation(self, delay_ms: float, metrics: DomainMetrics) -> float:
        """Apply human-like variations to delay."""
        # Time of day factor
        hour = datetime.now().hour
        if 22 <= hour or hour <= 6:  # Late night
            delay_ms *= random.uniform(1.2, 1.8)
        elif 12 <= hour <= 13:  # Lunch time
            delay_ms *= random.uniform(0.8, 1.2)
        
        # Reading time simulation
        if metrics.last_request:
            time_since_last = (datetime.now() - metrics.last_request).total_seconds()
            if time_since_last > 30:  # Been reading
                delay_ms *= random.uniform(0.5, 0.8)
        
        # Micro-pauses
        if random.random() < 0.1:  # 10% chance
            delay_ms += random.uniform(1000, 3000)  # 1-3 second pause
        
        return delay_ms
    
    def _handle_rate_limit(self, metrics: DomainMetrics) -> None:
        """Handle rate limit detection."""
        logger.warning(f"Rate limit detected for {metrics.domain}")
        
        # Increase delay significantly
        metrics.current_delay_ms = min(
            metrics.current_delay_ms * 2,
            30000  # Max 30 seconds
        )
        
        # Mark for pattern analysis
        self._pattern_detector.mark_rate_limit(metrics)
    
    def _optimize_delay(self, metrics: DomainMetrics, response_time_ms: float) -> None:
        """Optimize delay based on successful requests."""
        # Simple gradient descent on delay
        if metrics.consecutive_errors == 0 and len(metrics.response_times) >= 10:
            avg_response_time = np.mean(metrics.response_times[-10:])
            
            # If response times are good, try reducing delay
            if avg_response_time < 1000:  # Under 1 second
                new_delay = metrics.current_delay_ms * (1 - self._learning_rate)
                metrics.current_delay_ms = max(self.config.min_delay_ms, new_delay)
                
                # Update optimal delay
                if not metrics.optimal_delay_ms or new_delay < metrics.optimal_delay_ms:
                    metrics.optimal_delay_ms = new_delay
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc or parsed.path.split('/')[0]
    
    def get_metrics(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Get rate limiting metrics."""
        if domain:
            if domain in self._domain_metrics:
                metrics = self._domain_metrics[domain]
                return {
                    "domain": domain,
                    "current_delay_ms": metrics.current_delay_ms,
                    "optimal_delay_ms": metrics.optimal_delay_ms,
                    "success_count": metrics.success_count,
                    "error_counts": dict(metrics.error_counts),
                    "consecutive_errors": metrics.consecutive_errors,
                    "avg_response_time_ms": np.mean(metrics.response_times) if metrics.response_times else 0
                }
            return {}
        
        # Global metrics
        return {
            "total_domains": len(self._domain_metrics),
            "domains": {
                domain: {
                    "current_delay_ms": m.current_delay_ms,
                    "success_rate": m.success_count / (m.success_count + sum(m.error_counts.values()))
                    if (m.success_count + sum(m.error_counts.values())) > 0 else 0
                }
                for domain, m in self._domain_metrics.items()
            }
        }
    
    async def wait_if_needed(self, url: str) -> None:
        """Simple wait method for backwards compatibility."""
        await self.acquire(url)
        self.release()


class HumanBehaviorPatterns:
    """Simulates human browsing patterns."""
    
    def __init__(self):
        """Initialize human patterns."""
        self._reading_times = [2000, 5000, 10000, 15000, 30000]  # ms
        self._click_patterns = self._generate_click_patterns()
        self._session_state = "browsing"  # browsing, reading, thinking
    
    def _generate_click_patterns(self) -> List[float]:
        """Generate realistic click delay patterns."""
        patterns = []
        
        # Quick succession clicks (exploring)
        for _ in range(20):
            patterns.append(random.uniform(500, 2000))
        
        # Normal browsing
        for _ in range(50):
            patterns.append(random.uniform(2000, 5000))
        
        # Careful reading
        for _ in range(30):
            patterns.append(random.uniform(5000, 15000))
        
        return patterns
    
    def get_next_delay(self, metrics: DomainMetrics) -> float:
        """Get next human-like delay."""
        # Simulate state transitions
        if self._session_state == "browsing":
            if random.random() < 0.3:  # 30% chance to start reading
                self._session_state = "reading"
                return random.choice(self._reading_times)
            else:
                return random.choice(self._click_patterns[:50])
        
        elif self._session_state == "reading":
            if random.random() < 0.2:  # 20% chance to continue browsing
                self._session_state = "browsing"
                return random.uniform(1000, 3000)
            else:
                return random.choice(self._reading_times)
        
        return random.uniform(2000, 5000)


class PatternDetector:
    """Detects patterns in request/response behavior."""
    
    def __init__(self):
        """Initialize pattern detector."""
        self._patterns: Dict[str, List[float]] = defaultdict(list)
        self._rate_limit_patterns: Dict[str, List[datetime]] = defaultdict(list)
    
    def analyze(self, metrics: DomainMetrics) -> Optional[str]:
        """Analyze metrics for patterns."""
        domain = metrics.domain
        
        # Analyze request intervals
        if len(metrics.request_times) >= 2:
            intervals = []
            for i in range(1, len(metrics.request_times)):
                interval = (metrics.request_times[i] - metrics.request_times[i-1]).total_seconds()
                intervals.append(interval)
            
            self._patterns[domain] = intervals
            
            # Detect regular patterns
            if self._is_regular_pattern(intervals):
                logger.warning(f"Regular pattern detected for {domain} - adding variation")
                return "regular_pattern"
        
        return None
    
    def mark_rate_limit(self, metrics: DomainMetrics) -> None:
        """Mark rate limit occurrence."""
        self._rate_limit_patterns[metrics.domain].append(datetime.now())
        
        # Analyze rate limit patterns
        recent_limits = [
            t for t in self._rate_limit_patterns[metrics.domain]
            if t > datetime.now() - timedelta(hours=1)
        ]
        
        if len(recent_limits) >= 3:
            logger.warning(f"Frequent rate limits for {metrics.domain} - adjusting strategy")
    
    def _is_regular_pattern(self, intervals: List[float]) -> bool:
        """Check if intervals show regular pattern."""
        if len(intervals) < 5:
            return False
        
        # Calculate standard deviation
        std_dev = np.std(intervals)
        mean = np.mean(intervals)
        
        # Low variation indicates regular pattern
        coefficient_of_variation = std_dev / mean if mean > 0 else 0
        return coefficient_of_variation < 0.1


class AdaptiveTokenBucket:
    """Token bucket with adaptive refill rate."""
    
    def __init__(
        self,
        capacity: int = 10,
        refill_rate: float = 1.0,
        adaptive: bool = True
    ):
        """Initialize token bucket."""
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.adaptive = adaptive
        self._tokens = float(capacity)
        self._last_refill = datetime.now()
        self._lock = asyncio.Lock()
        
        # Adaptive parameters
        self._success_count = 0
        self._failure_count = 0
    
    async def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens from bucket.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if acquired, False otherwise
        """
        async with self._lock:
            # Refill tokens
            now = datetime.now()
            elapsed = (now - self._last_refill).total_seconds()
            self._tokens = min(
                self.capacity,
                self._tokens + elapsed * self.refill_rate
            )
            self._last_refill = now
            
            # Check if enough tokens
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            
            return False
    
    def record_result(self, success: bool) -> None:
        """Record request result for adaptation."""
        if success:
            self._success_count += 1
        else:
            self._failure_count += 1
        
        # Adapt refill rate
        if self.adaptive and (self._success_count + self._failure_count) % 10 == 0:
            self._adapt_rate()
    
    def _adapt_rate(self) -> None:
        """Adapt refill rate based on success/failure ratio."""
        total = self._success_count + self._failure_count
        if total == 0:
            return
        
        success_ratio = self._success_count / total
        
        if success_ratio > 0.95:  # Very successful, increase rate
            self.refill_rate = min(self.refill_rate * 1.1, self.capacity)
        elif success_ratio < 0.8:  # Too many failures, decrease rate
            self.refill_rate = max(self.refill_rate * 0.9, 0.1)