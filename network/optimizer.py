# stealthmaster/network/optimizer.py
"""Network optimization module for drastically reducing data usage."""

import logging
from typing import Set, Dict, Any, Optional
from playwright.async_api import Route, Request, Response, BrowserContext

logger = logging.getLogger(__name__)


class DataOptimizer:
    """Optimizes data usage by blocking unnecessary resources."""
    
    # Resource types to block in different optimization levels
    OPTIMIZATION_LEVELS = {
        "minimal": {
            "block": {"font", "media"},
            "allow_domains": set(),
            "block_domains": set()
        },
        "moderate": {
            "block": {"font", "media", "image"},
            "allow_domains": set(),
            "block_domains": {"googletagmanager.com", "google-analytics.com", "doubleclick.net", "facebook.com"}
        },
        "aggressive": {
            "block": {"font", "media", "image", "stylesheet"},
            "allow_domains": set(),
            "block_domains": {"googletagmanager.com", "google-analytics.com", "doubleclick.net", 
                            "facebook.com", "twitter.com", "pinterest.com", "linkedin.com",
                            "cloudflare.com", "cookielaw.org", "cookiebot.com"}
        },
        "extreme": {
            "block": {"font", "media", "image", "stylesheet", "websocket", "manifest", "other"},
            "allow_domains": {"ticketmaster.it", "fansale.it", "vivaticket.com"},  # Only allow target domains
            "block_domains": set(),
            "block_third_party_scripts": True
        }
    }
    
    def __init__(self, level: str = "moderate"):
        """Initialize optimizer with specified level."""
        self.level = level
        self.config = self.OPTIMIZATION_LEVELS.get(level, self.OPTIMIZATION_LEVELS["moderate"])
        self.stats = {
            "requests_blocked": 0,
            "requests_allowed": 0,
            "data_saved_bytes": 0,
            "blocked_by_type": {}
        }
        
    async def setup_context(self, context: BrowserContext) -> None:
        """Setup optimization for a browser context."""
        await context.route("**/*", self._handle_route)
        logger.info(f"Data optimizer configured with {self.level} level")
    
    async def _handle_route(self, route: Route) -> None:
        """Handle each network request."""
        request = route.request
        
        # Check if request should be blocked
        if self._should_block(request):
            self.stats["requests_blocked"] += 1
            resource_type = request.resource_type
            self.stats["blocked_by_type"][resource_type] = self.stats["blocked_by_type"].get(resource_type, 0) + 1
            
            # Estimate saved data (average sizes)
            estimated_sizes = {
                "image": 50 * 1024,  # 50KB average
                "stylesheet": 30 * 1024,  # 30KB
                "font": 40 * 1024,  # 40KB
                "media": 500 * 1024,  # 500KB
                "script": 50 * 1024,  # 50KB for blocked scripts
                "other": 10 * 1024  # 10KB
            }
            self.stats["data_saved_bytes"] += estimated_sizes.get(resource_type, 10 * 1024)
            
            await route.abort()
        else:
            self.stats["requests_allowed"] += 1
            await route.continue_()
    
    def _should_block(self, request: Request) -> bool:
        """Determine if request should be blocked."""
        url = request.url
        resource_type = request.resource_type
        
        # Always allow main document
        if resource_type == "document":
            return False
        
        # Check resource type blocking
        if resource_type in self.config["block"]:
            return True
        
        # Check domain blocking
        domain = self._extract_domain(url)
        
        # If we have allow list, only allow those domains
        if self.config["allow_domains"]:
            if not any(allowed in domain for allowed in self.config["allow_domains"]):
                return True
        
        # Block specific domains
        if any(blocked in domain for blocked in self.config["block_domains"]):
            return True
        
        # Block third-party scripts if configured
        if self.config.get("block_third_party_scripts") and resource_type == "script":
            # This is a simplified check - in production you'd compare with page domain
            if not any(allowed in domain for allowed in self.config.get("allow_domains", [])):
                return True
        
        # Block tracking and analytics
        tracking_patterns = [
            "analytics", "tracking", "metrics", "telemetry", "beacon",
            "pixel", "tag", "gtm", "_ga", "matomo", "piwik", "hotjar",
            "segment", "mixpanel", "amplitude", "heap", "fullstory"
        ]
        if any(pattern in url.lower() for pattern in tracking_patterns):
            return True
        
        # Block ads
        ad_patterns = [
            "doubleclick", "adsystem", "adserver", "adtech", "adzerk",
            "advertising", "amazon-adsystem", "googlesyndication", "adnxs",
            "adsafeprotected", "teads", "smartadserver"
        ]
        if any(pattern in url.lower() for pattern in ad_patterns):
            return True
        
        return False
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.lower()
        except:
            return ""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        total_requests = self.stats["requests_blocked"] + self.stats["requests_allowed"]
        block_rate = (self.stats["requests_blocked"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "level": self.level,
            "requests_blocked": self.stats["requests_blocked"],
            "requests_allowed": self.stats["requests_allowed"],
            "block_rate_percent": round(block_rate, 1),
            "data_saved_mb": round(self.stats["data_saved_bytes"] / (1024 * 1024), 2),
            "blocked_by_type": self.stats["blocked_by_type"]
        }
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self.stats = {
            "requests_blocked": 0,
            "requests_allowed": 0,
            "data_saved_bytes": 0,
            "blocked_by_type": {}
        }


class SmartCache:
    """Smart caching system for frequently accessed resources."""
    
    def __init__(self, max_size_mb: int = 50):
        """Initialize cache with size limit."""
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache: Dict[str, bytes] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.current_size = 0
        
    async def setup_context(self, context: BrowserContext) -> None:
        """Setup caching for a browser context."""
        await context.route("**/*", self._handle_cache_route)
        
    async def _handle_cache_route(self, route: Route) -> None:
        """Handle caching for routes."""
        request = route.request
        url = request.url
        
        # Only cache GET requests for certain resource types
        cacheable_types = {"stylesheet", "script", "font", "image"}
        if request.method != "GET" or request.resource_type not in cacheable_types:
            await route.continue_()
            return
        
        # Check cache
        if url in self.cache:
            self.cache_hits += 1
            await route.fulfill(
                body=self.cache[url],
                status=200,
                headers={"X-Cache": "HIT"}
            )
        else:
            self.cache_misses += 1
            
            # Fetch and cache response
            response = await route.fetch()
            if response.status == 200:
                body = await response.body()
                
                # Add to cache if within size limit
                if len(body) + self.current_size <= self.max_size_bytes:
                    self.cache[url] = body
                    self.current_size += len(body)
                elif len(body) < self.max_size_bytes:
                    # Evict old entries if needed
                    self._evict_to_fit(len(body))
                    self.cache[url] = body
                    self.current_size += len(body)
            
            await route.fulfill(
                response=response,
                headers={**dict(response.headers), "X-Cache": "MISS"}
            )
    
    def _evict_to_fit(self, needed_bytes: int) -> None:
        """Evict cache entries to fit new data."""
        # Simple FIFO eviction
        while self.current_size + needed_bytes > self.max_size_bytes and self.cache:
            url, data = self.cache.popitem()
            self.current_size -= len(data)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        hit_rate = (self.cache_hits / (self.cache_hits + self.cache_misses) * 100) if (self.cache_hits + self.cache_misses) > 0 else 0
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate_percent": round(hit_rate, 1),
            "cache_size_mb": round(self.current_size / (1024 * 1024), 2),
            "cached_urls": len(self.cache)
        }


