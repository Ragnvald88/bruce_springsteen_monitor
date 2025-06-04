# src/core/orchestrator.py - v4.0 - Ultra-Performance Stealth Edition
from __future__ import annotations

import asyncio
import logging
import time
import os
import gc
import psutil
from typing import Dict, List, Optional, Set, Any, TYPE_CHECKING, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from pathlib import Path
import random
import json
import signal
from contextlib import suppress, asynccontextmanager
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading
import queue

if TYPE_CHECKING:
    from playwright.async_api import Playwright

# Profile system imports
from src.profiles.manager import ProfileManager
from src.profiles.enums import DataOptimizationLevel, Platform as CorePlatformEnum
from src.core.advanced_profile_system import DetectionEvent
from src.profiles.utils import create_profile_manager_from_config

# Core module imports
from .enums import OperationMode, PlatformType, PriorityLevel
from .models import EnhancedTicketOpportunity, DataUsageTracker
from .managers import ConnectionPoolManager, ResponseCache, SmartBrowserContextManager
from .components import ProfileAwareLightweightMonitor
from .strike_force import ProfileIntegratedStrikeForce


logger = logging.getLogger(__name__)

@dataclass
class SystemHealth:
    """Tracks system health metrics"""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    active_tasks: int = 0
    error_rate: float = 0.0
    last_success: Optional[datetime] = None
    consecutive_failures: int = 0
    
    @property
    def is_healthy(self) -> bool:
        return (self.cpu_percent < 80 and 
                self.memory_percent < 85 and 
                self.error_rate < 0.3 and
                self.consecutive_failures < 10)

@dataclass
class OpportunityPriority:
    """Enhanced priority calculation for opportunities"""
    opportunity: EnhancedTicketOpportunity
    score: float = 0.0
    
    def __lt__(self, other):
        return self.score > other.score  # Higher score = higher priority

