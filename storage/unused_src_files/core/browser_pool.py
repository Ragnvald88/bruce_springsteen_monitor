"""
StealthMaster AI Browser Pool v3.0
High-performance browser pooling with lifecycle management
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Any, AsyncContextManager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from playwright.async_api import Browser, BrowserContext, Page, async_playwright, Playwright
import psutil
from ..stealth.cdp_stealth import CDPStealthEngine

logger = logging.getLogger(__name__)


@dataclass
class BrowserInstance:
    """Wrapper for browser instance with metadata"""
    browser: Browser
    playwright: Playwright
    created_at: datetime
    last_used: datetime
    usage_count: int = 0
    health_check_failures: int = 0
    is_healthy: bool = True
    contexts: List[BrowserContext] = field(default_factory=list)
    
    @property
    def age_seconds(self) -> float:
        """Get age of browser instance in seconds"""
        return (datetime.now() - self.created_at).total_seconds()
    
    @property
    def idle_seconds(self) -> float:
        """Get idle time in seconds"""
        return (datetime.now() - self.last_used).total_seconds()


class BrowserPool:
    """
    Advanced browser pool with:
    - Pre-warming capabilities
    - Health checking
    - Automatic recycling
    - Resource management
    - Performance monitoring
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Pool settings - reduced lifetimes for better stealth
        self.min_size = self.config.get('min_size', 2)
        self.max_size = self.config.get('max_size', 5)
        self.max_age_seconds = self.config.get('max_age_seconds', 600)  # 10 minutes (reduced from 1 hour)
        self.max_idle_seconds = self.config.get('max_idle_seconds', 180)  # 3 minutes (reduced from 5)
        self.max_requests_per_browser = self.config.get('max_requests_per_browser', 20)  # New limit
        self.health_check_interval = self.config.get('health_check_interval', 60)
        
        # Browser options
        self.browser_options = {
            'headless': self.config.get('headless', False),
            'channel': self.config.get('channel', 'chrome'),
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                # New args to avoid CDP detection
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
            ]
        }
        
        # Pool state
        self.pool: List[BrowserInstance] = []
        self.in_use: List[BrowserInstance] = []
        self.lock = asyncio.Lock()
        self.initialized = False
        self.shutdown = False
        
        # Monitoring
        self.stats = {
            'browsers_created': 0,
            'browsers_recycled': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'health_checks': 0,
            'avg_acquisition_time': 0.0,
            'total_acquisitions': 0
        }
        
        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._maintenance_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> None:
        """Initialize the browser pool"""
        if self.initialized:
            return
            
        logger.info(f"🚀 Initializing browser pool (min={self.min_size}, max={self.max_size})")
        
        # Pre-warm the pool
        await self._ensure_minimum_pool_size()
        
        # Start background tasks
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
        
        self.initialized = True
        logger.info(f"✅ Browser pool initialized with {len(self.pool)} browsers")
        
    async def shutdown_pool(self) -> None:
        """Gracefully shutdown the pool"""
        logger.info("🛑 Shutting down browser pool...")
        self.shutdown = True
        
        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._maintenance_task:
            self._maintenance_task.cancel()
            
        # Close all browsers
        async with self.lock:
            all_browsers = self.pool + self.in_use
            for instance in all_browsers:
                await self._close_browser(instance)
                
            self.pool.clear()
            self.in_use.clear()
            
        logger.info("✅ Browser pool shutdown complete")
        
    @asynccontextmanager
    async def acquire_browser(self):
        """
        Acquire a browser, context, and page from the pool
        Returns a context manager that automatically returns the browser
        """
        start_time = time.time()
        instance = None
        context = None
        page = None
        
        try:
            instance = await self._get_browser_instance()
            
            # Create fresh context with randomized stealth settings via CDP
            context = await CDPStealthEngine.create_stealth_context(instance.browser)
            
            # Track context
            instance.contexts.append(context)
            
            # Create page
            page = await context.new_page()
            
            # Apply CDP stealth to page
            await CDPStealthEngine.apply_page_stealth(page)
            
            # Update acquisition stats
            acquisition_time = time.time() - start_time
            self._update_acquisition_stats(acquisition_time, hit=instance.usage_count > 1)
            
            logger.debug(f"🎯 Browser acquired in {acquisition_time:.2f}s (pool hit: {instance.usage_count > 1})")
            
            yield instance.browser, context, page
            
        finally:
            # Cleanup
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
                    
            if context:
                try:
                    await context.close()
                    if instance:
                        instance.contexts.remove(context)
                except Exception:
                    pass
                    
            if instance:
                await self._return_browser_instance(instance)
                
    async def _get_browser_instance(self) -> BrowserInstance:
        """Get a browser instance from the pool or create new"""
        async with self.lock:
            # Try to get from pool
            while self.pool:
                instance = self.pool.pop(0)
                if await self._is_browser_healthy(instance):
                    instance.last_used = datetime.now()
                    instance.usage_count += 1
                    self.in_use.append(instance)
                    self.stats['pool_hits'] += 1
                    return instance
                else:
                    # Unhealthy browser, close it
                    await self._close_browser(instance)
                    
            # No healthy browsers in pool, create new
            if len(self.in_use) < self.max_size:
                instance = await self._create_browser_instance()
                self.in_use.append(instance)
                self.stats['pool_misses'] += 1
                return instance
            else:
                # Pool exhausted, wait for a browser to be returned
                logger.warning("⚠️  Browser pool exhausted, waiting...")
                # Release lock and wait
                self.lock.release()
                try:
                    await asyncio.sleep(0.5)
                    return await self._get_browser_instance()
                finally:
                    await self.lock.acquire()
                    
    async def _return_browser_instance(self, instance: BrowserInstance) -> None:
        """Return browser instance to pool"""
        async with self.lock:
            if instance in self.in_use:
                self.in_use.remove(instance)
                
            # Check if browser should be recycled
            if (instance.age_seconds > self.max_age_seconds or 
                instance.health_check_failures > 3 or
                not instance.is_healthy or
                instance.usage_count > self.max_requests_per_browser):
                logger.info(f"♻️  Recycling browser (age={instance.age_seconds:.0f}s, usage={instance.usage_count}, failures={instance.health_check_failures})")
                await self._close_browser(instance)
                self.stats['browsers_recycled'] += 1
            else:
                # Return to pool
                self.pool.append(instance)
                
    async def _create_browser_instance(self) -> BrowserInstance:
        """Create a new browser instance"""
        logger.debug("🌟 Creating new browser instance")
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(**self.browser_options)
        
        instance = BrowserInstance(
            browser=browser,
            playwright=playwright,
            created_at=datetime.now(),
            last_used=datetime.now(),
            usage_count=1
        )
        
        self.stats['browsers_created'] += 1
        return instance
        
    async def _close_browser(self, instance: BrowserInstance) -> None:
        """Close browser and cleanup"""
        try:
            # Close all contexts
            for context in instance.contexts[:]:
                try:
                    await context.close()
                except Exception:
                    pass
                    
            # Close browser
            if instance.browser:
                await instance.browser.close()
                
            # Stop playwright
            if instance.playwright:
                await instance.playwright.stop()
                
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
            
    async def _is_browser_healthy(self, instance: BrowserInstance) -> bool:
        """Check if browser instance is healthy"""
        if not instance.is_healthy:
            return False
            
        try:
            # Quick health check - verify browser is responsive
            contexts = instance.browser.contexts
            return True
        except Exception:
            instance.is_healthy = False
            return False
            
    async def _ensure_minimum_pool_size(self) -> None:
        """Ensure pool has minimum number of browsers"""
        async with self.lock:
            current_size = len(self.pool) + len(self.in_use)
            needed = max(0, self.min_size - current_size)
            
            for _ in range(needed):
                try:
                    instance = await self._create_browser_instance()
                    self.pool.append(instance)
                except Exception as e:
                    logger.error(f"Failed to create browser: {e}")
                    
    async def _health_check_loop(self) -> None:
        """Background task for health checking"""
        while not self.shutdown:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                
    async def _perform_health_checks(self) -> None:
        """Perform health checks on idle browsers"""
        async with self.lock:
            for instance in self.pool[:]:
                if not await self._is_browser_healthy(instance):
                    instance.health_check_failures += 1
                    if instance.health_check_failures > 3:
                        logger.warning(f"🏥 Removing unhealthy browser from pool")
                        self.pool.remove(instance)
                        await self._close_browser(instance)
                        
            self.stats['health_checks'] += 1
            
    async def _maintenance_loop(self) -> None:
        """Background task for pool maintenance"""
        while not self.shutdown:
            try:
                await asyncio.sleep(30)  # Run every 30 seconds
                await self._perform_maintenance()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Maintenance error: {e}")
                
    async def _perform_maintenance(self) -> None:
        """Perform pool maintenance tasks"""
        # Remove idle browsers
        async with self.lock:
            for instance in self.pool[:]:
                if instance.idle_seconds > self.max_idle_seconds:
                    logger.info(f"🧹 Removing idle browser (idle={instance.idle_seconds:.0f}s)")
                    self.pool.remove(instance)
                    await self._close_browser(instance)
                    
        # Ensure minimum pool size
        await self._ensure_minimum_pool_size()
        
        # Log stats periodically
        if self.stats['total_acquisitions'] % 100 == 0 and self.stats['total_acquisitions'] > 0:
            self._log_stats()
            
    def _update_acquisition_stats(self, acquisition_time: float, hit: bool) -> None:
        """Update acquisition statistics"""
        self.stats['total_acquisitions'] += 1
        
        # Update moving average
        prev_avg = self.stats['avg_acquisition_time']
        n = self.stats['total_acquisitions']
        self.stats['avg_acquisition_time'] = (prev_avg * (n - 1) + acquisition_time) / n
        
    def _log_stats(self) -> None:
        """Log pool statistics"""
        hit_rate = (self.stats['pool_hits'] / max(1, self.stats['total_acquisitions'])) * 100
        
        logger.info(f"""
📊 Browser Pool Statistics:
  - Pool size: {len(self.pool)} available, {len(self.in_use)} in use
  - Browsers created: {self.stats['browsers_created']}
  - Browsers recycled: {self.stats['browsers_recycled']}
  - Pool hit rate: {hit_rate:.1f}%
  - Avg acquisition time: {self.stats['avg_acquisition_time']:.3f}s
  - Health checks: {self.stats['health_checks']}
  - Memory usage: {psutil.Process().memory_info().rss / 1024 / 1024:.1f} MB
        """)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get current pool statistics"""
        return {
            **self.stats,
            'pool_size': len(self.pool),
            'in_use': len(self.in_use),
            'hit_rate': (self.stats['pool_hits'] / max(1, self.stats['total_acquisitions'])) * 100
        }


# Global browser pool instance
_browser_pool: Optional[BrowserPool] = None


async def get_browser_pool(config: Optional[Dict[str, Any]] = None) -> BrowserPool:
    """Get or create the global browser pool instance"""
    global _browser_pool
    
    if _browser_pool is None:
        _browser_pool = BrowserPool(config)
        await _browser_pool.initialize()
        
    return _browser_pool


async def shutdown_browser_pool() -> None:
    """Shutdown the global browser pool"""
    global _browser_pool
    
    if _browser_pool:
        await _browser_pool.shutdown_pool()
        _browser_pool = None