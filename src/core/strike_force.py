# src/core/strike_force.py
from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Any, TYPE_CHECKING
from collections import defaultdict
from contextlib import suppress
import random # for _strike_fansale example

if TYPE_CHECKING: # For type hinting Playwright's Page and your SmartBrowserContextManager
    from playwright.async_api import Page as PlaywrightPage
    from .managers import SmartBrowserContextManager # Assuming SmartBrowserContextManager is in src/core/managers.py

# Imports from your project's packages
from src.profiles import (
    ProfileManager,
    BrowserProfile, # Assuming this is the one from src.profiles.models exposed via src.profiles.__init__
    DataOptimizationLevel,
    ProfileQuality
)
# Import Enums, Models from their new locations within src.core
from .enums import OperationMode, PlatformType, PriorityLevel
from .models import EnhancedTicketOpportunity, DataUsageTracker
from .errors import BlockedError # Assuming BlockedError is in src.core.errors

logger = logging.getLogger(__name__)

class ProfileIntegratedStrikeForce:
    """Strike system fully integrated with new ProfileManager"""

    def __init__(self,
                 browser_manager: SmartBrowserContextManager, # Type hint with forward reference or direct import
                 profile_manager: ProfileManager,
                 data_tracker: DataUsageTracker,
                 config: Dict[str, Any]):
        self.browser_manager = browser_manager
        self.profile_manager = profile_manager
        self.data_tracker = data_tracker
        self.config = config

        self.max_parallel = config.get('strike_settings', {}).get('max_parallel', 5)
        self.strike_timeout = config.get('strike_settings', {}).get('timeout', 30)

        self.active_strikes: Dict[str, Set[str]] = defaultdict(set)
        self.strike_results: Dict[str, bool] = {}

        # Platform strategies now use the imported PlatformType
        self.platform_strategies = {
            PlatformType.FANSALE: self._strike_fansale,
            PlatformType.TICKETMASTER: self._strike_ticketmaster,
            PlatformType.VIVATICKET: self._strike_vivaticket
        }
    
    async def execute_coordinated_strike(self,
                                       opportunity: EnhancedTicketOpportunity,
                                       mode: OperationMode) -> bool:
        """Execute coordinated strike with intelligent profile selection"""
        strike_id = f"{opportunity.id}_{time.time()}"
        
        try:
            # Check if already being attempted
            if opportunity.id in self.active_strikes and self.active_strikes[opportunity.id]:
                logger.debug(f"Strike already active for {opportunity.id}")
                return False
            
            # Get strike parameters
            params = self._get_strike_params(mode, opportunity)
            
            # Get profiles from ProfileManager with scoring
            profiles = await self._select_profiles_for_strike(
                opportunity, params
            )
            
            if not profiles:
                logger.error(f"No suitable profiles for {opportunity.id}")
                return False
            
            # Create strike tasks
            tasks = []
            for i, profile in enumerate(profiles):
                task_id = f"{strike_id}_{i}"
                self.active_strikes[opportunity.id].add(task_id)
                
                task = asyncio.create_task(
                    self._execute_single_strike(
                        opportunity, profile, task_id, params
                    ),
                    name=f"strike_{task_id}"
                )
                tasks.append(task)
            
            # Execute strikes
            done, pending = await asyncio.wait(
                tasks,
                timeout=params['timeout'],
                return_when=asyncio.FIRST_COMPLETED if params['race_mode'] else asyncio.ALL_COMPLETED
            )
            
            # Check results
            success = any(task.result() for task in done if not task.cancelled())
            
            # Cancel pending if success
            if success and params['race_mode']:
                for task in pending:
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        await task
            
            return success
            
        finally:
            self.active_strikes[opportunity.id].clear()
    
    def _get_strike_params(self, mode: OperationMode, opportunity: EnhancedTicketOpportunity) -> Dict[str, Any]:
        """Get strike parameters based on mode"""
        base_params = {
            'profile_count': 1,
            'timeout': self.strike_timeout,
            'race_mode': True,
            'retry_on_block': True,
        }
        
        if mode == OperationMode.BEAST:
            base_params.update({
                'profile_count': min(5, self.max_parallel),
                'timeout': 20,
                'min_quality': ProfileQuality.LOW,
                'data_optimization': DataOptimizationLevel.MINIMAL
            })
        elif mode == OperationMode.ULTRA_STEALTH:
            base_params.update({
                'profile_count': 1,
                'timeout': 60,
                'race_mode': False,
                'min_quality': ProfileQuality.HIGH,
                'data_optimization': DataOptimizationLevel.AGGRESSIVE
            })
        elif mode == OperationMode.ADAPTIVE:
            if opportunity.priority == PriorityLevel.CRITICAL:
                base_params['profile_count'] = 3
                base_params['min_quality'] = ProfileQuality.MEDIUM
            
            if self.data_tracker.is_approaching_limit():
                base_params['data_optimization'] = DataOptimizationLevel.AGGRESSIVE
                base_params['profile_count'] = 1
        
        return base_params
    
    async def _select_profiles_for_strike(self,
                                        opportunity: EnhancedTicketOpportunity,
                                        params: Dict[str, Any]) -> List[BrowserProfile]:
        """Select optimal profiles using ProfileManager's scoring"""
        profile_count = params['profile_count']
        platform = opportunity.platform.to_core_platform()
        
        # Get scored profiles from ProfileManager
        profiles = []
        for _ in range(profile_count):
            profile = await self.profile_manager.get_profile(
                platform=platform,
                quality_preference=params.get('min_quality', ProfileQuality.MEDIUM),
                data_optimization_preference=params.get('data_optimization'),
                exclude_profiles=[p.profile_id for p in profiles]  # Don't reuse
            )
            
            if profile:
                profiles.append(profile)
                # Store profile score for opportunity
                opportunity.profile_scores[profile.profile_id] = \
                    profile.calculate_score(platform)
        
        return profiles
    
    async def _execute_single_strike(self,
                                   opportunity: EnhancedTicketOpportunity,
                                   profile: BrowserProfile,
                                   task_id: str,
                                   params: Dict[str, Any]) -> bool:
        """Execute single strike attempt"""
        start_time = time.time()
        logger.info(f"🎯 Strike initiated: {profile.name} -> {opportunity.event_name}")
        
        try:
            # Get browser context
            context = await self.browser_manager.get_context(profile)
            page = await context.new_page()
            
            try:
                # Execute platform strategy
                strategy = self.platform_strategies.get(opportunity.platform)
                if not strategy:
                    logger.error(f"No strategy for {opportunity.platform}")
                    return False
                
                success = await strategy(page, opportunity, profile)
                
                # Record in ProfileManager
                elapsed = (time.time() - start_time) * 1000
                await self.profile_manager.record_usage(
                    profile_id=profile.profile_id,
                    platform=opportunity.platform.to_core_platform(),
                    success=success,
                    response_time_ms=elapsed,
                    detected=False
                )
                
                if success:
                    logger.critical(f"✅ STRIKE SUCCESS: {profile.name} secured ticket!")
                    opportunity.selected_profile_id = profile.profile_id
                
                return success
                
            finally:
                await page.close()
                
        except BlockedError as e:
            logger.warning(f"Strike blocked: {profile.name} - {e}")
            await self.profile_manager.record_usage(
                profile_id=profile.profile_id,
                platform=opportunity.platform.to_core_platform(),
                success=False,
                error=str(e),
                detected=True
            )
            return False
        except Exception as e:
            logger.error(f"Strike error: {e}", exc_info=True)
            await self.profile_manager.record_usage(
                profile_id=profile.profile_id,
                platform=opportunity.platform.to_core_platform(),
                success=False,
                error=str(e)
            )
            return False
    
    async def _strike_fansale(self,
                            page: PlaywrightPage,
                            opportunity: EnhancedTicketOpportunity,
                            profile: BrowserProfile) -> bool:
        """FanSale strike implementation"""
        try:
            # Navigate with optimized loading
            await page.goto(opportunity.offer_url, wait_until='domcontentloaded')
            
            # Human-like delay
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Find buy button
            buy_selectors = [
                'button:has-text("Acquista")',
                'input[type="submit"][value*="Acquista"]',
                'button.buy-button',
                '#buy-button'
            ]
            
            clicked = False
            for selector in buy_selectors:
                try:
                    elem = page.locator(selector).first
                    if await elem.is_visible(timeout=2000):
                        await elem.hover()
                        await asyncio.sleep(random.uniform(0.1, 0.3))
                        await elem.click()
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                logger.warning("Could not find buy button")
                return False
            
            # Wait for result
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Check success
            success_indicators = ['carrello', 'cart', 'checkout', 'conferma']
            current_url = page.url.lower()
            page_content = await page.content()
            
            return any(indicator in current_url or indicator in page_content.lower()
                      for indicator in success_indicators)
            
        except Exception as e:
            logger.error(f"FanSale strike error: {e}")
            return False
    
    async def _strike_ticketmaster(self,
                                 page: PlaywrightPage,
                                 opportunity: EnhancedTicketOpportunity,
                                 profile: BrowserProfile) -> bool:
        """Ticketmaster strike implementation"""
        logger.warning("Ticketmaster strike not yet implemented")
        return False
    
    async def _strike_vivaticket(self,
                               page: PlaywrightPage,
                               opportunity: EnhancedTicketOpportunity,
                               profile: BrowserProfile) -> bool:
        """Vivaticket strike implementation"""
        logger.warning("Vivaticket strike not yet implemented")
        return False

