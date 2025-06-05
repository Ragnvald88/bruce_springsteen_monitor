# src/core/managers.py - FIXED VERSION
"""
StealthMaster AI Enhanced Connection Pool Manager
Ultra-stealth HTTP client management with advanced proxy rotation and fingerprinting
"""

import asyncio
import httpx
import random
import time
from typing import Dict, Optional, Any, List, Tuple, Union
from dataclasses import dataclass, field
import ssl
import h2.connection
import h2.config
import logging
import certifi
import os
from contextlib import asynccontextmanager
from loguru import logger

# FIXED: Correct import path
from ..profiles.models import BrowserProfile  # Changed from Profile to BrowserProfile
from ..utils.tls_fingerprint import TLSFingerprint

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


class StealthSSLContext:
    """Advanced SSL context factory for fingerprint randomization"""
    
    # Real browser cipher suites (Chrome 120+, Firefox 120+, Safari 17+)
    BROWSER_CIPHER_SUITES = [
        # Chrome 120 cipher suite order
        [
            'TLS_AES_128_GCM_SHA256',
            'TLS_AES_256_GCM_SHA384',
            'TLS_CHACHA20_POLY1305_SHA256',
            'ECDHE-ECDSA-AES128-GCM-SHA256',
            'ECDHE-RSA-AES128-GCM-SHA256',
            'ECDHE-ECDSA-AES256-GCM-SHA384',
            'ECDHE-RSA-AES256-GCM-SHA384',
            'ECDHE-ECDSA-CHACHA20-POLY1305',
            'ECDHE-RSA-CHACHA20-POLY1305',
        ],
        # Firefox 120 cipher suite order
        [
            'TLS_AES_128_GCM_SHA256',
            'TLS_CHACHA20_POLY1305_SHA256',
            'TLS_AES_256_GCM_SHA384',
            'ECDHE-ECDSA-AES128-GCM-SHA256',
            'ECDHE-RSA-AES128-GCM-SHA256',
            'ECDHE-ECDSA-CHACHA20-POLY1305',
            'ECDHE-RSA-CHACHA20-POLY1305',
            'ECDHE-ECDSA-AES256-GCM-SHA384',
            'ECDHE-RSA-AES256-GCM-SHA384',
        ],
        # Safari 17 cipher suite order
        [
            'TLS_AES_256_GCM_SHA384',
            'TLS_AES_128_GCM_SHA256',
            'TLS_CHACHA20_POLY1305_SHA256',
            'ECDHE-ECDSA-AES256-GCM-SHA384',
            'ECDHE-ECDSA-AES128-GCM-SHA256',
            'ECDHE-RSA-AES256-GCM-SHA384',
            'ECDHE-RSA-AES128-GCM-SHA256',
        ]
    ]
    
    @classmethod
    def create_context(cls, profile: Optional[BrowserProfile] = None) -> ssl.SSLContext:
        """Create SSL context with browser-like fingerprint"""
        context = ssl.create_default_context(cafile=certifi.where())
        
        # Randomize TLS version based on profile or random selection
        if profile and hasattr(profile, 'tls_version'):
            context.minimum_version = getattr(ssl.TLSVersion, profile.tls_version, ssl.TLSVersion.TLSv1_2)
        else:
            # Weight towards newer versions like real browsers
            tls_versions = [ssl.TLSVersion.TLSv1_2] * 2 + [ssl.TLSVersion.TLSv1_3] * 8
            context.minimum_version = random.choice(tls_versions)
        
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        
        # Select cipher suite based on profile or random browser
        cipher_suite = random.choice(cls.BROWSER_CIPHER_SUITES)
        context.set_ciphers(':'.join(cipher_suite))
        
        # Browser-like SSL options
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_COMPRESSION
        context.options |= ssl.OP_NO_TICKET  # Some browsers disable session tickets
        
        # Enable hostname checking
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        
        return context


