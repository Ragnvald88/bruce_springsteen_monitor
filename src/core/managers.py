# src/core/managers.py - v5.0 - Ultra-Performance Enhanced Edition
from __future__ import annotations

import asyncio
import hashlib
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple, Any, List, TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from playwright.async_api import (
        Playwright,
        Browser,
        BrowserContext as PlaywrightContext,
        Page as PlaywrightPage,
        Route,
        Request,
        Response
    )

# FIXED: Project-specific imports with correct paths
from ..profiles.manager import ProfileManager
from ..profiles.models import BrowserProfile
from ..profiles.enums import DataOptimizationLevel

from .models import DataUsageTracker

logger = logging.getLogger(__name__)


class ConnectionPoolManager:
    """Manage HTTP connection pools with profile integration"""

    def __init__(self, config: Dict[str, Any], profile_manager: ProfileManager):
        self.config = config
        self.profile_manager = profile_manager
        self.pools: Dict[str, httpx.AsyncClient] = {}
        self._lock = asyncio.Lock()

        network_config = self.config.get('network', {})
        self.max_connections = network_config.get('max_connections', 10)
        self.max_keepalive = network_config.get('max_keepalive_connections', 20)
        self.connect_timeout = network_config.get('connect_timeout', 10.0)
        self.read_timeout = network_config.get('read_timeout', 30.0)
        logger.info(f"ConnectionPoolManager initialized with max_connections={self.max_connections}, max_keepalive={self.max_keepalive}")


    async def get_client(self,
                        profile: BrowserProfile,
                        use_tls_fingerprint: bool = True) -> httpx.AsyncClient:
        async with self._lock:
            client_key = f"{profile.profile_id}_{use_tls_fingerprint}"
            if client_key not in self.pools:
                logger.debug(f"Creating new httpx client for key: {client_key}")
                limits = httpx.Limits(
                    max_connections=self.max_connections,
                    max_keepalive_connections=self.max_keepalive
                )
                headers = {}
                if hasattr(profile, 'get_headers') and callable(profile.get_headers):
                    headers = profile.get_headers()
                elif hasattr(profile, 'extra_http_headers'):
                    headers = profile.extra_http_headers.copy()
                    if not headers.get('User-Agent') and hasattr(profile, 'user_agent'): # Ensure UA
                         headers['User-Agent'] = profile.user_agent


                proxy_url_str = None
                if profile.proxy_config: # Corrected indentation for this block
                    proxy_url_str = profile.proxy_config.get_proxy_url(session_id=getattr(profile, 'proxy_session_id', None))

                transport_proxies_dict = None
                if proxy_url_str: # Ensure proxy_url_str is not None or empty
                    transport_proxies_dict = {"all://": proxy_url_str}

                # Configure transport with proxies if they exist
                if transport_proxies_dict:
                    transport = httpx.AsyncHTTPTransport(proxies=transport_proxies_dict, retries=1) # You can configure retries
                else:
                    # If no proxy, you might still want to configure retries or other transport settings
                    transport = httpx.AsyncHTTPTransport(retries=1) 

                try:
                    self.pools[client_key] = httpx.AsyncClient(
                        limits=limits,
                        headers=headers,
                        transport=transport, # <--- USE TRANSPORT ARGUMENT HERE
                        timeout=httpx.Timeout(self.connect_timeout, read=self.read_timeout),
                        follow_redirects=True,
                        verify=True, 
                        http2=True,
                    )
                    logger.info(f"Created httpx client for profile {profile.profile_id}. Proxy: {'Yes' if transport_proxies_dict else 'No'}")
                except Exception as e:
                    logger.error(f"Error creating httpx client for profile {profile.profile_id}: {e}", exc_info=True)
                    raise
            return self.pools[client_key] # This line was previously outdented, now correctly part of get_client

    async def close_all(self):
        async with self._lock:
            logger.info(f"Closing {len(self.pools)} HTTP connection pools.")
            for client_key, client in self.pools.items():
                try:
                    await client.aclose()
                    logger.debug(f"Closed client: {client_key}")
                except Exception as e:
                    logger.error(f"Error closing client {client_key}: {e}", exc_info=True)
            self.pools.clear()
            logger.info("All HTTP connection pools closed.")


