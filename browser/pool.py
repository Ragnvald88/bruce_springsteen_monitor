# stealthmaster/browser/pool.py
"""Browser instance pooling for efficient resource management."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from playwright.async_api import Browser, Playwright

from stealthmaster.browser.context import StealthContext
from stealthmaster.browser.launcher import StealthLauncher
from stealthmaster.config import BrowserConfig, ProxyConfig
from stealthmaster.constants import BrowserState

logger = logging.getLogger(__name__)


class BrowserInstance:
    """Represents a pooled browser instance."""
    
    def __init__(
        self,
        browser: Browser,
        proxy: Optional[ProxyConfig] = None,
        instance_id: Optional[str] = None,
    ):
        """Initialize browser instance."""
        self.browser = browser
        self.proxy = proxy
        self.instance_id = instance_id or str(id(browser))
        self.state = BrowserState.IDLE
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.contexts: List[StealthContext] = []
        self.error_count = 0
        self.success_count = 0
    
    @property
    def age(self) -> timedelta:
        """Get instance age."""
        return datetime.now() - self.created_at
    
    @property
    def idle_time(self) -> timedelta:
        """Get time since last use."""
        return datetime.now() - self.last_used
    
    def mark_used(self) -> None:
        """Mark instance as recently used."""
        self.last_used = datetime.now()
        self.state = BrowserState.ACTIVE
    
    def mark_idle(self) -> None:
        """Mark instance as idle."""
        self.state = BrowserState.IDLE
    
    def mark_error(self) -> None:
        """Mark instance as having an error."""
        self.error_count += 1
        if self.error_count >= 3:
            self.state = BrowserState.ERROR
    
    def mark_success(self) -> None:
        """Mark successful operation."""
        self.success_count += 1
        self.error_count = 0  # Reset error count on success
    
    async def close(self) -> None:
        """Close browser and all contexts."""
        # Close all contexts
        for context in self.contexts:
            try:
                await context.close()
            except Exception:
                pass
        
        # Close browser
        try:
            await self.browser.close()
        except Exception:
            pass
        
        self.state = BrowserState.ERROR


class BrowserPool:
    """Manages a pool of browser instances for efficiency and rotation."""
    
    def __init__(
        self,
        config: BrowserConfig,
        playwright: Playwright,
        proxies: Optional[List[ProxyConfig]] = None,
    ):
        """
        Initialize browser pool.
        
        Args:
            config: Browser configuration
            playwright: Playwright instance
            proxies: Optional list of proxies for rotation
        """
        self.config = config
        self.playwright = playwright
        self.proxies = proxies or []
        self.launcher = StealthLauncher(config)
        
        self._instances: Dict[str, BrowserInstance] = {}
        self._lock = asyncio.Lock()
        self._shutdown = False
        
        # Pool configuration
        self.max_instances = config.pool_size
        self.max_age = timedelta(hours=1)
        self.max_idle = timedelta(minutes=30)
    
    async def initialize(self) -> None:
        """Initialize the browser pool."""
        logger.info(f"Initializing browser pool with {self.max_instances} instances")
        
        # Start maintenance task
        asyncio.create_task(self._maintenance_loop())
        
        # Pre-create some instances
        await self._ensure_minimum_instances()
    
    async def acquire(self, prefer_proxy: bool = False) -> Tuple[BrowserInstance, StealthContext]:
        """
        Acquire a browser instance and context from the pool.
        
        Args:
            prefer_proxy: Whether to prefer proxied instances
            
        Returns:
            Tuple of browser instance and stealth context
        """
        async with self._lock:
            # Find available instance
            instance = await self._get_available_instance(prefer_proxy)
            
            if not instance:
                # Create new instance if under limit
                if len(self._instances) < self.max_instances:
                    instance = await self._create_instance(prefer_proxy)
                else:
                    # Wait for an instance to become available
                    for _ in range(10):  # Retry 10 times
                        await asyncio.sleep(1)
                        instance = await self._get_available_instance(prefer_proxy)
                        if instance:
                            break
                    
                    if not instance:
                        raise RuntimeError("No browser instances available")
            
            # Mark as used
            instance.mark_used()
            
            # Create new context
            fingerprint = self.launcher.stealth_core.generate_fingerprint()
            browser_context = await self.launcher.create_context(
                instance.browser,
                fingerprint,
            )
            
            context = StealthContext(browser_context, fingerprint)
            instance.contexts.append(context)
            
            logger.debug(f"Acquired browser instance {instance.instance_id}")
            
            return instance, context
    
    async def release(
        self,
        instance: BrowserInstance,
        context: StealthContext,
        success: bool = True,
    ) -> None:
        """
        Release a browser instance back to the pool.
        
        Args:
            instance: Browser instance to release
            context: Context to close
            success: Whether the operation was successful
        """
        async with self._lock:
            # Close the context
            try:
                await context.close()
                instance.contexts.remove(context)
            except Exception as e:
                logger.error(f"Error closing context: {e}")
            
            # Update instance state
            if success:
                instance.mark_success()
            else:
                instance.mark_error()
            
            # Mark as idle if healthy
            if instance.state != BrowserState.ERROR:
                instance.mark_idle()
            
            logger.debug(f"Released browser instance {instance.instance_id}")
    
    async def _get_available_instance(
        self,
        prefer_proxy: bool,
    ) -> Optional[BrowserInstance]:
        """Get an available instance from the pool."""
        available = [
            inst for inst in self._instances.values()
            if inst.state == BrowserState.IDLE
        ]
        
        if not available:
            return None
        
        # Sort by preference
        if prefer_proxy:
            # Prefer instances with proxy
            available.sort(key=lambda x: (x.proxy is None, x.last_used))
        else:
            # Prefer instances without proxy
            available.sort(key=lambda x: (x.proxy is not None, x.last_used))
        
        return available[0]
    
    async def _create_instance(self, use_proxy: bool) -> BrowserInstance:
        """Create a new browser instance."""
        # Select proxy if requested
        proxy = None
        if use_proxy and self.proxies:
            proxy = self.proxies[len(self._instances) % len(self.proxies)]
        
        # Launch browser
        browser = await self.launcher.launch(
            self.playwright,
            proxy=proxy,
            headless=False,  # Never use headless for stealth
        )
        
        # Create instance
        instance = BrowserInstance(browser, proxy)
        self._instances[instance.instance_id] = instance
        
        logger.info(
            f"Created browser instance {instance.instance_id} "
            f"{'with proxy' if proxy else 'without proxy'}"
        )
        
        return instance
    
    async def _ensure_minimum_instances(self) -> None:
        """Ensure minimum number of instances exist."""
        current_count = len(self._instances)
        min_instances = min(2, self.max_instances)
        
        if current_count < min_instances:
            for i in range(min_instances - current_count):
                # Alternate between proxy and non-proxy
                use_proxy = bool(self.proxies) and (i % 2 == 0)
                try:
                    await self._create_instance(use_proxy)
                except Exception as e:
                    logger.error(f"Failed to create instance: {e}")
    
    async def _maintenance_loop(self) -> None:
        """Perform periodic maintenance on the pool."""
        while not self._shutdown:
            try:
                async with self._lock:
                    await self._cleanup_old_instances()
                    await self._ensure_minimum_instances()
                
                # Run every 5 minutes
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Maintenance error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_old_instances(self) -> None:
        """Remove old or errored instances."""
        to_remove = []
        
        for instance_id, instance in self._instances.items():
            # Remove if errored
            if instance.state == BrowserState.ERROR:
                to_remove.append(instance_id)
                continue
            
            # Remove if too old
            if instance.age > self.max_age:
                to_remove.append(instance_id)
                continue
            
            # Remove if idle too long
            if instance.state == BrowserState.IDLE and instance.idle_time > self.max_idle:
                to_remove.append(instance_id)
        
        # Remove instances
        for instance_id in to_remove:
            instance = self._instances.pop(instance_id)
            await instance.close()
            logger.info(f"Removed instance {instance_id} from pool")
    
    async def shutdown(self) -> None:
        """Shutdown the browser pool."""
        logger.info("Shutting down browser pool")
        self._shutdown = True
        
        async with self._lock:
            # Close all instances
            for instance in self._instances.values():
                await instance.close()
            
            self._instances.clear()
        
        logger.info("Browser pool shutdown complete")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        total = len(self._instances)
        idle = sum(1 for i in self._instances.values() if i.state == BrowserState.IDLE)
        active = sum(1 for i in self._instances.values() if i.state == BrowserState.ACTIVE)
        error = sum(1 for i in self._instances.values() if i.state == BrowserState.ERROR)
        
        with_proxy = sum(1 for i in self._instances.values() if i.proxy is not None)
        
        return {
            "total_instances": total,
            "idle_instances": idle,
            "active_instances": active,
            "error_instances": error,
            "proxied_instances": with_proxy,
            "pool_utilization": active / total if total > 0 else 0,
        }