# src/core/data_optimization_engine.py
"""
StealthMaster AI v3.0 - Data Optimization Engine
Minimizes residential proxy data usage while maintaining stealth
"""

import asyncio
import logging
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from playwright.async_api import Page, Route, Request, Response
import gzip
import json

logger = logging.getLogger(__name__)


@dataclass
class DataUsageStats:
    """Track data usage statistics"""
    requests_blocked: int = 0
    requests_cached: int = 0
    bytes_saved: int = 0
    bytes_used: int = 0
    compression_ratio: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    
    @property
    def total_saved_mb(self) -> float:
        return self.bytes_saved / (1024 * 1024)
    
    @property
    def total_used_mb(self) -> float:
        return self.bytes_used / (1024 * 1024)
    
    @property
    def savings_percentage(self) -> float:
        total = self.bytes_saved + self.bytes_used
        return (self.bytes_saved / total * 100) if total > 0 else 0


class DataOptimizationEngine:
    """
    Advanced data optimization for minimal proxy usage
    Implements intelligent caching, compression, and resource blocking
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Optimization settings
        self.block_images = self.config.get('block_images', True)
        self.block_media = self.config.get('block_media', True)
        self.block_fonts = self.config.get('block_fonts', True)
        self.block_trackers = self.config.get('block_trackers', True)
        self.enable_caching = self.config.get('enable_caching', True)
        self.compression_level = self.config.get('compression_level', 9)
        
        # Resource patterns to block
        self.blocked_patterns = self._compile_block_patterns()
        
        # Cache for static resources
        self.resource_cache: Dict[str, bytes] = {}
        self.cache_max_size = 50 * 1024 * 1024  # 50MB cache
        self.cache_current_size = 0
        
        # Statistics
        self.stats = DataUsageStats()
        
        # Known tracker domains
        self.tracker_domains = {
            'google-analytics.com', 'googletagmanager.com', 'doubleclick.net',
            'facebook.com', 'fbcdn.net', 'twitter.com', 'linkedin.com',
            'hotjar.com', 'mixpanel.com', 'segment.com', 'amplitude.com',
            'clarity.ms', 'mouseflow.com', 'fullstory.com', 'heap.io',
            'quantserve.com', 'scorecardresearch.com', 'amazon-adsystem.com',
            'googlesyndication.com', 'googleadservices.com', 'adsrvr.org'
        }
    
    def _compile_block_patterns(self) -> Set[str]:
        """Compile patterns for resources to block"""
        patterns = set()
        
        if self.block_images:
            patterns.update(['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico', '.bmp'])
        
        if self.block_media:
            patterns.update(['.mp4', '.webm', '.mp3', '.wav', '.avi', '.mov', '.flv'])
        
        if self.block_fonts:
            patterns.update(['.woff', '.woff2', '.ttf', '.eot', '.otf'])
        
        # Always block these
        patterns.update(['.pdf', '.zip', '.exe', '.dmg', '.iso'])
        
        return patterns
    
    async def optimize_page(self, page: Page) -> None:
        """Apply all data optimizations to a page"""
        logger.info("📊 Applying data optimization to page...")
        
        # Route interception for optimization
        await page.route('**/*', self._handle_route)
        
        # Inject compression headers
        await page.set_extra_http_headers({
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/json,application/javascript',
            'Cache-Control': 'max-age=3600'
        })
        
        # Inject client-side optimizations
        await self._inject_client_optimizations(page)
        
        logger.info(f"✅ Data optimization active - {len(self.blocked_patterns)} resource types blocked")
    
    async def _handle_route(self, route: Route) -> None:
        """Intelligent request routing with optimization"""
        request = route.request
        url = request.url
        resource_type = request.resource_type
        
        # 1. Block unnecessary resources
        if self._should_block_resource(url, resource_type):
            self.stats.requests_blocked += 1
            self.stats.bytes_saved += self._estimate_resource_size(url, resource_type)
            await route.abort('blockedbyclient')
            return
        
        # 2. Check cache for static resources
        if self.enable_caching and self._is_cacheable(url, resource_type):
            cached = self._get_from_cache(url)
            if cached:
                self.stats.requests_cached += 1
                self.stats.bytes_saved += len(cached)
                await route.fulfill(
                    body=cached,
                    headers={'X-Cache': 'HIT', 'Content-Encoding': 'gzip'}
                )
                return
        
        # 3. Modify request for optimization
        headers = await self._optimize_request_headers(request)
        
        # Continue with optimized request
        try:
            response = await route.fetch(headers=headers)
            
            # Track data usage
            body = await response.body()
            self.stats.bytes_used += len(body)
            
            # Cache if applicable
            if self.enable_caching and response.status == 200:
                self._add_to_cache(url, body)
            
            # Compress response if not already
            if 'content-encoding' not in response.headers:
                compressed_body = gzip.compress(body, compresslevel=self.compression_level)
                compression_ratio = len(compressed_body) / len(body)
                self.stats.compression_ratio = (self.stats.compression_ratio + compression_ratio) / 2
                
                await route.fulfill(
                    response=response,
                    body=compressed_body,
                    headers={**response.headers, 'Content-Encoding': 'gzip'}
                )
            else:
                await route.fulfill(response=response)
                
        except Exception as e:
            logger.debug(f"Route handling error: {e}")
            await route.continue_()
    
    def _should_block_resource(self, url: str, resource_type: str) -> bool:
        """Determine if resource should be blocked"""
        
        # Block by resource type
        blocked_types = {'image', 'media', 'font', 'stylesheet'}
        if self.block_images and resource_type == 'image':
            return True
        if self.block_media and resource_type == 'media':
            return True
        if self.block_fonts and resource_type == 'font':
            return True
        
        # Block by extension
        for pattern in self.blocked_patterns:
            if pattern in url.lower():
                return True
        
        # Block trackers
        if self.block_trackers:
            for tracker in self.tracker_domains:
                if tracker in url:
                    return True
        
        # Block specific paths
        blocked_paths = ['/analytics', '/tracking', '/metrics', '/telemetry', '/beacon']
        for path in blocked_paths:
            if path in url:
                return True
        
        return False
    
    def _is_cacheable(self, url: str, resource_type: str) -> bool:
        """Check if resource should be cached"""
        
        # Cache these resource types
        cacheable_types = {'script', 'stylesheet', 'font'}
        if resource_type not in cacheable_types:
            return False
        
        # Don't cache dynamic content
        if any(param in url for param in ['?', 'timestamp=', 'v=', 'cache=']):
            return False
        
        # Cache static CDN resources
        cdn_domains = ['googleapis.com', 'cloudflare.com', 'jsdelivr.net', 'unpkg.com']
        return any(cdn in url for cdn in cdn_domains)
    
    def _get_from_cache(self, url: str) -> Optional[bytes]:
        """Retrieve resource from cache"""
        return self.resource_cache.get(url)
    
    def _add_to_cache(self, url: str, data: bytes) -> None:
        """Add resource to cache with size management"""
        
        # Check cache size
        if self.cache_current_size + len(data) > self.cache_max_size:
            # Evict oldest entries
            while self.cache_current_size + len(data) > self.cache_max_size and self.resource_cache:
                oldest_key = next(iter(self.resource_cache))
                old_size = len(self.resource_cache[oldest_key])
                del self.resource_cache[oldest_key]
                self.cache_current_size -= old_size
        
        # Add to cache
        self.resource_cache[url] = data
        self.cache_current_size += len(data)
    
    async def _optimize_request_headers(self, request: Request) -> Dict[str, str]:
        """Optimize request headers for minimal data transfer"""
        
        headers = dict(request.headers)
        
        # Request compressed content
        headers['Accept-Encoding'] = 'gzip, deflate, br'
        
        # Minimize accepted content types
        if request.resource_type == 'document':
            headers['Accept'] = 'text/html,application/xhtml+xml'
        elif request.resource_type == 'script':
            headers['Accept'] = 'application/javascript,text/javascript'
        elif request.resource_type == 'stylesheet':
            headers['Accept'] = 'text/css'
        else:
            headers['Accept'] = '*/*;q=0.1'
        
        # Remove unnecessary headers
        unnecessary_headers = [
            'X-DevTools-Emulate-Network-Conditions-Client-Id',
            'X-DevTools-Request-Id',
            'X-Chrome-Connected',
            'X-Client-Data'
        ]
        
        for header in unnecessary_headers:
            headers.pop(header, None)
        
        return headers
    
    async def _inject_client_optimizations(self, page: Page) -> None:
        """Inject client-side optimizations"""
        
        await page.add_init_script("""
        // Client-side data optimization
        (() => {
            // Disable prefetching
            const metaPrefetch = document.createElement('meta');
            metaPrefetch.httpEquiv = 'x-dns-prefetch-control';
            metaPrefetch.content = 'off';
            document.head.appendChild(metaPrefetch);
            
            // Block lazy loading
            if ('loading' in HTMLImageElement.prototype) {
                const images = document.querySelectorAll('img[loading="lazy"]');
                images.forEach(img => img.loading = 'manual');
            }
            
            // Disable video autoplay
            const videos = document.querySelectorAll('video[autoplay]');
            videos.forEach(video => {
                video.autoplay = false;
                video.pause();
            });
            
            // Block WebSocket connections to trackers
            const originalWebSocket = window.WebSocket;
            window.WebSocket = new Proxy(originalWebSocket, {
                construct(target, args) {
                    const url = args[0];
                    const blockedDomains = ['analytics', 'tracking', 'metrics'];
                    
                    if (blockedDomains.some(domain => url.includes(domain))) {
                        throw new Error('WebSocket blocked by optimization');
                    }
                    
                    return new target(...args);
                }
            });
            
            // Override fetch to block trackers
            const originalFetch = window.fetch;
            window.fetch = async (...args) => {
                const url = args[0]?.toString() || '';
                const blockedPatterns = ['/analytics', '/tracking', '/beacon', '/collect'];
                
                if (blockedPatterns.some(pattern => url.includes(pattern))) {
                    return new Response('', { status: 204 });
                }
                
                return originalFetch(...args);
            };
        })();
        """)
    
    def _estimate_resource_size(self, url: str, resource_type: str) -> int:
        """Estimate resource size for statistics"""
        
        # Average sizes by type (in bytes)
        size_estimates = {
            'image': 150 * 1024,      # 150KB
            'media': 5 * 1024 * 1024, # 5MB
            'font': 50 * 1024,        # 50KB
            'stylesheet': 30 * 1024,  # 30KB
            'script': 100 * 1024,     # 100KB
            'other': 20 * 1024        # 20KB
        }
        
        return size_estimates.get(resource_type, size_estimates['other'])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        
        runtime = (datetime.now() - self.stats.start_time).total_seconds()
        
        return {
            'runtime_seconds': runtime,
            'requests_blocked': self.stats.requests_blocked,
            'requests_cached': self.stats.requests_cached,
            'data_saved_mb': round(self.stats.total_saved_mb, 2),
            'data_used_mb': round(self.stats.total_used_mb, 2),
            'savings_percentage': round(self.stats.savings_percentage, 1),
            'compression_ratio': round(self.stats.compression_ratio, 2),
            'cache_size_mb': round(self.cache_current_size / (1024 * 1024), 2),
            'cached_resources': len(self.resource_cache)
        }
    
    def reset_stats(self) -> None:
        """Reset statistics"""
        self.stats = DataUsageStats()
    
    async def analyze_page_data_usage(self, page: Page) -> Dict[str, Any]:
        """Analyze potential data usage for a page"""
        
        # Evaluate page resources
        resources = await page.evaluate("""
        () => {
            const resources = performance.getEntriesByType('resource');
            return resources.map(r => ({
                name: r.name,
                type: r.initiatorType,
                size: r.transferSize || 0,
                duration: r.duration
            }));
        }
        """)
        
        # Categorize and sum
        usage_by_type = {}
        total_size = 0
        
        for resource in resources:
            res_type = resource.get('type', 'other')
            size = resource.get('size', 0)
            
            if res_type not in usage_by_type:
                usage_by_type[res_type] = {'count': 0, 'size': 0}
            
            usage_by_type[res_type]['count'] += 1
            usage_by_type[res_type]['size'] += size
            total_size += size
        
        return {
            'total_resources': len(resources),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'by_type': usage_by_type,
            'potential_savings_mb': round(
                sum(usage_by_type.get(t, {}).get('size', 0) 
                    for t in ['img', 'image', 'media', 'font']) / (1024 * 1024), 2
            )
        }


# Global instance
_data_optimization_engine: Optional[DataOptimizationEngine] = None

def get_data_optimization_engine(config: Optional[Dict[str, Any]] = None) -> DataOptimizationEngine:
    """Get or create global data optimization engine"""
    global _data_optimization_engine
    
    if _data_optimization_engine is None:
        _data_optimization_engine = DataOptimizationEngine(config)
    
    return _data_optimization_engine