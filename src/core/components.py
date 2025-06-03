# src/core/managers.py - v5.0 - Ultra-Performance Enhanced Edition
from __future__ import annotations

import asyncio
import hashlib
import logging
import json
import time
import weakref
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any, List, Set, Union
from collections import defaultdict, deque
from dataclasses import dataclass
from contextlib import asynccontextmanager

import httpx
import aiofiles
from playwright.async_api import (
    Playwright,
    BrowserContext as PlaywrightContext,
    Page as PlaywrightPage,
    Route,
    Request,
    Browser
)

# Project imports
from src.profiles.manager import ProfileManager
from src.profiles.models import BrowserProfile
from src.profiles.enums import DataOptimizationLevel, Platform

from .models import DataUsageTracker
from .errors import BlockedError

logger = logging.getLogger(__name__)


@dataclass
class ConnectionMetrics:
    """Track connection performance metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_used: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        return self.successful_requests / max(self.total_requests, 1)


@dataclass 
class CacheEntry:
    """Enhanced cache entry with metadata"""
    data: bytes
    timestamp: datetime
    response_headers: Dict[str, str]
    content_type: str
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    hits: int = 0
    
    @property
    def age_seconds(self) -> float:
        return (datetime.now() - self.timestamp).total_seconds()
    
    @property
    def size_bytes(self) -> int:
        return len(self.data) if self.data else 0


class AdvancedConnectionPoolManager:
    """Advanced HTTP connection pool with intelligent routing and health monitoring"""

    def __init__(self, config: Dict[str, Any], profile_manager: ProfileManager):
        self.config = config
        self.profile_manager = profile_manager
        
        # Connection pools per profile
        self.pools: Dict[str, httpx.AsyncClient] = {}
        self.pool_metrics: Dict[str, ConnectionMetrics] = defaultdict(ConnectionMetrics)
        self.pool_health: Dict[str, float] = defaultdict(lambda: 100.0)
        
        # Configuration
        network_config = self.config.get('network', {})
        self.max_connections = network_config.get('max_connections_per_host', 10)
        self.max_keepalive = network_config.get('max_keepalive_connections', 5)
        self.connect_timeout = network_config.get('connect_timeout_seconds', 15)
        self.read_timeout = network_config.get('read_timeout_seconds', 20)
        self.pool_ttl = network_config.get('pool_ttl_seconds', 3600)
        
        # Advanced features
        self.enable_http2 = network_config.get('http2_enabled', True)
        self.retry_config = {
            'max_retries': 3,
            'backoff_factor': 0.5,
            'status_forcelist': [429, 502, 503, 504]
        }
        
        # Health monitoring
        self.health_check_interval = 300  # 5 minutes
        self._health_check_task: Optional[asyncio.Task] = None
        self._pool_lock = asyncio.RLock()
        self._shutdown_event = asyncio.Event()
        
        # TLS fingerprinting
        self.tls_configs = self._load_tls_configurations()
        
        logger.info(f"AdvancedConnectionPoolManager initialized: {self.max_connections} max connections")

    def _load_tls_configurations(self) -> List[Dict[str, Any]]:
        """Load realistic TLS configurations for different browsers"""
        return [
            {
                'name': 'chrome_latest',
                'cipher_suites': [
                    'TLS_AES_128_GCM_SHA256',
                    'TLS_AES_256_GCM_SHA384', 
                    'TLS_CHACHA20_POLY1305_SHA256',
                    'ECDHE-ECDSA-AES128-GCM-SHA256',
                    'ECDHE-RSA-AES128-GCM-SHA256'
                ],
                'signature_algorithms': [
                    'ecdsa_secp256r1_sha256',
                    'rsa_pss_rsae_sha256',
                    'rsa_pkcs1_sha256'
                ]
            },
            {
                'name': 'firefox_latest',
                'cipher_suites': [
                    'TLS_AES_128_GCM_SHA256',
                    'TLS_CHACHA20_POLY1305_SHA256',
                    'TLS_AES_256_GCM_SHA384'
                ],
                'signature_algorithms': [
                    'ecdsa_secp256r1_sha256',
                    'rsa_pss_rsae_sha256'
                ]
            }
        ]

    async def start_health_monitoring(self):
        """Start background health monitoring"""
        if self._health_check_task:
            return
            
        self._health_check_task = asyncio.create_task(self._health_monitor_loop())
        logger.info("Connection pool health monitoring started")

    async def stop_health_monitoring(self):
        """Stop health monitoring"""
        self._shutdown_event.set()
        if self._health_check_task:
            await self._health_check_task
            self._health_check_task = None

    async def _health_monitor_loop(self):
        """Background health monitoring loop"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()
                await self._cleanup_stale_pools()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")

    async def _perform_health_checks(self):
        """Perform health checks on all pools"""
        async with self._pool_lock:
            for client_key, client in list(self.pools.items()):
                try:
                    # Check if client is still functional
                    if client.is_closed:
                        logger.warning(f"Removing closed client: {client_key}")
                        await self._remove_pool(client_key)
                        continue
                    
                    # Update health based on metrics
                    metrics = self.pool_metrics[client_key]
                    if metrics.total_requests > 10:
                        health = metrics.success_rate * 100
                        self.pool_health[client_key] = health
                        
                        if health < 50:
                            logger.warning(f"Unhealthy pool detected: {client_key} (health: {health:.1f}%)")
                            
                except Exception as e:
                    logger.error(f"Health check failed for {client_key}: {e}")

    async def _cleanup_stale_pools(self):
        """Remove stale and unused pools"""
        async with self._pool_lock:
            current_time = datetime.now()
            stale_keys = []
            
            for client_key, metrics in self.pool_metrics.items():
                if metrics.last_used:
                    age = (current_time - metrics.last_used).total_seconds()
                    if age > self.pool_ttl:
                        stale_keys.append(client_key)
            
            for key in stale_keys:
                logger.debug(f"Removing stale pool: {key}")
                await self._remove_pool(key)

    async def get_client(self,
                        profile: BrowserProfile,
                        use_tls_fingerprint: bool = True,
                        platform_hint: Optional[str] = None) -> httpx.AsyncClient:
        """Get optimized HTTP client for profile with advanced features"""
        
        async with self._pool_lock:
            # Generate client key based on profile and platform
            client_key = self._generate_client_key(profile, platform_hint)
            
            # Return existing healthy client
            if client_key in self.pools:
                client = self.pools[client_key]
                if not client.is_closed and self.pool_health[client_key] > 30:
                    self.pool_metrics[client_key].last_used = datetime.now()
                    return client
                else:
                    await self._remove_pool(client_key)
            
            # Create new optimized client
            logger.debug(f"Creating new HTTP client: {client_key}")
            client = await self._create_optimized_client(profile, use_tls_fingerprint, platform_hint)
            
            self.pools[client_key] = client
            self.pool_metrics[client_key].last_used = datetime.now()
            
            return client

    def _generate_client_key(self, profile: BrowserProfile, platform_hint: Optional[str]) -> str:
        """Generate unique client key"""
        key_parts = [
            profile.profile_id,
            profile.fingerprint_hash or "default",
            platform_hint or "generic"
        ]
        
        if profile.proxy_config:
            key_parts.append(f"proxy_{profile.proxy_config.host}_{profile.proxy_session_id}")
        
        return "_".join(key_parts)

    async def _create_optimized_client(self,
                                     profile: BrowserProfile,
                                     use_tls_fingerprint: bool,
                                     platform_hint: Optional[str]) -> httpx.AsyncClient:
        """Create optimized HTTP client with advanced fingerprinting"""
        
        # Base headers from profile
        headers = self._build_headers(profile, platform_hint)
        
        # Connection limits
        limits = httpx.Limits(
            max_connections=self.max_connections,
            max_keepalive_connections=self.max_keepalive,
            keepalive_expiry=300
        )
        
        # Timeout configuration
        timeout = httpx.Timeout(
            connect=self.connect_timeout,
            read=self.read_timeout,
            write=30.0,
            pool=60.0
        )
        
        # Proxy configuration
        proxies = None
        if profile.proxy_config:
            proxy_url = profile.proxy_config.get_proxy_url(profile.proxy_session_id)
            if proxy_url:
                proxies = {"all://": proxy_url}
                logger.debug(f"Using proxy: {profile.proxy_config.host}")
        
        # Advanced transport with TLS fingerprinting
        transport_kwargs = {
            'limits': limits,
            'retries': self.retry_config['max_retries'],
            'verify': True
        }
        
        if proxies:
            transport_kwargs['proxies'] = proxies
        
        # TLS fingerprinting
        if use_tls_fingerprint and self.tls_configs:
            browser_type = self._detect_browser_type(profile.user_agent)
            tls_config = next(
                (cfg for cfg in self.tls_configs if browser_type in cfg['name']),
                self.tls_configs[0]
            )
            # Note: httpx doesn't support direct TLS fingerprinting
            # This would need a custom transport implementation
            transport_kwargs['http2'] = self.enable_http2
        
        try:
            client = httpx.AsyncClient(
                headers=headers,
                timeout=timeout,
                limits=limits,
                follow_redirects=True,
                http2=self.enable_http2,
                proxies=proxies,
                verify=True
            )
            
            # Add request/response hooks for monitoring
            client.event_hooks['request'] = [self._request_hook]
            client.event_hooks['response'] = [self._response_hook]
            
            logger.info(f"Created HTTP client for {profile.profile_id}")
            return client
            
        except Exception as e:
            logger.error(f"Failed to create HTTP client: {e}")
            raise

    def _build_headers(self, profile: BrowserProfile, platform_hint: Optional[str]) -> Dict[str, str]:
        """Build comprehensive headers for profile"""
        headers = {
            'User-Agent': profile.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': profile.accept_language or 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': profile.accept_encoding,
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Add Client Hints
        if profile.sec_ch_ua:
            headers['sec-ch-ua'] = profile.sec_ch_ua
        if profile.sec_ch_ua_mobile:
            headers['sec-ch-ua-mobile'] = profile.sec_ch_ua_mobile
        if profile.sec_ch_ua_platform:
            headers['sec-ch-ua-platform'] = profile.sec_ch_ua_platform
        
        # Platform-specific headers
        if platform_hint:
            platform_headers = self._get_platform_headers(platform_hint)
            headers.update(platform_headers)
        
        # Additional profile headers
        headers.update(profile.extra_http_headers)
        
        return headers

    def _get_platform_headers(self, platform: str) -> Dict[str, str]:
        """Get platform-specific headers"""
        platform_headers = {
            'ticketmaster': {
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-dest': 'document',
                'Cache-Control': 'max-age=0'
            },
            'fansale': {
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1'
            },
            'vivaticket': {
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'navigate'
            }
        }
        
        return platform_headers.get(platform.lower(), {})

    def _detect_browser_type(self, user_agent: str) -> str:
        """Detect browser type from user agent"""
        ua_lower = user_agent.lower()
        if 'chrome' in ua_lower and 'edg' not in ua_lower:
            return 'chrome'
        elif 'firefox' in ua_lower:
            return 'firefox'
        elif 'safari' in ua_lower and 'chrome' not in ua_lower:
            return 'safari'
        elif 'edg' in ua_lower:
            return 'edge'
        return 'chrome'  # Default

    async def _request_hook(self, request: httpx.Request):
        """Hook called before sending request"""
        client_key = getattr(request, '_client_key', 'unknown')
        metrics = self.pool_metrics[client_key]
        metrics.total_requests += 1
        
        # Add timing
        request._start_time = time.time()

    async def _response_hook(self, response: httpx.Response):
        """Hook called after receiving response"""
        client_key = getattr(response.request, '_client_key', 'unknown')
        metrics = self.pool_metrics[client_key]
        
        # Update metrics
        if response.is_success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        # Update response time
        if hasattr(response.request, '_start_time'):
            response_time = time.time() - response.request._start_time
            if metrics.avg_response_time == 0:
                metrics.avg_response_time = response_time
            else:
                metrics.avg_response_time = (metrics.avg_response_time * 0.9) + (response_time * 0.1)

    async def _remove_pool(self, client_key: str):
        """Safely remove a connection pool"""
        try:
            client = self.pools.pop(client_key, None)
            if client and not client.is_closed:
                await client.aclose()
            
            self.pool_metrics.pop(client_key, None)
            self.pool_health.pop(client_key, None)
            
        except Exception as e:
            logger.error(f"Error removing pool {client_key}: {e}")

    async def record_request_result(self, profile_id: str, success: bool, response_time: float):
        """Record request result for monitoring"""
        # Find client key for profile
        client_key = None
        for key in self.pools.keys():
            if profile_id in key:
                client_key = key
                break
        
        if client_key:
            metrics = self.pool_metrics[client_key]
            if success:
                metrics.successful_requests += 1
            else:
                metrics.failed_requests += 1
            
            # Update health score
            success_rate = metrics.success_rate
            self.pool_health[client_key] = min(100, success_rate * 100 + 10)

    async def get_pool_statistics(self) -> Dict[str, Any]:
        """Get comprehensive pool statistics"""
        async with self._pool_lock:
            stats = {
                'active_pools': len(self.pools),
                'total_requests': sum(m.total_requests for m in self.pool_metrics.values()),
                'success_rate': 0.0,
                'avg_response_time': 0.0,
                'pool_health': dict(self.pool_health),
                'unhealthy_pools': len([h for h in self.pool_health.values() if h < 50])
            }
            
            if self.pool_metrics:
                total_requests = stats['total_requests']
                total_successes = sum(m.successful_requests for m in self.pool_metrics.values())
                total_response_time = sum(m.avg_response_time for m in self.pool_metrics.values())
                
                stats['success_rate'] = total_successes / max(total_requests, 1)
                stats['avg_response_time'] = total_response_time / len(self.pool_metrics)
            
            return stats

    async def close_all(self):
        """Gracefully close all connections"""
        await self.stop_health_monitoring()
        
        async with self._pool_lock:
            logger.info(f"Closing {len(self.pools)} HTTP connection pools")
            
            close_tasks = []
            for client_key, client in self.pools.items():
                if not client.is_closed:
                    task = asyncio.create_task(client.aclose())
                    close_tasks.append(task)
            
            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)
            
            self.pools.clear()
            self.pool_metrics.clear()
            self.pool_health.clear()
            
            logger.info("All HTTP connection pools closed")


