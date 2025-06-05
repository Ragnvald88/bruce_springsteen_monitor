# src/core/orchestrator.py - FIXED VERSION
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
    from playwright.async_api import Playwright, Browser, BrowserContext, Page
else:
    # Runtime fallback for type annotations
    Playwright = Any
    Browser = Any
    BrowserContext = Any
    Page = Any


# Profile system imports
from ..profiles.manager import ProfileManager, BrowserProfile
from ..profiles.enums import DataOptimizationLevel, Platform as CorePlatformEnum
from ..profiles.utils import create_profile_manager_from_config

# FIXED: Correct import for advanced_profile_system (it's in core, not profiles)
from .advanced_profile_system import DetectionEvent

# Core module imports (these are already correct as relative imports)
from .enums import OperationMode, PlatformType, PriorityLevel
from .models import EnhancedTicketOpportunity, DataUsageTracker
from .managers import ConnectionPoolManager, ResponseCache, SmartBrowserContextManager
from .components import ProfileAwareLightweightMonitor
from .strike_force import ProfileIntegratedStrikeForce

logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)

@dataclass
class SystemHealth:
    """Enhanced system health tracking"""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    active_tasks: int = 0
    error_rate: float = 0.0
    last_success: Optional[datetime] = None
    consecutive_failures: int = 0
    detection_events: int = 0
    profile_rotation_rate: float = 0.0
    
    @property
    def is_healthy(self) -> bool:
        return (self.cpu_percent < 80 and 
                self.memory_percent < 85 and 
                self.error_rate < 0.3 and
                self.consecutive_failures < 10 and
                self.detection_events < 20)
    
    @property
    def threat_level(self) -> str:
        if self.detection_events > 50: return "CRITICAL"
        elif self.detection_events > 20: return "HIGH"
        elif self.detection_events > 10: return "MEDIUM"
        return "LOW"

