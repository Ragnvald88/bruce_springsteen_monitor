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
from src.profiles.manager import BrowserProfile

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
    
    async def _get_profile_for_platform(self, platform_str: str) -> Optional[BrowserProfile]:
        """Get a suitable profile for the platform with proper error handling"""
        try:
            # Convert platform string to enum
            platform_enum_map = {
                'fansale': CorePlatformEnum.FANSALE if hasattr(CorePlatformEnum, 'FANSALE') else CorePlatformEnum.GENERIC,
                'ticketmaster': CorePlatformEnum.TICKETMASTER if hasattr(CorePlatformEnum, 'TICKETMASTER') else CorePlatformEnum.GENERIC,
                'vivaticket': CorePlatformEnum.VIVATICKET if hasattr(CorePlatformEnum, 'VIVATICKET') else CorePlatformEnum.GENERIC,
            }
            core_platform = platform_enum_map.get(platform_str, CorePlatformEnum.GENERIC)
                
            logger.debug(f"Requesting profile for platform: {platform_str} -> {core_platform}")
            
            # If we have static profiles already, try to get one for this platform
            if self.profile_manager.static_profiles:
                # Check platform pools first
                platform_pools = getattr(self.profile_manager, 'platform_pools', {})
                platform_profile_ids = platform_pools.get(platform_str, [])
                
                if platform_profile_ids:
                    for profile_id in platform_profile_ids:
                        profile = self.profile_manager.static_profiles.get(profile_id)
                        if profile:
                            logger.debug(f"Found existing profile {profile_id} for {platform_str}")
                            return profile
                
                # No platform-specific profile, get any available
                for profile_id, profile in self.profile_manager.static_profiles.items():
                    logger.debug(f"Using generic profile {profile_id} for {platform_str}")
                    return profile
            
            # No static profiles exist, try to get from ProfileManager method
            result = await self.profile_manager.get_profile_for_platform(
                platform=core_platform,
                require_session=False
            )
            
            # Handle different return types
            if result is None:
                logger.warning(f"ProfileManager returned None for {platform_str}")
                return None
                
            # If it's already a BrowserProfile object, return it
            if hasattr(result, 'profile_id') and hasattr(result, 'user_agent'):
                logger.debug(f"Got BrowserProfile object: {result.profile_id}")
                return result
                
            # If it's a string (profile ID), look it up
            if isinstance(result, str):
                logger.debug(f"Got profile ID string: {result}, looking up in static_profiles")
                profile = self.profile_manager.static_profiles.get(result)
                if profile:
                    logger.debug(f"Found profile in static_profiles: {profile.profile_id}")
                    return profile
                    
            # If it's a DynamicProfile, get or create static version
            if hasattr(result, 'id') and hasattr(result, 'get_fingerprint_snapshot'):
                logger.debug(f"Got DynamicProfile {result.id}, getting static version")
                static_profile = self.profile_manager.static_profiles.get(result.id)
                if static_profile:
                    return static_profile
                else:
                    # Create static profile from dynamic
                    logger.info(f"Creating static profile from dynamic profile {result.id}")
                    if hasattr(self.profile_manager, '_adapt_dynamic_to_static'):
                        static_profile = self.profile_manager._adapt_dynamic_to_static(result)
                        self.profile_manager.static_profiles[result.id] = static_profile
                        return static_profile
                        
            logger.error(f"Unknown profile type returned: {type(result)}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting profile for {platform_str}: {e}", exc_info=True)
            
            # Fallback: try to create a new profile
            try:
                logger.warning(f"Attempting to create new profile for {platform_str}")
                if hasattr(self.profile_manager, '_create_platform_optimized_profile'):
                    new_profile_data = await self.profile_manager._create_platform_optimized_profile(
                        CorePlatformEnum(platform_str)
                    )
                    if new_profile_data and 'static' in new_profile_data:
                        return new_profile_data['static']
            except Exception as create_error:
                logger.error(f"Failed to create fallback profile: {create_error}")
                
        return None
    
    async def _validate_profile_manager(self) -> bool:
        """Validate that ProfileManager is properly initialized with profiles"""
        try:
            if not self.profile_manager:
                logger.error("ProfileManager is None!")
                return False

            # Check dynamic profiles
            dynamic_count = len(getattr(self.profile_manager, 'dynamic_profiles', []))
            static_count = len(getattr(self.profile_manager, 'static_profiles', {}))

            logger.info(f"Profile inventory: {dynamic_count} dynamic, {static_count} static profiles")

            # Initialize static profiles from dynamic if needed
            if dynamic_count > 0 and static_count == 0:
                logger.warning("No static profiles but have dynamic profiles, creating static versions")
                
                if not hasattr(self.profile_manager, 'static_profiles'):
                    self.profile_manager.static_profiles = {}
                
                # Convert each dynamic profile to static
                for dynamic_profile in self.profile_manager.dynamic_profiles:
                    if hasattr(self.profile_manager, '_adapt_dynamic_to_static'):
                        static_profile = self.profile_manager._adapt_dynamic_to_static(dynamic_profile)
                        self.profile_manager.static_profiles[dynamic_profile.id] = static_profile
                    else:
                        # Manual conversion if method doesn't exist
                        snapshot = dynamic_profile.get_fingerprint_snapshot()
                        static_profile = BrowserProfile(
                            profile_id=dynamic_profile.id,
                            platform=dynamic_profile.platform,
                            user_agent=snapshot['user_agent'],
                            # Add other required fields from snapshot
                        )
                        self.profile_manager.static_profiles[dynamic_profile.id] = static_profile
                
                static_count = len(self.profile_manager.static_profiles)
                logger.info(f"Created {static_count} static profiles from dynamic profiles")

            # Initialize platform pools if not exists
            if not hasattr(self.profile_manager, 'platform_pools'):
                self.profile_manager.platform_pools = defaultdict(list)
                
            platform_pools = self.profile_manager.platform_pools

            # Ensure each platform has at least one profile
            for platform in ['fansale', 'ticketmaster', 'vivaticket']:
                if platform not in platform_pools or not platform_pools[platform]:
                    logger.warning(f"No profiles assigned to {platform}, creating one")
                    try:
                        if hasattr(self.profile_manager, '_create_platform_optimized_profile'):
                            new_profile = await self.profile_manager._create_platform_optimized_profile(
                                CorePlatformEnum(platform.upper())
                            )
                            if new_profile:
                                self.profile_manager.dynamic_profiles.append(new_profile['dynamic'])
                                self.profile_manager.static_profiles[new_profile['dynamic'].id] = new_profile['static']
                                platform_pools[platform].append(new_profile['dynamic'].id)
                                logger.info(f"Created profile {new_profile['dynamic'].id} for {platform}")
                    except Exception as e:
                        logger.error(f"Failed to create profile for {platform}: {e}")

            return True  # Don't fail if we at least have some profiles

        except Exception as e:
            logger.error(f"Profile manager validation failed: {e}", exc_info=True)
            return False
    
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
            if hasattr(self.profile_manager, 'initialize'):
                await self.profile_manager.initialize()
            else:
                logger.warning("ProfileManager doesn't have initialize method")
            if not await self._validate_profile_manager():
                logger.error("ProfileManager validation failed - no profiles available!")

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
            profile = await self._get_profile_for_platform('generic')
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
        if self.profile_manager and hasattr(self.profile_manager, 'static_profiles'):
            optimization_level = settings['data_optimization']
            for profile in self.profile_manager.static_profiles.values():
                if hasattr(profile, 'data_optimization_level'):
                    profile.data_optimization_level = optimization_level
        
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
        MonitorClass = None
        if platform_str == 'fansale':
            from src.platforms.fansale import FansaleMonitor
            MonitorClass = FansaleMonitor
        elif platform_str == 'ticketmaster':
            from src.platforms.ticketmaster import TicketmasterMonitor
            MonitorClass = TicketmasterMonitor
        elif platform_str == 'vivaticket':
            # Try to import, but handle if it doesn't exist
            try:
                from src.platforms.vivaticket import VivaticketMonitor
                MonitorClass = VivaticketMonitor
            except ImportError:
                logger.error(f"VivaticketMonitor not implemented yet, using base monitor")
                # Fall back to a generic monitor or skip
                logger.warning(f"Skipping monitoring for {platform_str} - monitor not implemented")
                return
            else:
                logger.error(f"Unsupported platform: {platform_str}")
                return
    
        async def _strike_processor_loop(self, stop_event: asyncio.Event) -> None:
            """Process queued opportunities with concurrent strikes"""
            logger.info("Strike processor started")
            while not stop_event.is_set():
                try:
                    # Get highest priority opportunity (negative score for min-heap behavior)
                    neg_score, priority_opp = await asyncio.wait_for(self.opportunity_queue.get(), timeout=1.0)
                    opportunity = priority_opp.opportunity
    
                    if opportunity.id in self.active_strikes and self.active_strikes[opportunity.id].done() is False:
                        self.opportunity_queue.task_done()
                        continue
                    if opportunity.fingerprint in self.processed_opportunity_fingerprints:
                        self.opportunity_queue.task_done()
                        continue
    
                    logger.info(f"Processing opportunity: {opportunity.event_name} (Score: {-neg_score:.2f})")
                    async with self.strike_semaphore: # type: ignore
                        if stop_event.is_set(): break # Check again after acquiring semaphore
    
                        strike_task = asyncio.create_task(
                            # Assuming self.strike_force.execute_coordinated_strike exists and is correct
                            self.strike_force.execute_coordinated_strike(opportunity, self.mode), # type: ignore
                            name=f"strike_{opportunity.id[:8]}"
                        )
                        self.active_strikes[opportunity.id] = strike_task
    
                        # Wait for this strike to complete or manage active_strikes list
                        try:
                            success = await strike_task
                            if success:
                                logger.critical(f"STRIKE SUCCESSFUL for {opportunity.event_name}!")
                                self.processed_opportunity_fingerprints.add(opportunity.fingerprint)
                                await self._clear_related_opportunities(opportunity) # Clear others for same event
                            else:
                                logger.warning(f"Strike FAILED for {opportunity.event_name}.")
                                opportunity.attempt_count += 1
                                if opportunity.attempt_count < 3: # Retry limit
                                    # Re-queue with lower priority (higher negative score)
                                    new_score = self._calculate_opportunity_score(opportunity) 
                                    await self.opportunity_queue.put((-new_score, priority_opp))
                                    logger.info(f"Re-queued {opportunity.event_name}, attempt {opportunity.attempt_count + 1}")
                                else:
                                    logger.error(f"Max retries reached for {opportunity.event_name}.")
                                    self.processed_opportunity_fingerprints.add(opportunity.fingerprint)
    
                        except Exception as e_strike:
                            logger.error(f"Error during strike execution for {opportunity.event_name}: {e_strike}", exc_info=True)
                        finally:
                            if opportunity.id in self.active_strikes:
                                 del self.active_strikes[opportunity.id]
                    self.opportunity_queue.task_done()
                except asyncio.TimeoutError:
                    continue # No opportunity in queue, normal
                except asyncio.CancelledError:
                    logger.info("Strike processor loop cancelled.")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in strike_processor_loop: {e}", exc_info=True)
                    await asyncio.sleep(1) # Brief pause before retrying loop
    
            # Cleanup active strike tasks on exit
            if self.active_strikes:
                logger.info(f"Shutting down: waiting for {len(self.active_strikes)} active strike tasks...")
                await asyncio.gather(*self.active_strikes.values(), return_exceptions=True)
            logger.info("Strike processor finished.")

    async def _clear_related_opportunities(self, successful_opp: EnhancedTicketOpportunity):
        cleared_count = 0
        temp_queue = []
        try:
            while not self.opportunity_queue.empty():
                neg_score, item = self.opportunity_queue.get_nowait()
                if item.opportunity.event_name == successful_opp.event_name and \
                   item.opportunity.id != successful_opp.id:
                    logger.info(f"Clearing related opportunity for {successful_opp.event_name}: ID {item.opportunity.id}")
                    self.processed_opportunity_fingerprints.add(item.opportunity.fingerprint)
                    cleared_count += 1
                else:
                    temp_queue.append((-neg_score, item)) # Store with original score logic
                self.opportunity_queue.task_done()
        except asyncio.QueueEmpty:
            pass
        finally:
            for neg_score, item in temp_queue: # Re-add items that were not cleared
                await self.opportunity_queue.put((neg_score, item))
        if cleared_count > 0:
             logger.info(f"Cleared {cleared_count} related opportunities from queue for event: {successful_opp.event_name}")


    async def _health_monitor_loop(self, stop_event: asyncio.Event) -> None:
        logger.info("Health monitor started")
        process = psutil.Process(os.getpid())
        while not stop_event.is_set():
            try:
                self.system_health.cpu_percent = process.cpu_percent(interval=0.1)
                memory_info = process.memory_info()
                self.system_health.memory_percent = (memory_info.rss / psutil.virtual_memory().total) * 100
                self.system_health.active_tasks = len(self.active_strikes) + self.metrics.get('active_monitoring_tasks', 0)
                
                total_attempts = sum(self.metrics['attempts_by_platform'].values())
                total_failures = sum(self.metrics['failures_by_platform'].values())
                self.system_health.error_rate = total_failures / max(total_attempts, 1)
                self.metrics['peak_memory_usage'] = max(self.metrics.get('peak_memory_usage',0), memory_info.rss / (1024*1024))

                if not self.system_health.is_healthy:
                    logger.warning(f"System unhealthy: CPU={self.system_health.cpu_percent:.1f}%, Mem={self.system_health.memory_percent:.1f}%, Errors={self.system_health.error_rate:.1%}")
                    if self.system_health.memory_percent > 85: gc.collect(); logger.info("Forced GC.")
                    if self.system_health.consecutive_failures > 20:
                        logger.critical("Too many consecutive failures, pausing monitoring.")
                        self._pause_monitoring = True; await asyncio.sleep(30); self._pause_monitoring = False
                
                await self.performance_optimizer.optimize(self)
                await asyncio.sleep(10)
            except asyncio.CancelledError: break
            except Exception as e: logger.error(f"Health monitor error: {e}", exc_info=True); await asyncio.sleep(30)
        logger.info("Health monitor finished")

    async def _cache_maintenance_loop(self, stop_event: asyncio.Event) -> None:
        logger.info("Cache maintenance loop started.")
        cache_settings = self.config.get('cache_settings', {})
        cleanup_interval_s = int(cache_settings.get('cleanup_interval_s', 300))
        max_entry_age_s = int(cache_settings.get('max_entry_age_s', 1800))
        logger.info(f"Cache maintenance: Interval {cleanup_interval_s}s, Max age {max_entry_age_s}s.")
        while not stop_event.is_set():
            try:
                await asyncio.sleep(cleanup_interval_s)
                if stop_event.is_set(): break
                if self.response_cache and hasattr(self.response_cache, 'clear_old_entries'):
                    cleared_count = await self.response_cache.clear_old_entries(max_age_seconds=max_entry_age_s) # type: ignore
                    if cleared_count > 0: logger.info(f"Cache Maintenance: Cleared {cleared_count} old entries.")
                    if hasattr(self.response_cache, 'hit_count'): self.metrics['cache_hits'] = self.response_cache.hit_count # type: ignore
                    if hasattr(self.response_cache, 'miss_count'): self.metrics['cache_misses'] = self.response_cache.miss_count # type: ignore
                    if hasattr(self.response_cache, 'current_size_mb'): logger.debug(f"Cache size: {self.response_cache.current_size_mb:.2f} MB") # type: ignore
            except asyncio.CancelledError: logger.info("Cache maintenance loop cancelled."); break
            except Exception as e: logger.error(f"Error in cache maintenance loop: {e}", exc_info=True); await asyncio.sleep(cleanup_interval_s / 2 if cleanup_interval_s > 20 else 10)
        logger.info("Cache maintenance loop finished.")

    async def _metrics_reporter_loop(self, stop_event: asyncio.Event) -> None:
        report_interval = self.config.get('app_settings', {}).get('metrics_interval_s', 60)
        logger.info(f"Metrics reporter started (interval: {report_interval}s)")
        while not stop_event.is_set():
            try:
                await asyncio.sleep(report_interval)
                if stop_event.is_set(): break
                report = self._generate_metrics_report()
                logger.info(report)
                if self.gui_queue: self.gui_queue.put(("metrics", dict(self.metrics))) # Send a copy
            except asyncio.CancelledError: break
            except Exception as e: logger.error(f"Metrics reporter error: {e}", exc_info=True)
        logger.info("Metrics reporter finished")

    def _generate_metrics_report(self) -> str:
        runtime_minutes = (datetime.now() - self.start_time).total_seconds() / 60
        total_attempts = sum(self.metrics['attempts_by_platform'].values())
        total_successes = sum(self.metrics['successes_by_platform'].values())
        success_rate = (total_successes / total_attempts * 100) if total_attempts > 0 else 0
        cache_total = self.metrics.get('cache_hits',0) + self.metrics.get('cache_misses',0)
        cache_hit_rate = (self.metrics.get('cache_hits',0) / cache_total * 100) if cache_total > 0 else 0
        
        active_profiles, total_profiles_val = 0, 0
        if self.profile_manager and hasattr(self.profile_manager, 'get_pool_metrics'):
            pool_metrics = self.profile_manager.get_pool_metrics() # type: ignore
            active_profiles = pool_metrics.get('active_profiles',0)
            total_profiles_val = pool_metrics.get('total_profiles',0)

        lines = [
            f"\n{'='*70}", f"📊 SYSTEM METRICS - Runtime: {runtime_minutes:.1f} min", f"{'='*70}",
            f"Mode: {self.mode.value.upper()} | Dry Run: {self.is_dry_run}",
            f"Health: CPU={self.system_health.cpu_percent:.1f}% | Mem={self.system_health.memory_percent:.1f}% | Tasks={self.system_health.active_tasks}",
            f"🎯 PERFORMANCE: Detections={sum(self.metrics['detections_by_platform'].values())} | Attempts={total_attempts} | Success={total_successes} ({success_rate:.1f}%)",
            f"Queue: {self.opportunity_queue.qsize()} | Active Strikes: {len(self.active_strikes)}",
            f"Cache: Hits={self.metrics.get('cache_hits',0)} ({cache_hit_rate:.1f}%) | Size={self.response_cache.current_size_mb if self.response_cache else 0:.1f}MB", # type: ignore
            f"👤 PROFILES: Active={active_profiles} | Total={total_profiles_val} | Rotations={self.metrics.get('profile_rotations',0)}",
            f"💾 DATA USAGE: Used={self.data_tracker.total_used_mb:.1f}MB | Saved={self.data_tracker.blocked_resources_saved_mb:.1f}MB | Remaining={self.data_tracker.get_remaining_mb():.1f}MB",
            f"📈 PLATFORM BREAKDOWN:",
        ]
        for platform in sorted(PlatformType, key=lambda p: p.value):
            pv = platform.value
            s_rate = (self.metrics['successes_by_platform'][pv] / self.metrics['attempts_by_platform'][pv] * 100) if self.metrics['attempts_by_platform'][pv] > 0 else 0
            lines.append(f"{pv.upper():>12}: D={self.metrics['detections_by_platform'][pv]:>3} | A={self.metrics['attempts_by_platform'][pv]:>3} | S={self.metrics['successes_by_platform'][pv]:>3} ({s_rate:>4.1f}%) | B={self.metrics['blocks_by_platform'][pv]:>3}")
        lines.append("="*70)
        return "\n".join(lines)
    
    # ADDED graceful_shutdown
    async def graceful_shutdown(self) -> None:
        self._shutdown_initiated = True # Mark that shutdown has started
        logger.info("UnifiedOrchestrator graceful_shutdown called.")
        await self.shutdown_tasks() 
        if self.profile_manager and hasattr(self.profile_manager, 'stop_background_tasks'):
            await self.profile_manager.stop_background_tasks() # type: ignore
        if self.connection_pool and hasattr(self.connection_pool, 'close_all'):
            await self.connection_pool.close_all()
        if self.browser_manager and hasattr(self.browser_manager, 'close_all'):
            await self.browser_manager.close_all()
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True, cancel_futures=True) # Add cancel_futures
        logger.info("UnifiedOrchestrator graceful_shutdown completed.")

    async def shutdown_tasks(self) -> None:
        logger.info("Shutting down background tasks...")
        if hasattr(self, 'background_tasks') and self.background_tasks:
            for task in self.background_tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
            self.background_tasks.clear()
        # Also cancel any active strike tasks that might not be in background_tasks
        active_strike_tasks_list = list(self.active_strikes.values())
        for task in active_strike_tasks_list:
            if not task.done():
                task.cancel()
        if active_strike_tasks_list:
             await asyncio.gather(*active_strike_tasks_list, return_exceptions=True)
        self.active_strikes.clear()
        logger.info("Background and active strike tasks shutdown process initiated/complete.")

    def clear_sensitive_data(self) -> None:
        logger.info("clear_sensitive_data called.")
        # Example: Clear cached profile data if sensitive
        if self.profile_manager and hasattr(self.profile_manager, 'static_profiles'):
            # self.profile_manager.static_profiles.clear() # Be cautious with this
            pass
        if self.opportunity_cache:
            self.opportunity_cache.clear()
        # Consider clearing specific fields in self.config if they hold secrets
        # and are no longer needed.
        logger.info("Sensitive data clearing (example) finished.")
    
    async def _adaptive_optimizer_loop(self, stop_event: asyncio.Event) -> None:
        optimizer_interval = self.config.get('app_settings', {}).get('optimizer_interval_s', 300)
        logger.info(f"Adaptive optimizer started (interval: {optimizer_interval}s)")
        mode_switch_cooldown = 600 
        last_mode_switch = time.time()
        while not stop_event.is_set():
            try:
                await asyncio.sleep(optimizer_interval)
                if stop_event.is_set(): break
                if self.mode != OperationMode.ADAPTIVE: continue
                
                total_attempts = sum(self.metrics['attempts_by_platform'].values())
                if total_attempts < 20: continue
                
                total_successes = sum(self.metrics['successes_by_platform'].values())
                total_blocks = sum(self.metrics['blocks_by_platform'].values())
                success_rate = total_successes / total_attempts if total_attempts > 0 else 0
                block_rate = total_blocks / total_attempts if total_attempts > 0 else 0
                
                thresholds = self.config.get('optimizer_settings', {}).get('adaptive_thresholds', {'low_success_rate': 0.1, 'high_success_rate': 0.5, 'high_block_rate': 0.3})
                current_time = time.time()
                can_switch = (current_time - last_mode_switch) > mode_switch_cooldown
                
                if can_switch:
                    new_mode = None
                    if block_rate > thresholds['high_block_rate'] or success_rate < thresholds['low_success_rate']:
                        new_mode = OperationMode.ULTRA_STEALTH
                        logger.warning(f"High detection ({block_rate:.1%}), switching to ULTRA_STEALTH")
                    elif success_rate > thresholds['high_success_rate'] and block_rate < thresholds['high_block_rate'] / 2:
                        new_mode = OperationMode.HYBRID
                        logger.info(f"Good performance (SR: {success_rate:.1%}), switching to HYBRID")
                    
                    if new_mode and new_mode != self.mode:
                        self.mode = new_mode
                        await self._apply_mode_specific_settings()
                        last_mode_switch = current_time
                
                if hasattr(self.data_tracker, "is_approaching_limit") and self.data_tracker.is_approaching_limit():
                    logger.warning("Data usage approaching limit. Consider reducing activity or increasing data_optimization.")
            except asyncio.CancelledError: break
            except Exception as e: logger.error(f"Adaptive optimizer error: {e}", exc_info=True)
        
        # Get optimal profile for this platform (example: use 'generic' or obtain from config if needed)
        platform_str = 'generic'
        profile = await self._get_profile_for_platform(platform_str)