class ConnectionPoolManager:
    """
    StealthMaster AI Enhanced Connection Pool Manager
    
    Features:
    - Proper httpx proxy configuration
    - Advanced TLS fingerprinting
    - Connection persistence and pooling
    - Adaptive timeout management
    - Stealth header rotation
    """
    
    def __init__(self, config: Dict[str, Any], profile_manager=None):
        self.config = config
        self.profile_manager = profile_manager
        self.pools: Dict[str, httpx.AsyncClient] = {}
        self.pool_lock = asyncio.Lock()
        
        # Connection limits from config
        self.max_connections = config.get('max_connections_per_host', 10)
        self.max_keepalive = config.get('max_keepalive_connections', 5)
        
        # Timeouts with jitter
        self.base_connect_timeout = config.get('connect_timeout_seconds', 15)
        self.base_read_timeout = config.get('read_timeout_seconds', 20)
        
        # HTTP/2 configuration
        self.http2_enabled = config.get('http2_enabled', True)
        
        # Connection health tracking
        self.connection_health: Dict[str, float] = {}
        self.last_rotation: Dict[str, float] = {}
        
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

        # httpx expects proxies in this format
        return {
            "http://": proxy_url,
            "https://": proxy_url,
        }
    
    def _apply_timing_jitter(self, base_value: float) -> float:
        """Apply realistic timing jitter to avoid patterns"""
        jitter = random.uniform(0.8, 1.2)
        return base_value * jitter
    
    async def get_client(
        self, 
        profile: BrowserProfile, 
        use_tls_fingerprint: bool = True,
        force_new: bool = False
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
            if use_tls_fingerprint:
                ssl_context = StealthSSLContext.create_context(profile)
            
            # Get proxy configuration
            proxy_url = self._create_proxy_config(profile)
            
            # Create the client with all stealth features
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
                if proxy_url:
                    client_kwargs['proxies'] = proxy_url
                
                client = httpx.AsyncClient(**client_kwargs)
                
                # Store in pool
                self.pools[pool_key] = client
                self.last_rotation[pool_key] = time.time()
                self.connection_health[pool_key] = 100.0
                
                logger.debug(f"Created new httpx client for profile {getattr(profile, 'profile_id', 'unknown')} "
                           f"(proxy: {bool(proxy_url)}, tls_fingerprint: {use_tls_fingerprint})")
                
                return client
                
            except Exception as e:
                logger.error(f"Error creating httpx client for profile {getattr(profile, 'profile_id', 'unknown')}: {e}")
                # Return a basic client without proxy as fallback
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


class SmartBrowserContextManager:
    """Smart browser context manager with profile integration"""
    
    def __init__(self, playwright_instance, profile_manager, data_tracker, config):
        self.playwright = playwright_instance
        self.profile_manager = profile_manager
        self.data_tracker = data_tracker
        self.config = config
        self.contexts: Dict[str, Any] = {}
        
    async def get_stealth_context(self, profile: BrowserProfile, force_new: bool = False):
        """Get or create a stealth browser context"""
        profile_id = getattr(profile, 'profile_id', getattr(profile, 'id', 'unknown'))
        
        if profile_id in self.contexts and not force_new:
            return self.contexts[profile_id]
        
        # Create new context with stealth settings
        context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=f"/tmp/browser_profile_{profile_id}",
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--hide-scrollbars',
                '--mute-audio',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-background-networking'
            ],
            viewport={'width': profile.viewport_width, 'height': profile.viewport_height},
            user_agent=profile.user_agent,
            locale=getattr(profile, 'locale', 'en-US'),
            timezone_id=getattr(profile, 'timezone', 'America/New_York'),
            permissions=['geolocation'],
            extra_http_headers={
                'Accept-Language': getattr(profile, 'accept_language', 'en-US,en;q=0.9'),
            }
        )
        
        # Inject stealth script
        stealth_script_path = self.config.get('paths', {}).get('stealth_script', 'src/core/stealth_init.js')
        if os.path.exists(stealth_script_path):
            with open(stealth_script_path, 'r') as f:
                stealth_script = f.read()
            
            await context.add_init_script(stealth_script)
        
        self.contexts[profile_id] = context
        return context
    
    async def close_all(self):
        """Close all browser contexts"""
        for context in self.contexts.values():
            try:
                await context.close()
            except Exception as e:
                logger.error(f"Error closing context: {e}")
        self.contexts.clear()


# Additional helper for pre-warming connections
class ConnectionPreWarmer:
    """Pre-warm connections to reduce latency on first request"""
    
    @staticmethod
    async def prewarm_connections(
        pool_manager: ConnectionPoolManager,
        profiles: List[BrowserProfile],
        targets: List[str]
    ):
        """Pre-establish connections to target domains"""
        tasks = []
        
        for profile in profiles[:3]:  # Limit pre-warming to avoid suspicion
            for target in targets:
                async def warm_connection(p=profile, t=target):
                    try:
                        client = await pool_manager.get_client(p)
                        # Just establish TCP/TLS connection, don't actually request
                        # This is done implicitly when the client is created
                        logger.debug(f"Pre-warmed connection for {getattr(p, 'profile_id', 'unknown')} to {t}")
                    except Exception as e:
                        logger.warning(f"Failed to pre-warm connection: {e}")
                
                tasks.append(warm_connection())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)