class UnifiedOrchestrator:
    """Ultra-performance orchestrator with complete strike processing"""
    
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
        
        # Opportunity management with priority queue
        self.opportunity_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=1000)
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
            'detection_timeline': deque(maxlen=1000),  # Track detection patterns
            'success_timeline': deque(maxlen=1000),    # Track success patterns
        }
    
    async def initialize_subsystems(self) -> bool:
        """Initialize all subsystems with enhanced error handling"""
        
        if self.is_initialized:
            logger.info("Subsystems already initialized")
            return True
        
        try:
            logger.info("🔧 Initializing orchestrator subsystems...")
            
            # 1. Profile Manager
            profile_settings = self.config.get('profile_manager_settings', {})
            
            if self.mode == OperationMode.ULTRA_STEALTH:
                profile_settings['evolution_interval'] = 300
                profile_settings['min_quality_threshold'] = 0.7
            elif self.mode == OperationMode.BEAST:
                profile_settings['evolution_interval'] = 60
                profile_settings['min_quality_threshold'] = 0.3
            
            self.profile_manager = create_profile_manager_from_config(
                str(self.config_file_path),
                config_overrides=profile_settings
            )
            
            if hasattr(self.profile_manager, 'initialize'):
                # Use fast initialization for better startup performance
                await self.profile_manager.initialize(lazy_load=True)
            
            if not await self._validate_profile_manager():
                logger.error("ProfileManager validation failed!")
                return False

            profile_count = len(getattr(self.profile_manager, 'dynamic_profiles', []))
            logger.info(f"✅ ProfileManager: {profile_count} profiles loaded")
            
            # 2. Connection Pool
            self.connection_pool = ConnectionPoolManager(self.config, self.profile_manager)
            logger.info("✅ ConnectionPoolManager: Pre-warmed connections")
            
            # 3. Response Cache
            cache_size_mb = self.config.get('cache_settings', {}).get('max_size_mb', 100)
            self.response_cache = ResponseCache(max_size_mb=cache_size_mb)
            logger.info(f"✅ ResponseCache: {cache_size_mb}MB capacity")
            
            # 4. Browser Manager
            self.browser_manager = SmartBrowserContextManager(
                self.playwright, self.profile_manager, self.data_tracker, self.config
            )
            logger.info("✅ SmartBrowserContextManager: Ready")
            
            # 5. Monitor
            self.monitor = ProfileAwareLightweightMonitor(
                self.config, self.profile_manager, self.connection_pool,
                self.response_cache, self.data_tracker
            )
            logger.info("✅ ProfileAwareLightweightMonitor: Configured")
            
            # 6. Strike Force
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
    
    async def _validate_profile_manager(self) -> bool:
        """Enhanced profile manager validation"""
        try:
            if not self.profile_manager:
                logger.error("ProfileManager is None!")
                return False

            dynamic_count = len(getattr(self.profile_manager, 'dynamic_profiles', []))
            static_count = len(getattr(self.profile_manager, 'static_profiles', {}))

            logger.info(f"Profile inventory: {dynamic_count} dynamic, {static_count} static profiles")

            if dynamic_count > 0 and static_count == 0:
                logger.warning("No static profiles but have dynamic profiles, creating static versions")
                
                if not hasattr(self.profile_manager, 'static_profiles'):
                    self.profile_manager.static_profiles = {}
                
                # Convert dynamic to static
                for dynamic_profile in self.profile_manager.dynamic_profiles:
                    if hasattr(self.profile_manager, '_adapt_dynamic_to_static'):
                        static_profile = self.profile_manager._adapt_dynamic_to_static(dynamic_profile)
                        self.profile_manager.static_profiles[dynamic_profile.id] = static_profile
                
                static_count = len(self.profile_manager.static_profiles)
                logger.info(f"Created {static_count} static profiles from dynamic profiles")

            # Initialize platform pools
            if not hasattr(self.profile_manager, 'platform_pools'):
                self.profile_manager.platform_pools = defaultdict(list)
                
            platform_pools = self.profile_manager.platform_pools

            # Ensure each platform has profiles
            for platform in ['fansale', 'ticketmaster', 'vivaticket']:
                if platform not in platform_pools or not platform_pools[platform]:
                    logger.warning(f"No profiles assigned to {platform}, creating one")
                    try:
                        if hasattr(self.profile_manager, '_create_platform_optimized_profile'):
                            # Convert string to enum
                            platform_enum = getattr(CorePlatformEnum, platform.upper(), CorePlatformEnum.GENERIC)
                            new_profile = await self.profile_manager._create_platform_optimized_profile(platform_enum)
                            if new_profile:
                                self.profile_manager.dynamic_profiles.append(new_profile['dynamic'])
                                self.profile_manager.static_profiles[new_profile['dynamic'].id] = new_profile['static']
                                platform_pools[platform].append(new_profile['dynamic'].id)
                                logger.info(f"Created profile {new_profile['dynamic'].id} for {platform}")
                    except Exception as e:
                        logger.error(f"Failed to create profile for {platform}: {e}")

            return True

        except Exception as e:
            logger.error(f"Profile manager validation failed: {e}", exc_info=True)
            return False
    
    async def run(self, stop_event: asyncio.Event) -> None:
        """Main execution loop with complete task management"""
        
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
            },
            OperationMode.STEALTH: {
                'max_concurrent_strikes': 2,
                'max_concurrent_monitors': 5,
                'min_interval_multiplier': 1.5,
                'data_optimization': DataOptimizationLevel.BALANCED,
            },
            OperationMode.BEAST: {
                'max_concurrent_strikes': 5,
                'max_concurrent_monitors': 20,
                'min_interval_multiplier': 0.5,
                'data_optimization': DataOptimizationLevel.MINIMAL,
            },
            OperationMode.ADAPTIVE: {
                'max_concurrent_strikes': 3,
                'max_concurrent_monitors': 10,
                'min_interval_multiplier': 1.0,
                'data_optimization': DataOptimizationLevel.BALANCED,
            },
            OperationMode.HYBRID: {
                'max_concurrent_strikes': 3,
                'max_concurrent_monitors': 8,
                'min_interval_multiplier': 1.2,
                'data_optimization': DataOptimizationLevel.BALANCED,
            }
        }
        
        settings = mode_configs.get(self.mode, mode_configs[OperationMode.ADAPTIVE])
        
        # Apply settings
        self.max_concurrent_strikes = settings['max_concurrent_strikes']
        self.max_concurrent_monitors = settings['max_concurrent_monitors']
        
        # Update semaphores
        self.monitor_semaphore = asyncio.Semaphore(self.max_concurrent_monitors)
        self.strike_semaphore = asyncio.Semaphore(self.max_concurrent_strikes)
        
        logger.info(f"Applied {self.mode.value} mode settings: "
                   f"Strikes={self.max_concurrent_strikes}, "
                   f"Monitors={self.max_concurrent_monitors}")
    
    async def _monitoring_loop(self, stop_event: asyncio.Event) -> None:
        """Enhanced monitoring loop with platform-specific monitors"""
        
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
        """Monitor a single target with enhanced error handling"""
        
        platform_str = target_config.get('platform', '').lower()
        event_name = target_config.get('event_name', 'Unknown Event')
        url = target_config.get('url', '')
        priority = PriorityLevel[target_config.get('priority', 'normal').upper()]
        
        if not url:
            logger.error(f"No URL for target {event_name}")
            return
        
        # Convert to PlatformType
        platform_map = {
            'fansale': PlatformType.FANSALE,
            'ticketmaster': PlatformType.TICKETMASTER,
            'vivaticket': PlatformType.VIVATICKET
        }
        platform = platform_map.get(platform_str, PlatformType.FANSALE)
        
        logger.info(f"🔍 Starting monitoring for {event_name} on {platform_str}")
        
        while not stop_event.is_set():
            try:
                if self._pause_monitoring:
                    await asyncio.sleep(30)
                    continue
                
                async with self.monitor_semaphore:
                    if stop_event.is_set():
                        break
                    
                    # Monitor this target
                    opportunities = await self.monitor.check_ultra_efficient(
                        platform, url, event_name, priority
                    )
                    
                    # Process opportunities
                    for opp in opportunities:
                        await self._queue_opportunity(opp)
                
                # Dynamic interval based on mode and performance
                base_interval = target_config.get('check_interval', 60)
                if self.mode == OperationMode.BEAST:
                    base_interval *= 0.5
                elif self.mode == OperationMode.ULTRA_STEALTH:
                    base_interval *= 2.0
                
                # Add jitter
                interval = base_interval + random.uniform(-5, 5)
                await asyncio.sleep(max(5, interval))
                
            except asyncio.CancelledError:
                logger.info(f"Monitor for {event_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Monitor error for {event_name}: {e}")
                await asyncio.sleep(30)  # Backoff on error
    
    async def _queue_opportunity(self, opportunity: EnhancedTicketOpportunity):
        """Enhanced opportunity queuing with deduplication"""
        
        # Check if already processed
        if opportunity.fingerprint in self.processed_opportunity_fingerprints:
            return
        
        # Check if already in queue
        if opportunity.id in self.opportunity_cache:
            return
        
        # Calculate priority score
        score = self._calculate_opportunity_score(opportunity)
        
        try:
            # Add to queue (negative score for min-heap priority)
            await self.opportunity_queue.put((-score, opportunity))
            self.opportunity_cache[opportunity.id] = opportunity
            self.metrics['opportunities_queued_total'] += 1
            
            logger.info(f"🎯 Queued opportunity: {opportunity.event_name} (Score: {score:.2f})")
            
            # Notify GUI
            if self.gui_queue:
                self.gui_queue.put(("opportunity", {
                    'id': opportunity.id,
                    'event': opportunity.event_name,
                    'platform': opportunity.platform.value,
                    'price': opportunity.price,
                    'section': opportunity.section,
                    'score': score
                }))
                
        except asyncio.QueueFull:
            logger.warning(f"Opportunity queue full, dropping: {opportunity.event_name}")
    
    def _calculate_opportunity_score(self, opportunity: EnhancedTicketOpportunity) -> float:
        """Calculate opportunity priority score"""
        base_score = 100.0
        
        # Priority weight
        priority_weights = {
            PriorityLevel.CRITICAL: 50,
            PriorityLevel.HIGH: 30,
            PriorityLevel.NORMAL: 10,
            PriorityLevel.LOW: 0
        }
        base_score += priority_weights.get(opportunity.priority, 0)
        
        # Freshness bonus
        age_minutes = opportunity.age_seconds / 60
        freshness_bonus = max(0, 20 - age_minutes * 2)
        base_score += freshness_bonus
        
        # Confidence bonus
        base_score += (opportunity.confidence_score - 0.5) * 40
        
        # Attempt penalty
        base_score -= opportunity.attempt_count * 10
        
        # Mode-specific adjustments
        if self.mode == OperationMode.BEAST:
            if opportunity.priority == PriorityLevel.CRITICAL:
                base_score += 30
        elif self.mode == OperationMode.ULTRA_STEALTH:
            if opportunity.verification_status:
                base_score += 15
        
        return max(0, base_score)
    
    # FIXED: Complete _strike_processor_loop implementation
    async def _strike_processor_loop(self, stop_event: asyncio.Event) -> None:
        """FIXED: Complete strike processor with proper error handling"""
        logger.info("Strike processor started")
        
        while not stop_event.is_set():
            try:
                # Get highest priority opportunity (with timeout)
                try:
                    neg_score, opportunity = await asyncio.wait_for(
                        self.opportunity_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue  # No opportunity in queue
                
                # Skip if already being processed
                if opportunity.id in self.active_strikes:
                    if not self.active_strikes[opportunity.id].done():
                        self.opportunity_queue.task_done()
                        continue
                
                # Skip if already processed
                if opportunity.fingerprint in self.processed_opportunity_fingerprints:
                    self.opportunity_queue.task_done()
                    continue
                
                logger.info(f"🎯 Processing opportunity: {opportunity.event_name} (Score: {-neg_score:.2f})")
                
                # Execute strike with semaphore control
                async with self.strike_semaphore:
                    if stop_event.is_set():
                        break
                    
                    # Create strike task
                    strike_task = asyncio.create_task(
                        self.strike_force.execute_coordinated_strike(opportunity, self.mode),
                        name=f"strike_{opportunity.id[:8]}"
                    )
                    self.active_strikes[opportunity.id] = strike_task
                    
                    try:
                        # Wait for strike completion
                        success = await strike_task
                        
                        # Record metrics
                        self.metrics['opportunities_processed_total'] += 1
                        self.metrics['attempts_by_platform'][opportunity.platform.value] += 1
                        
                        if success:
                            logger.critical(f"🎉 STRIKE SUCCESS for {opportunity.event_name}!")
                            self.metrics['successes_by_platform'][opportunity.platform.value] += 1
                            self.system_health.last_success = datetime.now()
                            self.system_health.consecutive_failures = 0
                            
                            # Mark as processed
                            self.processed_opportunity_fingerprints.add(opportunity.fingerprint)
                            
                            # Clear related opportunities
                            await self._clear_related_opportunities(opportunity)
                            
                            # Notify GUI
                            if self.gui_queue:
                                self.gui_queue.put(("strike_success", {
                                    'event': opportunity.event_name,
                                    'platform': opportunity.platform.value,
                                    'price': opportunity.price
                                }))
                        
                        else:
                            logger.warning(f"⚠️ Strike FAILED for {opportunity.event_name}")
                            self.metrics['failures_by_platform'][opportunity.platform.value] += 1
                            self.system_health.consecutive_failures += 1
                            
                            # Retry logic
                            opportunity.attempt_count += 1
                            if opportunity.attempt_count < 3:
                                # Re-queue with lower priority
                                new_score = self._calculate_opportunity_score(opportunity)
                                await self.opportunity_queue.put((-new_score, opportunity))
                                logger.info(f"♻️ Re-queued {opportunity.event_name}, attempt {opportunity.attempt_count + 1}")
                            else:
                                logger.error(f"❌ Max retries reached for {opportunity.event_name}")
                                self.processed_opportunity_fingerprints.add(opportunity.fingerprint)
                    
                    except Exception as e:
                        logger.error(f"Strike execution error for {opportunity.event_name}: {e}", exc_info=True)
                        self.metrics['failures_by_platform'][opportunity.platform.value] += 1
                        self.system_health.consecutive_failures += 1
                    
                    finally:
                        # Clean up active strike
                        if opportunity.id in self.active_strikes:
                            del self.active_strikes[opportunity.id]
                
                # Mark queue task as done
                self.opportunity_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info("Strike processor loop cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error in strike processor: {e}", exc_info=True)
                await asyncio.sleep(1)  # Brief pause before retrying
        
        # Cleanup active strikes on exit
        if self.active_strikes:
            logger.info(f"Shutting down: waiting for {len(self.active_strikes)} active strikes...")
            await asyncio.gather(*self.active_strikes.values(), return_exceptions=True)
        
        logger.info("Strike processor finished")
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
                platform=CorePlatformEnum.GENERIC,  # Assuming CorePlatformEnum is accessible
                require_session=False
            )
            if profile:
                client = await self.connection_pool.get_client(profile)
                # Just establish connection, don't fetch content
                await client.options(url, timeout=5.0)
        except Exception as e:
            logger.debug(f"Pre-warm failed for {url}: {e}")
        
    async def _clear_related_opportunities(self, successful_opp: EnhancedTicketOpportunity):
        """Clear related opportunities after success"""
        cleared_count = 0
        temp_queue = []
        
        try:
            # Drain queue and filter
            while not self.opportunity_queue.empty():
                try:
                    neg_score, item = self.opportunity_queue.get_nowait()
                    
                    # Check if related to successful opportunity
                    if (item.event_name == successful_opp.event_name and 
                        item.id != successful_opp.id):
                        logger.info(f"🗑️ Clearing related opportunity: {item.id}")
                        self.processed_opportunity_fingerprints.add(item.fingerprint)
                        cleared_count += 1
                    else:
                        temp_queue.append((neg_score, item))
                    
                    self.opportunity_queue.task_done()
                    
                except asyncio.QueueEmpty:
                    break
        
        except Exception as e:
            logger.error(f"Error clearing related opportunities: {e}")
        
        finally:
            # Re-add non-related items
            for neg_score, item in temp_queue:
                try:
                    await self.opportunity_queue.put((neg_score, item))
                except asyncio.QueueFull:
                    logger.warning(f"Queue full, dropping opportunity: {item.id}")
        
        if cleared_count > 0:
            logger.info(f"✅ Cleared {cleared_count} related opportunities for {successful_opp.event_name}")
    
    async def _health_monitor_loop(self, stop_event: asyncio.Event) -> None:
        """Enhanced health monitoring with threat detection"""
        logger.info("Health monitor started")
        process = psutil.Process(os.getpid())
        
        while not stop_event.is_set():
            try:
                # Collect system metrics
                self.system_health.cpu_percent = process.cpu_percent(interval=0.1)
                memory_info = process.memory_info()
                self.system_health.memory_percent = (memory_info.rss / psutil.virtual_memory().total) * 100
                self.system_health.active_tasks = len(self.active_strikes) + self.metrics.get('active_monitoring_tasks', 0)
                
                # Calculate error rate
                total_attempts = sum(self.metrics['attempts_by_platform'].values())
                total_failures = sum(self.metrics['failures_by_platform'].values())
                self.system_health.error_rate = total_failures / max(total_attempts, 1)
                
                # Track detection events
                total_blocks = sum(self.metrics['blocks_by_platform'].values())
                self.system_health.detection_events = total_blocks
                
                # Update peak memory
                self.metrics['peak_memory_usage'] = max(
                    self.metrics.get('peak_memory_usage', 0), 
                    memory_info.rss / (1024*1024)
                )
                
                # Health assessment and actions
                if not self.system_health.is_healthy:
                    threat_level = self.system_health.threat_level
                    logger.warning(f"🚨 System unhealthy [Threat: {threat_level}]: "
                                 f"CPU={self.system_health.cpu_percent:.1f}%, "
                                 f"Mem={self.system_health.memory_percent:.1f}%, "
                                 f"Errors={self.system_health.error_rate:.1%}, "
                                 f"Detections={self.system_health.detection_events}")
                    
                    # Automatic remediation
                    if self.system_health.memory_percent > 85:
                        gc.collect()
                        logger.info("🧹 Forced garbage collection")
                    
                    if self.system_health.consecutive_failures > 20:
                        logger.critical("🚨 Too many consecutive failures, activating defensive mode")
                        self._pause_monitoring = True
                        await asyncio.sleep(30)
                        self._pause_monitoring = False
                    
                    if threat_level == "CRITICAL":
                        logger.critical("🔴 CRITICAL threat level - implementing emergency protocols")
                        # Switch to ultra stealth mode temporarily
                        if self.mode != OperationMode.ULTRA_STEALTH:
                            logger.info("🥷 Emergency switch to ULTRA_STEALTH mode")
                            self.mode = OperationMode.ULTRA_STEALTH
                            await self._apply_mode_specific_settings()
                
                # Notify GUI of health status
                if self.gui_queue:
                    self.gui_queue.put(("health", {
                        'cpu': self.system_health.cpu_percent,
                        'memory': self.system_health.memory_percent,
                        'error_rate': self.system_health.error_rate,
                        'threat_level': self.system_health.threat_level,
                        'is_healthy': self.system_health.is_healthy,
                        'detection_events': self.system_health.detection_events,
                        'consecutive_failures': self.system_health.consecutive_failures
                    }))
                
                await asyncio.sleep(10)  # Health check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}", exc_info=True)
                await asyncio.sleep(30)
        
        logger.info("Health monitor finished")
    
    async def _cache_maintenance_loop(self, stop_event: asyncio.Event) -> None:
        """Enhanced cache maintenance with metrics"""
        logger.info("Cache maintenance loop started")
        cache_settings = self.config.get('cache_settings', {})
        cleanup_interval_s = int(cache_settings.get('cleanup_interval_s', 300))
        max_entry_age_s = int(cache_settings.get('max_entry_age_s', 1800))
        
        while not stop_event.is_set():
            try:
                await asyncio.sleep(cleanup_interval_s)
                if stop_event.is_set():
                    break
                
                if self.response_cache and hasattr(self.response_cache, 'clear_old_entries'):
                    cleared_count = await self.response_cache.clear_old_entries(max_age_seconds=max_entry_age_s)
                    if cleared_count > 0:
                        logger.info(f"🧹 Cache maintenance: Cleared {cleared_count} old entries")
                    
                    # Update cache metrics
                    if hasattr(self.response_cache, 'hit_count'):
                        self.metrics['cache_hits'] = self.response_cache.hit_count
                    if hasattr(self.response_cache, 'miss_count'):
                        self.metrics['cache_misses'] = self.response_cache.miss_count
                    if hasattr(self.response_cache, 'current_size_mb'):
                        cache_size = self.response_cache.current_size_mb
                        logger.debug(f"📊 Cache size: {cache_size:.2f} MB")
                        
                        # Notify GUI
                        if self.gui_queue:
                            self.gui_queue.put(("cache", {
                                'size_mb': cache_size,
                                'hits': self.metrics['cache_hits'],
                                'misses': self.metrics['cache_misses'],
                                'hit_rate': self.response_cache.hit_rate if hasattr(self.response_cache, 'hit_rate') else 0
                            }))
                
            except asyncio.CancelledError:
                logger.info("Cache maintenance loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cache maintenance loop: {e}", exc_info=True)
                await asyncio.sleep(cleanup_interval_s / 2 if cleanup_interval_s > 20 else 10)
        
        logger.info("Cache maintenance loop finished")
    
    async def _metrics_reporter_loop(self, stop_event: asyncio.Event) -> None:
        """Enhanced metrics reporting with GUI updates"""
        report_interval = self.config.get('app_settings', {}).get('metrics_interval_s', 60)
        logger.info(f"Metrics reporter started (interval: {report_interval}s)")
        
        while not stop_event.is_set():
            try:
                await asyncio.sleep(report_interval)
                if stop_event.is_set():
                    break
                
                # Generate and log report
                report = self._generate_metrics_report()
                logger.info(report)
                
                # Send detailed metrics to GUI
                if self.gui_queue:
                    detailed_metrics = self._get_detailed_metrics()
                    self.gui_queue.put(("metrics", detailed_metrics))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics reporter error: {e}", exc_info=True)
        
        logger.info("Metrics reporter finished")
    
    def _generate_metrics_report(self) -> str:
        """Generate comprehensive metrics report"""
        runtime_minutes = (datetime.now() - self.start_time).total_seconds() / 60
        total_attempts = sum(self.metrics['attempts_by_platform'].values())
        total_successes = sum(self.metrics['successes_by_platform'].values())
        success_rate = (total_successes / total_attempts * 100) if total_attempts > 0 else 0
        cache_total = self.metrics.get('cache_hits', 0) + self.metrics.get('cache_misses', 0)
        cache_hit_rate = (self.metrics.get('cache_hits', 0) / cache_total * 100) if cache_total > 0 else 0
        
        # Profile metrics
        active_profiles, total_profiles_val = 0, 0
        if self.profile_manager and hasattr(self.profile_manager, 'get_pool_metrics'):
            try:
                pool_metrics = self.profile_manager.get_pool_metrics()
                active_profiles = pool_metrics.get('active_profiles', 0)
                total_profiles_val = pool_metrics.get('total_profiles', 0)
            except Exception:
                pass
        
        lines = [
            f"\n{'='*80}",
            f"📊 ULTRA-STEALTH SYSTEM METRICS - Runtime: {runtime_minutes:.1f} min",
            f"{'='*80}",
            f"🎯 MODE: {self.mode.value.upper()} | Dry Run: {self.is_dry_run} | Threat: {self.system_health.threat_level}",
            f"💊 HEALTH: CPU={self.system_health.cpu_percent:.1f}% | Mem={self.system_health.memory_percent:.1f}% | Tasks={self.system_health.active_tasks}",
            f"🎯 PERFORMANCE: Detections={sum(self.metrics['detections_by_platform'].values())} | Attempts={total_attempts} | Success={total_successes} ({success_rate:.1f}%)",
            f"⚡ QUEUE: Pending={self.opportunity_queue.qsize()} | Active Strikes={len(self.active_strikes)} | Processed={self.metrics['opportunities_processed_total']}",
            f"💾 CACHE: Hits={self.metrics.get('cache_hits', 0)} ({cache_hit_rate:.1f}%) | Size={self.response_cache.current_size_mb if self.response_cache else 0:.1f}MB",
            f"👤 PROFILES: Active={active_profiles} | Total={total_profiles_val} | Rotations={self.metrics.get('profile_rotations', 0)}",
            f"📊 DATA USAGE: Used={self.data_tracker.total_used_mb:.1f}MB | Saved={self.data_tracker.blocked_resources_saved_mb:.1f}MB | Remaining={self.data_tracker.get_remaining_mb():.1f}MB",
            f"🏆 PLATFORM BREAKDOWN:",
        ]
        
        for platform in [PlatformType.FANSALE, PlatformType.TICKETMASTER, PlatformType.VIVATICKET]:
            pv = platform.value
            attempts = self.metrics['attempts_by_platform'][pv]
            successes = self.metrics['successes_by_platform'][pv]
            s_rate = (successes / attempts * 100) if attempts > 0 else 0
            blocks = self.metrics['blocks_by_platform'][pv]
            detections = self.metrics['detections_by_platform'][pv]
            
            lines.append(f"  {pv.upper():>12}: D={detections:>3} | A={attempts:>3} | S={successes:>3} ({s_rate:>4.1f}%) | B={blocks:>3}")
        
        lines.append("="*80)
        return "\n".join(lines)
    
    def _get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics for GUI dashboard"""
        runtime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'runtime_seconds': runtime_seconds,
            'mode': self.mode.value,
            'health': {
                'cpu_percent': self.system_health.cpu_percent,
                'memory_percent': self.system_health.memory_percent,
                'threat_level': self.system_health.threat_level,
                'is_healthy': self.system_health.is_healthy,
                'detection_events': self.system_health.detection_events,
                'consecutive_failures': self.system_health.consecutive_failures
            },
            'performance': {
                'total_attempts': sum(self.metrics['attempts_by_platform'].values()),
                'total_successes': sum(self.metrics['successes_by_platform'].values()),
                'total_detections': sum(self.metrics['detections_by_platform'].values()),
                'queue_size': self.opportunity_queue.qsize(),
                'active_strikes': len(self.active_strikes),
                'opportunities_processed': self.metrics['opportunities_processed_total']
            },
            'platforms': {
                platform.value: {
                    'attempts': self.metrics['attempts_by_platform'][platform.value],
                    'successes': self.metrics['successes_by_platform'][platform.value],
                    'failures': self.metrics['failures_by_platform'][platform.value],
                    'blocks': self.metrics['blocks_by_platform'][platform.value],
                    'detections': self.metrics['detections_by_platform'][platform.value]
                }
                for platform in [PlatformType.FANSALE, PlatformType.TICKETMASTER, PlatformType.VIVATICKET]
            },
            'cache': {
                'hits': self.metrics.get('cache_hits', 0),
                'misses': self.metrics.get('cache_misses', 0),
                'size_mb': self.response_cache.current_size_mb if self.response_cache else 0
            },
            'data': {
                'used_mb': self.data_tracker.total_used_mb,
                'saved_mb': self.data_tracker.blocked_resources_saved_mb,
                'remaining_mb': self.data_tracker.get_remaining_mb()
            }
        }
    
    async def graceful_shutdown(self) -> None:
        """Enhanced graceful shutdown"""
        self._shutdown_initiated = True
        logger.info("🛑 UnifiedOrchestrator graceful shutdown initiated")
        
        try:
            # Stop background tasks
            await self.shutdown_tasks()
            
            # Stop profile manager
            if self.profile_manager and hasattr(self.profile_manager, 'stop_background_tasks'):
                await self.profile_manager.stop_background_tasks()
            
            # Close connections
            if self.connection_pool and hasattr(self.connection_pool, 'close_all'):
                await self.connection_pool.close_all()
            
            # Close browsers
            if self.browser_manager and hasattr(self.browser_manager, 'close_all'):
                await self.browser_manager.close_all()
            
            logger.info("✅ UnifiedOrchestrator graceful shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}", exc_info=True)
    
    async def shutdown_tasks(self) -> None:
        """Enhanced task shutdown"""
        logger.info("🔄 Shutting down background tasks...")
        
        if hasattr(self, 'background_tasks') and self.background_tasks:
            # Cancel all tasks
            for task in self.background_tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for completion
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
            self.background_tasks.clear()
        
        # Cancel active strikes
        if self.active_strikes:
            active_strike_tasks = list(self.active_strikes.values())
            for task in active_strike_tasks:
                if not task.done():
                    task.cancel()
            
            await asyncio.gather(*active_strike_tasks, return_exceptions=True)
            self.active_strikes.clear()
        
        logger.info("✅ Background and strike tasks shutdown complete")
    
    def clear_sensitive_data(self) -> None:
        """Clear sensitive data for security"""
        logger.info("🔒 Clearing sensitive data...")
        
        # Clear opportunity data
        if self.opportunity_cache:
            self.opportunity_cache.clear()
        
        # Clear processed fingerprints
        self.processed_opportunity_fingerprints.clear()
        
        # Clear metrics that might contain sensitive info
        sensitive_metrics = ['profile_performance', 'detection_timeline', 'success_timeline']
        for metric in sensitive_metrics:
            if metric in self.metrics:
                self.metrics[metric].clear()
        
        logger.info("✅ Sensitive data cleared")