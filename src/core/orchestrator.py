# src/core/orchestrator_v2.py
"""
Ultimate Orchestrator v2.0 - StealthMaster AI
Quantum-enhanced control center for ultra-efficient ticket acquisition
"""

import asyncio
import gc
import logging
import psutil
import time
import random
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from collections import defaultdict, deque

from playwright.async_api import async_playwright, Playwright

# Core imports
from .enums import OperationMode, PlatformType, PriorityLevel
from .models import EnhancedTicketOpportunity
from .managers import ConnectionPoolManager, ResponseCache
from .ticket_reserver import TicketReserver

# Enhanced components
from .stealth.stealth_engine import get_stealthmaster_engine
from .strike_force import EnhancedStrikeForce
from .proxy_manager import get_proxy_manager
from ..platforms.unified_handler import UnifiedTicketingHandler
from ..profiles.manager import ProfileManager, BrowserProfile

logger = logging.getLogger(__name__)

# Define BlockedError if not imported from elsewhere
class BlockedError(Exception):
    """Raised when a monitor is blocked by the platform."""
    pass


class UltimateOrchestrator:
    """Quantum-enhanced orchestrator with revolutionary efficiency"""
    
    def __init__(self, config: Dict[str, Any], gui_queue=None):
        self.config = config
        self.gui_queue = gui_queue
        self.mode = OperationMode[config['app_settings']['mode'].upper()]
        
        # Performance settings
        self.max_concurrent_monitors = self._get_mode_setting('max_concurrent_monitors', 3)
        self.max_concurrent_strikes = self._get_mode_setting('max_concurrent_strikes', 5)
        
        # Core components (initialized in setup)
        self.playwright: Optional[Playwright] = None
        self.profile_manager: Optional[ProfileManager] = None
        self.connection_pool: Optional[ConnectionPoolManager] = None
        self.response_cache: Optional[ResponseCache] = None
        self.ticket_reserver: Optional[TicketReserver] = None
        self.strike_force: Optional[EnhancedStrikeForce] = None
        
        # StealthMaster AI Engine
        self.stealth_engine = get_stealthmaster_engine()
        
        # Monitoring infrastructure
        self.monitors: Dict[str, UnifiedTicketingHandler] = {}
        self.monitor_tasks: Dict[str, asyncio.Task] = {}
        
        # Opportunity management with quantum optimization
        self.opportunity_processor = QuantumOpportunityProcessor()
        self.active_opportunities: Set[str] = set()
        
        # System state
        self.running = False
        self.start_time = datetime.now()
        self._performance_monitor_task: Optional[asyncio.Task] = None
        
        # Quantum metrics
        self.quantum_metrics = QuantumMetrics()
        
        logger.info(f"🚀 Ultimate Orchestrator v2.0 initialized in {self.mode.value} mode")
    
    def _get_mode_setting(self, setting: str, default: Any) -> Any:
        """Get mode-specific setting with fallback"""
        mode_config = self.config['app_settings'].get('mode_configs', {}).get(self.mode.value, {})
        return mode_config.get(setting, default)
    
    async def initialize(self) -> None:
        """Initialize all subsystems with quantum enhancements"""
        logger.info("🔧 Initializing Ultimate Orchestrator subsystems...")
        
        try:
            # Initialize Playwright
            self.playwright = await async_playwright().start()
            
            # Initialize proxy manager
            self.proxy_manager = get_proxy_manager(self.config)
            if self.proxy_manager.enabled:
                await self.proxy_manager.validate_all_proxies()
                # Start periodic revalidation
                asyncio.create_task(self.proxy_manager.periodic_revalidation())
            
            # Initialize profile manager
            self.profile_manager = ProfileManager(self.config.get('profile_settings', {}))
            await self.profile_manager.initialize()
            
            # Initialize core components
            self.connection_pool = ConnectionPoolManager(
                max_connections=self._get_mode_setting('max_connections', 50)
            )
            
            self.response_cache = ResponseCache(
                max_size=self._get_mode_setting('cache_size', 1000),
                ttl=self.config['monitoring_settings'].get('cache_max_age_s', 300)
            )
            
            # Initialize ticket reserver
            self.ticket_reserver = TicketReserver(
                open_browser_mode=self.config['app_settings'].get('browser_open_mode', 'both')
            )
            
            # Initialize strike force v2
            self.strike_force = EnhancedStrikeForce(
                self.profile_manager,
                self.playwright.chromium,
                self.connection_pool,
                self.ticket_reserver
            )
            
            # Initialize monitors for all targets
            await self._initialize_monitors()
            
            logger.info("✅ All subsystems initialized successfully")
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            raise
    
    async def _initialize_monitors(self) -> None:
        """Initialize monitors for all configured targets"""
        targets = self.config.get('targets', [])
        enabled_targets = [t for t in targets if t.get('enabled', True)]
        
        logger.info(f"Initializing {len(enabled_targets)} target monitors")
        
        for target in enabled_targets:
            try:
                # Select optimal profile for monitoring
                profile = await self._select_monitoring_profile(target)
                
                if not profile:
                    logger.error(f"No suitable profile for {target['event_name']}")
                    continue
                
                # Create unified handler
                monitor = UnifiedTicketingHandler(
                    config=target,
                    profile=profile,
                    browser_manager=self.playwright.chromium,
                    connection_manager=self.connection_pool,
                    cache=self.response_cache
                )
                
                # Initialize with StealthMaster protection
                await monitor.initialize()
                
                # Store monitor
                monitor_id = f"{target['platform']}_{target['event_name']}"
                self.monitors[monitor_id] = monitor
                
                logger.info(f"✅ Monitor initialized: {target['event_name']}")
                
            except Exception as e:
                logger.error(f"Failed to initialize monitor for {target['event_name']}: {e}")
    
    async def _select_monitoring_profile(self, target: Dict[str, Any]) -> Optional[BrowserProfile]:
        """Select optimal profile for monitoring"""
        platform = target['platform']
        
        # Get profiles suitable for platform
        profiles = await self.profile_manager.get_healthy_profiles(
            platform=platform,
            min_quality_tier=2  # Lower quality OK for monitoring
        )
        
        if not profiles:
            return None
        
        # Select profile with best platform-specific performance
        best_profile = None
        best_score = -1
        
        for profile in profiles:
            platform_stats = profile.platform_stats.get(platform, {})
            score = platform_stats.get('success_rate', 0.5) * 100
            
            # Bonus for recent success
            if platform_stats.get('last_success'):
                recency_bonus = max(0, 30 - (time.time() - platform_stats['last_success']) / 3600)
                score += recency_bonus
            
            if score > best_score:
                best_score = score
                best_profile = profile
        
        return best_profile
    
    async def start(self) -> None:
        """Start orchestrator with quantum activation"""
        logger.critical("⚡ ULTIMATE ORCHESTRATOR V2.0 STARTING ⚡")
        self.running = True
        
        try:
            # Start monitoring tasks
            for monitor_id, monitor in self.monitors.items():
                task = asyncio.create_task(self._monitor_loop(monitor_id, monitor))
                self.monitor_tasks[monitor_id] = task
            
            # Start opportunity processor
            asyncio.create_task(self.opportunity_processor.process_loop(self))
            
            # Start performance monitor
            self._performance_monitor_task = asyncio.create_task(self._monitor_performance())
            
            # Start quantum optimizer
            asyncio.create_task(self._quantum_optimization_loop())
            
            logger.critical("🚀 All systems operational - Hunting for tickets!")
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)
            raise
    
    async def _monitor_loop(self, monitor_id: str, monitor: UnifiedTicketingHandler) -> None:
        """Enhanced monitoring loop with adaptive timing"""
        
        while self.running:
            try:
                # Calculate adaptive interval
                interval = self._calculate_adaptive_interval(monitor)
                
                # Check for tickets
                start_time = time.time()
                opportunities = await monitor.check_tickets()
                check_time = time.time() - start_time
                
                # Update quantum metrics
                self.quantum_metrics.record_scan(monitor_id, check_time, len(opportunities))
                
                # Process opportunities
                if opportunities:
                    logger.critical(f"🎯 {len(opportunities)} opportunities detected!")
                    
                    for opportunity in opportunities:
                        # Queue for processing
                        await self.opportunity_processor.queue_opportunity(opportunity)
                
                # Adaptive sleep
                sleep_time = max(0, interval - check_time)
                await asyncio.sleep(sleep_time)
                
            except BlockedError:
                logger.warning(f"Monitor {monitor_id} blocked - entering stealth mode")
                await self._handle_monitor_block(monitor_id, monitor)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(30)  # Error cooldown
    
    def _calculate_adaptive_interval(self, monitor: UnifiedTicketingHandler) -> float:
        """Calculate quantum-optimized monitoring interval"""
        
        base_interval = monitor.config.get('interval_s', 30)
        
        # Adjust based on mode
        mode_multipliers = {
            OperationMode.ULTRA_STEALTH: 2.0,
            OperationMode.STEALTH: 1.5,
            OperationMode.ADAPTIVE: 1.0,
            OperationMode.HYBRID: 0.8,
            OperationMode.BEAST: 0.5
        }
        
        interval = base_interval * mode_multipliers.get(self.mode, 1.0)
        
        # Adjust based on recent activity
        recent_opportunities = self.quantum_metrics.get_recent_opportunity_rate(monitor.platform.value)
        
        if recent_opportunities > 0.1:  # High activity
            interval *= 0.7
        elif recent_opportunities < 0.01:  # Low activity
            interval *= 1.3
        
        # Add quantum jitter
        jitter = random.gauss(0, interval * 0.1)
        interval += jitter
        
        # Apply burst mode if configured
        if monitor.config.get('burst_mode', {}).get('enabled'):
            if self._should_burst(monitor):
                interval = monitor.config['burst_mode'].get('min_interval_s', 3)
        
        return max(1, interval)  # Minimum 1 second
    
    def _should_burst(self, monitor: UnifiedTicketingHandler) -> bool:
        """Determine if burst mode should activate"""
        
        # Check recent opportunity rate
        rate = self.quantum_metrics.get_recent_opportunity_rate(monitor.platform.value)
        
        # Burst if high activity detected
        return rate > 0.05
    
    async def _handle_monitor_block(self, monitor_id: str, monitor: UnifiedTicketingHandler) -> None:
        """Handle blocked monitor with advanced recovery"""
        
        # Switch to ultra-stealth mode temporarily
        logger.info(f"Activating ultra-stealth recovery for {monitor_id}")
        
        # Cooldown with exponential backoff
        cooldown = 60 * (2 ** self.quantum_metrics.get_block_count(monitor_id))
        cooldown = min(cooldown, 3600)  # Max 1 hour
        
        logger.info(f"Cooling down for {cooldown}s")
        await asyncio.sleep(cooldown)
        
        # Try profile rotation
        new_profile = await self._select_monitoring_profile(monitor.config)
        if new_profile and new_profile.profile_id != monitor.profile.profile_id:
            logger.info("Rotating to fresh profile")
            # Reinitialize monitor with new profile
            monitor.profile = new_profile
            await monitor.initialize()
    
    async def _monitor_performance(self) -> None:
        """Monitor system performance and health"""
        
        while self.running:
            try:
                # System metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Calculate health score
                health_score = self._calculate_health_score(cpu_percent, memory.percent)
                
                # Log metrics
                if health_score < 70:
                    logger.warning(f"System health degraded: {health_score}%")
                
                # Update GUI
                if self.gui_queue:
                    self.gui_queue.put(("health", {
                        'cpu': cpu_percent,
                        'memory': memory.percent,
                        'health_score': health_score,
                        'monitors_active': len(self.monitor_tasks),
                        'opportunities_queued': self.opportunity_processor.queue_size()
                    }))
                
                # Perform cleanup if needed
                if memory.percent > 80:
                    gc.collect()
                    logger.info("Performed garbage collection")
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(30)
    
    def _calculate_health_score(self, cpu: float, memory: float) -> float:
        """Calculate system health score"""
        
        cpu_score = max(0, 100 - cpu)
        memory_score = max(0, 100 - memory)
        
        # Weight CPU less than memory
        health = (cpu_score * 0.3 + memory_score * 0.7)
        
        # Factor in error rates
        error_rate = self.quantum_metrics.get_error_rate()
        health *= (1 - error_rate)
        
        return health
    
    async def _quantum_optimization_loop(self) -> None:
        """Continuous quantum optimization of system parameters"""
        
        while self.running:
            try:
                # Analyze performance patterns
                patterns = self.quantum_metrics.analyze_patterns()
                
                # Optimize based on patterns
                if patterns.get('high_success_platform'):
                    # Allocate more resources to successful platform
                    platform = patterns['high_success_platform']
                    logger.info(f"Quantum optimizer: Boosting {platform} resources")
                    
                    # Increase monitoring frequency for that platform
                    for monitor_id, monitor in self.monitors.items():
                        if monitor.platform.value == platform:
                            monitor.config['interval_s'] *= 0.8
                
                if patterns.get('low_activity_time'):
                    # Reduce activity during low periods
                    logger.info("Quantum optimizer: Entering low-power mode")
                    self.mode = OperationMode.STEALTH
                
                await asyncio.sleep(60)  # Optimize every minute
                
            except Exception as e:
                logger.error(f"Quantum optimization error: {e}")
                await asyncio.sleep(300)
    
    async def stop(self) -> None:
        """Gracefully stop orchestrator"""
        logger.info("Stopping Ultimate Orchestrator...")
        self.running = False
        
        # Cancel all tasks
        for task in self.monitor_tasks.values():
            task.cancel()
        
        if self._performance_monitor_task:
            self._performance_monitor_task.cancel()
        
        # Close all monitors
        for monitor in self.monitors.values():
            try:
                await monitor.browser_context.close()
            except:
                pass
        
        # Cleanup
        if self.playwright:
            await self.playwright.stop()
        
        logger.info("Ultimate Orchestrator stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        stats = {
            'uptime': uptime,
            'mode': self.mode.value,
            'monitors_active': len(self.monitor_tasks),
            'opportunities_processed': self.quantum_metrics.total_opportunities,
            'strikes_executed': self.strike_force.get_strike_stats() if self.strike_force else {},
            'quantum_metrics': self.quantum_metrics.get_summary(),
            'success_rate': self.quantum_metrics.get_overall_success_rate()
        }
        
        # Add proxy statistics if enabled
        if hasattr(self, 'proxy_manager') and self.proxy_manager and self.proxy_manager.enabled:
            stats['proxy_stats'] = self.proxy_manager.get_proxy_stats()
        
        return stats


