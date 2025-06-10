# stealthmaster/browser/pool.py
"""
Enhanced Browser Pool with Advanced Lifecycle Management, Data Usage Tracking,
and Intelligent Recovery Mechanisms for 2025 Bot Detection Evasion
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from collections import defaultdict, deque
import psutil
import json

from playwright.async_api import Browser, Playwright, BrowserContext, Page, Request, Response

from browser.launcher import BrowserLauncher
from stealth.core import StealthCore
from detection.monitor import DetectionMonitor, DetectionType, MonitoringLevel
from network.tls_fingerprint import TLSFingerprintRotator
from config import Settings, ProxyConfig
from src.constants import BrowserState

logger = logging.getLogger(__name__)


class ContextHealth(Enum):
    """Context health status with recovery states"""
    PRISTINE = "pristine"       # Never used
    HEALTHY = "healthy"         # Normal operation
    WARMING = "warming"         # Building reputation
    SUSPICIOUS = "suspicious"   # Some detection signals
    DETECTED = "detected"       # Confirmed detection
    RECOVERING = "recovering"   # In recovery process
    QUARANTINE = "quarantine"   # Temporarily isolated


class DataUsageAlert(Enum):
    """Data usage alert levels"""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"


@dataclass
class DataUsageMetrics:
    """Detailed data usage tracking"""
    total_bytes: int = 0
    request_bytes: int = 0
    response_bytes: int = 0
    cached_bytes: int = 0
    blocked_bytes: int = 0
    
    # Per-domain tracking
    domain_usage: Dict[str, int] = field(default_factory=dict)
    
    # Time-based tracking
    hourly_usage: deque = field(default_factory=lambda: deque(maxlen=24))
    last_reset: datetime = field(default_factory=datetime.now)
    
    def add_request(self, size: int, domain: str):
        """Track request data"""
        self.request_bytes += size
        self.total_bytes += size
        self.domain_usage[domain] = self.domain_usage.get(domain, 0) + size
    
    def add_response(self, size: int, domain: str):
        """Track response data"""
        self.response_bytes += size
        self.total_bytes += size
        self.domain_usage[domain] = self.domain_usage.get(domain, 0) + size
    
    def add_cached(self, size: int):
        """Track cached data savings"""
        self.cached_bytes += size
    
    def add_blocked(self, size: int):
        """Track blocked resource savings"""
        self.blocked_bytes += size
    
    def get_mb_used(self) -> float:
        """Get total MB used"""
        return self.total_bytes / (1024 * 1024)
    
    def get_savings_mb(self) -> float:
        """Get total MB saved"""
        return (self.cached_bytes + self.blocked_bytes) / (1024 * 1024)
    
    def get_top_domains(self, limit: int = 5) -> List[Tuple[str, float]]:
        """Get top data-consuming domains"""
        sorted_domains = sorted(
            self.domain_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [(d, b/(1024*1024)) for d, b in sorted_domains[:limit]]


@dataclass
class ContextMetrics:
    """Enhanced metrics for context performance tracking"""
    requests_made: int = 0
    requests_successful: int = 0
    detections_encountered: int = 0
    captchas_encountered: int = 0
    last_detection: Optional[datetime] = None
    success_rate: float = 1.0
    reputation_score: float = 0.5
    
    # Data usage
    data_usage: DataUsageMetrics = field(default_factory=DataUsageMetrics)
    
    # Performance metrics
    avg_response_time: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def record_request(self, success: bool, response_time: float):
        """Record request outcome"""
        self.requests_made += 1
        if success:
            self.requests_successful += 1
        
        self.response_times.append(response_time)
        self.avg_response_time = sum(self.response_times) / len(self.response_times)
        
        # Update success rate
        if self.requests_made > 0:
            self.success_rate = self.requests_successful / self.requests_made
        
        self.update_activity()
    
    def record_detection(self, detection_type: DetectionType):
        """Record a detection event"""
        self.detections_encountered += 1
        self.last_detection = datetime.now()
        
        if detection_type in [DetectionType.CAPTCHA, DetectionType.RECAPTCHA, DetectionType.HCAPTCHA]:
            self.captchas_encountered += 1
        
        # Reduce reputation
        self.reputation_score = max(0.1, self.reputation_score * 0.8)
        
    def boost_reputation(self, amount: float = 0.05):
        """Boost reputation after successful operations"""
        self.reputation_score = min(1.0, self.reputation_score + amount)


@dataclass
class StealthContextV3:
    """Enhanced stealth browser context with metrics"""
    context: BrowserContext
    fingerprint: Dict[str, Any]
    proxy: Optional[ProxyConfig]
    context_id: str
    browser_id: str
    health: ContextHealth = ContextHealth.PRISTINE
    metrics: ContextMetrics = field(default_factory=ContextMetrics)
    pages: Set[Page] = field(default_factory=set)
    tls_profile: Optional[Dict[str, Any]] = None
    detection_monitor: Optional[DetectionMonitor] = None
    
    # Resource management
    resource_cache: Dict[str, bytes] = field(default_factory=dict)
    blocked_resources: Set[str] = field(default_factory=set)
    
    async def close(self):
        """Close context and cleanup"""
        try:
            # Stop monitoring
            if self.detection_monitor:
                for page in self.pages:
                    await self.detection_monitor.stop_monitoring(page)
            
            # Close all pages
            for page in list(self.pages):
                try:
                    await page.close()
                except Exception:
                    pass
            
            # Close context
            await self.context.close()
            
            # Clear caches
            self.resource_cache.clear()
            self.blocked_resources.clear()
            
        except Exception as e:
            logger.error(f"Error closing context {self.context_id}: {e}")
    
    def calculate_health_score(self) -> float:
        """Calculate context health score (0-1)"""
        score = 1.0
        
        # Factor in detection rate
        if self.metrics.requests_made > 0:
            detection_rate = self.metrics.detections_encountered / self.metrics.requests_made
            score *= (1 - detection_rate)
        
        # Factor in success rate
        score *= self.metrics.success_rate
        
        # Factor in reputation
        score *= self.metrics.reputation_score
        
        # Factor in age (contexts degrade over time)
        age_hours = (datetime.now() - self.metrics.created_at).total_seconds() / 3600
        if age_hours > 1:
            score *= 0.9
        if age_hours > 2:
            score *= 0.8
        
        # Factor in current health state
        health_multipliers = {
            ContextHealth.PRISTINE: 1.1,
            ContextHealth.HEALTHY: 1.0,
            ContextHealth.WARMING: 0.9,
            ContextHealth.SUSPICIOUS: 0.7,
            ContextHealth.DETECTED: 0.3,
            ContextHealth.RECOVERING: 0.5,
            ContextHealth.QUARANTINE: 0.1
        }
        score *= health_multipliers.get(self.health, 1.0)
        
        return max(0.1, min(1.0, score))


class BrowserInstance:
    """Enhanced browser instance with health monitoring and data tracking"""
    
    def __init__(
        self,
        browser: Browser,
        instance_id: str,
        proxy: Optional[ProxyConfig] = None,
        stealth_core: Optional[StealthCore] = None
    ):
        self.browser = browser
        self.instance_id = instance_id
        self.proxy = proxy
        self.stealth_core = stealth_core
        self.state = BrowserState.READY
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        
        # Contexts managed by this instance
        self.contexts: Dict[str, StealthContextV3] = {}
        
        # Performance tracking
        self.total_requests = 0
        self.total_detections = 0
        self.data_usage = DataUsageMetrics()
        
        # Health monitoring
        self.health_score = 1.0
        self.consecutive_failures = 0
        
        # Resource limits
        self.max_contexts = 5
        self.memory_usage_mb = 0.0
    
    @property
    def age(self) -> timedelta:
        """Get instance age"""
        return datetime.now() - self.created_at
    
    @property
    def idle_time(self) -> timedelta:
        """Get time since last use"""
        return datetime.now() - self.last_used
    
    def get_health_score(self) -> float:
        """Calculate current health score"""
        # Base score
        score = self.health_score
        
        # Penalize for age
        age_hours = self.age.total_seconds() / 3600
        if age_hours > 2:
            score *= 0.9
        if age_hours > 4:
            score *= 0.8
            
        # Penalize for detections
        if self.total_requests > 0:
            detection_rate = self.total_detections / self.total_requests
            score *= (1 - detection_rate)
        
        # Penalize for consecutive failures
        score *= (0.9 ** self.consecutive_failures)
        
        # Factor in context health
        if self.contexts:
            avg_context_health = sum(c.calculate_health_score() for c in self.contexts.values()) / len(self.contexts)
            score *= avg_context_health
        
        return max(0.1, min(1.0, score))
    
    async def create_context(
        self,
        stealth_core: StealthCore,
        fingerprint: Optional[Dict[str, Any]] = None,
        tls_profile: Optional[Dict[str, Any]] = None
    ) -> StealthContextV3:
        """Create a new stealth context with data tracking"""
        # Check context limit
        if len(self.contexts) >= self.max_contexts:
            raise Exception(f"Browser {self.instance_id} at context limit")
        
        # Create context with stealth
        context = await stealth_core.create_stealth_context(
            self.browser,
            fingerprint=fingerprint,
            proxy=self.proxy.__dict__ if self.proxy and hasattr(self.proxy, '__dict__') else self.proxy
        )
        
        # Generate context ID
        context_id = hashlib.md5(
            f"{self.instance_id}_{datetime.now().timestamp()}_{random.random()}".encode()
        ).hexdigest()[:8]
        
        # Create stealth context wrapper
        stealth_context = StealthContextV3(
            context=context,
            fingerprint=fingerprint or context._stealth_fingerprint,
            proxy=self.proxy,
            context_id=context_id,
            browser_id=self.instance_id,
            tls_profile=tls_profile.__dict__ if hasattr(tls_profile, '__dict__') else tls_profile
        )
        
        # Store context
        self.contexts[context_id] = stealth_context
        
        # Set up context event handlers
        context.on("page", lambda page: asyncio.create_task(
            self._on_page_created(page, stealth_context)
        ))
        
        # Set up request/response tracking
        context.on("request", lambda request: asyncio.create_task(
            self._track_request(request, stealth_context)
        ))
        
        context.on("response", lambda response: asyncio.create_task(
            self._track_response(response, stealth_context)
        ))
        
        logger.info(f"Created stealth context {context_id} in browser {self.instance_id}")
        return stealth_context
    
    async def _on_page_created(self, page: Page, context: StealthContextV3):
        """Handle new page creation in context"""
        context.pages.add(page)
        
        # Apply page-level stealth
        if self.stealth_core:
            await self.stealth_core.protect_page(page, context.fingerprint)
        
        # Set up page monitoring
        if context.detection_monitor:
            await context.detection_monitor.start_monitoring(page, MonitoringLevel.HIGH)
        
        # Set up resource blocking
        await page.route("**/*", lambda route: asyncio.create_task(
            self._handle_resource_blocking(route, context)
        ))
    
    async def _track_request(self, request: Request, context: StealthContextV3):
        """Track outgoing request data usage"""
        try:
            # Estimate request size
            size = len(request.url) + 500  # URL + headers estimate
            if request.post_data:
                size += len(request.post_data)
            
            # Extract domain
            from urllib.parse import urlparse
            domain = urlparse(request.url).netloc
            
            # Track in context
            context.metrics.data_usage.add_request(size, domain)
            
            # Track in browser
            self.data_usage.add_request(size, domain)
            self.total_requests += 1
            
        except Exception as e:
            logger.debug(f"Request tracking error: {e}")
    
    async def _track_response(self, response: Response, context: StealthContextV3):
        """Track incoming response data usage"""
        try:
            # Get response size
            headers = response.headers
            size = int(headers.get("content-length", 0))
            
            if size == 0:
                # Estimate from body if needed
                try:
                    body = await response.body()
                    size = len(body)
                except Exception:
                    size = 1000  # Default estimate
            
            # Extract domain
            from urllib.parse import urlparse
            domain = urlparse(response.url).netloc
            
            # Check if cached
            cache_key = f"{response.request.method}:{response.url}"
            if cache_key in context.resource_cache:
                context.metrics.data_usage.add_cached(size)
                self.data_usage.add_cached(size)
            else:
                # Track as new response
                context.metrics.data_usage.add_response(size, domain)
                self.data_usage.add_response(size, domain)
                
                # Cache if successful and cacheable
                if response.status == 200 and response.request.method == "GET":
                    await self._cache_response(response, context)
            
        except Exception as e:
            logger.debug(f"Response tracking error: {e}")
    
    async def _cache_response(self, response: Response, context: StealthContextV3):
        """Cache response for data savings"""
        try:
            # Only cache small resources
            headers = response.headers
            content_type = headers.get("content-type", "")
            
            cacheable_types = ["text/css", "application/javascript", "application/json", "text/plain"]
            if any(t in content_type for t in cacheable_types):
                body = await response.body()
                if len(body) < 500000:  # 500KB limit
                    cache_key = f"{response.request.method}:{response.url}"
                    context.resource_cache[cache_key] = body
                    
        except Exception:
            pass
    
    async def _handle_resource_blocking(self, route, context: StealthContextV3):
        """Handle resource blocking for data savings"""
        request = route.request
        resource_type = request.resource_type
        url = request.url
        
        # Check if should block
        should_block = False
        
        # Block based on settings
        if context.metrics.data_usage.get_mb_used() > 50:  # Aggressive blocking after 50MB
            blocked_types = ["image", "media", "font", "stylesheet"]
            if resource_type in blocked_types:
                should_block = True
        elif context.metrics.data_usage.get_mb_used() > 25:  # Moderate blocking after 25MB
            blocked_types = ["image", "media", "font"]
            if resource_type in blocked_types:
                should_block = True
        
        # Always block tracking/ads
        tracking_domains = [
            "google-analytics.com", "googletagmanager.com", "facebook.com/tr",
            "doubleclick.net", "amazon-adsystem.com", "googlesyndication.com"
        ]
        if any(domain in url for domain in tracking_domains):
            should_block = True
        
        if should_block:
            # Track blocked savings
            estimated_size = 50000 if resource_type == "image" else 10000
            context.metrics.data_usage.add_blocked(estimated_size)
            self.data_usage.add_blocked(estimated_size)
            context.blocked_resources.add(url)
            
            await route.abort()
        else:
            # Check cache
            cache_key = f"{request.method}:{url}"
            if cache_key in context.resource_cache:
                # Serve from cache
                await route.fulfill(
                    body=context.resource_cache[cache_key],
                    status=200,
                    headers={"X-From-Cache": "true"}
                )
            else:
                await route.continue_()
    
    async def close(self):
        """Close browser and all contexts"""
        self.state = BrowserState.CLOSING
        
        # Close all contexts
        for context in list(self.contexts.values()):
            await context.close()
        
        # Close browser
        try:
            await self.browser.close()
        except Exception:
            pass
        
        self.state = BrowserState.CLOSED
        logger.info(f"Closed browser {self.instance_id} - Total data used: {self.data_usage.get_mb_used():.2f}MB")


class EnhancedBrowserPool:
    """Advanced browser pool with detection recovery and data management"""
    
    def __init__(
        self,
        settings: Settings,
        playwright: Playwright,
    ):
        self.settings = settings
        self.playwright = playwright
        self.launcher = BrowserLauncher(settings.browser_options)
        self.stealth_core = StealthCore()
        self.tls_rotator = TLSFingerprintRotator()
        self.detection_monitor = DetectionMonitor()
        
        # Pool configuration
        self.max_browsers = getattr(settings.browser_options, 'pool_size', 5)
        self.max_contexts_per_browser = 5
        self.max_age_hours = 2
        self.max_detection_rate = 0.3
        self.data_limit_mb = settings.data_limits.session_limit_mb
        
        # Browser management
        self._browsers: Dict[str, BrowserInstance] = {}
        self._context_map: Dict[str, str] = {}  # context_id -> browser_id
        self._lock = asyncio.Lock()
        self._shutdown = False
        
        # Proxy management
        self._proxy_pool = settings.proxy_settings.primary_pool
        self._proxy_scores: Dict[str, float] = defaultdict(lambda: 1.0)
        self._proxy_last_used: Dict[str, datetime] = {}
        self._proxy_data_usage: Dict[str, float] = defaultdict(float)
        
        # Performance tracking
        self._acquisition_times: List[float] = []
        self._success_contexts: Set[str] = set()
        self._total_data_used_mb = 0.0
        
        # Recovery queues
        self._recovery_queue: asyncio.Queue = asyncio.Queue()
        self._quarantine_contexts: Dict[str, datetime] = {}
        
        # Start maintenance
        self._maintenance_task = None
        self._recovery_task = None
    
    async def initialize(self):
        """Initialize the browser pool"""
        logger.info(f"Initializing browser pool (max: {self.max_browsers}, data limit: {self.data_limit_mb}MB)")
        
        # Pre-warm pool with browsers
        await self._ensure_minimum_browsers()
        
        # Start maintenance loop
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
        
        # Start recovery loop
        self._recovery_task = asyncio.create_task(self._recovery_loop())
        
        # Register detection callbacks
        self.detection_monitor.register_callback(
            callback=self._on_detection_event
        )
    
    async def acquire_context(
        self,
        platform: str,
        prefer_fresh: bool = False,
        fingerprint: Optional[Dict[str, Any]] = None,
        data_limit_mb: Optional[float] = None
    ) -> Tuple[StealthContextV3, Page]:
        """
        Acquire a stealth context and page for use
        
        Args:
            platform: Target platform
            prefer_fresh: Prefer fresh context over reused
            fingerprint: Optional fingerprint override
            data_limit_mb: Optional data limit override
            
        Returns:
            Tuple of (context, page)
        """
        start_time = time.time()
        
        async with self._lock:
            # Check global data limit
            if self._total_data_used_mb >= self.data_limit_mb:
                raise Exception(f"Data limit exceeded: {self._total_data_used_mb:.1f}MB used")
            
            # Select optimal browser instance
            browser = await self._select_browser(prefer_fresh, data_limit_mb)
            
            if not browser:
                # Create new browser if needed
                browser = await self._create_browser()
            
            # Generate fingerprint if not provided
            if not fingerprint:
                fingerprint = self.stealth_core.fingerprint_generator.generate()
            
            # Get TLS profile matching fingerprint
            tls_profile = self.tls_rotator.get_profile(fingerprint["user_agent"])
            
            # Create context in selected browser
            context = await browser.create_context(
                self.stealth_core,
                fingerprint=fingerprint,
                tls_profile=tls_profile
            )
            
            # Set initial health based on browser state
            if browser.consecutive_failures > 0:
                context.health = ContextHealth.WARMING
            
            # Map context to browser
            self._context_map[context.context_id] = browser.instance_id
            
            # Create initial page
            page = await context.context.new_page()
            
            # Start detection monitoring
            context.detection_monitor = self.detection_monitor
            await self.detection_monitor.start_monitoring(page, MonitoringLevel.HIGH)
            
            # Update metrics
            browser.last_used = datetime.now()
            acquisition_time = time.time() - start_time
            self._acquisition_times.append(acquisition_time)
            
            logger.info(
                f"Acquired context {context.context_id} from browser "
                f"{browser.instance_id} in {acquisition_time:.2f}s "
                f"(Health: {context.health.value})"
            )
            
            return context, page
    
    async def release_context(
        self,
        context: StealthContextV3,
        success: bool = True,
        detection_encountered: bool = False,
        detection_type: Optional[DetectionType] = None
    ):
        """
        Release a context back to the pool
        
        Args:
            context: Context to release
            success: Whether operation was successful
            detection_encountered: Whether detection was encountered
            detection_type: Type of detection if encountered
        """
        async with self._lock:
            browser_id = self._context_map.get(context.context_id)
            if not browser_id or browser_id not in self._browsers:
                return
            
            browser = self._browsers[browser_id]
            
            # Update metrics
            if success:
                self._success_contexts.add(context.context_id)
                browser.consecutive_failures = 0
                context.metrics.boost_reputation()
            else:
                browser.consecutive_failures += 1
            
            if detection_encountered:
                browser.total_detections += 1
                context.metrics.record_detection(detection_type or DetectionType.UNKNOWN)
                
                # Update proxy score if using proxy
                if browser.proxy:
                    proxy_key = f"{browser.proxy.host}:{browser.proxy.port}"
                    self._proxy_scores[proxy_key] *= 0.9
                
                # Update context health
                if context.health == ContextHealth.HEALTHY:
                    context.health = ContextHealth.SUSPICIOUS
                elif context.health == ContextHealth.SUSPICIOUS:
                    context.health = ContextHealth.DETECTED
            
            # Update data usage tracking
            data_used_mb = context.metrics.data_usage.get_mb_used()
            self._total_data_used_mb += data_used_mb
            
            if browser.proxy:
                proxy_key = f"{browser.proxy.host}:{browser.proxy.port}"
                self._proxy_data_usage[proxy_key] += data_used_mb
            
            logger.info(
                f"Released context {context.context_id} - "
                f"Data used: {data_used_mb:.2f}MB, "
                f"Health: {context.health.value}, "
                f"Success: {success}"
            )
            
            # Determine context fate
            should_close = False
            should_quarantine = False
            
            if context.health == ContextHealth.DETECTED:
                should_quarantine = True
            elif context.metrics.detections_encountered > 3:
                should_close = True
            elif not success and browser.consecutive_failures > 2:
                should_close = True
            elif data_used_mb > 100:  # Close high-usage contexts
                should_close = True
            
            if should_quarantine:
                # Add to quarantine
                await self._quarantine_context(context)
            elif should_close:
                # Close and remove context
                await context.close()
                del browser.contexts[context.context_id]
                del self._context_map[context.context_id]
                logger.info(f"Closed context {context.context_id} due to poor health")
            else:
                # Keep context for reuse
                context.metrics.update_activity()
    
    async def _select_browser(self, prefer_fresh: bool, data_limit_mb: Optional[float]) -> Optional[BrowserInstance]:
        """Select optimal browser instance"""
        if not self._browsers:
            return None
        
        # Score all browsers
        scored_browsers = []
        
        for browser in self._browsers.values():
            if browser.state != BrowserState.READY:
                continue
            
            # Skip browsers over data limit
            if data_limit_mb and browser.data_usage.get_mb_used() >= data_limit_mb:
                continue
            
            score = browser.get_health_score()
            
            # Bonus for fewer contexts
            context_ratio = len(browser.contexts) / self.max_contexts_per_browser
            score *= (2 - context_ratio)
            
            # Bonus for matching proxy preference
            if prefer_fresh and not browser.contexts:
                score *= 1.5
            
            # Penalty for high data usage
            data_ratio = browser.data_usage.get_mb_used() / self.data_limit_mb
            score *= (1 - data_ratio * 0.5)
            
            scored_browsers.append((score, browser))
        
        if not scored_browsers:
            return None
        
        # Sort by score and select
        scored_browsers.sort(key=lambda x: x[0], reverse=True)
        
        # Use weighted random selection from top candidates
        top_candidates = scored_browsers[:3]
        weights = [score for score, _ in top_candidates]
        selected = random.choices(
            [browser for _, browser in top_candidates],
            weights=weights,
            k=1
        )[0]
        
        return selected
    
    async def _create_browser(self) -> BrowserInstance:
        """Create a new browser instance"""
        # Check if at capacity
        if len(self._browsers) >= self.max_browsers:
            # Remove worst performing browser
            await self._remove_worst_browser()
        
        # Select proxy with best data efficiency
        proxy = self._select_proxy()
        
        # Generate instance ID
        instance_id = hashlib.md5(
            f"browser_{datetime.now().timestamp()}_{random.random()}".encode()
        ).hexdigest()[:8]
        
        # Launch browser
        browser = await self.launcher.launch(
            self.playwright,
            proxy=proxy,
            headless=self.settings.browser_options.headless
        )
        
        # Apply browser-level stealth
        await self.stealth_core.create_stealth_browser(browser)
        
        # Create instance
        instance = BrowserInstance(
            browser=browser,
            instance_id=instance_id,
            proxy=proxy,
            stealth_core=self.stealth_core
        )
        
        self._browsers[instance_id] = instance
        
        logger.info(
            f"Created browser {instance_id} "
            f"{'with proxy ' + proxy.host if proxy else 'without proxy'}"
        )
        
        return instance
    
    def _select_proxy(self) -> Optional[ProxyConfig]:
        """Select optimal proxy based on data usage and performance"""
        if not self.settings.proxy_settings.enabled:
            return None
            
        if not self._proxy_pool:
            return None
        
        # Score proxies
        scored_proxies = []
        now = datetime.now()
        
        for proxy in self._proxy_pool:
            # Ensure proxy has proper format
            if not hasattr(proxy, 'host') or not hasattr(proxy, 'port'):
                continue
                
            proxy_key = f"{proxy.host}:{proxy.port}"
            
            # Base score from configuration
            score = getattr(proxy, 'quality_score', 1.0)
            
            # Apply current performance score
            score *= self._proxy_scores[proxy_key]
            
            # Bonus for low data usage
            data_used = self._proxy_data_usage[proxy_key]
            if data_used < 100:
                score *= 1.2
            elif data_used > 500:
                score *= 0.8
            
            # Bonus for not recently used
            if proxy_key in self._proxy_last_used:
                minutes_since_use = (now - self._proxy_last_used[proxy_key]).total_seconds() / 60
                score *= min(2.0, 1 + minutes_since_use / 60)
            
            scored_proxies.append((score, proxy))
        
        if not scored_proxies:
            return None
            
        # Sort and select
        scored_proxies.sort(key=lambda x: x[0], reverse=True)
        selected_proxy = scored_proxies[0][1]
        
        # Update last used
        proxy_key = f"{selected_proxy.host}:{selected_proxy.port}"
        self._proxy_last_used[proxy_key] = now
        
        return selected_proxy
    
    async def _quarantine_context(self, context: StealthContextV3):
        """Put context in quarantine for recovery"""
        context.health = ContextHealth.QUARANTINE
        self._quarantine_contexts[context.context_id] = datetime.now()
        
        # Add to recovery queue
        await self._recovery_queue.put(context.context_id)
        
        logger.info(f"Quarantined context {context.context_id} for recovery")
    
    async def _recovery_loop(self):
        """Process quarantined contexts for recovery"""
        while not self._shutdown:
            try:
                # Get context from recovery queue
                context_id = await asyncio.wait_for(
                    self._recovery_queue.get(),
                    timeout=60.0
                )
                
                # Find context
                browser_id = self._context_map.get(context_id)
                if not browser_id or browser_id not in self._browsers:
                    continue
                
                browser = self._browsers[browser_id]
                context = browser.contexts.get(context_id)
                if not context:
                    continue
                
                # Perform recovery actions
                logger.info(f"Starting recovery for context {context_id}")
                
                # Rotate TLS fingerprint
                new_tls = self.tls_rotator.rotate()
                context.tls_profile = new_tls
                
                # Enhance evasion
                for page in context.pages:
                    await self.stealth_core.enhance_evasion(page)
                
                # Clear cookies and storage
                await context.context.clear_cookies()
                
                # Wait cooldown period
                await asyncio.sleep(300)  # 5 minutes
                
                # Check if quarantine time exceeded
                quarantine_time = (datetime.now() - self._quarantine_contexts[context_id]).total_seconds() / 3600
                
                if quarantine_time > 1:  # 1 hour quarantine
                    # Move to recovering state
                    context.health = ContextHealth.RECOVERING
                    context.metrics.reputation_score = 0.5
                    del self._quarantine_contexts[context_id]
                    logger.info(f"Context {context_id} moved to recovering state")
                else:
                    # Re-queue for more recovery
                    await self._recovery_queue.put(context_id)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Recovery loop error: {e}")
    
    async def _maintenance_loop(self):
        """Periodic maintenance tasks"""
        while not self._shutdown:
            try:
                await asyncio.sleep(300)  # 5 minutes
                
                async with self._lock:
                    # Remove old browsers
                    await self._cleanup_old_browsers()
                    
                    # Remove unhealthy contexts
                    await self._cleanup_unhealthy_contexts()
                    
                    # Ensure minimum browsers
                    await self._ensure_minimum_browsers()
                    
                    # Log statistics
                    self._log_statistics()
                    
            except Exception as e:
                logger.error(f"Maintenance error: {e}")
    
    async def _cleanup_old_browsers(self):
        """Remove browsers that are too old or over data limit"""
        to_remove = []
        
        for browser_id, browser in self._browsers.items():
            # Check age
            if browser.age.total_seconds() > self.max_age_hours * 3600:
                to_remove.append(browser_id)
                continue
            
            # Check health
            if browser.get_health_score() < 0.3:
                to_remove.append(browser_id)
                continue
            
            # Check data usage
            if browser.data_usage.get_mb_used() > self.data_limit_mb * 0.8:
                to_remove.append(browser_id)
        
        for browser_id in to_remove:
            browser = self._browsers[browser_id]
            await browser.close()
            del self._browsers[browser_id]
            logger.info(
                f"Removed browser {browser_id} - "
                f"Age: {browser.age.total_seconds()/3600:.1f}h, "
                f"Data: {browser.data_usage.get_mb_used():.1f}MB"
            )
    
    async def _cleanup_unhealthy_contexts(self):
        """Remove contexts with poor health"""
        for browser in self._browsers.values():
            to_remove = []
            
            for ctx_id, context in browser.contexts.items():
                # Skip quarantined contexts
                if ctx_id in self._quarantine_contexts:
                    continue
                
                # Check detection rate
                if context.metrics.requests_made > 10:
                    detection_rate = context.metrics.detections_encountered / context.metrics.requests_made
                    if detection_rate > self.max_detection_rate:
                        to_remove.append(ctx_id)
                
                # Check age
                age = datetime.now() - context.metrics.created_at
                if age.total_seconds() > 3600:  # 1 hour
                    to_remove.append(ctx_id)
                
                # Check data usage
                if context.metrics.data_usage.get_mb_used() > 100:
                    to_remove.append(ctx_id)
            
            for ctx_id in to_remove:
                context = browser.contexts[ctx_id]
                await context.close()
                del browser.contexts[ctx_id]
                if ctx_id in self._context_map:
                    del self._context_map[ctx_id]
                logger.info(f"Cleaned up unhealthy context {ctx_id}")
    
    async def _ensure_minimum_browsers(self):
        """Ensure minimum number of browsers exist"""
        min_browsers = min(2, self.max_browsers)
        
        while len(self._browsers) < min_browsers:
            if self._total_data_used_mb >= self.data_limit_mb * 0.9:
                logger.warning("Cannot create new browser - approaching data limit")
                break
            await self._create_browser()
    
    async def _remove_worst_browser(self):
        """Remove the worst performing browser"""
        if not self._browsers:
            return
        
        # Find worst browser
        worst_score = float('inf')
        worst_browser = None
        
        for browser in self._browsers.values():
            score = browser.get_health_score()
            
            # Factor in data efficiency
            if browser.data_usage.get_mb_used() > 0:
                efficiency = browser.total_requests / browser.data_usage.get_mb_used()
                score *= efficiency / 100  # Normalize
            
            if score < worst_score:
                worst_score = score
                worst_browser = browser
        
        if worst_browser:
            # Close browser
            await worst_browser.close()
            
            # Remove from pool
            del self._browsers[worst_browser.instance_id]
            
            # Clean up context mappings
            for ctx_id, browser_id in list(self._context_map.items()):
                if browser_id == worst_browser.instance_id:
                    del self._context_map[ctx_id]
            
            logger.info(f"Removed browser {worst_browser.instance_id} (score: {worst_score:.2f})")
    
    def _on_detection_event(self, event):
        """Handle detection events"""
        logger.warning(
            f"Detection event: {event.detection_type.value} - "
            f"{event.url} (confidence: {event.confidence:.2f})"
        )
        
        # Update context health if severe detection
        if event.confidence > 0.8:
            # Find context from page URL
            for browser in self._browsers.values():
                for context in browser.contexts.values():
                    for page in context.pages:
                        try:
                            if page.url == event.url:
                                context.metrics.record_detection(event.detection_type)
                                if context.health == ContextHealth.HEALTHY:
                                    context.health = ContextHealth.SUSPICIOUS
                                break
                        except Exception:
                            pass
    
    def _log_statistics(self):
        """Log comprehensive pool statistics"""
        total_contexts = sum(len(b.contexts) for b in self._browsers.values())
        avg_health = sum(b.get_health_score() for b in self._browsers.values()) / len(self._browsers) if self._browsers else 0
        
        # Calculate data statistics
        total_saved_mb = sum(b.data_usage.get_savings_mb() for b in self._browsers.values())
        efficiency = (total_saved_mb / self._total_data_used_mb * 100) if self._total_data_used_mb > 0 else 0
        
        stats = {
            "browsers": len(self._browsers),
            "contexts": total_contexts,
            "quarantined": len(self._quarantine_contexts),
            "avg_health": avg_health,
            "success_rate": len(self._success_contexts) / total_contexts if total_contexts > 0 else 0,
            "data_used_mb": self._total_data_used_mb,
            "data_saved_mb": total_saved_mb,
            "data_efficiency": f"{efficiency:.1f}%",
            "avg_acquisition_time": sum(self._acquisition_times[-100:]) / len(self._acquisition_times[-100:]) if self._acquisition_times else 0
        }
        
        # Log top data consuming domains
        all_domains = defaultdict(float)
        for browser in self._browsers.values():
            for domain, bytes_used in browser.data_usage.domain_usage.items():
                all_domains[domain] += bytes_used / (1024 * 1024)
        
        top_domains = sorted(all_domains.items(), key=lambda x: x[1], reverse=True)[:5]
        stats["top_domains"] = [(d, f"{mb:.1f}MB") for d, mb in top_domains]
        
        logger.info(f"Pool statistics: {stats}")
    
    async def shutdown(self):
        """Shutdown the browser pool"""
        logger.info("Shutting down browser pool")
        self._shutdown = True
        
        # Cancel tasks
        if self._maintenance_task:
            self._maintenance_task.cancel()
        if self._recovery_task:
            self._recovery_task.cancel()
        
        async with self._lock:
            # Close all browsers
            for browser in list(self._browsers.values()):
                await browser.close()
            
            self._browsers.clear()
            self._context_map.clear()
        
        logger.info(
            f"Browser pool shutdown complete - "
            f"Total data used: {self._total_data_used_mb:.1f}MB"
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current pool status with detailed metrics"""
        return {
            "browsers": {
                browser_id: {
                    "health": browser.get_health_score(),
                    "contexts": len(browser.contexts),
                    "requests": browser.total_requests,
                    "detections": browser.total_detections,
                    "age_minutes": browser.age.total_seconds() / 60,
                    "data_used_mb": browser.data_usage.get_mb_used(),
                    "data_saved_mb": browser.data_usage.get_savings_mb(),
                    "proxy": browser.proxy.host if browser.proxy else None
                }
                for browser_id, browser in self._browsers.items()
            },
            "total_contexts": sum(len(b.contexts) for b in self._browsers.values()),
            "quarantined_contexts": len(self._quarantine_contexts),
            "proxy_scores": dict(self._proxy_scores),
            "proxy_data_usage": {k: f"{v:.1f}MB" for k, v in self._proxy_data_usage.items()},
            "success_contexts": len(self._success_contexts),
            "total_data_used_mb": self._total_data_used_mb,
            "data_limit_mb": self.data_limit_mb,
            "data_usage_percent": (self._total_data_used_mb / self.data_limit_mb * 100) if self.data_limit_mb > 0 else 0,
            "avg_acquisition_time_ms": (sum(self._acquisition_times[-100:]) / len(self._acquisition_times[-100:]) * 1000) if self._acquisition_times else 0
        }
    
    async def get_data_usage_report(self) -> Dict[str, Any]:
        """Get detailed data usage report"""
        report = {
            "total_used_mb": self._total_data_used_mb,
            "limit_mb": self.data_limit_mb,
            "usage_percent": (self._total_data_used_mb / self.data_limit_mb * 100) if self.data_limit_mb > 0 else 0,
            "browsers": {},
            "proxies": {},
            "top_domains": {},
            "savings": {
                "cached_mb": 0,
                "blocked_mb": 0,
                "total_saved_mb": 0
            }
        }
        
        # Aggregate data from all browsers
        all_domains = defaultdict(float)
        
        for browser_id, browser in self._browsers.items():
            browser_data = {
                "data_used_mb": browser.data_usage.get_mb_used(),
                "data_saved_mb": browser.data_usage.get_savings_mb(),
                "requests": browser.total_requests,
                "efficiency": browser.total_requests / browser.data_usage.get_mb_used() if browser.data_usage.get_mb_used() > 0 else 0
            }
            report["browsers"][browser_id] = browser_data
            
            # Aggregate savings
            report["savings"]["cached_mb"] += browser.data_usage.cached_bytes / (1024 * 1024)
            report["savings"]["blocked_mb"] += browser.data_usage.blocked_bytes / (1024 * 1024)
            
            # Aggregate domains
            for domain, bytes_used in browser.data_usage.domain_usage.items():
                all_domains[domain] += bytes_used / (1024 * 1024)
        
        # Calculate total savings
        report["savings"]["total_saved_mb"] = report["savings"]["cached_mb"] + report["savings"]["blocked_mb"]
        
        # Top domains
        top_domains = sorted(all_domains.items(), key=lambda x: x[1], reverse=True)[:10]
        report["top_domains"] = {d: f"{mb:.2f}MB" for d, mb in top_domains}
        
        # Proxy usage
        report["proxies"] = {k: f"{v:.2f}MB" for k, v in self._proxy_data_usage.items()}
        
        return report