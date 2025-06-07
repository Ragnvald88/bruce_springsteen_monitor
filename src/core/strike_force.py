# src/core/strike_force_v2.py
"""
Enhanced Strike Force v2.0 - StealthMaster AI
Lightning-fast coordinated ticket acquisition with quantum efficiency
"""

import asyncio
import logging
import time
import random
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass

from ..core.models import EnhancedTicketOpportunity
from ..core.enums import OperationMode, PlatformType, PriorityLevel
from ..profiles.manager import ProfileManager
from ..profiles.models import BrowserProfile
from ..core.ticket_reserver import TicketReserver

logger = logging.getLogger(__name__)


@dataclass
class StrikeMetrics:
    """Real-time strike performance metrics"""
    total_strikes: int = 0
    successful_strikes: int = 0
    failed_strikes: int = 0
    avg_response_time: float = 0
    fastest_strike: float = float('inf')
    profile_performance: Dict[str, float] = None
    
    def __post_init__(self):
        if self.profile_performance is None:
            self.profile_performance = {}


class EnhancedStrikeForce:
    """Next-generation strike force with quantum coordination capabilities"""
    
    def __init__(self, profile_manager: ProfileManager, browser_manager, 
                 connection_manager, ticket_reserver: TicketReserver):
        self.profile_manager = profile_manager
        self.browser_manager = browser_manager
        self.connection_manager = connection_manager
        self.ticket_reserver = ticket_reserver
        
        # Strike coordination
        self.active_strikes: Dict[str, asyncio.Task] = {}
        self.strike_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.profile_assignments: Dict[str, str] = {}  # opportunity_id -> profile_id
        
        # Performance tracking
        self.strike_metrics = StrikeMetrics()
        self.profile_cooldowns: Dict[str, float] = {}
        
        # Strike strategies
        self.strike_strategies = {
            OperationMode.STEALTH: StealthStrikeStrategy(),
            OperationMode.BEAST: BeastStrikeStrategy(),
            OperationMode.ULTRA_STEALTH: UltraStealthStrikeStrategy(),
            OperationMode.ADAPTIVE: AdaptiveStrikeStrategy(),
            OperationMode.HYBRID: HybridStrikeStrategy()
        }
        
        # Quantum coordination engine
        self.quantum_coordinator = QuantumCoordinator()
        
        logger.info("⚡ Enhanced Strike Force v2.0 initialized")
    
    async def execute_lightning_strike(
        self,
        opportunity: EnhancedTicketOpportunity,
        mode: OperationMode
    ) -> bool:
        """Execute lightning-fast coordinated strike"""
        
        strike_id = f"strike_{opportunity.id}_{int(time.time() * 1000)}"
        start_time = time.time()
        
        logger.critical(f"⚡ LIGHTNING STRIKE INITIATED: {opportunity.event_name}")
        logger.critical(f"   Target: {opportunity.section} - €{opportunity.price}")
        logger.critical(f"   Mode: {mode.value.upper()}")
        
        try:
            # Get optimal strike strategy
            strategy = self.strike_strategies[mode]
            
            # Select optimal profiles using quantum selection
            profiles = await self._quantum_profile_selection(opportunity, strategy)
            
            if not profiles:
                logger.error("No suitable profiles available")
                return False
            
            logger.info(f"🎯 Deploying {len(profiles)} profiles for coordinated strike")
            
            # Execute parallel strikes with coordination
            results = await self._execute_coordinated_strikes(
                opportunity, profiles, strategy, strike_id
            )
            
            # Evaluate results
            success = any(results.values())
            strike_time = time.time() - start_time
            
            # Update metrics
            self._update_strike_metrics(strike_time, success, profiles)
            
            if success:
                logger.critical(f"🎉 STRIKE SUCCESSFUL in {strike_time:.2f}s!")
                logger.critical(f"   Winning profile: {[p for p, r in results.items() if r][0]}")
            else:
                logger.warning(f"❌ Strike failed after {strike_time:.2f}s")
            
            return success
            
        except Exception as e:
            logger.error(f"Strike execution failed: {e}", exc_info=True)
            return False
        finally:
            # Cleanup
            if strike_id in self.active_strikes:
                del self.active_strikes[strike_id]
    
    async def _quantum_profile_selection(
        self,
        opportunity: EnhancedTicketOpportunity,
        strategy: 'StrikeStrategy'
    ) -> List[BrowserProfile]:
        """Select optimal profiles using quantum optimization"""
        
        # Get all available profiles
        all_profiles = await self.profile_manager.get_healthy_profiles(
            platform=opportunity.platform.value,
            min_quality_tier=strategy.min_quality_tier
        )
        
        # Filter by cooldown
        available_profiles = [
            p for p in all_profiles
            if self._is_profile_ready(p.profile_id)
        ]
        
        if not available_profiles:
            return []
        
        # Quantum optimization for profile selection
        scored_profiles = []
        
        for profile in available_profiles:
            score = self.quantum_coordinator.calculate_profile_score(
                profile, opportunity, self.strike_metrics
            )
            scored_profiles.append((score, profile))
        
        # Sort by quantum score
        scored_profiles.sort(key=lambda x: x[0], reverse=True)
        
        # Select top profiles based on strategy
        num_profiles = min(strategy.max_parallel_profiles, len(scored_profiles))
        selected = [p[1] for p in scored_profiles[:num_profiles]]
        
        logger.info(f"Quantum selection: {len(selected)} profiles chosen from {len(available_profiles)}")
        
        return selected
    
    def _is_profile_ready(self, profile_id: str) -> bool:
        """Check if profile is ready (not in cooldown)"""
        if profile_id not in self.profile_cooldowns:
            return True
        
        return time.time() > self.profile_cooldowns[profile_id]
    
    async def _execute_coordinated_strikes(
        self,
        opportunity: EnhancedTicketOpportunity,
        profiles: List[BrowserProfile],
        strategy: 'StrikeStrategy',
        strike_id: str
    ) -> Dict[str, bool]:
        """Execute coordinated strikes across multiple profiles"""
        
        tasks = []
        results = {}
        
        # Create coordination event for synchronized execution
        coordination_event = asyncio.Event()
        
        for i, profile in enumerate(profiles):
            # Stagger starts based on strategy
            delay = strategy.get_stagger_delay(i, len(profiles))
            
            task = asyncio.create_task(
                self._execute_single_profile_strike(
                    opportunity, profile, strategy, coordination_event, delay
                )
            )
            
            tasks.append((profile.profile_id, task))
        
        # Signal coordinated start
        await asyncio.sleep(0.1)  # Let all tasks initialize
        coordination_event.set()
        
        # Wait for all strikes with timeout
        timeout = strategy.strike_timeout
        
        try:
            for profile_id, task in tasks:
                try:
                    result = await asyncio.wait_for(task, timeout=timeout)
                    results[profile_id] = result
                    
                    # Early termination on success (for some strategies)
                    if result and strategy.early_termination_on_success:
                        logger.info(f"Early termination - success achieved by {profile_id}")
                        # Cancel remaining tasks
                        for _, remaining_task in tasks:
                            if not remaining_task.done():
                                remaining_task.cancel()
                        break
                        
                except asyncio.TimeoutError:
                    logger.warning(f"Strike timeout for profile {profile_id}")
                    results[profile_id] = False
                    task.cancel()
                    
        except Exception as e:
            logger.error(f"Coordination error: {e}")
        
        return results
    
    async def _execute_single_profile_strike(
        self,
        opportunity: EnhancedTicketOpportunity,
        profile: BrowserProfile,
        strategy: 'StrikeStrategy',
        coordination_event: asyncio.Event,
        delay: float
    ) -> bool:
        """Execute strike with single profile"""
        
        try:
            # Wait for coordination signal
            await coordination_event.wait()
            
            # Apply stagger delay
            if delay > 0:
                await asyncio.sleep(delay)
            
            logger.debug(f"Profile {profile.profile_id} striking {opportunity.id}")
            
            # Create browser context
            context = await self.browser_manager.create_context(profile)
            
            try:
                # Execute reservation attempt
                success = await self.ticket_reserver.attempt_reservation(
                    opportunity,
                    browser_context=context
                )
                
                # Update profile cooldown
                cooldown_time = strategy.get_profile_cooldown(success)
                self.profile_cooldowns[profile.profile_id] = time.time() + cooldown_time
                
                # Record profile feedback
                await self._record_strike_feedback(profile, opportunity, success)
                
                return success
                
            finally:
                # Always close context
                try:
                    await context.close()
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Profile strike failed: {e}")
            return False
    
    async def _record_strike_feedback(
        self,
        profile: BrowserProfile,
        opportunity: EnhancedTicketOpportunity,
        success: bool
    ) -> None:
        """Record strike feedback for profile optimization"""
        
        event_type = 'reservation_success' if success else 'reservation_failed'
        
        await self.profile_manager.record_feedback(
            profile_id=profile.profile_id,
            event=event_type,
            platform=opportunity.platform.value,
            metadata={
                'opportunity_id': opportunity.id,
                'price': opportunity.price,
                'section': opportunity.section,
                'timestamp': time.time()
            }
        )
    
    def _update_strike_metrics(
        self,
        strike_time: float,
        success: bool,
        profiles: List[BrowserProfile]
    ) -> None:
        """Update strike performance metrics"""
        
        self.strike_metrics.total_strikes += 1
        
        if success:
            self.strike_metrics.successful_strikes += 1
        else:
            self.strike_metrics.failed_strikes += 1
        
        # Update average response time
        total = self.strike_metrics.total_strikes
        prev_avg = self.strike_metrics.avg_response_time
        self.strike_metrics.avg_response_time = (prev_avg * (total - 1) + strike_time) / total
        
        # Update fastest strike
        if success and strike_time < self.strike_metrics.fastest_strike:
            self.strike_metrics.fastest_strike = strike_time
        
        # Update profile performance
        for profile in profiles:
            if profile.profile_id not in self.strike_metrics.profile_performance:
                self.strike_metrics.profile_performance[profile.profile_id] = 0
            
            if success:
                self.strike_metrics.profile_performance[profile.profile_id] += 1
    
    def get_strike_stats(self) -> Dict[str, Any]:
        """Get comprehensive strike statistics"""
        
        success_rate = 0
        if self.strike_metrics.total_strikes > 0:
            success_rate = self.strike_metrics.successful_strikes / self.strike_metrics.total_strikes
        
        # Get top performing profiles
        top_profiles = sorted(
            self.strike_metrics.profile_performance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'total_strikes': self.strike_metrics.total_strikes,
            'successful_strikes': self.strike_metrics.successful_strikes,
            'success_rate': success_rate,
            'avg_response_time': self.strike_metrics.avg_response_time,
            'fastest_strike': self.strike_metrics.fastest_strike,
            'top_profiles': top_profiles,
            'active_strikes': len(self.active_strikes)
        }