class RequestPrioritizer:
    """Prioritizes critical requests over non-essential ones."""
    
    def __init__(self):
        """Initialize request prioritizer."""
        self.critical_patterns = {
            "ticketmaster.it/api",
            "fansale.it/api",
            "vivaticket.com/api",
            "/ticket",
            "/availability",
            "/checkout",
            "/cart",
            "/purchase"
        }
        
    async def setup_context(self, context: BrowserContext) -> None:
        """Setup request prioritization."""
        # Playwright doesn't support request prioritization directly,
        # but we can abort non-critical requests when load is high
        self.request_count = 0
        self.high_load_threshold = 50  # requests per second
        self.last_reset = time.time()
        
        await context.route("**/*", self._handle_priority_route)
    
    async def _handle_priority_route(self, route: Route) -> None:
        """Handle request prioritization."""
        import time
        
        # Reset counter every second
        current_time = time.time()
        if current_time - self.last_reset > 1:
            self.request_count = 0
            self.last_reset = current_time
        
        self.request_count += 1
        
        # Under high load, only allow critical requests
        if self.request_count > self.high_load_threshold:
            if not self._is_critical(route.request):
                await route.abort()
                return
        
        await route.continue_()
    
    def _is_critical(self, request: Request) -> bool:
        """Check if request is critical."""
        url = request.url.lower()
        return any(pattern in url for pattern in self.critical_patterns)