class ResponseCache:
    """Intelligent response caching to minimize data usage"""

    def __init__(self, max_size_mb: float = 50):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.current_size_bytes = 0
        self.cache: Dict[str, Tuple[bytes, datetime, Optional[Dict[str, str]]]] = {}
        self._lock = asyncio.Lock()
        self.hit_count = 0 # Added missing attribute
        self.miss_count = 0 # Added missing attribute
    
    @property
    def current_size_mb(self) -> float:
        """Get current cache size in MB"""
        return self.current_size_bytes / (1024 * 1024)
    
    async def clear_old_entries(self, max_age_seconds: int) -> int: # Correctly indented
        async with self._lock:
            now = datetime.now()
            keys_to_delete = []
            for key, cached_item_tuple in list(self.cache.items()):
                if len(cached_item_tuple) >= 2:
                    timestamp = cached_item_tuple[1]
                    if isinstance(timestamp, datetime):
                        age = (now - timestamp).total_seconds()
                        if age > max_age_seconds:
                            keys_to_delete.append(key)
                    else:
                        logger.warning(f"Cache item {key} has unexpected timestamp format: {timestamp}")
                else:
                    logger.warning(f"Cache item {key} has unexpected structure: {cached_item_tuple}")

            cleared_count = 0
            for key in keys_to_delete:
                if key in self.cache:
                    cached_item_to_pop = self.cache.pop(key)
                    if cached_item_to_pop and isinstance(cached_item_to_pop, (tuple, list)) and len(cached_item_to_pop) > 0:
                        content_bytes = cached_item_to_pop[0]
                        if content_bytes is not None and isinstance(content_bytes, bytes):
                            self.current_size_bytes -= len(content_bytes)
                    cleared_count += 1

            if cleared_count > 0:
                logger.debug(f"Cache maintenance: Cleared {cleared_count} old entries older than {max_age_seconds}s.")
            return cleared_count

    def _generate_key(self, url: str, headers: Optional[Dict[str, str]] = None) -> str: # Correctly indented
        key_parts = [url]
        if headers:
            for header_name in ['Accept', 'Accept-Language', 'X-Platform-Specific-Cache-Key']:
                if header_name in headers:
                    key_parts.append(f"{header_name}:{headers[header_name]}")
        return hashlib.sha256("|".join(key_parts).encode()).hexdigest()

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None,
                  max_age_seconds: int = 300) -> Optional[bytes]: # Correctly indented
        async with self._lock:
            key = self._generate_key(url, headers)
            cached_item = self.cache.get(key)
            if cached_item:
                content, timestamp, response_headers = cached_item
                age = (datetime.now() - timestamp).total_seconds()
                if age <= max_age_seconds:
                    self.hit_count += 1
                    logger.debug(f"Cache hit for {url} (age: {age:.1f}s)")
                    return content
                else:
                    logger.debug(f"Cache stale for {url} (age: {age:.1f}s > {max_age_seconds}s). Evicting.")
                    if content is not None:
                        self.current_size_bytes -= len(content)
                    del self.cache[key]
            self.miss_count += 1
            logger.debug(f"Cache miss for {url}")
            return None

    async def put(self, url: str, content: bytes,
                  headers: Optional[Dict[str, str]] = None,
                  response_headers: Optional[Dict[str, str]] = None): # Correctly indented
        async with self._lock:
            key = self._generate_key(url, headers)
            if content is None:
                logger.debug(f"Not caching None content for {url}")
                return
            content_size = len(content)
            while (self.current_size_bytes + content_size > self.max_size_bytes) and self.cache:
                try:
                    oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                except ValueError:
                    break
                old_content_bytes, _, _ = self.cache.pop(oldest_key)
                if old_content_bytes is not None:
                    self.current_size_bytes -= len(old_content_bytes)
                logger.debug(f"Cache eviction: Removed {oldest_key} to free space.")
            if self.current_size_bytes + content_size <= self.max_size_bytes:
                self.cache[key] = (content, datetime.now(), response_headers or {})
                self.current_size_bytes += content_size
                logger.debug(f"Cached {url} ({content_size / 1024:.2f} KB). Cache: {self.current_size_bytes / (1024*1024):.2f} MB")
            else:
                logger.warning(f"Could not cache {url} ({content_size / 1024:.2f} KB). Cache full.")

    @property
    def hit_rate(self) -> float: # Correctly indented
        total_requests = self.hit_count + self.miss_count
        return self.hit_count / max(1, total_requests)

    async def clear_cache(self): # Correctly indented
        async with self._lock:
            self.cache.clear()
            self.current_size_bytes = 0
            self.hit_count = 0
            self.miss_count = 0
            logger.info("ResponseCache cleared.")