class QuantumCoordinator:
    """Quantum optimization for strike coordination"""
    
    def calculate_profile_score(
        self,
        profile: BrowserProfile,
        opportunity: EnhancedTicketOpportunity,
        metrics: StrikeMetrics
    ) -> float:
        """Calculate quantum-optimized profile score"""
        
        score = 0.0
        
        # Base quality score
        quality_score = profile.quality.success_rate * 100
        score += quality_score * 0.3
        
        # Platform compatibility
        platform_stats = profile.platform_stats.get(opportunity.platform.value, {})
        platform_success_rate = platform_stats.get('success_rate', 0)
        score += platform_success_rate * 100 * 0.3
        
        # Historical performance
        historical_score = metrics.profile_performance.get(profile.profile_id, 0)
        score += min(historical_score * 10, 100) * 0.2
        
        # Fingerprint uniqueness
        uniqueness_score = self._calculate_fingerprint_uniqueness(profile)
        score += uniqueness_score * 0.2
        
        # Add quantum noise for diversity
        quantum_noise = random.gauss(0, 5)
        score += quantum_noise
        
        return max(0, min(100, score))
    
    def _calculate_fingerprint_uniqueness(self, profile: BrowserProfile) -> float:
        """Calculate fingerprint uniqueness score"""
        # Simplified uniqueness calculation
        unique_factors = [
            profile.user_agent,
            profile.canvas_fingerprint,
            f"{profile.screen_width}x{profile.screen_height}",
            profile.timezone
        ]
        
        # Hash to get uniqueness score
        combined = ''.join(str(f) for f in unique_factors)
        hash_value = hash(combined)
        
        # Normalize to 0-100
        return (hash_value % 100)


