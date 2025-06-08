"""
StealthMaster AI v3.0 - Ultimate Orchestrator
Complete rewrite with focus on stealth, efficiency, and visibility
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from dataclasses import dataclass
import psutil

# Core v3 components
from .stealth_browser_launcher import get_stealth_launcher
from .human_behavior_engine import HumanBehaviorEngine, PersonalityType
from .adaptive_scheduler import AdaptiveScheduler, MultiAccountCoordinator
from .rate_limiter import get_rate_limiter, RateLimitConfig

# Stealth and monitoring
from ..stealth.advanced_fingerprint import AdvancedFingerprint
from ..ui.detection_monitor import DetectionMonitor, ThreatLevel

# Platform handling
from ..platforms.unified_handler import UnifiedHandler
from ..profiles.manager import ProfileManager

# Models and types
from .models import EnhancedTicketOpportunity
from .enums import OperationMode, PlatformType, PriorityLevel

logger = logging.getLogger(__name__)


@dataclass
class MonitorInstance:
    """Enhanced monitor instance for"""
    monitor_id: str
    handler: UnifiedHandler
    behavior_engine: HumanBehaviorEngine
    last_check: Optional[datetime] = None
    check_count: int = 0
    tickets_found: int = 0
    errors: int = 0
    active: bool = True


class Orchestrator:
    

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Core components
        self.browser_launcher = None
        self.adaptive_scheduler = AdaptiveScheduler()
        self.profile_manager = None
        self.detection_monitor = None
        
        # Rate limiting with conservative defaults
        rate_config = RateLimitConfig(
            min_interval=45.0,  # 45 seconds minimum
            max_interval=300.0,  # 5 minutes maximum
            burst_min_interval=20.0,  # 20 seconds in burst
            burst_max_requests=3,  # Only 3 burst requests
        )
        self.rate_limiter = get_rate_limiter(rate_config)
        
        # Monitor management
        self.monitors: Dict[str, MonitorInstance] = {}
        self.monitor_tasks: Dict[str, asyncio.Task] = {}
        
        # Multi-account coordination
        num_profiles = len(config.get('targets', []))
        self.account_coordinator = MultiAccountCoordinator(num_profiles)
        
        # System state
        self.running = False
        self.paused = False
        self.start_time = datetime.now()
        
        # Statistics
        self.total_checks = 0
        self.total_tickets_found = 0
        self.total_errors = 0
        self.data_usage_mb = 0.0
        
        logger.info("🚀 StealthMaster AI Orchestrator initialized")
        
    async def initialize(self):
        """Initialize all v3 subsystems"""
        logger.info("Initializing StealthMaster AI subsystems...")
        
        # 1. Initialize browser launcher
        self.browser_launcher = await get_stealth_launcher()
        logger.info("✅ Stealth browser launcher ready")
        
        # 2. Initialize profile manager
        self.profile_manager = ProfileManager(self.config)
        await self.profile_manager.initialize()
        logger.info("✅ Profile manager initialized")
        
        # 3. Initialize detection monitor
        self.detection_monitor = DetectionMonitor()
        logger.info("✅ Detection monitor active")
        
        # 4. Initialize monitors for each target
        await self._initialize_monitors()
        
        # 5. Import learned patterns if available
        try:
            self.adaptive_scheduler.import_patterns("learned_patterns.json")
            logger.info("✅ Imported learned scheduling patterns")
        except:
            logger.info("No learned patterns found, starting fresh")
            
        logger.info("✅ All subsystems initialized successfully")
        
    async def _initialize_monitors(self):
        """Initialize monitors with enhancements"""
        
        targets = self.config.get('targets', [])
        
        for i, target in enumerate(targets):
            if not target.get('enabled', True):
                continue
                
            monitor_id = f"monitor_{i}_{target['platform']}"
            
            # Select personality for human behavior
            personalities = list(PersonalityType)
            personality = personalities[i % len(personalities)]
            
            # Create behavior engine
            behavior_engine = HumanBehaviorEngine(personality)
            
            # Get profile with fingerprint
            profile = await self.profile_manager.get_healthy_profiles(
                platform=target['platform'],
                min_quality_tier=3
            )
            
            if not profile:
                logger.error(f"No healthy profile available for {target['platform']}")
                continue
                
            # Generate fingerprint
            fingerprint = AdvancedFingerprint.generate_fingerprint()
            
            # Launch stealth browser
            browser = await self.browser_launcher.launch_stealth_browser(
                proxy=self._get_proxy_config(profile),
                fingerprint=fingerprint
            )
            
            # Create handler
            handler = UnifiedHandler(
                config=target,
                browser=browser,
                behavior_engine=behavior_engine,
                fingerprint=fingerprint,
                detection_callback=self._on_detection_event
            )
            
            await handler.initialize()
            
            # Create monitor instance
            monitor = MonitorInstance(
                monitor_id=monitor_id,
                handler=handler,
                behavior_engine=behavior_engine
            )
            
            self.monitors[monitor_id] = monitor
            logger.info(f"✅ Monitor initialized: {target['event_name']} ({personality.value} personality)")
            
        # Update detection monitor
        self.detection_monitor.update_system_status({
            'active_monitors': len(self.monitors),
            'proxy_health': 100.0,
            'data_usage_mb': 0.0,
            'success_rate': 0.0
        })
        
    def _get_proxy_config(self, profile) -> Optional[Dict[str, str]]:
        """Get proxy configuration for profile"""
        
        if not self.config.get('proxy_settings', {}).get('enabled'):
            return None
            
        # In v3, we use the profile's assigned proxy
        if hasattr(profile, 'proxy_config') and profile.proxy_config:
            return {
                'server': profile.proxy_config.get('server'),
                'username': profile.proxy_config.get('username'),
                'password': profile.proxy_config.get('password')
            }
            
        return None
        
    async def start(self):
        """Start the orchestrator"""
        
        logger.critical("=" * 80)
        logger.critical("🚀 STEALTHMASTER AI V3.0 STARTING")
        logger.critical("🎯 Target: Bruce Springsteen Tickets")
        logger.critical("🛡️ Mode: Maximum Stealth")
        logger.critical("=" * 80)
        
        self.running = True
        self.start_time = datetime.now()
        
        # Start monitor tasks
        for monitor_id, monitor in self.monitors.items():
            task = asyncio.create_task(self._monitor_loop_v3(monitor_id, monitor))
            self.monitor_tasks[monitor_id] = task
            
        # Start background tasks
        asyncio.create_task(self._status_updater())
        asyncio.create_task(self._pattern_exporter())
        asyncio.create_task(self._health_monitor())
        
        # Keep running
        try:
            while self.running:
                await asyncio.sleep(1)
                
                # Check for sleep mode
                sleep_duration = self.adaptive_scheduler.get_sleep_mode_duration()
                if sleep_duration:
                    logger.info(f"😴 Entering sleep mode for {sleep_duration/3600:.1f} hours")
                    self.detection_monitor.add_detection_event(
                        platform="system",
                        event_type="sleep_mode",
                        threat_level=ThreatLevel.CLEAR,
                        message=f"Sleep mode: {sleep_duration/3600:.1f} hours",
                        details={}
                    )
                    await asyncio.sleep(sleep_duration)
                    
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            await self.shutdown()
            
    async def _monitor_loop_v3(self, monitor_id: str, monitor: MonitorInstance):
        """Enhanced monitor loop with v3 features"""
        
        while self.running and monitor.active:
            try:
                # Check if paused
                if self.paused:
                    await asyncio.sleep(5)
                    continue
                    
                # Get platform and priority
                platform = monitor.handler.platform
                priority = monitor.handler.priority
                
                # Check with adaptive scheduler
                if not self.adaptive_scheduler.should_check_now(platform, monitor.last_check):
                    await asyncio.sleep(1)
                    continue
                    
                # Check multi-account coordination
                if not self.account_coordinator.should_account_check(monitor_id):
                    await asyncio.sleep(5)
                    continue
                    
                # Apply intelligent rate limiting
                await self.rate_limiter.wait_if_needed(platform, priority)
                
                # Check if behavior engine needs break
                if monitor.behavior_engine.should_take_break():
                    await monitor.behavior_engine.take_break()
                    
                # Log check attempt
                logger.info(f"🔍 Checking {platform} ({monitor.behavior_engine.personality.value} personality)")
                
                # Perform check with timing
                start_time = time.time()
                opportunities = await monitor.handler.check_tickets()
                check_time = time.time() - start_time
                
                # Update statistics
                monitor.check_count += 1
                monitor.last_check = datetime.now()
                self.total_checks += 1
                
                # Record in scheduler
                self.adaptive_scheduler.record_check_result(
                    platform=platform,
                    success=True,
                    tickets_found=len(opportunities),
                    response_time=check_time
                )
                
                # Record in rate limiter
                self.rate_limiter.record_request(platform, success=True)
                
                # Record in coordinator
                self.account_coordinator.record_account_check(monitor_id)
                
                # Process opportunities
                if opportunities:
                    monitor.tickets_found += len(opportunities)
                    self.total_tickets_found += len(opportunities)
                    
                    logger.critical(f"🎯 TICKETS FOUND: {len(opportunities)} on {platform}!")
                    
                    # Send to detection monitor
                    self.detection_monitor.add_detection_event(
                        platform=platform,
                        event_type="tickets_found",
                        threat_level=ThreatLevel.CLEAR,
                        message=f"Found {len(opportunities)} tickets!",
                        details={"count": len(opportunities)}
                    )
                    
                    # Process tickets (strike force would go here)
                    for opp in opportunities:
                        logger.info(f"  - {opp.section}: €{opp.price} x{opp.quantity}")
                        
            except Exception as e:
                # Error handling
                error_type = type(e).__name__
                monitor.errors += 1
                self.total_errors += 1
                
                logger.error(f"Monitor error for {platform}: {error_type}: {e}")
                
                # Record failure
                self.rate_limiter.record_request(platform, success=False)
                
                # Detection event
                if "block" in str(e).lower() or "captcha" in str(e).lower():
                    threat_level = ThreatLevel.HIGH
                    self.rate_limiter.record_detection(platform, "blocked")
                else:
                    threat_level = ThreatLevel.MEDIUM
                    
                self.detection_monitor.add_detection_event(
                    platform=platform,
                    event_type="error",
                    threat_level=threat_level,
                    message=f"{error_type}: {str(e)[:100]}",
                    details={"error": str(e)}
                )
                
                # Backoff on error
                await asyncio.sleep(60)
                
    async def _on_detection_event(self, event_data: Dict[str, Any]):
        """Handle detection events from monitors"""
        
        platform = event_data.get('platform', 'unknown')
        event_type = event_data.get('type', 'unknown')
        severity = event_data.get('severity', 'medium')
        message = event_data.get('message', 'Detection event')
        
        # Map severity to threat level
        threat_map = {
            'low': ThreatLevel.LOW,
            'medium': ThreatLevel.MEDIUM,
            'high': ThreatLevel.HIGH,
            'critical': ThreatLevel.CRITICAL
        }
        
        threat_level = threat_map.get(severity, ThreatLevel.MEDIUM)
        
        # Send to detection monitor
        self.detection_monitor.add_detection_event(
            platform=platform,
            event_type=event_type,
            threat_level=threat_level,
            message=message,
            details=event_data.get('details', {})
        )
        
        # Take action based on severity
        if severity == 'critical':
            # Pause the affected monitor
            for monitor_id, monitor in self.monitors.items():
                if monitor.handler.platform == platform:
                    monitor.active = False
                    logger.error(f"⛔ Pausing monitor {monitor_id} due to critical detection")
                    
    async def _status_updater(self):
        """Update detection monitor with system status"""
        
        while self.running:
            try:
                # Calculate metrics
                success_rate = self.total_tickets_found / max(1, self.total_checks)
                
                # Get system resources
                memory = psutil.virtual_memory()
                
                # Update detection monitor
                self.detection_monitor.update_system_status({
                    'active_monitors': sum(1 for m in self.monitors.values() if m.active),
                    'proxy_health': self._calculate_proxy_health(),
                    'data_usage_mb': self.data_usage_mb,
                    'success_rate': success_rate,
                    'stealth_score': self._calculate_stealth_score()
                })
                
                # Log summary every 5 minutes
                if self.total_checks % 100 == 0 and self.total_checks > 0:
                    self._log_summary()
                    
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Status updater error: {e}")
                await asyncio.sleep(30)
                
    def _calculate_proxy_health(self) -> float:
        """Calculate overall proxy health"""
        
        # In real implementation, this would check actual proxy status
        # For now, simulate based on error rate
        if self.total_checks == 0:
            return 100.0
            
        error_rate = self.total_errors / self.total_checks
        health = (1 - error_rate) * 100
        
        return max(0, min(100, health))
        
    def _calculate_stealth_score(self) -> float:
        """Calculate overall stealth score"""
        
        # Start at 100
        score = 100.0
        
        # Deduct for errors
        if self.total_checks > 0:
            error_rate = self.total_errors / self.total_checks
            score -= error_rate * 50
            
        # Deduct for detection events
        # This would check actual detection events in real implementation
        
        return max(0, min(100, score))
        
    async def _pattern_exporter(self):
        """Periodically export learned patterns"""
        
        while self.running:
            # Export every hour
            await asyncio.sleep(3600)
            
            try:
                self.adaptive_scheduler.export_patterns("learned_patterns.json")
                logger.info("📊 Exported learned patterns")
            except Exception as e:
                logger.error(f"Failed to export patterns: {e}")
                
    async def _health_monitor(self):
        """Monitor system health and take corrective actions"""
        
        while self.running:
            try:
                # Check memory usage
                memory = psutil.virtual_memory()
                if memory.percent > 80:
                    logger.warning(f"High memory usage: {memory.percent}%")
                    # Could trigger browser recycling here
                    
                # Check CPU usage
                cpu = psutil.cpu_percent(interval=1)
                if cpu > 80:
                    logger.warning(f"High CPU usage: {cpu}%")
                    
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(60)
                
    def _log_summary(self):
        """Log performance summary"""
        
        runtime = (datetime.now() - self.start_time).total_seconds() / 3600
        
        logger.info("=" * 60)
        logger.info("📊 PERFORMANCE SUMMARY")
        logger.info(f"Runtime: {runtime:.1f} hours")
        logger.info(f"Total checks: {self.total_checks}")
        logger.info(f"Tickets found: {self.total_tickets_found}")
        logger.info(f"Error rate: {(self.total_errors/max(1,self.total_checks))*100:.1f}%")
        logger.info(f"Data usage: {self.data_usage_mb:.1f} MB")
        
        # Per-platform stats
        for monitor_id, monitor in self.monitors.items():
            logger.info(f"\n{monitor.handler.platform}:")
            logger.info(f"  Checks: {monitor.check_count}")
            logger.info(f"  Tickets: {monitor.tickets_found}")
            logger.info(f"  Errors: {monitor.errors}")
            
        # Scheduler stats
        scheduler_stats = self.adaptive_scheduler.get_statistics()
        logger.info(f"\n📅 Scheduler Stats:")
        logger.info(f"  Request savings: {scheduler_stats['request_savings_percent']:.1f}%")
        logger.info(f"  Active platforms: {scheduler_stats['active_platforms']}")
        
        logger.info("=" * 60)
        
    async def shutdown(self):
        """Gracefully shutdown v3 orchestrator"""
        
        logger.info("Shutting down StealthMaster AI v3.0...")
        
        self.running = False
        
        # Cancel all monitor tasks
        for task in self.monitor_tasks.values():
            task.cancel()
            
        # Close all browsers
        for monitor in self.monitors.values():
            try:
                await monitor.handler.cleanup()
            except:
                pass
                
        # Clean up browser launcher
        if self.browser_launcher:
            await self.browser_launcher.cleanup()
            
        # Export patterns one last time
        try:
            self.adaptive_scheduler.export_patterns("learned_patterns.json")
        except:
            pass
            
        # Stop detection monitor
        if self.detection_monitor:
            self.detection_monitor.stop()
            
        logger.info("✅ Shutdown complete")
        
    def pause_all(self):
        """Pause all monitoring"""
        self.paused = True
        logger.info("⏸️ All monitoring paused")
        
    def resume_all(self):
        """Resume all monitoring"""
        self.paused = False
        logger.info("▶️ All monitoring resumed")