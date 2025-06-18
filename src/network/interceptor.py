# stealthmaster/network/interceptor.py
"""Advanced request/response interception with anti-detection measures."""

import asyncio
import json
import logging
import random
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Union, Tuple
from urllib.parse import urlparse, parse_qs
import hashlib
from collections import defaultdict
from email.utils import parsedate_to_datetime

from playwright.async_api import Request, Response, Route, Page
import httpx

logger = logging.getLogger(__name__)


class InterceptorMode:
    """Interception modes."""
    PASSIVE = "passive"      # Monitor only
    ACTIVE = "active"        # Modify requests/responses
    AGGRESSIVE = "aggressive" # Block/redirect requests


class CachedResponse:
    """Cached response data."""
    def __init__(self, data: bytes, headers: Dict[str, str], status: int, max_age: int = 300):
        self.data = data
        self.headers = headers
        self.status = status
        self.max_age = max_age
        self.timestamp = datetime.now()


class InterceptRule:
    """Rule for intercepting requests."""
    def __init__(self, pattern: str, action: Callable, priority: int = 0):
        self.pattern = pattern
        self.action = action
        self.priority = priority


class BasicPatternAnalyzer:
    """Basic analyzer for request patterns."""
    def __init__(self):
        self.patterns = []
    
    def analyze(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze request pattern."""
        return {"risk_score": 0.0}


class RequestInterceptor:
    """Advanced request/response interception with stealth modifications."""
    
    def __init__(self):
        """Initialize request interceptor."""
        self._intercept_rules: List[InterceptRule] = []
        self._request_history: List[Dict[str, Any]] = []
        self._blocked_patterns: List[str] = []
        self._modified_count = 0
        self._intercepted_count = 0
        
        # TLS fingerprint management
        self._tls_profiles = self._load_tls_profiles()
        self._current_tls_profile = None
        
        # Request pattern analysis
        self._request_patterns = defaultdict(list)
        self._pattern_analyzer = None  # Will be initialized later with the full PatternAnalyzer
        
        # Response cache for efficiency
        self._response_cache: Dict[str, CachedResponse] = {}
        self._cache_size_limit = 100 * 1024 * 1024  # 100MB
        self._current_cache_size = 0
    
    def _load_tls_profiles(self) -> List[Dict[str, Any]]:
        """Load realistic TLS fingerprint profiles."""
        return [
            {
                "name": "Chrome_131",
                "ja3": "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513-21,29-23-24,0",
                "h2_settings": {
                    "HEADER_TABLE_SIZE": 65536,
                    "ENABLE_PUSH": 0,
                    "INITIAL_WINDOW_SIZE": 6291456,
                    "MAX_HEADER_LIST_SIZE": 262144
                },
                "h2_window_update": 15663105,
                "h2_priority": {
                    "weight": 256,
                    "depends_on": 0,
                    "exclusive": 1
                }
            },
            {
                "name": "Firefox_133",
                "ja3": "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0",
                "h2_settings": {
                    "HEADER_TABLE_SIZE": 65536,
                    "INITIAL_WINDOW_SIZE": 131072,
                    "MAX_FRAME_SIZE": 16777215
                }
            },
            {
                "name": "Safari_17",
                "ja3": "771,4865-4866-4867-49196-49195-52393-49200-49199-52392-49162-49161-49172-49171-157-156-53-47-49160-49170-10,0-23-65281-10-11-16-5-13-18-51-45-43-27-21,29-23-24-25,0",
                "h2_settings": {
                    "HEADER_TABLE_SIZE": 4096,
                    "ENABLE_PUSH": 0,
                    "INITIAL_WINDOW_SIZE": 1048576,
                    "MAX_CONCURRENT_STREAMS": 100
                }
            }
        ]
    
    async def setup_page_interception(
        self,
        page: Page,
        mode: str = InterceptorMode.ACTIVE
    ) -> None:
        """
        Setup request/response interception for a page.
        
        Args:
            page: Page to intercept
            mode: Interception mode
        """
        self._mode = mode
        
        # Setup route handlers
        await page.route("**/*", self._handle_route)
        
        # Monitor responses
        page.on("response", self._on_response)
        
        # Monitor requests
        page.on("request", self._on_request)
        
        logger.info(f"Interception setup complete in {mode} mode")
    
    async def _handle_route(self, route: Route, request: Request) -> None:
        """Handle intercepted routes with caching."""
        self._intercepted_count += 1
        
        # Check if should block
        if self._should_block_request(request):
            await route.abort()
            return
        
        # PERFORMANCE FIX: Check cache before making request
        if request.method == "GET" and self._mode != InterceptorMode.PASSIVE:
            cache_key = self._generate_cache_key(request)
            cached = self._response_cache.get(cache_key)
            
            if cached and self._is_cache_valid(cached):
                # Serve from cache
                await route.fulfill(
                    status=cached.status,
                    headers=cached.headers,
                    body=cached.body
                )
                logger.debug(f"Served from cache: {request.url}")
                return
        
        # Passive mode - just continue
        if self._mode == InterceptorMode.PASSIVE:
            await route.continue_()
            return
        
        # Active/Aggressive mode - modify request
        override_options = await self._modify_request(request)
        
        if override_options:
            self._modified_count += 1
            await route.continue_(**override_options)
        else:
            await route.continue_()
    
    def _should_block_request(self, request: Request) -> bool:
        """Check if request should be blocked."""
        url = request.url
        resource_type = request.resource_type
        
        # Block tracking/analytics
        tracking_domains = [
            "google-analytics.com",
            "googletagmanager.com",
            "facebook.com/tr",
            "doubleclick.net",
            "scorecardresearch.com",
            "quantserve.com",
            "adsystem.com",
            "amazon-adsystem.com",
            "googlesyndication.com"
        ]
        
        for domain in tracking_domains:
            if domain in url:
                logger.debug(f"Blocking tracking request: {url}")
                return True
        
        # Block based on resource type (for data saving)
        if self._mode == InterceptorMode.AGGRESSIVE:
            blocked_types = ["image", "media", "font", "stylesheet"]
            if resource_type in blocked_types:
                logger.debug(f"Blocking {resource_type}: {url}")
                return True
        
        # Check custom patterns
        for pattern in self._blocked_patterns:
            if pattern in url:
                return True
        
        return False
    
    async def _modify_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """Modify request headers and parameters."""
        headers = dict(request.headers)
        
        # Remove automation indicators
        suspicious_headers = [
            "sec-ch-ua-platform-version",
            "sec-ch-ua-full-version",
            "sec-ch-ua-full-version-list",
            "sec-ch-ua-bitness",
            "sec-ch-ua-arch",
            "sec-ch-ua-model"
        ]
        
        for header in suspicious_headers:
            headers.pop(header.lower(), None)
        
        # Add/modify headers for stealth
        stealth_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        headers.update(stealth_headers)
        
        # Randomize header order (important for fingerprinting)
        header_items = list(headers.items())
        random.shuffle(header_items)
        headers = dict(header_items)
        
        # Apply TLS fingerprint if available
        if self._current_tls_profile:
            headers["__tls_profile__"] = json.dumps(self._current_tls_profile)
        
        return {"headers": headers}
    
    def _on_request(self, request: Request) -> None:
        """Monitor outgoing requests."""
        # Record request pattern
        domain = urlparse(request.url).netloc
        self._request_patterns[domain].append({
            "timestamp": datetime.now(),
            "method": request.method,
            "resource_type": request.resource_type,
            "headers": dict(request.headers)
        })
        
        # Analyze patterns
        if len(self._request_patterns[domain]) > 10:
            self._initialize_pattern_analyzer()
            self._pattern_analyzer.analyze(domain, self._request_patterns[domain])
    
    async def _on_response(self, response: Response) -> None:
        """Monitor responses for detection signatures."""
        url = response.url
        status = response.status
        headers = response.headers
        
        # Check for detection indicators
        detection_indicators = {
            "cf-ray": "Cloudflare",
            "cf-cache-status": "Cloudflare", 
            "server": ["cloudflare", "ddos-guard", "incapsula"],
            "x-datadome": "DataDome",
            "x-perimeterx": "PerimeterX"
        }
        
        for header, indicator in detection_indicators.items():
            value = headers.get(header, "").lower()
            if isinstance(indicator, list):
                for ind in indicator:
                    if ind in value:
                        logger.warning(f"Detected {ind} protection on {url}")
                        break
            elif indicator.lower() in value:
                logger.warning(f"Detected {indicator} protection on {url}")
        
        # Cache successful responses
        if status == 200 and response.request.method == "GET":
            await self._cache_response(response)
    
    async def _cache_response(self, response: Response) -> None:
        """Cache response for efficiency."""
        try:
            # PERFORMANCE FIX: Only cache cacheable responses
            if not self._is_cacheable(response):
                return
                
            body = await response.body()
            size = len(body)
            
            # Skip large responses
            if size > 5 * 1024 * 1024:  # 5MB limit per response
                return
            
            # Check cache size limit
            if self._current_cache_size + size > self._cache_size_limit:
                await self._evict_cache()
            
            cache_key = self._generate_cache_key(response.request)
            self._response_cache[cache_key] = CachedResponse(
                url=response.url,
                status=response.status,
                headers=dict(response.headers),
                body=body,
                timestamp=datetime.now(),
                max_age=self._extract_max_age(response.headers)
            )
            self._current_cache_size += size
            
        except Exception as e:
            logger.debug(f"Failed to cache response: {e}")
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate optimized cache key for request."""
        # PERFORMANCE FIX: Optimize cache key generation
        # Don't include volatile headers that change frequently
        headers_to_exclude = {
            'date', 'x-request-id', 'x-correlation-id', 'x-trace-id',
            'x-amzn-trace-id', 'x-b3-traceid', 'x-b3-spanid',
            'cookie', 'authorization', 'x-csrf-token'
        }
        
        # Filter headers for cache key
        filtered_headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in headers_to_exclude
        }
        
        # Create more efficient cache key
        parsed_url = urlparse(request.url)
        cache_components = [
            request.method,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.query or '',
            # Only include important headers
            filtered_headers.get('accept', ''),
            filtered_headers.get('accept-language', ''),
            filtered_headers.get('user-agent', '')
        ]
        
        # Use a more efficient hash
        return hashlib.blake2b(
            '|'.join(cache_components).encode(),
            digest_size=16
        ).hexdigest()
    
    async def _evict_cache(self) -> None:
        """Evict old cache entries."""
        # Sort by timestamp and remove oldest
        sorted_cache = sorted(
            self._response_cache.items(),
            key=lambda x: x[1].timestamp
        )
        
        # Remove oldest 25%
        to_remove = len(sorted_cache) // 4
        for key, cached in sorted_cache[:to_remove]:
            self._current_cache_size -= len(cached.body)
            del self._response_cache[key]
    
    def add_intercept_rule(self, rule: 'InterceptRule') -> None:
        """Add custom interception rule."""
        self._intercept_rules.append(rule)
    
    def add_blocked_pattern(self, pattern: str) -> None:
        """Add URL pattern to block."""
        self._blocked_patterns.append(pattern)
    
    def rotate_tls_profile(self) -> None:
        """Rotate to a different TLS fingerprint."""
        if self._tls_profiles:
            self._current_tls_profile = random.choice(self._tls_profiles)
            logger.info(f"Rotated to TLS profile: {self._current_tls_profile['name']}")
    
    def _is_cache_valid(self, cached: CachedResponse) -> bool:
        """Check if cached response is still valid."""
        age = (datetime.now() - cached.timestamp).total_seconds()
        return age < cached.max_age
    
    def _is_cacheable(self, response: Response) -> bool:
        """Check if response should be cached."""
        # Only cache successful GET requests
        if response.request.method != "GET" or response.status != 200:
            return False
            
        # Check cache-control headers
        cache_control = response.headers.get('cache-control', '').lower()
        if any(directive in cache_control for directive in ['no-cache', 'no-store', 'private']):
            return False
            
        # Don't cache dynamic content
        content_type = response.headers.get('content-type', '').lower()
        non_cacheable_types = ['text/event-stream', 'application/json', 'application/x-ndjson']
        if any(ct in content_type for ct in non_cacheable_types):
            return False
            
        return True
    
    def _extract_max_age(self, headers: Dict[str, str]) -> int:
        """Extract max-age from cache-control header."""
        cache_control = headers.get('cache-control', '').lower()
        
        # Look for max-age directive
        import re
        match = re.search(r'max-age=(\d+)', cache_control)
        if match:
            return int(match.group(1))
            
        # Check expires header
        expires = headers.get('expires')
        if expires:
            try:
                from email.utils import parsedate_to_datetime
                expires_dt = parsedate_to_datetime(expires)
                age = (expires_dt - datetime.now()).total_seconds()
                if age > 0:
                    return int(age)
            except:
                pass
                
        # Default cache time based on content type
        content_type = headers.get('content-type', '').lower()
        if 'text/html' in content_type:
            return 60  # 1 minute for HTML
        elif any(t in content_type for t in ['css', 'javascript', 'font']):
            return 3600  # 1 hour for static assets
        elif 'image' in content_type:
            return 86400  # 24 hours for images
            
        return 300  # Default 5 minutes
    
    def _initialize_pattern_analyzer(self):
        """Initialize the pattern analyzer when needed."""
        if self._pattern_analyzer is None:
            self._pattern_analyzer = PatternAnalyzer()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get interception statistics."""
        # Calculate cache hit rate
        cache_hits = sum(1 for cached in self._response_cache.values() if self._is_cache_valid(cached))
        cache_hit_rate = (cache_hits / len(self._response_cache) * 100) if self._response_cache else 0
        
        return {
            "intercepted_requests": self._intercepted_count,
            "modified_requests": self._modified_count,
            "cached_responses": len(self._response_cache),
            "cache_hit_rate": cache_hit_rate,
            "cache_size_mb": self._current_cache_size / (1024 * 1024),
            "blocked_patterns": len(self._blocked_patterns),
            "monitored_domains": len(self._request_patterns)
        }


class InterceptRule:
    """Custom interception rule."""
    
    def __init__(
        self,
        pattern: str,
        action: str = "modify",
        modifications: Optional[Dict[str, Any]] = None,
        condition: Optional[Callable] = None
    ):
        """
        Initialize interception rule.
        
        Args:
            pattern: URL pattern to match
            action: Action to take (modify, block, redirect)
            modifications: Modifications to apply
            condition: Optional condition function
        """
        self.pattern = pattern
        self.action = action
        self.modifications = modifications or {}
        self.condition = condition
    
    def matches(self, request: Request) -> bool:
        """Check if rule matches request."""
        if self.pattern not in request.url:
            return False
        
        if self.condition:
            return self.condition(request)
        
        return True
    
    def apply(self, request: Request) -> Dict[str, Any]:
        """Apply rule modifications."""
        if self.action == "block":
            return {"abort": True}
        
        if self.action == "modify":
            return self.modifications
        
        return {}


class CachedResponse:
    """Cached response data."""
    
    def __init__(
        self,
        url: str,
        status: int,
        headers: Dict[str, str],
        body: bytes,
        timestamp: datetime,
        max_age: Optional[int] = None
    ):
        self.url = url
        self.status = status
        self.headers = headers
        self.body = body
        self.timestamp = timestamp
        self.max_age = max_age or 300  # Default 5 minutes


class PatternAnalyzer:
    """Analyze request patterns for anomaly detection."""
    
    def __init__(self):
        """Initialize pattern analyzer."""
        self._patterns: Dict[str, DomainPattern] = {}
    
    def analyze(self, domain: str, requests: List[Dict[str, Any]]) -> None:
        """Analyze request patterns for a domain."""
        if domain not in self._patterns:
            self._patterns[domain] = DomainPattern(domain)
        
        pattern = self._patterns[domain]
        pattern.analyze_requests(requests)
        
        # Check for anomalies
        if pattern.is_rate_limited():
            logger.warning(f"Rate limiting detected on {domain}")
        
        if pattern.has_bot_detection():
            logger.warning(f"Bot detection patterns found on {domain}")


class DomainPattern:
    """Pattern analysis for a specific domain."""
    
    def __init__(self, domain: str):
        """Initialize domain pattern."""
        self.domain = domain
        self.request_intervals: List[float] = []
        self.resource_types: Dict[str, int] = defaultdict(int)
        self.response_times: List[float] = []
        self.error_rate = 0.0
    
    def analyze_requests(self, requests: List[Dict[str, Any]]) -> None:
        """Analyze request patterns."""
        # Calculate intervals
        for i in range(1, len(requests)):
            interval = (requests[i]["timestamp"] - requests[i-1]["timestamp"]).total_seconds()
            self.request_intervals.append(interval)
        
        # Count resource types
        for req in requests:
            self.resource_types[req["resource_type"]] += 1
    
    def is_rate_limited(self) -> bool:
        """Check if showing rate limit patterns."""
        if not self.request_intervals:
            return False
        
        # Check for increasing delays (exponential backoff)
        increasing_delays = 0
        for i in range(1, len(self.request_intervals)):
            if self.request_intervals[i] > self.request_intervals[i-1] * 1.5:
                increasing_delays += 1
        
        return increasing_delays > 3
    
    def has_bot_detection(self) -> bool:
        """Check for bot detection patterns."""
        # High percentage of document requests might indicate challenges
        total_requests = sum(self.resource_types.values())
        doc_requests = self.resource_types.get("document", 0)
        
        if total_requests > 0:
            doc_percentage = doc_requests / total_requests
            return doc_percentage > 0.8  # Unusually high
        
        return False


class HeaderNormalizer:
    """Normalize headers to match browser behavior."""
    
    @staticmethod
    def normalize_headers(
        headers: Dict[str, str],
        browser: str = "chrome"
    ) -> Dict[str, str]:
        """Normalize headers to match browser fingerprint."""
        # Browser-specific header order
        header_order = {
            "chrome": [
                "host", "connection", "cache-control", "sec-ch-ua", 
                "sec-ch-ua-mobile", "user-agent", "accept",
                "sec-fetch-site", "sec-fetch-mode", "sec-fetch-dest",
                "referer", "accept-encoding", "accept-language", "cookie"
            ],
            "firefox": [
                "host", "user-agent", "accept", "accept-language",
                "accept-encoding", "connection", "referer", "cookie",
                "upgrade-insecure-requests", "sec-fetch-dest",
                "sec-fetch-mode", "sec-fetch-site"
            ]
        }
        
        # Get browser-specific order
        order = header_order.get(browser, header_order["chrome"])
        
        # Normalize header names
        normalized = {}
        for key, value in headers.items():
            normalized[key.lower()] = value
        
        # Reorder headers
        ordered = {}
        for header in order:
            if header in normalized:
                ordered[header] = normalized[header]
        
        # Add remaining headers
        for key, value in normalized.items():
            if key not in ordered:
                ordered[key] = value
        
        return ordered