class StrikeStrategy:
    """Base class for strike strategies"""
    
    max_parallel_profiles: int = 3
    min_quality_tier: int = 2
    strike_timeout: float = 30.0
    early_termination_on_success: bool = True
    
    def get_stagger_delay(self, index: int, total: int) -> float:
        """Get stagger delay for profile index"""
        return 0.0
    
    def get_profile_cooldown(self, success: bool) -> float:
        """Get cooldown time for profile"""
        return 60.0 if success else 30.0


class StealthStrikeStrategy(StrikeStrategy):
    """Ultra-careful stealth strategy"""
    
    max_parallel_profiles = 1
    min_quality_tier = 4
    strike_timeout = 45.0
    
    def get_stagger_delay(self, index: int, total: int) -> float:
        # No parallel execution in stealth mode
        return index * 10.0
    
    def get_profile_cooldown(self, success: bool) -> float:
        return 300.0 if success else 120.0


class BeastStrikeStrategy(StrikeStrategy):
    """Maximum aggression strategy"""
    
    max_parallel_profiles = 10
    min_quality_tier = 1
    strike_timeout = 20.0
    early_termination_on_success = False
    
    def get_stagger_delay(self, index: int, total: int) -> float:
        # Minimal stagger for maximum speed
        return index * 0.1
    
    def get_profile_cooldown(self, success: bool) -> float:
        return 30.0 if success else 10.0


