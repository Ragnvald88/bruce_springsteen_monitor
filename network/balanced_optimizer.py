# stealthmaster/network/balanced_optimizer.py
"""Balanced network optimization for maximum data savings while maintaining functionality."""

import logging
from typing import Set, Dict, Any, Optional
from playwright.async_api import Route, Request, Response, BrowserContext
import re

logger = logging.getLogger(__name__)


class BalancedDataOptimizer:
    """Smart optimization that maintains functionality while reducing data usage."""
    
    def __init__(self):
        """Initialize with smart defaults."""
        self.stats = {
            "requests_blocked": 0,
            "requests_allowed": 0,
            "data_saved_bytes": 0,
            "blocked_by_type": {},
            "cache_hits": 0
        }
        
        # Essential scripts patterns for ticketing sites
        self.essential_patterns = [
            # Ticket functionality
            r'/ticket', r'/event', r'/seat', r'/cart', r'/checkout',
            r'/availability', r'/pricing', r'/purchase',
            # Core frameworks (minimal)
            r'jquery.min.js$', r'react.production.min.js$', r'vue.min.js$',
            # API endpoints
            r'/api/', r'/graphql', r'/rest/',
            # Authentication
            r'/auth', r'/login', r'/session',
            # Payment
            r'/payment', r'/stripe', r'/paypal',
        ]
        
        # Always block these domains
        self.blocked_domains = {
            # Analytics & Tracking
            'google-analytics.com', 'googletagmanager.com', 'doubleclick.net',
            'facebook.com', 'twitter.com', 'pinterest.com', 'linkedin.com',
            'hotjar.com', 'mixpanel.com', 'segment.com', 'amplitude.com',
            'matomo.org', 'piwik.pro', 'heap.io', 'fullstory.com',
            # Ads
            'googlesyndication.com', 'adsystem.com', 'adzerk.net', 'adnxs.com',
            'amazon-adsystem.com', 'smartadserver.com', 'teads.tv',
            # Social & Widgets
            'disqus.com', 'livechat.com', 'drift.com', 'intercom.io',
            'zendesk.com', 'tawk.to', 'crisp.chat',
            # CDNs for non-essential content
            'fontawesome.com', 'fonts.googleapis.com', 'typekit.net',
            # Cookie consent
            'cookielaw.org', 'cookiebot.com', 'onetrust.com', 'trustarc.com',
        }
        
        # Smart resource blocking
        self.block_rules = {
            'font': lambda req: True,  # Always block fonts
            'media': lambda req: True,  # Always block media
            'image': lambda req: self._should_block_image(req),
            'stylesheet': lambda req: self._should_block_css(req),
            'script': lambda req: self._should_block_script(req),
        }
        
        # Simple cache for repeated resources
        self.cache = {}
        self.max_cache_size = 20 * 1024 * 1024  # 20MB cache
        self.current_cache_size = 0
        
    def _should_block_image(self, request: Request) -> bool:
        """Smart image blocking - allow only essential images."""
        url = request.url.lower()
        
        # Allow logos and essential UI images
        if any(pattern in url for pattern in ['logo', 'icon', 'button', 'arrow']):
            return False
        
        # Allow small images (likely UI elements)
        if 'thumb' in url or 'small' in url:
            return False
            
        # Block everything else
        return True
    
    def _should_block_css(self, request: Request) -> bool:
        """Smart CSS blocking - only allow critical styles."""
        url = request.url.lower()
        
        # Allow main/critical CSS
        if any(pattern in url for pattern in ['main.css', 'critical.css', 'app.css', 'style.css']):
            return False
            
        # Block third-party CSS
        domain = self._extract_domain(url)
        if any(blocked in domain for blocked in self.blocked_domains):
            return True
            
        # Allow first-party CSS
        return False
    
    def _should_block_script(self, request: Request) -> bool:
        """Smart script blocking - only allow essential functionality."""
        url = request.url
        
        # Check if it's an essential script
        for pattern in self.essential_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # Block known tracking/ad domains
        domain = self._extract_domain(url)
        if any(blocked in domain for blocked in self.blocked_domains):
            return True
        
        # Block inline tracking scripts
        tracking_patterns = [
            'analytics', 'tracking', 'metrics', 'telemetry', 'beacon',
            'pixel', 'tag', 'gtm', '_ga', 'matomo', 'piwik', 'hotjar',
            'segment', 'mixpanel', 'amplitude', 'heap', 'fullstory',
            'adsystem', 'adserver', 'doubleclick', 'googlesyndication'
        ]
        
        if any(pattern in url.lower() for pattern in tracking_patterns):
            return True
        
        # Allow first-party scripts by default
        return False
    
    async def setup_context(self, context: BrowserContext) -> None:
        """Setup optimization for a browser context."""
        await context.route("**/*", self._handle_route)
        
        # Add response compression headers
        await context.set_extra_http_headers({
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=3600'
        })
        
        logger.info("Balanced data optimizer configured")
    
    async def _handle_route(self, route: Route) -> None:
        """Handle each network request with smart optimization."""
        request = route.request
        url = request.url
        resource_type = request.resource_type
        
        # Always allow main document
        if resource_type == 'document':
            self.stats['requests_allowed'] += 1
            await route.continue_()
            return
        
        # Check cache first
        if url in self.cache and request.method == 'GET':
            self.stats['cache_hits'] += 1
            await route.fulfill(
                body=self.cache[url]['body'],
                status=200,
                headers=self.cache[url]['headers']
            )
            return
        
        # Apply smart blocking rules
        should_block = False
        
        # Check domain blocking first
        domain = self._extract_domain(url)
        if any(blocked in domain for blocked in self.blocked_domains):
            should_block = True
        
        # Check resource-specific rules
        elif resource_type in self.block_rules:
            should_block = self.block_rules[resource_type](request)
        
        # Default blocking for non-essential types
        elif resource_type in ['websocket', 'manifest', 'other', 'eventsource']:
            should_block = True
        
        if should_block:
            self.stats['requests_blocked'] += 1
            self.stats['blocked_by_type'][resource_type] = \
                self.stats['blocked_by_type'].get(resource_type, 0) + 1
            
            # Estimate saved data
            estimated_sizes = {
                'image': 50 * 1024,
                'stylesheet': 30 * 1024,
                'font': 40 * 1024,
                'media': 500 * 1024,
                'script': 50 * 1024,
                'other': 10 * 1024
            }
            self.stats['data_saved_bytes'] += estimated_sizes.get(resource_type, 10 * 1024)
            
            await route.abort()
        else:
            self.stats['requests_allowed'] += 1
            
            # Intercept response for caching
            response = await route.fetch()
            
            # Cache small, successful responses
            if response.status == 200 and request.method == 'GET':
                try:
                    body = await response.body()
                    if len(body) < 500 * 1024:  # Only cache resources < 500KB
                        self._add_to_cache(url, body, dict(response.headers))
                except:
                    pass
            
            await route.fulfill(response=response)
    
    def _add_to_cache(self, url: str, body: bytes, headers: Dict) -> None:
        """Add resource to cache with size management."""
        size = len(body)
        
        # Check if we need to make room
        if self.current_cache_size + size > self.max_cache_size:
            # Remove oldest entries (FIFO)
            while self.cache and self.current_cache_size + size > self.max_cache_size:
                removed_url = next(iter(self.cache))
                removed_size = len(self.cache[removed_url]['body'])
                del self.cache[removed_url]
                self.current_cache_size -= removed_size
        
        # Add to cache
        self.cache[url] = {'body': body, 'headers': headers}
        self.current_cache_size += size
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.lower()
        except:
            return ""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        total_requests = self.stats['requests_blocked'] + self.stats['requests_allowed']
        block_rate = (self.stats['requests_blocked'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'requests_blocked': self.stats['requests_blocked'],
            'requests_allowed': self.stats['requests_allowed'],
            'block_rate_percent': round(block_rate, 1),
            'data_saved_mb': round(self.stats['data_saved_bytes'] / (1024 * 1024), 2),
            'cache_hits': self.stats['cache_hits'],
            'cache_size_mb': round(self.current_cache_size / (1024 * 1024), 2),
            'blocked_by_type': self.stats['blocked_by_type']
        }
    
    def reset_stats(self) -> None:
        """Reset statistics but keep cache."""
        self.stats = {
            'requests_blocked': 0,
            'requests_allowed': 0,
            'data_saved_bytes': 0,
            'blocked_by_type': {},
            'cache_hits': self.stats.get('cache_hits', 0)
        }


class ConnectionOptimizer:
    """Optimize network connections for reduced overhead."""
    
    @staticmethod
    async def optimize_context(context: BrowserContext) -> None:
        """Apply connection optimizations to context."""
        # Enable HTTP/2 and connection pooling
        await context.route("**/*", lambda route: route.continue_(
            max_redirects=2  # Limit redirects
        ))
        
        # Set optimal timeouts
        context.set_default_timeout(15000)  # 15s default timeout
        context.set_default_navigation_timeout(30000)  # 30s navigation
        
        # Disable service workers for lower overhead
        await context.add_init_script("""
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.getRegistrations().then(registrations => {
                    registrations.forEach(reg => reg.unregister());
                });
            }
        """)