class QuantumOpportunityProcessor:
    """Quantum-enhanced opportunity processing with ML optimization"""
    
    def __init__(self):
        self.opportunity_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.processing_history = deque(maxlen=1000)
        self.ml_scorer = OpportunityScorer()
    
    async def queue_opportunity(self, opportunity: EnhancedTicketOpportunity) -> None:
        """Queue opportunity with quantum priority scoring"""
        
        # Calculate quantum priority score
        priority_score = self.ml_scorer.score_opportunity(opportunity)
        
        # Add to priority queue (negative for proper ordering)
        await self.opportunity_queue.put((-priority_score, opportunity))
    
    async def process_loop(self, orchestrator: UltimateOrchestrator) -> None:
        """Process opportunities with quantum efficiency"""
        
        while orchestrator.running:
            try:
                # Get highest priority opportunity
                priority, opportunity = await asyncio.wait_for(
                    self.opportunity_queue.get(),
                    timeout=1.0
                )
                
                # Check if already being processed
                if opportunity.id in orchestrator.active_opportunities:
                    continue
                
                orchestrator.active_opportunities.add(opportunity.id)
                
                try:
                    # Execute lightning strike
                    success = await orchestrator.strike_force.execute_lightning_strike(
                        opportunity,
                        orchestrator.mode
                    )
                    
                    # Record result
                    self.processing_history.append({
                        'opportunity': opportunity,
                        'success': success,
                        'timestamp': time.time()
                    })
                    
                    # Update ML model
                    self.ml_scorer.update_model(opportunity, success)
                    
                finally:
                    orchestrator.active_opportunities.remove(opportunity.id)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Opportunity processing error: {e}")
    
    def queue_size(self) -> int:
        """Get current queue size"""
        return self.opportunity_queue.qsize()