class UltraStealthStrikeStrategy(StrikeStrategy):
    """Maximum stealth with adaptive timing"""
    
    max_parallel_profiles = 1
    min_quality_tier = 5
    strike_timeout = 60.0
    
    def get_stagger_delay(self, index: int, total: int) -> float:
        # Add random delay for unpredictability
        base_delay = index * 20.0
        jitter = random.uniform(-5, 10)
        return max(0, base_delay + jitter)
    
    def get_profile_cooldown(self, success: bool) -> float:
        # Long random cooldown
        base = 600.0 if success else 300.0
        return base + random.uniform(0, 300)


class AdaptiveStrikeStrategy(StrikeStrategy):
    """Dynamically adapts based on conditions"""
    
    def __init__(self):
        self.recent_success_rate = 0.5
        self.detection_level = 0.0
    
    @property
    def max_parallel_profiles(self) -> int:
        # Adapt based on success rate
        if self.recent_success_rate > 0.7:
            return 5
        elif self.recent_success_rate > 0.4:
            return 3
        else:
            return 1
    
    @property
    def min_quality_tier(self) -> int:
        # Higher quality when detection is high
        if self.detection_level > 0.7:
            return 4
        elif self.detection_level > 0.3:
            return 3
        else:
            return 2
    
    def get_stagger_delay(self, index: int, total: int) -> float:
        # Adaptive stagger based on detection
        base = index * (1.0 + self.detection_level * 5.0)
        return base + random.uniform(0, 1)


class HybridStrikeStrategy(StrikeStrategy):
    """Balanced approach between speed and stealth"""
    
    max_parallel_profiles = 3
    min_quality_tier = 3
    strike_timeout = 30.0
    
    def get_stagger_delay(self, index: int, total: int) -> float:
        # Progressive stagger
        return index ** 1.5 * 0.5
    
    def get_profile_cooldown(self, success: bool) -> float:
        return 120.0 if success else 60.0