class IntelligentResponseCache:
    """Advanced response cache with intelligent caching strategies"""

    def __init__(self, max_size_mb: float = 100):
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.current_size_bytes = 0
        
        # Multi-tier cache storage
        self.cache: Dict[str, CacheEntry] = {}
        self.hot_cache: Dict[str, CacheEntry] = {}  # Frequently accessed
        self.lru_order: deque = deque()
        
        # Cache analytics
        self.hit_count = 0
        self.miss_count = 0
        self.eviction_count = 0
        
        # Cache policies
        self.hot_cache_threshold = 5  # Hits needed to be "hot"
        self.max_hot_entries = 100
        self.compression_enabled = True
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cache_lock = asyncio.RLock()
        
        logger.info(f"IntelligentResponseCache initialized: {max_size_mb}MB capacity")

    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def stop_background_tasks(self):
        """Stop background tasks"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _periodic_cleanup(self):
        """Periodic cache cleanup and optimization"""
        while True:
            try:
                await asyncio.sleep(300)  # 5 minutes
                await self._optimize_cache()
                await self._update_hot_cache()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")

    async def _optimize_cache(self):
        """Optimize cache by removing stale entries"""
        async with self._cache_lock:
            current_time = datetime.now()
            stale_keys = []
            
            # Find stale entries (older than 1 hour)
            for key, entry in self.cache.items():
                if entry.age_seconds > 3600:
                    stale_keys.append(key)
            
            # Remove stale entries
            for key in stale_keys:
                await self._remove_entry(key)
            
            if stale_keys:
                logger.debug(f"Removed {len(stale_keys)} stale cache entries")

    async def _update_hot_cache(self):
        """Update hot cache with frequently accessed items"""
        async with self._cache_lock:
            # Find hot entries
            hot_candidates = [
                (key, entry) for key, entry in self.cache.items()
                if entry.hits >= self.hot_cache_threshold
            ]
            
            # Sort by hits and recency
            hot_candidates.sort(key=lambda x: (x[1].hits, -x[1].age_seconds), reverse=True)
            
            # Update hot cache
            self.hot_cache.clear()
            for key, entry in hot_candidates[:self.max_hot_entries]:
                self.hot_cache[key] = entry

    def _generate_cache_key(self, url: str, headers: Optional[Dict[str, str]] = None) -> str:
        """Generate cache key with header fingerprinting"""
        key_parts = [url]
        
        if headers:
            # Include relevant headers that affect response
            relevant_headers = ['Accept', 'Accept-Language', 'User-Agent']
            for header in relevant_headers:
                if header in headers:
                    key_parts.append(f"{header}:{headers[header]}")
        
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def get(self, url: str, 
                 headers: Optional[Dict[str, str]] = None,
                 max_age_seconds: int = 300) -> Optional[bytes]:
        """Get cached response with intelligent retrieval"""
        
        async with self._cache_lock:
            key = self._generate_cache_key(url, headers)
            
            # Check hot cache first
            entry = self.hot_cache.get(key)
            if not entry:
                entry = self.cache.get(key)
            
            if entry:
                # Check if still valid
                if entry.age_seconds <= max_age_seconds:
                    entry.hits += 1
                    self.hit_count += 1
                    
                    # Update LRU order
                    if key in self.lru_order:
                        self.lru_order.remove(key)
                    self.lru_order.append(key)
                    
                    logger.debug(f"Cache hit: {url} (age: {entry.age_seconds:.1f}s, hits: {entry.hits})")
                    return entry.data
                else:
                    # Expired entry
                    await self._remove_entry(key)
            
            self.miss_count += 1
            logger.debug(f"Cache miss: {url}")
            return None

    async def put(self, url: str, content: bytes,
                 headers: Optional[Dict[str, str]] = None,
                 response_headers: Optional[Dict[str, str]] = None) -> bool:
        """Store response in cache with intelligent policies"""
        
        if not content:
            return False
        
        async with self._cache_lock:
            key = self._generate_cache_key(url, headers)
            content_size = len(content)
            
            # Check if we need to make space
            while (self.current_size_bytes + content_size) > self.max_size_bytes and self.cache:
                await self._evict_lru_entry()
            
            # Don't cache if too large
            if content_size > self.max_size_bytes * 0.1:  # Max 10% of cache
                logger.debug(f"Skipping cache: too large ({content_size / 1024:.1f}KB)")
                return False
            
            # Create cache entry
            entry = CacheEntry(
                data=content,
                timestamp=datetime.now(),
                response_headers=response_headers or {},
                content_type=self._extract_content_type(response_headers),
                etag=response_headers.get('etag') if response_headers else None,
                last_modified=response_headers.get('last-modified') if response_headers else None
            )
            
            # Store in cache
            old_entry = self.cache.get(key)
            if old_entry:
                self.current_size_bytes -= old_entry.size_bytes
            
            self.cache[key] = entry
            self.current_size_bytes += content_size
            
            # Update LRU order
            if key in self.lru_order:
                self.lru_order.remove(key)
            self.lru_order.append(key)
            
            logger.debug(f"Cached: {url} ({content_size / 1024:.1f}KB)")
            return True

    def _extract_content_type(self, headers: Optional[Dict[str, str]]) -> str:
        """Extract content type from headers"""
        if not headers:
            return 'unknown'
        
        content_type = headers.get('content-type', 'unknown')
        return content_type.split(';')[0].strip()

    async def _evict_lru_entry(self):
        """Evict least recently used entry"""
        if not self.lru_order:
            return
        
        lru_key = self.lru_order.popleft()
        await self._remove_entry(lru_key)
        self.eviction_count += 1

    async def _remove_entry(self, key: str):
        """Remove entry from all caches"""
        entry = self.cache.pop(key, None)
        if entry:
            self.current_size_bytes -= entry.size_bytes
        
        self.hot_cache.pop(key, None)
        
        if key in self.lru_order:
            self.lru_order.remove(key)

    async def clear_old_entries(self, max_age_seconds: int) -> int:
        """Clear entries older than specified age"""
        async with self._cache_lock:
            current_time = datetime.now()
            old_keys = []
            
            for key, entry in self.cache.items():
                if entry.age_seconds > max_age_seconds:
                    old_keys.append(key)
            
            for key in old_keys:
                await self._remove_entry(key)
            
            return len(old_keys)

    async def clear_cache(self):
        """Clear entire cache"""
        async with self._cache_lock:
            self.cache.clear()
            self.hot_cache.clear()
            self.lru_order.clear()
            self.current_size_bytes = 0
            self.hit_count = 0
            self.miss_count = 0
            self.eviction_count = 0
            
            logger.info("Cache cleared")

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total_requests = self.hit_count + self.miss_count
        return self.hit_count / max(total_requests, 1)

    @property
    def current_size_mb(self) -> float:
        """Get current cache size in MB"""
        return self.current_size_bytes / (1024 * 1024)

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return {
            'size_mb': self.current_size_mb,
            'max_size_mb': self.max_size_bytes / (1024 * 1024),
            'entries': len(self.cache),
            'hot_entries': len(self.hot_cache),
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': self.hit_rate,
            'eviction_count': self.eviction_count,
            'utilization': self.current_size_bytes / self.max_size_bytes
        }


class UltraSmartBrowserContextManager:
    """Ultra-advanced browser context manager with comprehensive stealth"""

    def __init__(self,
                 playwright: Playwright,
                 profile_manager: ProfileManager,
                 data_tracker: DataUsageTracker,
                 config: Dict[str, Any]):
        
        self.playwright = playwright
        self.profile_manager = profile_manager
        self.data_tracker = data_tracker
        self.config = config
        
        # Context management
        self.contexts: Dict[str, PlaywrightContext] = {}
        self.context_locks: Dict[str, asyncio.Lock] = {}
        self.context_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Browser pools
        self.browsers: Dict[str, Browser] = {}
        self.browser_usage: Dict[str, int] = defaultdict(int)
        
        # Configuration
        browser_config = self.config.get('browser_options', {})
        self.context_ttl_minutes = browser_config.get('context_ttl_minutes', 30)
        self.max_contexts_per_browser = browser_config.get('max_contexts_per_browser', 10)
        self.browser_max_age_seconds = browser_config.get('browser_max_age_seconds', 1800)
        
        # Stealth configuration
        self.stealth_script_path = Path(self.config.get('paths', {}).get('stealth_script', "src/core/stealth_init.js"))
        self.enable_stealth_mode = True
        
        # Resource optimization
        self.resource_optimization = True
        self.blocked_resource_count = 0
        self.total_request_count = 0
        
        # Background tasks
        self._maintenance_task: Optional[asyncio.Task] = None
        self._pool_lock = asyncio.RLock()
        self._shutdown_event = asyncio.Event()
        
        logger.info(f"UltraSmartBrowserContextManager initialized - Stealth: {self.stealth_script_path.exists()}")

    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        if not self._maintenance_task:
            self._maintenance_task = asyncio.create_task(self._maintenance_loop())

    async def stop_background_tasks(self):
        """Stop background tasks"""
        self._shutdown_event.set()
        if self._maintenance_task:
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass

    async def _maintenance_loop(self):
        """Background maintenance for contexts and browsers"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._cleanup_stale_contexts()
                await self._optimize_browser_pool()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Context maintenance error: {e}")

    async def _cleanup_stale_contexts(self):
        """Clean up stale browser contexts"""
        async with self._pool_lock:
            current_time = datetime.now()
            stale_keys = []
            
            for context_key, metadata in self.context_metadata.items():
                age_minutes = (current_time - metadata['created_at']).total_seconds() / 60
                if age_minutes > self.context_ttl_minutes:
                    stale_keys.append(context_key)
            
            for key in stale_keys:
                await self._close_context(key)
                logger.debug(f"Cleaned up stale context: {key}")

    async def _optimize_browser_pool(self):
        """Optimize browser pool by closing underused browsers"""
        async with self._pool_lock:
            for browser_key, browser in list(self.browsers.items()):
                try:
                    if not browser.is_connected():
                        logger.warning(f"Removing disconnected browser: {browser_key}")
                        self.browsers.pop(browser_key, None)
                        self.browser_usage.pop(browser_key, None)
                        continue
                    
                    # Check if browser is underused
                    usage_count = self.browser_usage[browser_key]
                    contexts_using_browser = sum(
                        1 for metadata in self.context_metadata.values()
                        if metadata.get('browser_key') == browser_key
                    )
                    
                    # Close browser if no active contexts and low usage
                    if contexts_using_browser == 0 and usage_count < 5:
                        logger.debug(f"Closing underused browser: {browser_key}")
                        await browser.close()
                        self.browsers.pop(browser_key, None)
                        self.browser_usage.pop(browser_key, None)
                        
                except Exception as e:
                    logger.error(f"Error optimizing browser {browser_key}: {e}")

    async def get_context(self, profile: BrowserProfile) -> PlaywrightContext:
        """Get optimized browser context with full stealth capabilities"""
        
        profile_lock = self.context_locks.setdefault(profile.profile_id, asyncio.Lock())
        
        async with profile_lock:
            # Check for existing valid context
            if profile.profile_id in self.contexts:
                context = self.contexts[profile.profile_id]
                if await self._is_context_valid(context):
                    metadata = self.context_metadata[profile.profile_id]
                    metadata['last_used'] = datetime.now()
                    logger.debug(f"Reusing context for profile {profile.profile_id}")
                    return context
                else:
                    logger.info(f"Invalid context for profile {profile.profile_id}, recreating")
                    await self._close_context(profile.profile_id)
            
            # Create new context
            logger.info(f"Creating new context for profile {profile.profile_id} ({profile.name})")
            new_context = await self._create_advanced_context(profile)
            
            self.contexts[profile.profile_id] = new_context
            self.context_metadata[profile.profile_id] = {
                'created_at': datetime.now(),
                'last_used': datetime.now(),
                'profile_id': profile.profile_id,
                'browser_key': self._get_browser_key(profile),
                'stealth_enabled': True
            }
            
            return new_context

    async def _is_context_valid(self, context: PlaywrightContext) -> bool:
        """Comprehensive context validity check"""
        try:
            # Check browser connection
            if not context.browser or not context.browser.is_connected():
                return False
            
            # Check if we can access context properties
            pages = context.pages
            if pages is None:
                return False
            
            # Try a simple operation
            await context.new_page()
            test_page = context.pages[-1]
            await test_page.close()
            
            return True
            
        except Exception as e:
            logger.debug(f"Context validity check failed: {e}")
            return False

    def _get_browser_key(self, profile: BrowserProfile) -> str:
        """Get browser key for profile"""
        ua_lower = profile.user_agent.lower()
        
        if 'firefox' in ua_lower:
            return 'firefox'
        elif 'webkit' in ua_lower and 'chrome' not in ua_lower:
            return 'webkit'
        elif 'edg' in ua_lower:
            return 'msedge'
        else:
            return 'chromium'

    async def _create_advanced_context(self, profile: BrowserProfile) -> PlaywrightContext:
        """Create browser context with maximum stealth and optimization"""
        
        browser_key = self._get_browser_key(profile)
        
        # Get or create browser
        browser = await self._get_or_create_browser(browser_key, profile)
        
        # Build context parameters
        context_params = self._build_context_params(profile)
        
        # Create context
        context = await browser.new_context(**context_params)
        
        # Apply stealth enhancements
        if self.enable_stealth_mode:
            await self._apply_stealth_enhancements(context, profile)
        
        # Setup resource optimization
        if self.resource_optimization and profile.data_optimization_level != DataOptimizationLevel.OFF:
            await self._setup_resource_optimization(context, profile)
        
        # Track browser usage
        self.browser_usage[browser_key] += 1
        
        logger.info(f"Created advanced context for {profile.profile_id} (Browser: {browser_key})")
        return context

    async def _get_or_create_browser(self, browser_key: str, profile: BrowserProfile) -> Browser:
        """Get or create browser instance"""
        
        async with self._pool_lock:
            # Return existing browser if valid
            if browser_key in self.browsers:
                browser = self.browsers[browser_key]
                if browser.is_connected():
                    return browser
                else:
                    logger.warning(f"Browser {browser_key} disconnected, creating new one")
                    self.browsers.pop(browser_key, None)
            
            # Create new browser
            logger.info(f"Creating new {browser_key} browser")
            
            browser_launcher = getattr(self.playwright, browser_key)
            launch_options = self._get_launch_options(profile, browser_key)
            
            browser = await browser_launcher.launch(**launch_options)
            self.browsers[browser_key] = browser
            
            return browser

    def _build_context_params(self, profile: BrowserProfile) -> Dict[str, Any]:
        """Build comprehensive context parameters"""
        
        params = profile.get_context_params()
        
        # Enhanced viewport simulation
        params.update({
            'viewport': {
                'width': profile.viewport_width,
                'height': profile.viewport_height
            },
            'screen': {
                'width': profile.screen_width,
                'height': profile.screen_height
            },
            'device_scale_factor': profile.device_pixel_ratio,
            'is_mobile': 'mobile' in profile.user_agent.lower(),
            'has_touch': 'mobile' in profile.user_agent.lower(),
            'user_agent': profile.user_agent,
            'locale': profile.locale,
            'timezone_id': profile.timezone,
            'color_scheme': 'light',
            'reduced_motion': 'no-preference',
            'forced_colors': 'none'
        })
        
        # Enhanced permissions
        params['permissions'] = ['geolocation']
        params['geolocation'] = {'latitude': 41.9028, 'longitude': 12.4964}  # Rome
        
        # HTTP credentials
        if profile.proxy_config and profile.proxy_config.username:
            params['http_credentials'] = {
                'username': profile.proxy_config.username,
                'password': profile.proxy_config.password or ''
            }
        
        # Offline simulation
        params['offline'] = False
        
        # Java and Flash disabled for security
        params['java_script_enabled'] = True
        params['accept_downloads'] = True
        
        return params

    def _get_launch_options(self, profile: BrowserProfile, browser_key: str) -> Dict[str, Any]:
        """Get optimized browser launch options"""
        
        base_options = profile.get_launch_options()
        
        # Browser-specific optimizations
        if browser_key == 'chromium':
            base_options['args'].extend([
                # Enhanced stealth arguments
                '--disable-features=VizDisplayCompositor',
                '--disable-features=AudioServiceOutOfProcess', 
                '--disable-default-apps',
                '--disable-extensions',
                '--disable-component-updates',
                '--disable-background-networking',
                '--disable-sync',
                '--metrics-recording-only',
                '--no-report-upload',
                '--no-crash-upload',
                
                # Performance optimizations
                '--aggressive-cache-discard',
                '--enable-aggressive-domstorage-flushing',
                '--enable-features=VaapiVideoDecoder',
                '--use-gl=swiftshader',  # Software rendering for consistency
                
                # Additional stealth
                '--disable-blink-features=AutomationControlled',
                '--disable-features=UserAgentClientHint',
                '--disable-ipc-flooding-protection'
            ])
        
        elif browser_key == 'firefox':
            # Firefox-specific arguments
            base_options.setdefault('firefox_user_prefs', {}).update({
                'dom.webdriver.enabled': False,
                'useAutomationExtension': False,
                'general.platform.override': profile.js_platform,
                'general.useragent.override': profile.user_agent,
                'geo.enabled': True,
                'geo.wifi.uri': 'data:application/json,{"location": {"lat": 41.9028, "lng": 12.4964}, "accuracy": 100.0}'
            })
        
        # Common options
        base_options.update({
            'headless': self.config.get('browser_options', {}).get('headless', True),
            'slow_mo': 0,  # No artificial delays
            'timeout': 60000,
            'handle_sigint': False,
            'handle_sigterm': False,
            'handle_sighup': False
        })
        
        return base_options

    async def _apply_stealth_enhancements(self, context: PlaywrightContext, profile: BrowserProfile):
        """Apply comprehensive stealth enhancements"""
        
        # Load and execute stealth script
        if self.stealth_script_path.exists():
            try:
                stealth_content = await self._load_stealth_script(profile)
                await context.add_init_script(stealth_content)
                logger.debug(f"Applied stealth script for {profile.profile_id}")
                
            except Exception as e:
                logger.error(f"Failed to apply stealth script: {e}")
        
        # Additional context-level stealth
        await self._apply_context_stealth(context, profile)

    async def _load_stealth_script(self, profile: BrowserProfile) -> str:
        """Load and customize stealth script for profile"""
        
        async with aiofiles.open(self.stealth_script_path, 'r', encoding='utf-8') as f:
            stealth_content = await f.read()
        
        # Prepare profile data for injection
        if hasattr(profile, 'get_stealth_init_js_profile_data'):
            js_data = profile.get_stealth_init_js_profile_data()
        else:
            # Fallback profile data
            js_data = {
                'name': profile.name,
                'user_agent': profile.user_agent,
                'viewport_width': profile.viewport_width,
                'viewport_height': profile.viewport_height,
                'screen_width': profile.screen_width,
                'screen_height': profile.screen_height,
                'timezone': profile.timezone,
                'locale': profile.locale,
                'extra_js_props': profile.extra_js_props
            }
        
        # Inject profile data
        profile_injection = f"window.__fingerprint_profile__ = {json.dumps(js_data, default=str)};\n"
        
        return profile_injection + stealth_content

    async def _apply_context_stealth(self, context: PlaywrightContext, profile: BrowserProfile):
        """Apply additional context-level stealth measures"""
        
        # Override navigator.webdriver
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
        """)
        
        # Override permissions API
        await context.add_init_script(f"""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({{ state: Notification.permission }}) :
                    originalQuery(parameters)
            );
        """)
        
        # Set realistic language preferences
        await context.add_init_script(f"""
            Object.defineProperty(navigator, 'languages', {{
                get: () => {json.dumps(profile.languages_override)}
            }});
        """)

    async def _setup_resource_optimization(self, context: PlaywrightContext, profile: BrowserProfile):
        """Setup intelligent resource blocking and optimization"""
        
        block_patterns = profile.get_resource_block_patterns()
        resource_types_to_block = getattr(profile, 'block_resources', set())
        
        async def handle_route(route: Route):
            request = route.request
            url = request.url
            resource_type = request.resource_type
            
            # Track total requests
            self.total_request_count += 1
            
            # Determine if should block
            should_block = False
            
            # Block by resource type
            if resource_type in resource_types_to_block:
                should_block = True
            
            # Block by pattern matching
            elif any(self._pattern_matches(pattern, url) for pattern in block_patterns):
                should_block = True
            
            # Block obvious tracking and advertising
            elif any(tracker in url.lower() for tracker in [
                'google-analytics', 'googletagmanager', 'facebook.com/tr',
                'doubleclick', 'adsystem', 'googlesyndication'
            ]):
                should_block = True
            
            if should_block:
                self.blocked_resource_count += 1
                self.data_tracker.blocked_resources_saved_mb += 0.05  # Estimate
                
                try:
                    await route.abort()
                    logger.debug(f"Blocked: {url} ({resource_type})")
                except Exception as e:
                    logger.debug(f"Could not block {url}: {e}")
            else:
                try:
                    await route.continue_()
                except Exception as e:
                    logger.debug(f"Could not continue {url}: {e}")
        
        try:
            await context.route("**/*", handle_route)
            optimization_level = profile.data_optimization_level.value
            logger.info(f"Resource optimization enabled for {profile.profile_id} (Level: {optimization_level})")
            
        except Exception as e:
            logger.error(f"Failed to setup resource optimization: {e}")

    def _pattern_matches(self, pattern: str, url: str) -> bool:
        """Check if URL matches blocking pattern"""
        if pattern.startswith("*") and pattern.endswith("*"):
            return pattern[1:-1] in url
        elif pattern.startswith("*"):
            return url.endswith(pattern[1:])
        elif pattern.endswith("*"):
            return url.startswith(pattern[:-1])
        else:
            return pattern == url

    async def _close_context(self, context_key: str):
        """Safely close browser context"""
        
        context = self.contexts.pop(context_key, None)
        self.context_locks.pop(context_key, None)
        self.context_metadata.pop(context_key, None)
        
        if context:
            try:
                # Close all pages first
                for page in context.pages:
                    await page.close()
                
                # Close context
                await context.close()
                logger.debug(f"Successfully closed context: {context_key}")
                
            except Exception as e:
                logger.error(f"Error closing context {context_key}: {e}")

    async def get_context_statistics(self) -> Dict[str, Any]:
        """Get comprehensive context statistics"""
        async with self._pool_lock:
            stats = {
                'active_contexts': len(self.contexts),
                'active_browsers': len(self.browsers),
                'total_requests': self.total_request_count,
                'blocked_requests': self.blocked_resource_count,
                'block_rate': self.blocked_resource_count / max(self.total_request_count, 1),
                'data_saved_mb': self.data_tracker.blocked_resources_saved_mb,
                'browser_usage': dict(self.browser_usage),
                'contexts_by_browser': defaultdict(int)
            }
            
            # Count contexts per browser
            for metadata in self.context_metadata.values():
                browser_key = metadata.get('browser_key', 'unknown')
                stats['contexts_by_browser'][browser_key] += 1
            
            return stats

    async def close_all(self):
        """Gracefully close all contexts and browsers"""
        await self.stop_background_tasks()
        
        async with self._pool_lock:
            logger.info("Closing all browser contexts and browsers...")
            
            # Close all contexts
            context_keys = list(self.contexts.keys())
            for context_key in context_keys:
                await self._close_context(context_key)
            
            # Close all browsers
            browser_keys = list(self.browsers.keys())
            for browser_key in browser_keys:
                browser = self.browsers.pop(browser_key, None)
                if browser and browser.is_connected():
                    try:
                        logger.info(f"Closing browser: {browser_key}")
                        await browser.close()
                    except Exception as e:
                        logger.error(f"Error closing browser {browser_key}: {e}")
            
            self.browser_usage.clear()
            logger.info("All browser resources closed")


# Aliases for backward compatibility
ConnectionPoolManager = AdvancedConnectionPoolManager
ResponseCache = IntelligentResponseCache
SmartBrowserContextManager = UltraSmartBrowserContextManager