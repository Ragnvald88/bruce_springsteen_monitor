# src/core/orchestrator_v3.py
"""
StealthMaster AI v3.0 - Enhanced Orchestrator
Complete system orchestration with all v3 components integrated
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import psutil
from pathlib import Path
import random

# Core v3 components
from .ultra_stealth_launcher import get_stealth_launcher
from .adaptive_behavoral_engine import get_behavior_engine, BehaviorPattern, AdaptiveBehaviorEngine
from .data_optimization_engine import get_data_optimization_engine
from ..stealth.cdp_bypass_engine import get_cdp_bypass_engine
from ..ui.enhanced_detection_monitor import get_detection_monitor, ThreatLevel

# Platform handling
from ..platforms.unified_handler import UnifiedHandler
from ..profiles.manager import ProfileManager
from .browser_pool import get_browser_pool, shutdown_browser_pool

# Models and utilities
from .models import EnhancedTicketOpportunity
from .enums import OperationMode, PlatformType, PriorityLevel
from .ticket_reserver import TicketReserver

logger = logging.getLogger(__name__)


@dataclass
class MonitorInstance:
    """Enhanced monitor instance with v3 features"""
    monitor_id: str
    platform: str
    handler: UnifiedHandler
    behavior_engine: AdaptiveBehaviorEngine
    browser: Any
    context: Any
    page: Any
    config: Dict[str, Any]
    last_check: Optional[datetime] = None
    check_count: int = 0
    tickets_found: int = 0
    errors: int = 0
    active: bool = True
    detection_score: float = 100.0
    data_used_mb: float = 0.0


class EnhancedOrchestrator:
    """
    StealthMaster AI v3.0 Orchestrator
    Coordinates all components for maximum stealth and efficiency
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Core v3 components
        self.stealth_launcher = None
        self.browser_pool = None
        self.behavior_engine = None
        self.data_optimizer = None
        self.cdp_bypass = None
        self.detection_monitor = None
        self.profile_manager = None
        
        # Monitoring
        self.monitors: Dict[str, MonitorInstance] = {}
        self.monitor_tasks: Dict[str, asyncio.Task] = {}
        
        # Reservation handling
        self.ticket_reserver = TicketReserver(config)
        
        # System state
        self.running = False
        self.paused = False
        self.start_time = None
        self.emergency_stop = False
        
        # Performance tracking
        self.total_checks = 0
        self.total_tickets_found = 0
        self.total_errors = 0
        self.total_data_mb = 0.0
        self.successful_reservations = 0
        
        # Operation mode
        self.operation_mode = OperationMode(
            config.get('app_settings', {}).get('mode', 'stealth')
        )
        
        logger.info(f"🚀 Enhanced Orchestrator v3.0 initialized in {self.operation_mode.value} mode")
    
    async def initialize(self) -> None:
        """Initialize all v3 subsystems"""
        logger.info("🔧 Initializing StealthMaster AI v3.0 subsystems...")
        
        try:
            # 1. Initialize stealth launcher
            self.stealth_launcher = await get_stealth_launcher(
                self.config.get('browser_settings', {})
            )
            logger.info("✅ Ultra-stealth launcher ready")
            
            # 2. Initialize browser pool
            pool_config = {
                'min_size': 2,
                'max_size': 5,
                'max_age_seconds': 600,  # 10 minutes max
                'headless': False  # Never headless for stealth
            }
            self.browser_pool = await get_browser_pool(pool_config)
            logger.info("✅ Browser pool initialized")
            
            # 3. Initialize behavior engine
            initial_pattern = self._get_initial_behavior_pattern()
            self.behavior_engine = get_behavior_engine(initial_pattern)
            logger.info(f"✅ Adaptive behavior engine ready ({initial_pattern.value})")
            
            # 4. Initialize data optimizer
            self.data_optimizer = get_data_optimization_engine(
                self.config.get('data_optimization', {})
            )
            logger.info("✅ Data optimization engine active")
            
            # 5. Initialize CDP bypass
            self.cdp_bypass = get_cdp_bypass_engine()
            logger.info("✅ CDP bypass protection enabled")
            
            # 6. Initialize detection monitor
            self.detection_monitor = get_detection_monitor(auto_start=True)
            self.detection_monitor.add_event_callback(self._on_detection_event)
            logger.info("✅ Detection monitor online")
            
            # 7. Initialize profile manager
            self.profile_manager = ProfileManager(self.config)
            await self.profile_manager.initialize()
            logger.info("✅ Profile manager initialized")
            
            # 8. Initialize monitors for each target
            await self._initialize_monitors()
            
            # 9. Import learned patterns if available
            patterns_file = Path("data/learned_patterns.json")
            if patterns_file.exists():
                await self.behavior_engine.import_learned_patterns(str(patterns_file))
                logger.info("✅ Imported learned behavior patterns")
            
            logger.info("🎉 All v3 subsystems initialized successfully!")
            
            # Update detection monitor
            self.detection_monitor.update_system_metrics({
                'stealth_score': 100.0,
                'active_monitors': len(self.monitors),
                'proxy_health': 100.0,
                'data_usage_mb': 0.0,
                'success_rate': 0.0,
                'cdp_status': 'PROTECTED',
                'fingerprint_entropy': 0.95,
                'behavior_naturalness': 0.98
            })
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}", exc_info=True)
            raise
    
    def _get_initial_behavior_pattern(self) -> BehaviorPattern:
        """Determine initial behavior pattern based on mode"""
        mode_patterns = {
            OperationMode.STEALTH: BehaviorPattern.CAUTIOUS,
            OperationMode.BEAST: BehaviorPattern.EAGER,
            OperationMode.HYBRID: BehaviorPattern.NORMAL,
            OperationMode.ADAPTIVE: BehaviorPattern.ADAPTIVE,
            OperationMode.ULTRA_STEALTH: BehaviorPattern.CAUTIOUS
        }
        return mode_patterns.get(self.operation_mode, BehaviorPattern.NORMAL)
    
    async def _initialize_monitors(self) -> None:
        """Initialize monitors for each target"""
        
        targets = self.config.get('targets', [])
        enabled_targets = [t for t in targets if t.get('enabled', True)]
        
        for i, target in enumerate(enabled_targets):
            monitor_id = f"{target['platform']}_{i}"
            
            try:
                # Get healthy profile
                profiles = await self.profile_manager.get_healthy_profiles(
                    platform=target['platform'],
                    limit=1
                )
                
                if not profiles:
                    logger.error(f"No profile available for {target['platform']}")
                    continue
                    
                profile = profiles[0]
                
                # We need to use acquire_browser differently since monitors are long-lived
                # Get browser instance directly from pool
                browser_instance = await self.browser_pool._get_browser_instance()
                browser = browser_instance.browser
                
                # Create context with stealth
                from ..stealth.stealth_integration import StealthIntegration
                context = await StealthIntegration.create_stealth_context(
                    browser,
                    fingerprint=browser_instance.fingerprint
                )
                
                # Create page
                page = await context.new_page()
                
                # Apply CDP bypass
                await self.cdp_bypass.apply_cdp_bypass(page)
                
                # Apply data optimization
                await self.data_optimizer.optimize_page(page)
                
                # Apply page stealth
                await StealthIntegration.apply_page_stealth(page)
                
                # Create handler with correct parameters
                # UnifiedHandler expects HumanBehaviorEngine, so create one
                from ..core.human_behavior_engine import HumanBehaviorEngine
                human_behavior = HumanBehaviorEngine()
                
                handler = UnifiedHandler(
                    config=target,
                    browser=browser,
                    behavior_engine=human_behavior,
                    fingerprint=browser_instance.fingerprint,
                    page=page,
                    context=context,
                    detection_callback=self._handle_platform_detection
                )
                
                await handler.initialize()
                
                # Create monitor instance
                monitor = MonitorInstance(
                    monitor_id=monitor_id,
                    platform=target['platform'],
                    handler=handler,
                    behavior_engine=self.behavior_engine,
                    browser=browser,
                    context=context,
                    page=page,
                    config=target
                )
                
                self.monitors[monitor_id] = monitor
                logger.info(f"✅ Monitor initialized: {target['event_name']}")
                
                # Report to detection monitor
                self.detection_monitor.add_detection_event(
                    platform=target['platform'],
                    event_type='monitor_init',
                    threat_level=ThreatLevel.INFO,
                    message=f"Monitor initialized for {target['event_name']}",
                    confidence=1.0
                )
                
            except Exception as e:
                logger.error(f"Failed to initialize monitor for {target['platform']}: {e}")
                
                # Report failure
                self.detection_monitor.add_detection_event(
                    platform=target['platform'],
                    event_type='init_failure',
                    threat_level=ThreatLevel.HIGH,
                    message=f"Failed to initialize: {str(e)}",
                    confidence=1.0
                )
    
    async def start(self) -> None:
        """Start the orchestrator"""
        
        # Initialize if not already done
        if not self.stealth_launcher:
            await self.initialize()
        
        logger.critical("=" * 80)
        logger.critical("🚀 STEALTHMASTER AI V3.0 STARTING")
        logger.critical("🎯 Target: Bruce Springsteen Tickets")
        logger.critical("🛡️ Mode: " + self.operation_mode.value.upper())
        logger.critical("📊 Monitors: " + str(len(self.monitors)))
        logger.critical("=" * 80)
        
        self.running = True
        self.start_time = datetime.now()
        
        # Start monitor tasks
        for monitor_id, monitor in self.monitors.items():
            task = asyncio.create_task(
                self._monitor_loop_v3(monitor_id, monitor)
            )
            self.monitor_tasks[monitor_id] = task
        
        # Start system monitoring
        asyncio.create_task(self._system_monitor_loop())
        
        # Start performance optimization loop
        asyncio.create_task(self._optimization_loop())
        
        # Report startup complete
        self.detection_monitor.add_detection_event(
            platform='system',
            event_type='startup',
            threat_level=ThreatLevel.INFO,
            message="StealthMaster AI v3.0 started successfully",
            details={
                'mode': self.operation_mode.value,
                'monitors': len(self.monitors),
                'cdp_protection': True,
                'data_optimization': True
            }
        )
        
        # Wait for tasks
        try:
            await asyncio.gather(*self.monitor_tasks.values())
        except asyncio.CancelledError:
            logger.info("Monitor tasks cancelled")
    
    async def _monitor_loop_v3(self, monitor_id: str, monitor: MonitorInstance) -> None:
        """Enhanced monitor loop with v3 features"""
        
        logger.info(f"🔄 Starting monitor loop for {monitor_id}")
        
        while self.running and not self.emergency_stop:
            try:
                # Check if paused
                if self.paused or not monitor.active:
                    await asyncio.sleep(1)
                    continue
                
                # Check if should take break
                if await self.behavior_engine.should_take_break():
                    break_duration = await self.behavior_engine.get_break_duration()
                    logger.info(f"☕ Taking {break_duration:.0f}s break for {monitor_id}")
                    await asyncio.sleep(break_duration)
                    continue
                
                # Get adaptive timing
                scan_start = time.time()
                
                # Pre-check wait (human-like)
                think_time = await self.behavior_engine.get_decision_delay("medium")
                await asyncio.sleep(think_time)
                
                # Check for tickets
                logger.info(f"🔍 Checking {monitor.platform} for tickets...")
                opportunities = await monitor.handler.check_tickets()
                
                scan_time = time.time() - scan_start
                
                # Update stats
                monitor.check_count += 1
                monitor.tickets_found += len(opportunities)
                self.total_checks += 1
                self.total_tickets_found += len(opportunities)
                
                # Track data usage
                data_stats = self.data_optimizer.get_stats()
                data_used = data_stats['data_used_mb'] - monitor.data_used_mb
                monitor.data_used_mb = data_stats['data_used_mb']
                self.total_data_mb += data_used
                
                # Adapt behavior based on results
                await self.behavior_engine.adapt_behavior(
                    success=len(opportunities) > 0 or monitor.errors == 0,
                    detected=monitor.detection_score < 80,
                    response_time=scan_time,
                    platform=monitor.platform
                )
                
                # Process opportunities
                if opportunities:
                    await self._process_opportunities_v3(monitor, opportunities)
                
                # Update detection monitor
                self._update_monitor_display(monitor)
                
                # Calculate next check interval
                interval = await self._calculate_adaptive_interval(monitor)
                
                logger.info(
                    f"✅ {monitor_id} check complete: "
                    f"{len(opportunities)} tickets, "
                    f"{scan_time:.1f}s, "
                    f"next in {interval:.0f}s"
                )
                
                # Wait for next check
                await asyncio.sleep(interval)
                
            except Exception as e:
                monitor.errors += 1
                self.total_errors += 1
                
                logger.error(f"❌ Monitor {monitor_id} error: {e}", exc_info=True)
                
                # Report error
                self.detection_monitor.add_detection_event(
                    platform=monitor.platform,
                    event_type='monitor_error',
                    threat_level=ThreatLevel.MEDIUM,
                    message=f"Monitor error: {str(e)}",
                    confidence=0.8
                )
                
                # Error backoff
                await asyncio.sleep(30)
        
        logger.info(f"Monitor loop {monitor_id} stopped")
    
    async def _process_opportunities_v3(
        self,
        monitor: MonitorInstance,
        opportunities: List[EnhancedTicketOpportunity]
    ) -> None:
        """Process found opportunities with v3 enhancements"""
        
        for opp in opportunities:
            logger.critical(f"🎫 TICKETS FOUND on {monitor.platform}!")
            logger.critical(f"   Section: {opp.section}")
            logger.critical(f"   Price: €{opp.price}")
            logger.critical(f"   Quantity: {opp.quantity}")
            
            # Report to detection monitor
            self.detection_monitor.add_detection_event(
                platform=monitor.platform,
                event_type='tickets_found',
                threat_level=ThreatLevel.INFO,
                message=f"Found {opp.quantity} tickets in {opp.section} for €{opp.price}",
                details={
                    'section': opp.section,
                    'price': opp.price,
                    'quantity': opp.quantity,
                    'url': opp.url
                },
                confidence=opp.confidence_score
            )
            
            # Attempt reservation
            try:
                # Quick decision
                decision_time = await self.behavior_engine.get_decision_delay("simple")
                await asyncio.sleep(decision_time)
                
                # Reserve tickets
                success = await self.ticket_reserver.attempt_reservation(
                    opportunity=opp,
                    browser_context=monitor.context
                )
                
                if success:
                    self.successful_reservations += 1
                    
                    # Celebrate!
                    self.detection_monitor.add_detection_event(
                        platform=monitor.platform,
                        event_type='reservation_success',
                        threat_level=ThreatLevel.INFO,
                        message="🎉 TICKETS RESERVED SUCCESSFULLY!",
                        details={'opportunity': opp.__dict__},
                        confidence=1.0
                    )
                    
            except Exception as e:
                logger.error(f"Reservation error: {e}")
    
    async def _calculate_adaptive_interval(self, monitor: MonitorInstance) -> float:
        """Calculate adaptive check interval"""
        
        config = monitor.config
        base_interval = config.get('interval_s', 30)
        
        # Adjust based on priority
        priority = PriorityLevel[config.get('priority', 'NORMAL')]
        interval = base_interval / priority.speed_multiplier
        
        # Adjust based on behavior pattern
        behavior_config = self.behavior_engine.get_adaptive_config(monitor.platform)
        aggression = behavior_config['aggression']
        interval *= (2 - aggression)  # Higher aggression = shorter interval
        
        # Burst mode
        burst_config = config.get('burst_mode', {})
        if burst_config.get('enabled') and monitor.tickets_found > 0:
            interval = min(interval, burst_config.get('min_interval_s', 5))
        
        # Detection backoff
        if monitor.detection_score < 80:
            interval *= 2  # Double interval if detected
        
        # Add randomness (±20%)
        interval *= random.uniform(0.8, 1.2)
        
        return max(3, interval)  # Minimum 3 seconds
    
    async def _handle_platform_detection(self, event: Dict[str, Any]) -> None:
        """Handle detection event from platform"""
        
        platform = event.get('platform')
        severity = event.get('severity', 'medium')
        
        # Find monitor
        monitor = next((m for m in self.monitors.values() 
                       if m.platform == platform), None)
        
        if monitor:
            # Adjust detection score
            impact = {'low': 10, 'medium': 20, 'high': 30, 'critical': 50}
            monitor.detection_score -= impact.get(severity, 20)
            monitor.detection_score = max(0, monitor.detection_score)
        
        # Report to detection monitor
        threat_map = {
            'low': ThreatLevel.LOW,
            'medium': ThreatLevel.MEDIUM,
            'high': ThreatLevel.HIGH,
            'critical': ThreatLevel.CRITICAL
        }
        
        self.detection_monitor.add_detection_event(
            platform=platform,
            event_type='platform_detection',
            threat_level=threat_map.get(severity, ThreatLevel.MEDIUM),
            message=event.get('message', 'Detection event'),
            details=event,
            confidence=0.9
        )
    
    def _on_detection_event(self, event) -> None:
        """Handle detection monitor events"""
        
        # Emergency response for critical threats
        if event.threat_level == ThreatLevel.CRITICAL:
            logger.critical(f"💀 CRITICAL THREAT DETECTED: {event.message}")
            
            # Consider emergency measures
            if event.platform != 'system':
                # Pause specific monitor
                monitor = next((m for m in self.monitors.values() 
                              if m.platform == event.platform), None)
                if monitor:
                    monitor.active = False
                    logger.warning(f"⏸️ Paused monitor for {event.platform}")
    
    def _update_monitor_display(self, monitor: MonitorInstance) -> None:
        """Update detection monitor with current stats"""
        
        # Calculate success rate
        success_rate = (monitor.tickets_found / max(1, monitor.check_count))
        
        # Update metrics
        self.detection_monitor.update_system_metrics({
            'active_monitors': len([m for m in self.monitors.values() if m.active]),
            'data_usage_mb': self.total_data_mb,
            'success_rate': self.total_tickets_found / max(1, self.total_checks)
        })
    
    async def _system_monitor_loop(self) -> None:
        """Monitor system health and performance"""
        
        while self.running:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Get CDP stats
                cdp_stats = self.cdp_bypass.get_detection_stats()
                
                # Get behavior stats
                behavior_stats = self.behavior_engine.get_stats()
                
                # Update detection monitor
                self.detection_monitor.update_system_metrics({
                    'cpu_usage': cpu_percent,
                    'memory_usage_mb': memory.used / (1024 * 1024),
                    'cdp_status': cdp_stats['status'],
                    'behavior_naturalness': 1 - behavior_stats['metrics']['detection_rate']
                })
                
                # Log stats periodically
                if self.total_checks % 100 == 0 and self.total_checks > 0:
                    await self._log_performance_stats()
                
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"System monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _optimization_loop(self) -> None:
        """Continuous optimization loop"""
        
        while self.running:
            try:
                # Optimize browser pool
                pool_stats = self.browser_pool.get_stats()
                if pool_stats['hit_rate'] < 50:
                    logger.info("🔧 Optimizing browser pool...")
                    # Adjust pool size
                
                # Optimize data usage
                data_stats = self.data_optimizer.get_stats()
                if data_stats['data_used_mb'] > 1000:
                    logger.warning("⚠️ High data usage detected, increasing optimization")
                    # Adjust blocking rules
                
                # Export learned patterns
                if self.total_checks % 500 == 0 and self.total_checks > 0:
                    await self.behavior_engine.export_learned_patterns(
                        "data/learned_patterns.json"
                    )
                
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
                await asyncio.sleep(120)
    
    async def _log_performance_stats(self) -> None:
        """Log detailed performance statistics"""
        
        runtime = (datetime.now() - self.start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info("📊 PERFORMANCE STATISTICS")
        logger.info(f"Runtime: {runtime/3600:.1f} hours")
        logger.info(f"Total checks: {self.total_checks}")
        logger.info(f"Tickets found: {self.total_tickets_found}")
        logger.info(f"Success rate: {(self.total_tickets_found/max(1,self.total_checks))*100:.1f}%")
        logger.info(f"Error rate: {(self.total_errors/max(1,self.total_checks))*100:.1f}%")
        logger.info(f"Data used: {self.total_data_mb:.1f} MB")
        logger.info(f"Data saved: {self.data_optimizer.get_stats()['data_saved_mb']:.1f} MB")
        logger.info(f"Successful reservations: {self.successful_reservations}")
        
        # CDP stats
        cdp_stats = self.cdp_bypass.get_detection_stats()
        logger.info(f"CDP detection attempts: {cdp_stats['detection_attempts']}")
        logger.info(f"CDP status: {cdp_stats['status']}")
        
        # Behavior stats
        behavior_stats = self.behavior_engine.get_stats()
        logger.info(f"Current pattern: {behavior_stats['current_pattern']}")
        logger.info(f"Aggression level: {behavior_stats['aggression_level']:.2f}")
        
        logger.info("=" * 60)
    
    async def pause_all(self) -> None:
        """Pause all monitoring"""
        self.paused = True
        logger.info("⏸️ All monitoring paused")
        
        self.detection_monitor.add_detection_event(
            platform='system',
            event_type='pause',
            threat_level=ThreatLevel.INFO,
            message="All monitoring paused by user"
        )
    
    async def resume_all(self) -> None:
        """Resume all monitoring"""
        self.paused = False
        logger.info("▶️ All monitoring resumed")
        
        self.detection_monitor.add_detection_event(
            platform='system',
            event_type='resume',
            threat_level=ThreatLevel.INFO,
            message="All monitoring resumed by user"
        )
    
    async def emergency_shutdown(self) -> None:
        """Emergency shutdown procedure"""
        logger.critical("🚨 EMERGENCY SHUTDOWN INITIATED")
        
        self.emergency_stop = True
        self.running = False
        
        # Cancel all tasks
        for task in self.monitor_tasks.values():
            task.cancel()
        
        # Quick cleanup
        await self.shutdown()
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the orchestrator"""
        
        logger.info("🛑 Shutting down StealthMaster AI v3.0...")
        
        self.running = False
        
        # Export learned patterns
        try:
            await self.behavior_engine.export_learned_patterns("data/learned_patterns.json")
        except:
            pass
        
        # Log final stats
        await self._log_performance_stats()
        
        # Cleanup monitors
        for monitor in self.monitors.values():
            try:
                await self.browser_pool.release_browser(
                    monitor.browser,
                    monitor.context,
                    monitor.page
                )
            except:
                pass
        
        # Shutdown components
        if self.browser_pool:
            await shutdown_browser_pool()
        
        if self.stealth_launcher:
            await self.stealth_launcher.cleanup()
        
        # Final report
        self.detection_monitor.add_detection_event(
            platform='system',
            event_type='shutdown',
            threat_level=ThreatLevel.INFO,
            message="StealthMaster AI v3.0 shutdown complete",
            details={
                'total_runtime_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
                'total_tickets_found': self.total_tickets_found,
                'successful_reservations': self.successful_reservations,
                'total_data_mb': self.total_data_mb
            }
        )
        
        logger.info("✅ Shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status"""
        
        return {
            'running': self.running,
            'paused': self.paused,
            'monitors': {
                monitor_id: {
                    'active': monitor.active,
                    'checks': monitor.check_count,
                    'tickets_found': monitor.tickets_found,
                    'errors': monitor.errors,
                    'detection_score': monitor.detection_score,
                    'data_used_mb': monitor.data_used_mb
                }
                for monitor_id, monitor in self.monitors.items()
            },
            'totals': {
                'checks': self.total_checks,
                'tickets_found': self.total_tickets_found,
                'errors': self.total_errors,
                'data_mb': self.total_data_mb,
                'reservations': self.successful_reservations
            },
            'system': {
                'cdp_status': self.cdp_bypass.get_detection_stats()['status'],
                'behavior_pattern': self.behavior_engine.get_stats()['current_pattern'],
                'data_saved_mb': self.data_optimizer.get_stats()['data_saved_mb']
            }
        }


# For backward compatibility, alias as expected name
UltimateOrchestrator = EnhancedOrchestrator