class OpportunityScorer:
    """ML-based opportunity scoring"""
    
    def __init__(self):
        self.feature_weights = {
            'price_value': 0.3,
            'section_quality': 0.2,
            'platform_success': 0.2,
            'time_criticality': 0.15,
            'confidence': 0.15
        }
        
        self.platform_success_rates = defaultdict(lambda: 0.5)
        self.section_success_rates = defaultdict(lambda: 0.5)
    
    def score_opportunity(self, opportunity: EnhancedTicketOpportunity) -> float:
        """Score opportunity using ML features"""
        
        features = {}
        
        # Price value (lower is better)
        features['price_value'] = 1.0 / (1 + opportunity.price / 100)
        
        # Section quality
        section_lower = opportunity.section.lower()
        if any(term in section_lower for term in ['floor', 'pit', 'vip', 'gold']):
            features['section_quality'] = 1.0
        elif any(term in section_lower for term in ['lower', 'club', 'premium']):
            features['section_quality'] = 0.8
        else:
            features['section_quality'] = 0.5
        
        # Platform success rate
        features['platform_success'] = self.platform_success_rates[opportunity.platform.value]
        
        # Time criticality
        age_minutes = (datetime.now() - opportunity.detected_at).total_seconds() / 60
        features['time_criticality'] = 1.0 / (1 + age_minutes / 5)
        
        # Confidence
        features['confidence'] = opportunity.confidence_score
        
        # Calculate weighted score
        score = sum(
            features[feature] * weight
            for feature, weight in self.feature_weights.items()
        )
        
        # Apply priority multiplier
        priority_multipliers = {
            PriorityLevel.CRITICAL: 2.0,
            PriorityLevel.HIGH: 1.5,
            PriorityLevel.NORMAL: 1.0,
            PriorityLevel.LOW: 0.7
        }
        
        score *= priority_multipliers.get(opportunity.priority, 1.0)
        
        return score
    
    def update_model(self, opportunity: EnhancedTicketOpportunity, success: bool) -> None:
        """Update ML model with result"""
        
        # Update platform success rate
        platform = opportunity.platform.value
        old_rate = self.platform_success_rates[platform]
        self.platform_success_rates[platform] = old_rate * 0.9 + (1.0 if success else 0.0) * 0.1
        
        # Update section success rate
        section = opportunity.section.lower()
        old_rate = self.section_success_rates[section]
        self.section_success_rates[section] = old_rate * 0.9 + (1.0 if success else 0.0) * 0.1


