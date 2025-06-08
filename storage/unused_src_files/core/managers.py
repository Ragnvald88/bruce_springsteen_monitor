# src/core/managers.py - FIXED VERSION
"""
StealthMaster AI Enhanced Connection Pool Manager
Ultra-stealth HTTP client management with advanced proxy rotation and fingerprinting
"""

import asyncio
import httpx
import random
import time
from typing import Dict, Optional, Any, List, Tuple, Union, Set
from dataclasses import dataclass, field
import ssl
import h2.connection
import h2.config
import logging
import certifi
import os
from contextlib import asynccontextmanager
from loguru import logger

# Profile imports
from ..profiles.models import BrowserProfile
# TLS fingerprinting now handled by stealth_engine.py
# from ..utils.tls_fingerprint import TLSFingerprint  # Deprecated - use stealth_engine.py

logger = logging.getLogger(__name__)

@dataclass
class ProxyConfig:
    """Enhanced proxy configuration with stealth features"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    
    def to_httpx_proxy(self) -> str:
        """Convert to httpx-compatible proxy URL format"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"


# StealthSSLContext moved to storage - superseded by stealth_engine.py TLS handling
# Advanced TLS fingerprinting is now handled by stealth_engine.py's create_tls_session()


class ConnectionPoolManager:
    """
    StealthMaster AI Enhanced Connection Pool Manager - INTEGRATED WITH STEALTH_ENGINE
    
    Features:
    - Proper httpx proxy configuration
    - Integration with stealth_engine.py for advanced TLS fingerprinting
    - Connection persistence and pooling
    - Adaptive timeout management
    - Stealth header rotation via stealth_integration
    - Pre-warming and performance optimization
    """
    
    def __init__(self, config: Dict[str, Any], profile_manager=None):
        self.config = config
        self.profile_manager = profile_manager
        self.pools: Dict[str, httpx.AsyncClient] = {}
        self.pool_lock = asyncio.Lock()
        
        # Connection limits from config (optimized defaults)
        self.max_connections = config.get('max_connections_per_host', 20)  # Increased
        self.max_keepalive = config.get('max_keepalive_connections', 10)   # Increased
        
        # Optimized timeouts
        self.base_connect_timeout = config.get('connect_timeout_seconds', 10)  # Reduced
        self.base_read_timeout = config.get('read_timeout_seconds', 15)        # Reduced
        
        # HTTP/2 configuration
        self.http2_enabled = config.get('http2_enabled', True)
        
        # Connection health tracking
        self.connection_health: Dict[str, float] = {}
        self.last_rotation: Dict[str, float] = {}
        
        # Performance optimization
        self.pre_warmed_pools: Set[str] = set()
        self.warm_up_tasks: Dict[str, asyncio.Task] = {}
        
        # Connection reuse optimization
        self.connection_reuse_count: Dict[str, int] = {}
        self.max_reuse_per_connection = config.get('max_reuse_per_connection', 100)
        
        logger.info(f"ConnectionPoolManager initialized with max_connections={self.max_connections}, "
                   f"max_keepalive={self.max_keepalive}")
    
    def _get_pool_key(self, profile: BrowserProfile, use_tls_fingerprint: bool = True) -> str:
        """Generate unique pool key for connection reuse"""
        proxy_key = ""
        if hasattr(profile, 'proxy_config') and profile.proxy_config:
            proxy = profile.proxy_config
            # Robust handling for any proxy config format
            host = None
            port = None

            if hasattr(proxy, 'host'):
                host = proxy.host
                port = proxy.port
            elif isinstance(proxy, dict):
                host = proxy.get('host')
                port = proxy.get('port')

            if host and port:
                proxy_key = f"{host}:{port}"

        tls_key = f"tls_{getattr(profile, 'tls_fingerprint', '')}" if use_tls_fingerprint and hasattr(profile, 'tls_fingerprint') else "default"
        profile_id = getattr(profile, 'id', getattr(profile, 'profile_id', 'unknown'))
        return f"{profile_id}_{proxy_key}_{tls_key}"
    
    def _create_stealth_headers(self, profile: BrowserProfile) -> Dict[str, str]:
        """Generate browser-like headers with controlled randomization"""
        # Base headers that all browsers send
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Add user agent from profile
        if hasattr(profile, 'user_agent') and profile.user_agent:
            headers['User-Agent'] = profile.user_agent
        else:
            # Fallback to recent Chrome
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        # Randomize sec-ch-ua headers for Chromium browsers
        if 'Chrome' in headers.get('User-Agent', ''):
            headers.update({
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
            })
        
        return headers
    
    async def pre_warm_connections(self, profiles: List[BrowserProfile], target_domains: List[str]):
        """Pre-warm connections for faster first requests."""
        logger.info(f"Pre-warming connections for {len(profiles)} profiles to {len(target_domains)} domains")
        
        warm_up_tasks = []
        for profile in profiles[:5]:  # Limit to avoid overwhelming
            for domain in target_domains:
                task = asyncio.create_task(self._warm_single_connection(profile, domain))
                warm_up_tasks.append(task)
        
        # Run warm-up tasks concurrently with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*warm_up_tasks, return_exceptions=True),
                timeout=10.0  # Maximum 10 seconds for warm-up
            )
            logger.info("Connection pre-warming completed")
        except asyncio.TimeoutError:
            logger.warning("Connection pre-warming timed out, proceeding anyway")
    
    async def _warm_single_connection(self, profile: BrowserProfile, domain: str):
        """Warm up a single connection."""
        try:
            client = await self.get_client(profile)
            # Make a minimal HEAD request to establish connection
            test_url = f"https://{domain.replace('https://', '').replace('http://', '')}"
            response = await client.head(test_url, timeout=3.0)
            
            pool_key = self._get_pool_key(profile)
            self.pre_warmed_pools.add(pool_key)
            
            logger.debug(f"Pre-warmed connection to {domain} via profile {getattr(profile, 'profile_id', 'unknown')}")
            
        except Exception as e:
            logger.debug(f"Pre-warm failed for {domain}: {str(e)[:50]}...")
    
    def _create_proxy_config(self, profile: BrowserProfile) -> Optional[Dict[str, Any]]:
        """Create httpx-compatible proxy configuration"""
        if not hasattr(profile, 'proxy_config') or not profile.proxy_config:
            return None

        proxy_data = profile.proxy_config

        # Extract values with multiple fallbacks
        protocol = None
        host = None
        port = None
        username = None
        password = None

        # Try object attributes first
        if hasattr(proxy_data, '__dict__'):
            # It's an object with attributes
            protocol = getattr(proxy_data, 'protocol', None) or getattr(proxy_data, 'proxy_type', None) or 'http'
            host = getattr(proxy_data, 'host', None)
            port = getattr(proxy_data, 'port', None)
            username = getattr(proxy_data, 'username', None)
            password = getattr(proxy_data, 'password', None)
        elif isinstance(proxy_data, dict):
            # It's a dictionary
            protocol = proxy_data.get('protocol') or proxy_data.get('proxy_type', 'http')
            host = proxy_data.get('host')
            port = proxy_data.get('port')
            username = proxy_data.get('username')
            password = proxy_data.get('password')
        else:
            logger.warning(f"Unknown proxy config type: {type(proxy_data)}")
            return None

        # Validate required fields
        if not host or not port:
            logger.warning(f"Invalid proxy config: missing host ({host}) or port ({port})")
            return None

        # Build proxy URL
        if username and password:
            proxy_url = f"{protocol}://{username}:{password}@{host}:{port}"
        else:
            proxy_url = f"{protocol}://{host}:{port}"

        logger.debug(f"Created proxy URL: {protocol}://{host}:{port} (auth: {bool(username and password)})")

        # httpx expects proxies in this format (string or dict)
        return proxy_url
    
    def _apply_timing_jitter(self, base_value: float) -> float:
        """Apply realistic timing jitter to avoid patterns"""
        jitter = random.uniform(0.8, 1.2)
        return base_value * jitter
    
    async def get_client(
        self, 
        profile: BrowserProfile, 
        use_tls_fingerprint: bool = True,
        force_new: bool = False,
        max_retries: int = 3
    ) -> httpx.AsyncClient:
        """
        Get or create an HTTP client with proper proxy and stealth configuration
        
        CRITICAL FIX: Properly configure httpx with proxies parameter
        """
        pool_key = self._get_pool_key(profile, use_tls_fingerprint)
        
        async with self.pool_lock:
            # Check if we need to rotate the connection
            if pool_key in self.pools and not force_new:
                last_rotation = self.last_rotation.get(pool_key, 0)
                if time.time() - last_rotation < 300:  # 5 minute rotation
                    return self.pools[pool_key]
                else:
                    # Close old client before creating new one
                    await self.pools[pool_key].aclose()
            
            # Create connection limits
            limits = httpx.Limits(
                max_keepalive_connections=self.max_keepalive,
                max_connections=self.max_connections,
                keepalive_expiry=30.0,
            )
            
            # Configure timeouts with jitter
            timeout = httpx.Timeout(
                connect=self._apply_timing_jitter(self.base_connect_timeout),
                read=self._apply_timing_jitter(self.base_read_timeout),
                write=10.0,
                pool=5.0,
            )
            
            # Create SSL context if using TLS fingerprinting
            ssl_context = None
            # TLS fingerprinting is now handled by stealth_engine.py, so ssl_context remains None
            
            # Get proxy configuration
            proxy_config = self._create_proxy_config(profile)
            
            # Create the client with all stealth features and retry logic
            for attempt in range(max_retries):
                try:
                    client_kwargs = {
                        'limits': limits,
                        'timeout': timeout,
                        'headers': self._create_stealth_headers(profile),
                        'http2': self.http2_enabled,
                        'verify': ssl_context if ssl_context else True,
                        'follow_redirects': True,
                        'max_redirects': 5,
                    }
                    
                    # Add proxy configuration if available
                    if proxy_config:
                        client_kwargs['proxy'] = proxy_config
                    
                    client = httpx.AsyncClient(**client_kwargs)
                    
                    # Store in pool on success
                    self.pools[pool_key] = client
                    self.last_rotation[pool_key] = time.time()
                    self.connection_health[pool_key] = 100.0
                    
                    logger.debug(f"Created new httpx client for profile {getattr(profile, 'profile_id', 'unknown')} "
                               f"(proxy: {bool(proxy_config)}, tls_fingerprint: {use_tls_fingerprint})")
                    
                    return client
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        wait_time = (2 ** attempt) * 0.1
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # Final attempt failed - return fallback client
                        logger.error(f"Failed to create httpx client after {max_retries} attempts for profile {getattr(profile, 'profile_id', 'unknown')}: {e}")
                        return httpx.AsyncClient(
                            limits=limits,
                            timeout=timeout,
                            headers=self._create_stealth_headers(profile),
                            http2=self.http2_enabled,
                        )
    
    async def release_client(self, profile: BrowserProfile, client: httpx.AsyncClient):
        """Release client back to pool (no-op for persistent connections)"""
        # Connections are persistent in the pool, so we just track health
        pool_key = self._get_pool_key(profile)
        if pool_key in self.connection_health:
            # Decay health slightly to encourage rotation
            self.connection_health[pool_key] *= 0.99
    
    async def mark_client_compromised(self, profile: BrowserProfile):
        """Mark a client as potentially detected"""
        pool_key = self._get_pool_key(profile)
        async with self.pool_lock:
            if pool_key in self.pools:
                logger.warning(f"Marking client for profile {getattr(profile, 'profile_id', 'unknown')} as compromised")
                await self.pools[pool_key].aclose()
                del self.pools[pool_key]
                if pool_key in self.connection_health:
                    del self.connection_health[pool_key]
                if pool_key in self.last_rotation:
                    del self.last_rotation[pool_key]
    
    async def close_all(self):
        """Gracefully close all connections"""
        async with self.pool_lock:
            for client in self.pools.values():
                try:
                    await client.aclose()
                except Exception as e:
                    logger.error(f"Error closing client: {e}")
            self.pools.clear()
            self.connection_health.clear()
            self.last_rotation.clear()
    
    async def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            'active_pools': len(self.pools),
            'total_connections': sum(1 for _ in self.pools.values()),
            'average_health': sum(self.connection_health.values()) / max(len(self.connection_health), 1),
            'pools': [
                {
                    'key': key,
                    'health': self.connection_health.get(key, 0),
                    'age': time.time() - self.last_rotation.get(key, time.time())
                }
                for key in self.pools.keys()
            ]
        }
    
    async def pre_warm(self, count: int = 5):
        """Pre-warm connection pools for faster startup"""
        logger.info(f"Pre-warming {count} connection pools for faster startup")
        
        try:
            # Get available profiles from profile manager
            if not self.profile_manager:
                logger.warning("No profile manager available for pre-warming")
                return
                
            # Get profiles to pre-warm
            profiles_to_warm = []
            if hasattr(self.profile_manager, 'get_profiles_for_platform'):
                # Try to get profiles for main platforms
                for platform in ['fansale', 'ticketmaster', 'vivaticket']:
                    try:
                        platform_profiles = await self.profile_manager.get_profiles_for_platform(platform, count=2)
                        profiles_to_warm.extend(platform_profiles[:2])
                    except Exception as e:
                        logger.debug(f"Failed to get profiles for {platform}: {e}")
                        
            elif hasattr(self.profile_manager, 'static_profiles') and self.profile_manager.static_profiles:
                # Fallback to static profiles
                profiles_to_warm = list(self.profile_manager.static_profiles.values())[:count]
                
            elif hasattr(self.profile_manager, 'dynamic_profiles') and self.profile_manager.dynamic_profiles:
                # Fallback to dynamic profiles  
                profiles_to_warm = self.profile_manager.dynamic_profiles[:count]
            
            if not profiles_to_warm:
                logger.warning("No profiles available for pre-warming")
                return
                
            # Pre-warm connections for each profile
            warm_up_tasks = []
            for profile in profiles_to_warm[:count]:
                task = asyncio.create_task(self._pre_warm_single_profile(profile))
                warm_up_tasks.append(task)
            
            # Run pre-warming with timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(*warm_up_tasks, return_exceptions=True),
                    timeout=10.0
                )
                logger.info(f"Pre-warming completed for {len(profiles_to_warm)} profiles")
            except asyncio.TimeoutError:
                logger.warning("Pre-warming timed out, proceeding anyway")
                
        except Exception as e:
            logger.error(f"Error during pre-warming: {e}")
    
    async def _pre_warm_single_profile(self, profile):
        """Pre-warm connections for a single profile"""
        try:
            # Create client (this establishes the connection pool)
            client = await self.get_client(profile, force_new=False)
            pool_key = self._get_pool_key(profile)
            self.pre_warmed_pools.add(pool_key)
            logger.debug(f"Pre-warmed connection pool for profile {getattr(profile, 'profile_id', getattr(profile, 'id', 'unknown'))}")
        except Exception as e:
            logger.debug(f"Failed to pre-warm profile: {e}")