class SmartBrowserContextManager:
    """Manages Playwright BrowserContexts with profile integration"""
    def __init__(self,
                 playwright: Playwright,
                 profile_manager: ProfileManager,
                 data_tracker: DataUsageTracker,
                 config: Dict[str, Any]):
        self.playwright = playwright
        self.profile_manager = profile_manager
        self.data_tracker = data_tracker
        self.config = config
        self.contexts: Dict[str, PlaywrightContext] = {}
        self.context_locks: Dict[str, asyncio.Lock] = {}
        self._pool_lock = asyncio.Lock()
        self.browsers: Dict[str, Any] = {}
        self.context_ttl_minutes = self.config.get('browser_pool', {}).get('context_ttl_minutes', 30)
        self.stealth_script_path = Path(self.config.get('paths', {}).get('stealth_script', "src/core/stealth_init.js"))
        logger.info(f"SmartBrowserContextManager initialized. Stealth script: {self.stealth_script_path}")

    async def get_context(self, profile: BrowserProfile) -> PlaywrightContext:
        profile_specific_lock = self.context_locks.setdefault(profile.profile_id, asyncio.Lock())
        async with profile_specific_lock:
            if profile.profile_id in self.contexts:
                context = self.contexts[profile.profile_id]
                if await self._is_context_valid(context):
                    logger.debug(f"Reusing context for profile {profile.profile_id}")
                    return context
                else:
                    logger.info(f"Invalid context for profile {profile.profile_id}. Recreating.")
                    await self._close_context(profile.profile_id)
            logger.info(f"Creating new context for profile {profile.profile_id} ({profile.name})")
            new_context = await self._create_context(profile)
            self.contexts[profile.profile_id] = new_context
            return new_context

    async def _is_context_valid(self, context: PlaywrightContext) -> bool:
        try:
            if not context.browser or not context.browser.is_connected():
                logger.warning("Context's browser not connected.")
                return False
            _ = context.pages # Simple check
            return True
        except Exception as e:
            logger.warning(f"Context validity check failed: {e}")
            return False

    async def _create_context(self, profile: BrowserProfile) -> PlaywrightContext:
        ua_lower = profile.user_agent.lower()
        if 'firefox' in ua_lower: browser_key = 'firefox'
        elif 'webkit' in ua_lower and 'chrome' not in ua_lower: browser_key = 'webkit'
        else: browser_key = 'chromium'
        logger.debug(f"Browser key '{browser_key}' for profile {profile.profile_id}.")
        try:
            async with self._pool_lock:
                if browser_key not in self.browsers or not self.browsers[browser_key].is_connected():
                    logger.info(f"Launching new '{browser_key}' browser.")
                    browser_launcher = getattr(self.playwright, browser_key)
                    launch_options = profile.get_launch_options()
                    launch_options['headless'] = self.config.get('browser_settings', {}).get('headless', True)
                    self.browsers[browser_key] = await browser_launcher.launch(**launch_options)
            browser = self.browsers[browser_key]
            context_params = profile.get_context_params()
            full_init_script = None
            if self.stealth_script_path.exists():
                try:
                    stealth_content = self.stealth_script_path.read_text(encoding='utf-8')
                    js_data = (profile.get_stealth_init_js_profile_data()
                               if hasattr(profile, 'get_stealth_init_js_profile_data')
                               else {'name': profile.name, 'user_agent': profile.user_agent}) # Basic fallback
                    full_init_script = f"window.__fingerprint_profile__ = {json.dumps(js_data)};\n{stealth_content}"
                except Exception as e: logger.error(f"Failed to prep stealth script for {profile.profile_id}: {e}", exc_info=True)
            else: logger.warning(f"Stealth script not found: {self.stealth_script_path}")
            context = await browser.new_context(**context_params)
            if full_init_script:
                await context.add_init_script(full_init_script)
                logger.debug(f"Added init script for {profile.profile_id}")
            if profile.data_optimization_level != DataOptimizationLevel.OFF:
                await self._setup_request_interception(context, profile)
            logger.info(f"Created context for profile {profile.profile_id} ({profile.name})")
            return context
        except Exception as e:
            logger.error(f"Fatal error creating context for {profile.profile_id}: {e}", exc_info=True)
            async with self._pool_lock: # Check if browser needs cleanup
                if browser_key in self.browsers and self.browsers[browser_key].is_connected():
                    is_used = any(hasattr(ctx, 'browser') and ctx.browser == self.browsers[browser_key] and pid != profile.profile_id
                                  for pid, ctx in self.contexts.items())
                    if not is_used:
                        logger.warning(f"Closing browser '{browser_key}' due to creation error.")
                        await self.browsers[browser_key].close()
                        del self.browsers[browser_key]
            raise

    async def _setup_request_interception(self, context: PlaywrightContext, profile: BrowserProfile):
        block_patterns = profile.get_resource_block_patterns()
        resource_types_to_block = getattr(profile, 'block_resources', set())
        async def handle_route(route: Route):
            request = route.request; url = request.url; resource_type = request.resource_type.lower()
            should_block = False
            if resource_type in resource_types_to_block: should_block = True
            else:
                for p_str in block_patterns:
                    if (p_str.startswith("*") and p_str.endswith("*") and p_str[1:-1] in url) or \
                       (p_str.startswith("*") and url.endswith(p_str[1:])) or \
                       (p_str.endswith("*") and url.startswith(p_str[:-1])) or (p_str == url):
                        should_block = True; break
            if should_block:
                logger.debug(f"Blocking: {url} (Type: {resource_type}) for prof {profile.profile_id}")
                self.data_tracker.blocked_resources_saved_mb += 0.05
                try: await route.abort()
                except Exception as e: logger.debug(f"Could not abort {url}: {e}")
            else:
                try: await route.continue_()
                except Exception as e: logger.debug(f"Could not continue {url}: {e}")
        try:
            await context.route("**/*", handle_route)
            logger.info(f"Req interception for prof {profile.profile_id} (Opt: {profile.data_optimization_level.value})")
        except Exception as e: logger.error(f"Failed to set up req interception for {profile.profile_id}: {e}", exc_info=True)

    async def _close_context(self, context_key: str):
        context = self.contexts.pop(context_key, None)
        self.context_locks.pop(context_key, None)
        if context:
            try:
                logger.debug(f"Attempting to close context for key {context_key}")
                await context.close()
                logger.info(f"Successfully closed context for key {context_key}")
            except Exception as e: logger.error(f"Error closing context {context_key}: {e}", exc_info=True)

    async def close_all(self):
        logger.info("Closing all SmartBrowserContextManager resources...")
        context_keys = list(self.contexts.keys())
        for context_key in context_keys: await self._close_context(context_key)
        async with self._pool_lock:
            browser_keys = list(self.browsers.keys())
            for browser_key in browser_keys:
                browser = self.browsers.pop(browser_key, None)
                if browser and browser.is_connected():
                    try:
                        logger.info(f"Closing browser instance: {browser_key}")
                        await browser.close()
                    except Exception as e: logger.error(f"Error closing browser {browser_key}: {e}", exc_info=True)
            self.browsers.clear()
        self.contexts.clear(); self.context_locks.clear()
        logger.info("All SmartBrowserContextManager resources closed.")