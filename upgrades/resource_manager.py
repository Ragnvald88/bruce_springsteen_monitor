"""
Resource Manager - Fixes Memory Leaks and Browser Cleanup
=========================================================
Solves the broken pipe errors and selenium session issues
"""

import asyncio
import psutil
import os
import signal
import logging
from typing import Dict, Set, Optional, Any
from contextlib import asynccontextmanager
import weakref
import gc
import atexit
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class BrowserResource:
    """Tracks a browser instance and its resources"""
    
    def __init__(self, browser_id: str, driver: Any, process_pid: int):
        self.browser_id = browser_id
        self.driver_ref = weakref.ref(driver)  # Weak reference to prevent cycles
        self.process_pid = process_pid
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.page_count = 0
        self.memory_usage = 0
        self.is_alive = True
        
    @property
    def driver(self):
        """Get driver if still alive"""
        return self.driver_ref()
    
    @property
    def age_minutes(self) -> float:
        """Age of browser in minutes"""
        return (datetime.now() - self.created_at).total_seconds() / 60
    
    @property
    def idle_minutes(self) -> float:
        """Time since last use in minutes"""
        return (datetime.now() - self.last_used).total_seconds() / 60
    
    def update_memory_usage(self):
        """Update memory usage from process"""
        try:
            process = psutil.Process(self.process_pid)
            self.memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.is_alive = False
            self.memory_usage = 0


