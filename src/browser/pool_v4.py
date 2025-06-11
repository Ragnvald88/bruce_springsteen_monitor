"""
V4 Browser Pool with Nodriver Integration
High-performance browser pool using undetectable automation
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import time
import uuid
from contextlib import asynccontextmanager
import queue

from ..stealth.nodriver_core import nodriver_core
from ..browser.nodriver_launcher import v4_launcher
from ..utils.logging import get_logger
from ..database.statistics import stats_manager

logger = get_logger(__name__)


@dataclass
class BrowserContext:
    """V4 Browser context with metadata"""
    id: str
    browser_id: str
    page: Any  # Selenium WebDriver or Playwright Page
    platform: Optional[str]
    created_at: float
    last_used: float
    health_score: float = 100.0
    requests_handled: int = 0
    fingerprint: Dict[str, Any] = None


class V4BrowserPool:
    """
    High-performance browser pool for V4
    Implements smart pooling with health monitoring
    """
    
    def __init__(self, min_size: int = 3, max_size: int = 10):
        self.min_size = min_size
        self.max_size = max_size
        
        # Pool storage
        self._available = asyncio.Queue(maxsize=max_size)
        self._in_use: Dict[str, BrowserContext] = {}
        self._all_contexts: Dict[str, BrowserContext] = {}
        
        # Performance tracking
        self._metrics = {
            "acquisitions": 0,
            "releases": 0,
            "creations": 0,
            "health_checks": 0,
            "acquisition_times": []
        }
        
        # Pool state
        self._initialized = False
        self._shutdown = False
        self._maintenance_task = None
        
        logger.info(f"V4 Browser Pool initialized (min={min_size}, max={max_size})")
    
    async def initialize(self):
        """Initialize the pool with minimum browsers"""
        if self._initialized:
            return
        
        logger.info("Initializing V4 browser pool...")
        
        # Create initial browsers
        create_tasks = []
        for i in range(self.min_size):
            create_tasks.append(self._create_context())
        
        # Wait for all to complete
        contexts = await asyncio.gather(*create_tasks, return_exceptions=True)
        
        # Add successful contexts to pool
        for ctx in contexts:
            if isinstance(ctx, BrowserContext):
                await self._available.put(ctx)
                self._all_contexts[ctx.id] = ctx
            else:
                logger.error(f"Failed to create initial context: {ctx}")
        
        # Start maintenance task
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
        
        self._initialized = True
        logger.info(f"V4 pool initialized with {self._available.qsize()} contexts")
    
    async def _create_context(self, platform: Optional[str] = None) -> BrowserContext:
        """Create a new browser context"""
        start_time = time.time()
        
        try:
            # Launch browser
            browser_id = await v4_launcher.launch_browser()
            
            # Create context
            context_id = await v4_launcher.create_context(browser_id)
            
            # Create page
            page = await v4_launcher.new_page(context_id)
            
            # Get fingerprint
            fingerprint = v4_launcher.fingerprints.get(browser_id, {})
            
            # Create context object
            ctx = BrowserContext(
                id=context_id,
                browser_id=browser_id,
                page=page,
                platform=platform,
                created_at=time.time(),
                last_used=time.time(),
                fingerprint=fingerprint
            )
            
            self._metrics["creations"] += 1
            
            # Record performance metric
            creation_time = (time.time() - start_time) * 1000
            stats_manager.record_performance_metric(
                "pool_v4",
                "context_creation",
                creation_time,
                success=True,
                platform=platform
            )
            
            logger.debug(f"Created V4 context {ctx.id} in {creation_time:.0f}ms")
            return ctx
            
        except Exception as e:
            logger.error(f"Failed to create V4 context: {e}")
            stats_manager.record_performance_metric(
                "pool_v4",
                "context_creation",
                (time.time() - start_time) * 1000,
                success=False,
                platform=platform
            )
            raise
    
    @asynccontextmanager
    async def acquire(self, platform: Optional[str] = None, timeout: float = 30.0):
        """
        Acquire a browser context from the pool
        
        Args:
            platform: Optional platform preference
            timeout: Acquisition timeout
            
        Yields:
            BrowserContext ready for use
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        context = None
        
        try:
            # Try to get from pool
            try:
                context = await asyncio.wait_for(
                    self._get_context(platform),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Pool acquisition timeout after {timeout}s")
                # Create new context if pool is exhausted
                if len(self._all_contexts) < self.max_size:
                    context = await self._create_context(platform)
                    self._all_contexts[context.id] = context
                else:
                    raise RuntimeError("Browser pool exhausted")
            
            # Mark as in use
            self._in_use[context.id] = context
            context.last_used = time.time()
            context.requests_handled += 1
            
            # Track metrics
            acquisition_time = (time.time() - start_time) * 1000
            self._metrics["acquisitions"] += 1
            self._metrics["acquisition_times"].append(acquisition_time)
            
            # Keep only last 100 times for memory efficiency
            if len(self._metrics["acquisition_times"]) > 100:
                self._metrics["acquisition_times"] = self._metrics["acquisition_times"][-100:]
            
            logger.debug(f"Acquired context {context.id} in {acquisition_time:.0f}ms")
            
            yield context
            
        finally:
            # Release context back to pool
            if context and not self._shutdown:
                await self._release_context(context)
    
    async def _get_context(self, platform: Optional[str] = None) -> BrowserContext:
        """Get context from pool, preferring platform match"""
        # If platform specified, try to find matching context
        if platform and self._available.qsize() > 0:
            temp_contexts = []
            found = None
            
            # Check up to pool size for platform match
            for _ in range(self._available.qsize()):
                try:
                    ctx = self._available.get_nowait()
                    if not found and ctx.platform == platform:
                        found = ctx
                    else:
                        temp_contexts.append(ctx)
                except asyncio.QueueEmpty:
                    break
            
            # Put back non-matching contexts
            for ctx in temp_contexts:
                await self._available.put(ctx)
            
            if found:
                return found
        
        # Get any available context
        return await self._available.get()
    
    async def _release_context(self, context: BrowserContext):
        """Release context back to pool"""
        try:
            # Remove from in-use
            if context.id in self._in_use:
                del self._in_use[context.id]
            
            # Check health
            if context.health_score < 50 or context.requests_handled > 100:
                # Retire unhealthy context
                logger.info(f"Retiring unhealthy context {context.id}")
                await self._destroy_context(context)
                
                # Create replacement if below minimum
                if len(self._all_contexts) < self.min_size:
                    new_context = await self._create_context()
                    self._all_contexts[new_context.id] = new_context
                    await self._available.put(new_context)
            else:
                # Return to pool
                await self._available.put(context)
                self._metrics["releases"] += 1
                
        except Exception as e:
            logger.error(f"Error releasing context {context.id}: {e}")
    
    async def _destroy_context(self, context: BrowserContext):
        """Destroy a browser context"""
        try:
            # Close page
            if hasattr(context.page, "close"):
                await context.page.close()
            elif hasattr(context.page, "quit"):
                context.page.quit()
            
            # Remove from tracking
            if context.id in self._all_contexts:
                del self._all_contexts[context.id]
            
            logger.debug(f"Destroyed context {context.id}")
            
        except Exception as e:
            logger.error(f"Error destroying context {context.id}: {e}")
    
    async def _maintenance_loop(self):
        """Periodic maintenance tasks"""
        while not self._shutdown:
            try:
                await asyncio.sleep(30)  # Run every 30 seconds
                
                # Health check contexts
                await self._health_check()
                
                # Ensure minimum pool size
                current_size = len(self._all_contexts)
                if current_size < self.min_size:
                    create_count = self.min_size - current_size
                    logger.info(f"Creating {create_count} contexts to maintain pool size")
                    
                    for _ in range(create_count):
                        try:
                            ctx = await self._create_context()
                            self._all_contexts[ctx.id] = ctx
                            await self._available.put(ctx)
                        except Exception as e:
                            logger.error(f"Maintenance context creation failed: {e}")
                
            except Exception as e:
                logger.error(f"Maintenance loop error: {e}")
    
    async def _health_check(self):
        """Check health of all contexts"""
        self._metrics["health_checks"] += 1
        
        # Check in-use contexts for staleness
        stale_threshold = 300  # 5 minutes
        current_time = time.time()
        
        for ctx_id, ctx in list(self._in_use.items()):
            if current_time - ctx.last_used > stale_threshold:
                logger.warning(f"Context {ctx_id} is stale, marking unhealthy")
                ctx.health_score = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        avg_acquisition = (
            sum(self._metrics["acquisition_times"]) / len(self._metrics["acquisition_times"])
            if self._metrics["acquisition_times"] else 0
        )
        
        return {
            "pool_size": len(self._all_contexts),
            "available": self._available.qsize(),
            "in_use": len(self._in_use),
            "total_acquisitions": self._metrics["acquisitions"],
            "total_releases": self._metrics["releases"],
            "total_creations": self._metrics["creations"],
            "health_checks": self._metrics["health_checks"],
            "avg_acquisition_ms": avg_acquisition,
            "contexts_per_second": self._metrics["acquisitions"] / (time.time() - min(
                ctx.created_at for ctx in self._all_contexts.values()
            )) if self._all_contexts else 0
        }
    
    async def shutdown(self):
        """Shutdown the pool"""
        logger.info("Shutting down V4 browser pool...")
        self._shutdown = True
        
        # Cancel maintenance
        if self._maintenance_task:
            self._maintenance_task.cancel()
        
        # Destroy all contexts
        for ctx in list(self._all_contexts.values()):
            await self._destroy_context(ctx)
        
        self._all_contexts.clear()
        self._in_use.clear()
        
        logger.info("V4 browser pool shutdown complete")


# Global instance
v4_pool = V4BrowserPool()