class QuantumMetrics:
    """Advanced metrics with quantum analysis"""
    
    def __init__(self):
        self.scan_times = defaultdict(deque)
        self.opportunities_found = defaultdict(int)
        self.blocks_encountered = defaultdict(int)
        self.total_opportunities = 0
        self.successful_strikes = 0
        self.total_strikes = 0
    
    def record_scan(self, monitor_id: str, scan_time: float, opportunities: int) -> None:
        """Record scan metrics"""
        self.scan_times[monitor_id].append((time.time(), scan_time))
        if len(self.scan_times[monitor_id]) > 100:
            self.scan_times[monitor_id].popleft()
        
        if opportunities > 0:
            self.opportunities_found[monitor_id] += opportunities
            self.total_opportunities += opportunities
    
    def get_recent_opportunity_rate(self, platform: str) -> float:
        """Get recent opportunity detection rate"""
        relevant_monitors = [
            monitor_id for monitor_id in self.opportunities_found
            if platform in monitor_id
        ]
        
        if not relevant_monitors:
            return 0.0
        
        total_opportunities = sum(
            self.opportunities_found[m] for m in relevant_monitors
        )
        
        # Calculate rate per minute
        time_window = 300  # 5 minutes
        return total_opportunities / (time_window / 60)
    
    def get_block_count(self, monitor_id: str) -> int:
        """Get block count for monitor"""
        return self.blocks_encountered.get(monitor_id, 0)
    
    def get_error_rate(self) -> float:
        """Calculate overall error rate"""
        if self.total_strikes == 0:
            return 0.0
        
        return 1.0 - (self.successful_strikes / self.total_strikes)
    
    def get_overall_success_rate(self) -> float:
        """Get overall system success rate"""
        if self.total_strikes == 0:
            return 0.0
        
        return self.successful_strikes / self.total_strikes
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in metrics"""
        patterns = {}
        
        # Find highest success platform
        platform_opps = defaultdict(int)
        for monitor_id, count in self.opportunities_found.items():
            platform = monitor_id.split('_')[0]
            platform_opps[platform] += count
        
        if platform_opps:
            patterns['high_success_platform'] = max(
                platform_opps.items(),
                key=lambda x: x[1]
            )[0]
        
        # Detect low activity periods
        recent_total = sum(
            len(times) for times in self.scan_times.values()
        )
        
        if recent_total < 10:
            patterns['low_activity_time'] = True
        
        return patterns
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            'total_opportunities': self.total_opportunities,
            'total_strikes': self.total_strikes,
            'successful_strikes': self.successful_strikes,
            'success_rate': self.get_overall_success_rate(),
            'active_monitors': len(self.scan_times),
            'blocks_encountered': sum(self.blocks_encountered.values())
        }