class ResourceManager:
    """
    Manages browser resources to prevent memory leaks and broken pipes
    
    Key features:
    - Tracks all browser processes
    - Automatic cleanup of dead browsers
    - Memory monitoring and limits
    - Graceful shutdown handling
    - Connection keepalive management
    """
    
    def __init__(self):
        self.browsers: Dict[str, BrowserResource] = {}
        self.orphan_processes: Set[int] = set()
        self.max_browser_age_minutes = 7  # Kill browsers before 10-minute detection
        self.max_idle_minutes = 3
        self.max_memory_mb = 500  # Per browser
        self.total_memory_limit_mb = 2000
        self._cleanup_task = None
        self._monitoring = False
        self._lock = asyncio.Lock()
        
        # Register cleanup on exit
        atexit.register(self._emergency_cleanup)
        
        # Start monitoring
        self.start_monitoring()
    
    def start_monitoring(self):
        """Start resource monitoring"""
        if not self._monitoring:
            self._monitoring = True
            self._cleanup_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Resource monitoring started")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                await self._cleanup_cycle()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
    
    async def _cleanup_cycle(self):
        """Perform cleanup cycle"""
        async with self._lock:
            # Update memory usage
            for browser in list(self.browsers.values()):
                browser.update_memory_usage()
            
            # Find browsers to clean up
            to_remove = []
            total_memory = 0
            
            for browser_id, browser in self.browsers.items():
                total_memory += browser.memory_usage
                
                # Check if browser should be removed
                if (not browser.is_alive or
                    browser.age_minutes > self.max_browser_age_minutes or
                    browser.idle_minutes > self.max_idle_minutes or
                    browser.memory_usage > self.max_memory_mb):
                    
                    reason = "unknown"
                    if not browser.is_alive:
                        reason = "dead"
                    elif browser.age_minutes > self.max_browser_age_minutes:
                        reason = f"too old ({browser.age_minutes:.1f} min)"
                    elif browser.idle_minutes > self.max_idle_minutes:
                        reason = f"idle ({browser.idle_minutes:.1f} min)"
                    elif browser.memory_usage > self.max_memory_mb:
                        reason = f"high memory ({browser.memory_usage:.0f} MB)"
                    
                    logger.info(f"Marking browser {browser_id} for cleanup: {reason}")
                    to_remove.append(browser_id)
            
            # Remove browsers over total memory limit
            if total_memory > self.total_memory_limit_mb:
                # Sort by memory usage and remove highest
                sorted_browsers = sorted(
                    self.browsers.items(),
                    key=lambda x: x[1].memory_usage,
                    reverse=True
                )
                
                for browser_id, browser in sorted_browsers:
                    if browser_id not in to_remove:
                        to_remove.append(browser_id)
                        total_memory -= browser.memory_usage
                        if total_memory <= self.total_memory_limit_mb:
                            break
            
            # Clean up marked browsers
            for browser_id in to_remove:
                await self._cleanup_browser(browser_id)
            
            # Find and kill orphan processes
            await self._find_orphan_processes()
            
            # Log status
            active_browsers = len(self.browsers)
            if active_browsers > 0:
                logger.info(
                    f"Resource status: {active_browsers} browsers, "
                    f"{total_memory:.0f} MB total memory"
                )
    
    async def register_browser(
        self, 
        browser_id: str, 
        driver: Any, 
        process_pid: Optional[int] = None
    ) -> BrowserResource:
        """Register a new browser instance"""
        async with self._lock:
            # Try to detect PID if not provided
            if not process_pid and hasattr(driver, 'service') and hasattr(driver.service, 'process'):
                process_pid = driver.service.process.pid
            
            browser = BrowserResource(browser_id, driver, process_pid)
            self.browsers[browser_id] = browser
            
            logger.info(f"Registered browser {browser_id} (PID: {process_pid})")
            return browser
    
    async def mark_browser_active(self, browser_id: str):
        """Mark browser as recently used"""
        async with self._lock:
            if browser_id in self.browsers:
                self.browsers[browser_id].last_used = datetime.now()
    
    @asynccontextmanager
    async def managed_browser(self, driver: Any, browser_id: str):
        """Context manager for browser lifecycle"""
        browser = None
        try:
            # Register browser
            browser = await self.register_browser(browser_id, driver)
            
            # Set up keepalive for Selenium
            if hasattr(driver, 'execute_script'):
                # Prevent timeout with periodic commands
                async def keepalive():
                    while browser.is_alive:
                        try:
                            await asyncio.sleep(4)  # Every 4 seconds
                            if browser.driver:
                                # Simple command to keep connection alive
                                browser.driver.execute_script("return 1;")
                                await self.mark_browser_active(browser_id)
                        except:
                            browser.is_alive = False
                            break
                
                keepalive_task = asyncio.create_task(keepalive())
            
            yield driver
            
        finally:
            # Cleanup
            if browser_id in self.browsers:
                await self._cleanup_browser(browser_id)
            
            if 'keepalive_task' in locals():
                keepalive_task.cancel()
    
    async def _cleanup_browser(self, browser_id: str):
        """Clean up a specific browser"""
        browser = self.browsers.pop(browser_id, None)
        if not browser:
            return
        
        logger.info(f"Cleaning up browser {browser_id}")
        
        try:
            driver = browser.driver
            if driver:
                # For Selenium
                if hasattr(driver, 'quit'):
                    try:
                        # Close all windows first
                        if hasattr(driver, 'window_handles'):
                            for handle in driver.window_handles[1:]:
                                driver.switch_to.window(handle)
                                driver.close()
                            if driver.window_handles:
                                driver.switch_to.window(driver.window_handles[0])
                    except:
                        pass
                    
                    # Quit driver
                    driver.quit()
                
                # For Playwright
                elif hasattr(driver, 'close'):
                    await driver.close()
            
            # Force kill process if still alive
            if browser.process_pid:
                await self._kill_process_tree(browser.process_pid)
                
        except Exception as e:
            logger.error(f"Error cleaning up browser: {e}")
            # Force kill on error
            if browser.process_pid:
                await self._kill_process_tree(browser.process_pid)
    
    async def _kill_process_tree(self, pid: int):
        """Kill a process and all its children"""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Kill children first
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            
            # Wait a bit
            gone, alive = psutil.wait_procs(children, timeout=3)
            
            # Force kill remaining
            for p in alive:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
            
            # Kill parent
            try:
                parent.terminate()
                parent.wait(timeout=3)
            except psutil.TimeoutExpired:
                parent.kill()
            except psutil.NoSuchProcess:
                pass
                
            logger.debug(f"Killed process tree for PID {pid}")
            
        except psutil.NoSuchProcess:
            pass
        except Exception as e:
            logger.error(f"Error killing process tree: {e}")
    
    async def _find_orphan_processes(self):
        """Find and kill orphan browser processes"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    pinfo = proc.info
                    name = pinfo['name'].lower()
                    
                    # Check for browser processes
                    if any(browser in name for browser in ['chrome', 'firefox', 'msedge']):
                        # Check if it's a webdriver process
                        cmdline = ' '.join(pinfo.get('cmdline', []))
                        if 'webdriver' in cmdline or '--remote-debugging' in cmdline:
                            # Check if we're tracking this PID
                            tracked = any(
                                b.process_pid == pinfo['pid'] 
                                for b in self.browsers.values()
                            )
                            
                            if not tracked and pinfo['pid'] not in self.orphan_processes:
                                self.orphan_processes.add(pinfo['pid'])
                                logger.warning(f"Found orphan browser process: {pinfo['pid']}")
                                await self._kill_process_tree(pinfo['pid'])
                                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
        except Exception as e:
            logger.error(f"Error finding orphan processes: {e}")
    
    def _emergency_cleanup(self):
        """Emergency cleanup on exit"""
        logger.info("Performing emergency cleanup...")
        
        # Kill all tracked browsers
        for browser in self.browsers.values():
            try:
                if browser.driver and hasattr(browser.driver, 'quit'):
                    browser.driver.quit()
            except:
                pass
            
            if browser.process_pid:
                try:
                    os.kill(browser.process_pid, signal.SIGTERM)
                except:
                    pass
        
        # Kill known orphans
        for pid in self.orphan_processes:
            try:
                os.kill(pid, signal.SIGTERM)
            except:
                pass
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get resource manager statistics"""
        async with self._lock:
            total_memory = sum(b.memory_usage for b in self.browsers.values())
            
            return {
                'active_browsers': len(self.browsers),
                'orphan_processes_killed': len(self.orphan_processes),
                'total_memory_mb': total_memory,
                'oldest_browser_minutes': max(
                    (b.age_minutes for b in self.browsers.values()),
                    default=0
                ),
                'browsers': {
                    bid: {
                        'age_minutes': b.age_minutes,
                        'idle_minutes': b.idle_minutes,
                        'memory_mb': b.memory_usage,
                        'is_alive': b.is_alive
                    }
                    for bid, b in self.browsers.items()
                }
            }
    
    async def cleanup_all(self):
        """Clean up all browsers"""
        logger.info("Cleaning up all browsers...")
        browser_ids = list(self.browsers.keys())
        
        for browser_id in browser_ids:
            await self._cleanup_browser(browser_id)
        
        self._monitoring = False
        if self._cleanup_task:
            self._cleanup_task.cancel()


# Global instance
resource_manager = ResourceManager()