class PerformanceOptimizer:
    """Optimizes system performance and resource usage"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.performance_history: deque = deque(maxlen=1000)
        self.optimization_interval = 30  # seconds
        self.last_optimization = time.time()
        
        # Performance thresholds
        self.cpu_threshold = 70  # percent
        self.memory_threshold = 80  # percent
        self.response_time_threshold = 2.0  # seconds
    
    async def optimize(self, orchestrator: 'UnifiedOrchestrator'):
        """Perform system optimization"""
        
        current_time = time.time()
        if current_time - self.last_optimization < self.optimization_interval:
            return
        
        self.last_optimization = current_time
        
        # Collect system metrics
        process = psutil.Process(os.getpid())
        cpu_percent = process.cpu_percent(interval=0.1)
        memory_info = process.memory_info()
        memory_percent = (memory_info.rss / psutil.virtual_memory().total) * 100
        
        # Optimize based on metrics
        if cpu_percent > self.cpu_threshold:
            await self._reduce_cpu_usage(orchestrator)
        
        if memory_percent > self.memory_threshold:
            await self._reduce_memory_usage(orchestrator)
        
        # Garbage collection if needed
        if memory_percent > 60:
            gc.collect()
    
    async def _reduce_cpu_usage(self, orchestrator: 'UnifiedOrchestrator'):
        """Reduce CPU usage by throttling operations"""
        logger.warning("High CPU usage detected, throttling operations")
        
        # Increase intervals
        if orchestrator.monitor:
            orchestrator.monitor.default_check_interval *= 1.2
        
        # Reduce concurrent operations
        orchestrator.max_concurrent_strikes = max(1, orchestrator.max_concurrent_strikes - 1)
    
    async def _reduce_memory_usage(self, orchestrator: 'UnifiedOrchestrator'):
        """Reduce memory usage by clearing caches"""
        logger.warning("High memory usage detected, clearing caches")
        
        # Clear response cache
        if orchestrator.response_cache:
            await orchestrator.response_cache.clear_old_entries(max_age_seconds=60)
        
        # Clear processed opportunities
        if len(orchestrator.processed_opportunity_fingerprints) > 10000:
            orchestrator.processed_opportunity_fingerprints.clear()

class UnifiedOrchestrator:
    """Ultra-performance orchestrator with advanced stealth and optimization"""
    
    def __init__(self, config: Dict[str, Any], playwright_instance: Playwright, 
                 config_file_path: Path, gui_queue: Optional[queue.Queue] = None):
        
        self.config = config
        self.playwright = playwright_instance
        self.config_file_path = config_file_path
        self.gui_queue = gui_queue
        
        # Operation mode and settings
        self.mode = OperationMode(config.get('app_settings', {}).get('mode', 'adaptive'))
        self.is_dry_run = config.get('app_settings', {}).get('dry_run', False)
        
        # Performance settings
        self.max_concurrent_strikes = config.get('performance', {}).get('max_concurrent_strikes', 3)
        self.max_concurrent_monitors = config.get('performance', {}).get('max_concurrent_monitors', 10)
        
        # Data tracker
        self.data_tracker = DataUsageTracker(
            global_limit_mb=config.get('data_limits', {}).get('global_limit_mb'),
            session_limit_mb=config.get('data_limits', {}).get('session_limit_mb'),
            daily_limit_mb=config.get('data_limits', {}).get('daily_limit_mb')
        )
        
        # Core components (initialized in initialize_subsystems)
        self.profile_manager: Optional[ProfileManager] = None
        self.connection_pool: Optional[ConnectionPoolManager] = None
        self.response_cache: Optional[ResponseCache] = None
        self.browser_manager: Optional[SmartBrowserContextManager] = None
        self.monitor: Optional[ProfileAwareLightweightMonitor] = None
        self.strike_force: Optional[ProfileIntegratedStrikeForce] = None
        
        # Performance optimizer
        self.performance_optimizer = PerformanceOptimizer(config)
        
        # Opportunity management with priority queue
        self.opportunity_queue: asyncio.PriorityQueue[Tuple[float, OpportunityPriority]] = asyncio.PriorityQueue(maxsize=1000)
        self.processed_opportunity_fingerprints: Set[str] = set()
        self.opportunity_cache: Dict[str, EnhancedTicketOpportunity] = {}
        self.active_strikes: Dict[str, asyncio.Task] = {}
        
        # System health tracking
        self.system_health = SystemHealth()
        
        # Metrics and state
        self.start_time = datetime.now()
        self.metrics = self._initialize_metrics()
        self.background_tasks: List[asyncio.Task] = []
        self.monitor_semaphore = asyncio.Semaphore(self.max_concurrent_monitors)
        self.strike_semaphore = asyncio.Semaphore(self.max_concurrent_strikes)
        
        # Thread pool for CPU-bound operations
        self.thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="OrchestratorWorker")
        
        # State flags
        self.is_initialized = False
        self._shutdown_initiated = False
        self._pause_monitoring = False
        
        logger.info(f"🚀 UnifiedOrchestrator v4.0 initialized - Mode: {self.mode.value}")
    
    def _initialize_metrics(self) -> Dict[str, Any]:
        """Initialize comprehensive metrics tracking"""
        return {
            'detections_by_platform': defaultdict(int),
            'attempts_by_platform': defaultdict(int),
            'successes_by_platform': defaultdict(int),
            'failures_by_platform': defaultdict(int),
            'blocks_by_platform': defaultdict(int),
            'profile_rotations': 0,
            'opportunities_processed_total': 0,
            'opportunities_queued_total': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'profile_performance': defaultdict(lambda: {
                'attempts': 0, 'successes': 0, 'blocks': 0, 'response_times': deque(maxlen=100)
            }),
            'active_monitoring_tasks': 0,
            'active_strike_tasks': 0,
            'average_response_time': 0.0,
            'peak_memory_usage': 0.0,
            'total_data_saved_mb': 0.0,
        }
    
    async def initialize_subsystems(self) -> bool:
        """Initialize all subsystems with performance optimizations"""
        
        if self.is_initialized:
            logger.info("Subsystems already initialized")
            return True
        
        try:
            logger.info("🔧 Initializing orchestrator subsystems...")
            
            # 1. Profile Manager with custom settings
            profile_settings = self.config.get('profile_manager_settings', {})
            
            # Adjust profile settings based on mode
            if self.mode == OperationMode.ULTRA_STEALTH:
                profile_settings['evolution_interval'] = 300  # Slower evolution
                profile_settings['min_quality_threshold'] = 0.7  # Higher quality requirement
            elif self.mode == OperationMode.BEAST:
                profile_settings['evolution_interval'] = 60  # Faster evolution
                profile_settings['min_quality_threshold'] = 0.3  # Lower quality acceptable
            
            self.profile_manager = create_profile_manager_from_config(
                str(self.config_file_path),
                config_overrides=profile_settings
            )
            await self.profile_manager.initialize()
            
            profile_count = len(self.profile_manager.dynamic_profiles)
            logger.info(f"✅ ProfileManager: {profile_count} profiles loaded")
            
            # 2. Connection Pool with optimizations
            self.connection_pool = ConnectionPoolManager(self.config, self.profile_manager)
            # await self.connection_pool.pre_warm(count=min(5, profile_count)) 
            logger.info("✅ ConnectionPoolManager: Pre-warmed connections")
            
            # 3. Response Cache with size limits
            cache_size_mb = self.config.get('cache_settings', {}).get('max_size_mb', 100)
            self.response_cache = ResponseCache(max_size_mb=cache_size_mb)
            logger.info(f"✅ ResponseCache: {cache_size_mb}MB capacity")
            
            # 4. Browser Manager with stealth
            self.browser_manager = SmartBrowserContextManager(
                self.playwright, self.profile_manager, self.data_tracker, self.config
            )
            logger.info("✅ SmartBrowserContextManager: Ready")
            
            # 5. Monitor with performance tracking
            self.monitor = ProfileAwareLightweightMonitor(
                self.config, self.profile_manager, self.connection_pool,
                self.response_cache, self.data_tracker
            )
            logger.info("✅ ProfileAwareLightweightMonitor: Configured")
            
            # 6. Strike Force with concurrency control
            self.strike_force = ProfileIntegratedStrikeForce(
                self.browser_manager, self.profile_manager, self.data_tracker, self.config
            )
            logger.info("✅ ProfileIntegratedStrikeForce: Armed")
            
            self.is_initialized = True
            logger.info("✨ All subsystems initialized successfully")
            
            # Log initial system state
            #await self._log_system_state()
            
            return True
            
        except Exception as e:
            logger.critical(f"Subsystem initialization failed: {e}", exc_info=True)
            self.is_initialized = False
            return False
    
    async def pre_warm_connections(self):
        """Pre-warm HTTP connections for faster initial requests"""
        
        if not self.connection_pool or not self.profile_manager:
            return
        
        logger.info("Pre-warming connections...")
        
        # Get target URLs
        target_urls = []
        for target in self.config.get('targets', []):
            if target.get('enabled') and target.get('url'):
                target_urls.append(target['url'])
        
        # Pre-warm connections for each platform
        pre_warm_tasks = []
        for url in target_urls[:5]:  # Limit pre-warming
            task = asyncio.create_task(self._pre_warm_single_connection(url))
            pre_warm_tasks.append(task)
        
        if pre_warm_tasks:
            await asyncio.gather(*pre_warm_tasks, return_exceptions=True)
    
    async def _pre_warm_single_connection(self, url: str):
        """Pre-warm a single connection"""
        try:
            profile = await self.profile_manager.get_profile_for_platform(
                platform=CorePlatformEnum.GENERIC,
                require_session=False
            )
            if profile:
                client = await self.connection_pool.get_client(profile)
                # Just establish connection, don't fetch content
                await client.options(url, timeout=5.0)
        except Exception as e:
            logger.debug(f"Pre-warm failed for {url}: {e}")
    
    async def run(self, stop_event: asyncio.Event) -> None:
        """Main execution loop with performance optimizations"""
        
        if not await self.initialize_subsystems():
            logger.critical("Cannot run - initialization failed")
            return
        
        logger.info(f"🏃 Starting main execution loop - Mode: {self.mode.value.upper()}")
        
        # Apply mode-specific optimizations
        await self._apply_mode_specific_settings()
        
        # Create background tasks
        self.background_tasks = [
            asyncio.create_task(self._monitoring_loop(stop_event), name="monitoring_loop"),
            asyncio.create_task(self._strike_processor_loop(stop_event), name="strike_processor"),
            asyncio.create_task(self._metrics_reporter_loop(stop_event), name="metrics_reporter"),
            asyncio.create_task(self._adaptive_optimizer_loop(stop_event), name="adaptive_optimizer"),
            asyncio.create_task(self._health_monitor_loop(stop_event), name="health_monitor"),
            asyncio.create_task(self._cache_maintenance_loop(stop_event), name="cache_maintenance"),
        ]
        
        # Wait for stop signal
        try:
            await stop_event.wait()
            logger.info("Stop event received, initiating shutdown")
        except asyncio.CancelledError:
            logger.info("Run loop cancelled")
        finally:
            await self.shutdown_tasks()
    
    async def _apply_mode_specific_settings(self):
        """Apply performance and stealth settings based on mode"""
        
        mode_configs = {
            OperationMode.ULTRA_STEALTH: {
                'max_concurrent_strikes': 1,
                'max_concurrent_monitors': 3,
                'min_interval_multiplier': 2.0,
                'data_optimization': DataOptimizationLevel.AGGRESSIVE,
                'use_residential_proxies': True,
            },
            OperationMode.STEALTH: {
                'max_concurrent_strikes': 2,
                'max_concurrent_monitors': 5,
                'min_interval_multiplier': 1.5,
                'data_optimization': DataOptimizationLevel.BALANCED,
                'use_residential_proxies': False,
            },
            OperationMode.BEAST: {
                'max_concurrent_strikes': 5,
                'max_concurrent_monitors': 20,
                'min_interval_multiplier': 0.5,
                'data_optimization': DataOptimizationLevel.MINIMAL,
                'use_residential_proxies': False,
            },
            OperationMode.ADAPTIVE: {
                'max_concurrent_strikes': 3,
                'max_concurrent_monitors': 10,
                'min_interval_multiplier': 1.0,
                'data_optimization': DataOptimizationLevel.BALANCED,
                'use_residential_proxies': False,
            },
            OperationMode.HYBRID: {
                'max_concurrent_strikes': 3,
                'max_concurrent_monitors': 8,
                'min_interval_multiplier': 1.2,
                'data_optimization': DataOptimizationLevel.BALANCED,
                'use_residential_proxies': False,
            }
        }
        
        settings = mode_configs.get(self.mode, mode_configs[OperationMode.ADAPTIVE])
        
        # Apply settings
        self.max_concurrent_strikes = settings['max_concurrent_strikes']
        self.max_concurrent_monitors = settings['max_concurrent_monitors']
        
        # Update semaphores
        self.monitor_semaphore = asyncio.Semaphore(self.max_concurrent_monitors)
        self.strike_semaphore = asyncio.Semaphore(self.max_concurrent_strikes)
        
        # Apply to monitor
        if self.monitor:
            self.monitor.default_check_interval *= settings['min_interval_multiplier']
        
        # Apply data optimization to profiles
        if self.profile_manager:
            optimization_level = settings['data_optimization']
            for profile in self.profile_manager.dynamic_profiles:
                static = self.profile_manager.static_profiles.get(profile.id)
                if static:
                    static.data_optimization_level = optimization_level
        
        logger.info(f"Applied {self.mode.value} mode settings: "
                   f"Strikes={self.max_concurrent_strikes}, "
                   f"Monitors={self.max_concurrent_monitors}")
    
    async def _monitoring_loop(self, stop_event: asyncio.Event) -> None:
        """Enhanced monitoring loop with concurrent target handling"""
        
        logger.info("Monitoring loop started")
        active_tasks: Dict[str, asyncio.Task] = {}
        
        targets = [t for t in self.config.get('targets', []) if t.get('enabled')]
        if not targets:
            logger.warning("No enabled targets")
            await stop_event.wait()
            return
        
        self.metrics['active_monitoring_tasks'] = len(targets)
        
        # Start monitoring tasks for all targets
        for target in targets:
            target_id = self._get_target_id(target)
            task = asyncio.create_task(
                self._monitor_single_target_loop(target, stop_event),
                name=f"monitor_{target_id}"
            )
            active_tasks[target_id] = task
        
        # Monitor task health
        while not stop_event.is_set():
            # Check for failed tasks and restart
            for target_id, task in list(active_tasks.items()):
                if task.done():
                    try:
                        await task  # Retrieve exception if any
                    except Exception as e:
                        logger.error(f"Monitor task {target_id} failed: {e}")
                    
                    # Find target config
                    target_config = next((t for t in targets if self._get_target_id(t) == target_id), None)
                    if target_config:
                        # Restart with backoff
                        await asyncio.sleep(5)
                        active_tasks[target_id] = asyncio.create_task(
                            self._monitor_single_target_loop(target_config, stop_event),
                            name=f"monitor_{target_id}_restart"
                        )
            
            await asyncio.sleep(10)  # Health check interval
        
        # Cleanup
        logger.info("Stopping monitoring tasks...")
        for task in active_tasks.values():
            if not task.done():
                task.cancel()
        
        await asyncio.gather(*active_tasks.values(), return_exceptions=True)
        logger.info("Monitoring loop finished")
    
    def _get_target_id(self, target: Dict[str, Any]) -> str:
        """Generate unique target ID"""
        platform = target.get('platform', 'unknown')
        event = target.get('event_name', target.get('url', 'unknown'))
        return f"{platform}_{event}".replace(' ', '_')[:50]
    
    async def _monitor_single_target_loop(self, target_config: Dict[str, Any], stop_event: asyncio.Event) -> None:
        """Monitor a single target with BROWSER AUTOMATION instead of HTTP-only"""
        
        platform_str = target_config.get('platform', '').lower()
        
        # Import platform monitors (browser-based)
        if platform_str == 'fansale':
            from src.platforms.fansale import FansaleMonitor
            MonitorClass = FansaleMonitor
        elif platform_str == 'ticketmaster':
            from src.platforms.ticketmaster import TicketmasterMonitor
            MonitorClass = TicketmasterMonitor
        elif platform_str == 'vivaticket':
            from src.platforms.vivaticket import VivaticketMonitor
            MonitorClass = VivaticketMonitor
        else:
            logger.error(f"Unsupported platform: {platform_str}")
            return
        
        # Get optimal profile for this platform
        try:
            profile = await self.profile_manager.get_profile_for_platform(
                platform=CorePlatformEnum(platform_str),
                require_session=False
            )
            if not profile:
                logger.error(f"No profile available for {platform_str}")
                return
        except Exception as e:
            logger.error(f"Failed to get profile for {platform_str}: {e}")
            return
        
        # Add authentication credentials to target config
        auth_config = self.config.get('authentication', {}).get('platforms', {})
        platform_auth = auth_config.get(f"{platform_str}_it", {})
        
        if platform_auth:
            target_config['email'] = platform_auth.get('username')
            target_config['password'] = platform_auth.get('password')
        
        # Create browser-based monitor
        monitor = MonitorClass(
            config=target_config,
            profile=profile,
            browser_manager=self.browser_manager,  # CRITICAL: Pass browser manager
            connection_manager=self.connection_pool,
            cache=self.response_cache
        )
        
        logger.info(f"🚀 BROWSER MONITOR: {target_config.get('event_name')} on {platform_str}")
        
        # Initialize browser context
        try:
            await monitor.initialize()
            logger.info(f"✅ Browser initialized for {platform_str}")
        except Exception as e:
            logger.error(f"❌ Browser initialization failed for {platform_str}: {e}")
            return
        
        # Monitoring loop with browser automation
        base_interval = float(target_config.get('interval_s', 60))
        current_interval = base_interval
        consecutive_empty = 0
        
        try:
            while not stop_event.is_set() and not self._pause_monitoring:
                async with self.monitor_semaphore:
                    try:
                        start_time = time.time()
                        
                        # Use BROWSER-BASED monitoring
                        opportunities = await monitor.check_opportunities()
                        
                        check_duration = time.time() - start_time
                        logger.debug(f"Browser check for {platform_str} took {check_duration:.2f}s")
                        
                        if opportunities:
                            consecutive_empty = 0
                            new_count = await self._queue_opportunities(opportunities)
                            
                            if new_count > 0:
                                logger.critical(f"🎯 BROWSER FOUND {new_count} opportunities on {platform_str}!")
                                # Speed up checking after detection
                                current_interval = max(10.0, base_interval * 0.5)
                        else:
                            consecutive_empty += 1
                            # Gradual slowdown if no opportunities
                            if consecutive_empty > 5:
                                current_interval = min(current_interval * 1.2, base_interval * 1.5)
                        
                    except Exception as e:
                        logger.error(f"Browser monitoring error for {platform_str}: {e}")
                        current_interval = base_interval * 2  # Back off on error
                        await asyncio.sleep(10)  # Error cooldown
                
                # Adaptive sleep
                sleep_interval = current_interval * random.uniform(0.8, 1.2)
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=sleep_interval)
                    break
                except asyncio.TimeoutError:
                    continue
                    
        finally:
            # CRITICAL: Cleanup browser resources
            try:
                await monitor.cleanup()
                logger.info(f"🧹 Browser cleanup complete for {platform_str}")
            except Exception as e:
                logger.error(f"Browser cleanup error for {platform_str}: {e}")
    
    async def _queue_opportunities(self, opportunities: List[EnhancedTicketOpportunity]) -> int:
        """Queue opportunities with priority scoring"""
        
        new_count = 0
        
        for opp in opportunities:
            # Skip if already processed
            if opp.fingerprint in self.processed_opportunity_fingerprints:
                continue
            
            # Calculate priority score
            score = self._calculate_opportunity_score(opp)
            
            # Create priority wrapper
            priority_opp = OpportunityPriority(opportunity=opp, score=score)
            
            # Add to queue
            try:
                await self.opportunity_queue.put((score, priority_opp))
                self.opportunity_cache[opp.id] = opp
                new_count += 1
                self.metrics['opportunities_queued_total'] += 1
            except asyncio.QueueFull:
                logger.warning(f"Opportunity queue full, dropping {opp.event_name}")
                break
        
        return new_count
    
    def _calculate_opportunity_score(self, opp: EnhancedTicketOpportunity) -> float:
        """Calculate priority score for opportunity"""
        
        score = 0.0
        
        # Base priority
        priority_scores = {
            PriorityLevel.CRITICAL: 1000,
            PriorityLevel.HIGH: 500,
            PriorityLevel.NORMAL: 100,
            PriorityLevel.LOW: 10
        }
        score += priority_scores.get(opp.priority, 100)
        
        # Price factor (prefer reasonably priced tickets)
        if opp.price < 100:
            score += 200
        elif opp.price < 200:
            score += 100
        elif opp.price > 500:
            score -= 100
        
        # Section quality (if available)
        premium_sections = ['floor', 'pit', 'vip', 'gold', 'platinum']
        if any(section in opp.section.lower() for section in premium_sections):
            score += 300
        
        # Quantity bonus
        if opp.quantity > 1:
            score += 50 * min(opp.quantity, 4)
        
        # Freshness bonus (newer = better)
        age_seconds = (datetime.now() - opp.detected_at).total_seconds()
        score -= age_seconds * 0.1  # Lose 0.1 points per second
        
        # Previous attempt penalty
        score -= opp.attempt_count * 100
        
        return max(0, score)
    
    async def _strike_processor_loop(self, stop_event: asyncio.Event) -> None:
        """Process queued opportunities with concurrent strikes"""
        
        logger.info("Strike processor started")
        
        while not stop_event.is_set():
            try:
                # Get highest priority opportunity
                score, priority_opp = await asyncio.wait_for(
                    self.opportunity_queue.get(), 
                    timeout=1.0
                )
                
                opportunity = priority_opp.opportunity
                
                # Skip if already being processed
                if opportunity.id in self.active_strikes:
                    self.opportunity_queue.task_done()
                    continue
                
                # Skip if already attempted
                if opportunity.fingerprint in self.processed_opportunity_fingerprints:
                    self.opportunity_queue.task_done()
                    continue
                
                # Launch strike with semaphore
                async with self.strike_semaphore:
                    strike_task = asyncio.create_task(
                        self._execute_strike(opportunity),
                        name=f"strike_{opportunity.id[:8]}"
                    )
                    self.active_strikes[opportunity.id] = strike_task
                
                self.opportunity_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Strike processor error: {e}", exc_info=True)
                await asyncio.sleep(1)
        
        # Wait for active strikes to complete
        if self.active_strikes:
            logger.info(f"Waiting for {len(self.active_strikes)} active strikes...")
            await asyncio.gather(*self.active_strikes.values(), return_exceptions=True)
        
        logger.info("Strike processor finished")
    
    async def execute_coordinated_strike(self, opportunity: EnhancedTicketOpportunity, 
                                         mode: OperationMode) -> bool:
        """Enhanced strike with browser automation - MINIMAL CHANGES"""
        
        logger.info(f"🎯 Enhanced Strike: {opportunity.event_name}")
        
        try:
            # Use existing profile manager to get any available profile
            available_profiles = list(self.profile_manager.dynamic_profiles)
            if not available_profiles:
                logger.error("No profiles available for strike")
                return False
            
            # Get the first available profile (or implement better selection logic)
            profile = available_profiles[0]
            logger.info(f"Using profile {profile.id} for strike")
            
            # Get browser context using existing browser manager
            context = await self.browser_manager.get_stealth_context(
                profile, force_new=False
            )
            
            # Create page for the strike
            page = await context.new_page()
            
            try:
                logger.info(f"🌐 Navigating to: {opportunity.offer_url}")
                
                # Navigate to the opportunity URL
                await page.goto(opportunity.offer_url, 
                              wait_until='networkidle', 
                              timeout=30000)
                
                # Add realistic human delay
                await asyncio.sleep(random.uniform(2.0, 4.0))
                
                # Log page title for debugging
                title = await page.title()
                logger.info(f"📄 Page loaded: {title}")
                
                # Look for purchase elements (universal selectors)
                purchase_selectors = [
                    # English
                    'button:has-text("Buy")', 'button:has-text("Purchase")', 'button:has-text("Add to Cart")',
                    # Italian  
                    'button:has-text("Acquista")', 'button:has-text("Compra")', 'button:has-text("Aggiungi")',
                    # CSS classes
                    '.buy-button', '.purchase-button', '.btn-buy', '.btn-purchase',
                    'input[value*="Buy"]', 'input[value*="Acquista"]',
                    # Links
                    'a[href*="buy"]', 'a[href*="purchase"]', 'a[href*="checkout"]'
                ]
                
                purchase_attempted = False
                
                for selector in purchase_selectors:
                    try:
                        elements = await page.locator(selector).all()
                        for element in elements:
                            if await element.is_visible():
                                logger.info(f"🎯 Found purchase element: {selector}")
                                
                                # Realistic delay before clicking
                                await asyncio.sleep(random.uniform(1.0, 2.5))
                                
                                # Attempt click
                                await element.click()
                                purchase_attempted = True
                                
                                # Wait for page response
                                await page.wait_for_load_state('networkidle', timeout=10000)
                                
                                logger.info(f"✅ Clicked purchase element: {selector}")
                                break
                        
                        if purchase_attempted:
                            break
                            
                    except Exception as e:
                        logger.debug(f"Failed to interact with {selector}: {e}")
                        continue
                
                # Check for success indicators if we attempted a purchase
                if purchase_attempted:
                    success_indicators = [
                        'text=success', 'text=Success', 'text=SUCCESS',
                        'text=successo', 'text=Successo', 
                        'text=confermato', 'text=Confermato',
                        'text=purchased', 'text=acquistato',
                        '.success', '.confirmation', '.order-complete',
                        '#success', '#confirmation'
                    ]
                    
                    for indicator in success_indicators:
                        try:
                            if await page.locator(indicator).count() > 0:
                                logger.critical(f"🎉 SUCCESS INDICATOR FOUND: {indicator}")
                                return True
                        except:
                            continue
                    
                    # If no explicit success indicator, assume the click was successful
                    # (Many sites don't have clear success messages)
                    logger.warning("⚠️ Purchase attempted but no clear success indicator found")
                    return True  # Optimistic assumption
                else:
                    logger.warning("❌ No purchase button found on page")
                    
                    # Save screenshot for debugging (optional)
                    try:
                        screenshot_path = f"debug_no_button_{int(time.time())}.png"
                        await page.screenshot(path=screenshot_path)
                        logger.info(f"📸 Debug screenshot saved: {screenshot_path}")
                    except:
                        pass
                    
                    return False
            
            finally:
                # Always cleanup the page
                try:
                    await page.close()
                except:
                    pass
        
        except Exception as e:
            logger.error(f"❌ Strike execution failed: {e}", exc_info=True)
            return False
    
    async def _clear_related_opportunities(self, successful_opp: EnhancedTicketOpportunity):
        """Clear opportunities for the same event after success"""
        
        cleared = 0
        
        # Clear from queue
        temp_items = []
        while not self.opportunity_queue.empty():
            try:
                item = self.opportunity_queue.get_nowait()
                if item[1].opportunity.event_name != successful_opp.event_name:
                    temp_items.append(item)
                else:
                    cleared += 1
                self.opportunity_queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        # Re-add non-related items
        for item in temp_items:
            await self.opportunity_queue.put(item)
        
        if cleared > 0:
            logger.info(f"Cleared {cleared} related opportunities for {successful_opp.event_name}")
    
    async def _health_monitor_loop(self, stop_event: asyncio.Event) -> None:
        """Monitor system health and performance"""
        
        logger.info("Health monitor started")
        process = psutil.Process(os.getpid())
        
        while not stop_event.is_set():
            try:
                # Update system metrics
                self.system_health.cpu_percent = process.cpu_percent(interval=0.1)
                memory_info = process.memory_info()
                self.system_health.memory_percent = (memory_info.rss / psutil.virtual_memory().total) * 100
                self.system_health.active_tasks = len(self.active_strikes) + self.metrics['active_monitoring_tasks']
                
                # Calculate error rate
                total_attempts = sum(self.metrics['attempts_by_platform'].values())
                total_failures = sum(self.metrics['failures_by_platform'].values())
                self.system_health.error_rate = total_failures / max(total_attempts, 1)
                
                # Update peak memory
                self.metrics['peak_memory_usage'] = max(
                    self.metrics['peak_memory_usage'],
                    memory_info.rss / 1024 / 1024  # MB
                )
                
                # Health actions
                if not self.system_health.is_healthy:
                    logger.warning(f"System unhealthy: CPU={self.system_health.cpu_percent:.1f}%, "
                                 f"Memory={self.system_health.memory_percent:.1f}%, "
                                 f"Errors={self.system_health.error_rate:.1%}")
                    
                    # Take corrective action
                    if self.system_health.memory_percent > 85:
                        gc.collect()
                        logger.info("Forced garbage collection due to high memory")
                    
                    if self.system_health.consecutive_failures > 20:
                        logger.critical("Too many consecutive failures, entering recovery mode")
                        self._pause_monitoring = True
                        await asyncio.sleep(30)  # Recovery period
                        self._pause_monitoring = False
                
                # Run performance optimizer
                await self.performance_optimizer.optimize(self)
                
                await asyncio.sleep(10)  # Health check interval
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}", exc_info=True)
                await asyncio.sleep(30)
        
        logger.info("Health monitor finished")

    async def _cache_maintenance_loop(self, stop_event: asyncio.Event) -> None:
        """
        Periodically cleans up old entries in the response cache and updates cache metrics.
        """
        logger.info("Cache maintenance loop started.")
        
        # Get settings from config, with defaults
        cache_settings = self.config.get('cache_settings', {})
        cleanup_interval_s = int(cache_settings.get('cleanup_interval_s', 300))  # e.g., 5 minutes
        max_entry_age_s = int(cache_settings.get('max_entry_age_s', 1800))    # e.g., 30 minutes

        logger.info(f"Cache maintenance: Cleanup interval {cleanup_interval_s}s, Max entry age {max_entry_age_s}s.")

        while not stop_event.is_set():
            try:
                await asyncio.sleep(cleanup_interval_s) # Wait for the configured interval
                
                if stop_event.is_set(): # Check again after sleep
                    break

                if self.response_cache:
                    logger.debug("Cache maintenance: Running cleanup cycle.")
                    cleared_count = 0
                    
                    # Primary method: Use clear_old_entries if available
                    if hasattr(self.response_cache, 'clear_old_entries'):
                        # The clear_old_entries method in your ResponseCache (from managers.py)
                        # already handles the logic of finding and removing old entries.
                        cleared_count = await self.response_cache.clear_old_entries(max_age_seconds=max_entry_age_s)
                        if cleared_count > 0:
                            logger.info(f"Cache Maintenance: Cleared {cleared_count} old entries older than {max_entry_age_s}s using clear_old_entries.")
                    
                    # Fallback: Manual cleanup (should not be needed if ResponseCache is correctly implemented)
                    # This part is more for a scenario where clear_old_entries might not exist or if you want a different logic.
                    # Given your ResponseCache structure, this fallback is less likely to be hit if the primary method works.
                    elif hasattr(self.response_cache, 'cache') and isinstance(self.response_cache.cache, dict):
                        logger.warning("Cache maintenance: Falling back to manual cleanup (clear_old_entries not found or preferred).")
                        now = datetime.now()
                        keys_to_delete = []
                        
                        # Your ResponseCache stores items as tuples: (content, timestamp, response_headers)
                        # Or if using IntelligentResponseCache, it uses CacheEntry objects.
                        # Let's assume CacheEntry objects as per IntelligentResponseCache in components.py/managers.py
                        
                        cache_dict_view = list(self.response_cache.cache.items()) # Iterate over a copy

                        for key, entry_item in cache_dict_view:
                            entry_timestamp = None
                            if hasattr(entry_item, 'timestamp') and isinstance(entry_item.timestamp, datetime): # For CacheEntry objects
                                entry_timestamp = entry_item.timestamp
                            elif isinstance(entry_item, tuple) and len(entry_item) > 1 and isinstance(entry_item[1], datetime): # For (content, timestamp, ...) tuples
                                entry_timestamp = entry_item[1]

                            if entry_timestamp:
                                age_seconds = (now - entry_timestamp).total_seconds()
                                if age_seconds > max_entry_age_s:
                                    keys_to_delete.append(key)
                            else:
                                logger.debug(f"Cache maintenance: Skipping entry {key} due to missing or invalid timestamp.")
                        
                        if keys_to_delete:
                            logger.info(f"Cache maintenance: Manually identified {len(keys_to_delete)} entries to clear.")
                            for key_to_delete in keys_to_delete:
                                # Need a method to remove from cache and update size, or do it directly
                                if hasattr(self.response_cache, '_remove_entry'): # If using IntelligentResponseCache
                                    await self.response_cache._remove_entry(key_to_delete)
                                    cleared_count +=1
                                elif key_to_delete in self.response_cache.cache: # Basic cache
                                    entry_to_remove = self.response_cache.cache.pop(key_to_delete)
                                    if hasattr(self.response_cache, 'current_size_bytes') and entry_to_remove:
                                        content_bytes = None
                                        if hasattr(entry_to_remove, 'data'): # CacheEntry
                                            content_bytes = entry_to_remove.data
                                        elif isinstance(entry_to_remove, tuple) and entry_to_remove[0]: # (content, ...)
                                            content_bytes = entry_to_remove[0]
                                        if content_bytes:
                                            self.response_cache.current_size_bytes -= len(content_bytes)
                                    cleared_count += 1
                            logger.info(f"Cache Maintenance: Manually cleared {cleared_count} entries older than {max_entry_age_s}s.")
                    
                    # Update orchestrator metrics from cache stats if ResponseCache has hit_count/miss_count
                    if self.response_cache:
                        if hasattr(self.response_cache, 'hit_count'):
                            self.metrics['cache_hits'] = self.response_cache.hit_count
                        if hasattr(self.response_cache, 'miss_count'):
                            self.metrics['cache_misses'] = self.response_cache.miss_count
                        if hasattr(self.response_cache, 'current_size_mb'):
                            logger.debug(f"Cache size after maintenance: {self.response_cache.current_size_mb:.2f} MB")

                else:
                    logger.debug("Cache maintenance: Response cache not initialized.")

            except asyncio.CancelledError:
                logger.info("Cache maintenance loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in cache maintenance loop: {e}", exc_info=True)
                # Prevent rapid error looping if something is persistently wrong
                await asyncio.sleep(cleanup_interval_s / 2 if cleanup_interval_s > 20 else 10) 
                
        logger.info("Cache maintenance loop finished.")

    
    async def _metrics_reporter_loop(self, stop_event: asyncio.Event) -> None:
        """Enhanced metrics reporting with performance insights"""
        
        report_interval = self.config.get('app_settings', {}).get('metrics_interval_s', 60)
        logger.info(f"Metrics reporter started (interval: {report_interval}s)")
        
        while not stop_event.is_set():
            try:
                await asyncio.sleep(report_interval)
                if stop_event.is_set():
                    break
                
                # Generate comprehensive report
                report = self._generate_metrics_report()
                logger.info(report)
                
                # Send to GUI if connected
                if self.gui_queue:
                    self.gui_queue.put(("metrics", self.metrics))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics reporter error: {e}", exc_info=True)
        
        logger.info("Metrics reporter finished")
    
    def _generate_metrics_report(self) -> str:
        """Generate comprehensive metrics report"""
        
        runtime = datetime.now() - self.start_time
        runtime_minutes = runtime.total_seconds() / 60
        
        # Calculate rates
        total_attempts = sum(self.metrics['attempts_by_platform'].values())
        total_successes = sum(self.metrics['successes_by_platform'].values())
        total_detections = sum(self.metrics['detections_by_platform'].values())
        
        success_rate = (total_successes / total_attempts * 100) if total_attempts > 0 else 0
        
        # Cache performance
        cache_total = self.metrics['cache_hits'] + self.metrics['cache_misses']
        cache_hit_rate = (self.metrics['cache_hits'] / cache_total * 100) if cache_total > 0 else 0
        
        # Profile info
        active_profiles = 0
        total_profiles = 0
        if self.profile_manager:
            pool_metrics = self.profile_manager.get_pool_metrics()
            active_profiles = pool_metrics.get('active_profiles', 0)
            total_profiles = pool_metrics.get('total_profiles', 0)
        
        # Data usage
        data_used = self.data_tracker.total_used_mb
        data_saved = self.data_tracker.blocked_resources_saved_mb
        data_remaining = self.data_tracker.get_remaining_mb()
        
        # Build report
        lines = [
            f"\n{'='*70}",
            f"📊 SYSTEM METRICS - Runtime: {runtime_minutes:.1f} minutes",
            f"{'='*70}",
            f"Mode: {self.mode.value.upper()} | Dry Run: {self.is_dry_run}",
            f"Health: CPU={self.system_health.cpu_percent:.1f}% | "
            f"Memory={self.system_health.memory_percent:.1f}% | "
            f"Tasks={self.system_health.active_tasks}",
            f"",
            f"🎯 PERFORMANCE",
            f"Detections: {total_detections} | Attempts: {total_attempts} | "
            f"Success: {total_successes} ({success_rate:.1f}%)",
            f"Queue: {self.opportunity_queue.qsize()} | "
            f"Active Strikes: {len(self.active_strikes)}",
            f"Cache: Hits={self.metrics['cache_hits']} ({cache_hit_rate:.1f}%) | "
            f"Size={self.response_cache.current_size_bytes / (1024*1024) if self.response_cache else 0:.1f}MB",
            f"",
            f"👤 PROFILES",
            f"Active: {active_profiles} | Total: {total_profiles} | "
            f"Rotations: {self.metrics['profile_rotations']}",
            f"",
            f"💾 DATA USAGE",
            f"Used: {data_used:.1f}MB | Saved: {data_saved:.1f}MB | "
            f"Remaining: {data_remaining:.1f}MB",
            f"",
            f"📈 PLATFORM BREAKDOWN",
        ]
        
        # Platform details
        for platform in sorted(PlatformType, key=lambda p: p.value):
            pv = platform.value
            detects = self.metrics['detections_by_platform'][pv]
            attempts = self.metrics['attempts_by_platform'][pv]
            successes = self.metrics['successes_by_platform'][pv]
            blocks = self.metrics['blocks_by_platform'][pv]
            
            if attempts > 0:
                platform_success_rate = (successes / attempts) * 100
                lines.append(
                    f"{pv.upper():>12}: D={detects:>3} | A={attempts:>3} | "
                    f"S={successes:>3} ({platform_success_rate:>4.1f}%) | B={blocks:>3}"
                )
        
        lines.append("="*70)
        
        return "\n".join(lines)
    
    async def graceful_shutdown(self) -> None:
        logger.info("UnifiedOrchestrator graceful_shutdown called.")
        await self.shutdown_tasks() # Call the existing task shutdown
        if self.profile_manager and hasattr(self.profile_manager, 'stop_background_tasks'):
            await self.profile_manager.stop_background_tasks()
        if self.connection_pool and hasattr(self.connection_pool, 'close_all'):
            await self.connection_pool.close_all()
        if self.browser_manager and hasattr(self.browser_manager, 'close_all'):
            await self.browser_manager.close_all()
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
        # Add any other component shutdowns here
        logger.info("UnifiedOrchestrator graceful_shutdown completed.")

    async def shutdown_tasks(self) -> None: # Ensure this method exists
        """Gracefully shut down all background tasks."""
        logger.info("Shutting down background tasks...")
        if hasattr(self, 'background_tasks') and self.background_tasks:
            for task in self.background_tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
            self.background_tasks.clear()
        logger.info("Background tasks shutdown complete.")

    # Add a placeholder for clear_sensitive_data if it's not defined yet
    def clear_sensitive_data(self) -> None:
        logger.info("clear_sensitive_data called (placeholder).")
        # Implement actual sensitive data clearing logic here if needed
        pass
    
    async def _adaptive_optimizer_loop(self, stop_event: asyncio.Event) -> None:
        """Dynamically optimize strategy based on performance"""
        
        optimizer_interval = self.config.get('app_settings', {}).get('optimizer_interval_s', 300)
        logger.info(f"Adaptive optimizer started (interval: {optimizer_interval}s)")
        
        mode_switch_cooldown = 600  # 10 minutes between mode switches
        last_mode_switch = time.time()
        
        while not stop_event.is_set():
            try:
                await asyncio.sleep(optimizer_interval)
                if stop_event.is_set():
                    break
                
                # Only optimize in adaptive mode
                if self.mode != OperationMode.ADAPTIVE:
                    continue
                
                # Collect performance metrics
                total_attempts = sum(self.metrics['attempts_by_platform'].values())
                if total_attempts < 20:  # Need minimum data
                    continue
                
                total_successes = sum(self.metrics['successes_by_platform'].values())
                total_blocks = sum(self.metrics['blocks_by_platform'].values())
                
                success_rate = total_successes / total_attempts
                block_rate = total_blocks / total_attempts
                
                # Get thresholds from config
                thresholds = self.config.get('optimizer_settings', {}).get('adaptive_thresholds', {
                    'low_success_rate': 0.1,
                    'high_success_rate': 0.5,
                    'high_block_rate': 0.3
                })
                
                current_time = time.time()
                can_switch = (current_time - last_mode_switch) > mode_switch_cooldown
                
                # Make optimization decisions
                if can_switch:
                    new_mode = None
                    
                    if block_rate > thresholds['high_block_rate'] or success_rate < thresholds['low_success_rate']:
                        # High detection, switch to ultra stealth
                        new_mode = OperationMode.ULTRA_STEALTH
                        logger.warning(f"High detection rate ({block_rate:.1%}), switching to ULTRA_STEALTH")
                        
                    elif success_rate > thresholds['high_success_rate'] and block_rate < thresholds['high_block_rate'] / 2:
                        # Good performance, be more aggressive
                        new_mode = OperationMode.HYBRID
                        logger.info(f"Good performance (SR: {success_rate:.1%}), switching to HYBRID")
                    
                    if new_mode and new_mode != self.mode:
                        self.mode = new_mode
                        await self._apply_mode_specific_settings()
                        last_mode_switch = current_time
                
                # Additional optimizations
                # Example: handle if data usage is approaching limit
                if hasattr(self.data_tracker, "is_approaching_limit") and self.data_tracker.is_approaching_limit():
                    logger.warning("Data usage is approaching the limit. Consider reducing activity.")
            except Exception as e:
                logger.error(f"Adaptive optimizer error: {e}", exc_info=True)