class ResponseCache:
    """Response cache implementation"""
    
    def __init__(self, max_size_mb: int = 50):
        self.max_size_mb = max_size_mb
        self.cache: Dict[str, Any] = {}
        self.hit_count = 0
        self.miss_count = 0
        self.current_size_mb = 0.0
        
    async def get(self, url: str, max_age_seconds: int = 300) -> Optional[bytes]:
        """Get cached response if not expired"""
        cache_key = self._get_cache_key(url)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            age = time.time() - entry['timestamp']
            
            if age < max_age_seconds:
                self.hit_count += 1
                return entry['content']
            else:
                # Remove expired entry
                del self.cache[cache_key]
        
        self.miss_count += 1
        return None
    
    async def put(self, url: str, content: bytes, headers: Dict[str, str], response_headers: Dict[str, str]):
        """Store response in cache"""
        cache_key = self._get_cache_key(url)
        
        entry = {
            'content': content,
            'headers': headers,
            'response_headers': response_headers,
            'timestamp': time.time(),
            'size': len(content)
        }
        
        self.cache[cache_key] = entry
        self.current_size_mb += len(content) / (1024 * 1024)
        
        # Clean up if over limit
        if self.current_size_mb > self.max_size_mb:
            await self._cleanup_cache()
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL"""
        import hashlib
        return hashlib.sha256(url.encode()).hexdigest()[:16]
    
    async def _cleanup_cache(self):
        """Remove oldest entries to stay under size limit"""
        # Sort by timestamp and remove oldest
        sorted_items = sorted(
            self.cache.items(),
            key=lambda x: x[1]['timestamp']
        )
        
        while self.current_size_mb > self.max_size_mb * 0.8 and sorted_items:
            key, entry = sorted_items.pop(0)
            self.current_size_mb -= entry['size'] / (1024 * 1024)
            del self.cache[key]
    
    async def clear_old_entries(self, max_age_seconds: int = 1800) -> int:
        """Clear entries older than max_age_seconds"""
        now = time.time()
        to_remove = []
        
        for key, entry in self.cache.items():
            if now - entry['timestamp'] > max_age_seconds:
                to_remove.append(key)
        
        for key in to_remove:
            entry = self.cache[key]
            self.current_size_mb -= entry['size'] / (1024 * 1024)
            del self.cache[key]
        
        return len(to_remove)
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0


# SmartBrowserContextManager moved to storage/old/legacy_browser_context_manager.py
# Functionality superseded by stealth_engine.py integration


# Legacy classes moved to storage/old/legacy_browser_context_manager.py
# SmartBrowserContextManager and ConnectionPreWarmer functionality
# has been superseded by stealth_engine.py

# Modern browser context creation is now handled by:
# from src.core.stealth_integration import get_bruce_stealth_integration
# stealth_integration = get_bruce_stealth_integration()
# context = await stealth_integration.create_stealth_browser_context(browser, profile, platform)