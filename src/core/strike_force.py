# src/core/strike_force.py - REWRITTEN WITH ALL FIXES AND IMPROVEMENTS
from __future__ import annotations

import asyncio
import logging
import time
import random
from typing import Dict, List, Optional, Set, Any, TYPE_CHECKING
from collections import defaultdict
from contextlib import suppress
from datetime import datetime

if TYPE_CHECKING:
    from playwright.async_api import Page as PlaywrightPage
    # SmartBrowserContextManager replaced by stealth_integration
    from .stealth_integration import BruceStealthIntegration

# FIXED: Imports from profiles package
from ..profiles import (
    ProfileManager,
    BrowserProfile,
    DataOptimizationLevel,
    ProfileQuality
)

# Core imports (already correct)
from .enums import OperationMode, PlatformType, PriorityLevel
from .models import EnhancedTicketOpportunity, DataUsageTracker

logger = logging.getLogger(__name__)

class BlockedError(Exception):
    """Raised when a request is blocked"""
    pass

class ProfileIntegratedStrikeForce:
    """Enhanced strike system with robust browser automation"""

    def __init__(self,
                 stealth_integration: 'BruceStealthIntegration',
                 profile_manager: ProfileManager,
                 data_tracker: DataUsageTracker,
                 config: Dict[str, Any]):
        self.stealth_integration = stealth_integration
        self.profile_manager = profile_manager
        self.data_tracker = data_tracker
        self.config = config

        self.max_parallel = config.get('strike_settings', {}).get('max_parallel', 5)
        self.strike_timeout = config.get('strike_settings', {}).get('timeout', 30)

        self.active_strikes: Dict[str, Set[str]] = defaultdict(set)
        self.strike_results: Dict[str, bool] = {}

        # Platform strategies
        self.platform_strategies = {
            PlatformType.FANSALE: self._strike_fansale,
            PlatformType.TICKETMASTER: self._strike_ticketmaster,
            PlatformType.VIVATICKET: self._strike_vivaticket
        }
        
        logger.info("🎯 ProfileIntegratedStrikeForce initialized with StealthMaster AI integration")
    
    async def execute_coordinated_strike(self,
                                       opportunity: EnhancedTicketOpportunity,
                                       mode: OperationMode) -> bool:
        """Execute coordinated strike with intelligent profile selection"""
        strike_id = f"{opportunity.id}_{int(time.time())}"
        
        try:
            # Check if already being attempted
            if opportunity.id in self.active_strikes and self.active_strikes[opportunity.id]:
                logger.debug(f"Strike already active for {opportunity.id}")
                return False
            
            # Get strike parameters
            params = self._get_strike_params(mode, opportunity)
            logger.info(f"🎯 Initiating {mode.value} strike for {opportunity.event_name}")
            logger.info(f"   Parameters: {params['profile_count']} profiles, {params['timeout']}s timeout")
            
            # Get profiles for strike
            profiles = await self._select_profiles_for_strike(opportunity, params)
            
            if not profiles:
                logger.error(f"No suitable profiles for {opportunity.id}")
                return False
            
            logger.info(f"🔥 Launching strike with {len(profiles)} profiles")
            
            # Create strike tasks
            tasks = []
            for i, profile in enumerate(profiles):
                task_id = f"{strike_id}_{i}"
                self.active_strikes[opportunity.id].add(task_id)
                
                task = asyncio.create_task(
                    self._execute_single_strike(opportunity, profile, task_id, params),
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
            success = False
            for task in done:
                if not task.cancelled():
                    try:
                        result = task.result()
                        if result:
                            success = True
                            break
                    except Exception as e:
                        logger.error(f"Task error: {e}")
            
            # Cancel pending if success and in race mode
            if success and params['race_mode']:
                logger.info(f"🎉 Success achieved, cancelling {len(pending)} pending strikes")
                for task in pending:
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        await task
            
            if success:
                logger.critical(f"🎉 STRIKE SUCCESS: {opportunity.event_name} secured!")
            else:
                logger.warning(f"⚠️ Strike failed for {opportunity.event_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Coordinated strike error: {e}", exc_info=True)
            return False
        finally:
            # Cleanup
            if opportunity.id in self.active_strikes:
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
        elif mode == OperationMode.STEALTH:
            base_params.update({
                'profile_count': 2,
                'timeout': 45,
                'min_quality': ProfileQuality.MEDIUM,
                'data_optimization': DataOptimizationLevel.BALANCED
            })
        elif mode == OperationMode.HYBRID:
            base_params.update({
                'profile_count': 3,
                'timeout': 35,
                'min_quality': ProfileQuality.MEDIUM,
                'data_optimization': DataOptimizationLevel.BALANCED
            })
        elif mode == OperationMode.ADAPTIVE:
            if opportunity.priority == PriorityLevel.CRITICAL:
                base_params['profile_count'] = 3
                base_params['min_quality'] = ProfileQuality.MEDIUM
            
            if hasattr(self.data_tracker, 'is_approaching_limit') and self.data_tracker.is_approaching_limit():
                base_params['data_optimization'] = DataOptimizationLevel.AGGRESSIVE
                base_params['profile_count'] = 1
        
        return base_params
    
    async def _select_profiles_for_strike(self,
                                        opportunity: EnhancedTicketOpportunity,
                                        params: Dict[str, Any]) -> List[BrowserProfile]:
        """Select optimal profiles with robust fallback logic"""
        profile_count = params['profile_count']
        profiles = []
        used_profile_ids = set()
        
        try:
            # Convert platform with fallback
            core_platform = self._convert_platform_safe(opportunity.platform)
            
            logger.info(f"Selecting {profile_count} profiles for {core_platform}")
            
            # Method 1: Try advanced ProfileManager methods
            for i in range(profile_count):
                profile = None
                
                # Try get_profile_for_platform first (most likely to exist)
                try:
                    if hasattr(self.profile_manager, 'get_profile_for_platform'):
                        profile = await self.profile_manager.get_profile_for_platform(
                            platform=core_platform,
                            require_session=False
                        )
                        
                        # Check if already used
                        if profile and hasattr(profile, 'profile_id') and profile.profile_id in used_profile_ids:
                            profile = None
                            
                except Exception as e:
                    logger.debug(f"get_profile_for_platform failed: {e}")
                
                # Try alternative get_profile method
                if not profile:
                    try:
                        if hasattr(self.profile_manager, 'get_profile'):
                            profile = await self.profile_manager.get_profile(
                                platform=core_platform,
                                quality_preference=params.get('min_quality', ProfileQuality.MEDIUM),
                                exclude_profiles=list(used_profile_ids)
                            )
                    except Exception as e:
                        logger.debug(f"get_profile failed: {e}")
                
                # Add profile if valid
                if profile:
                    profiles.append(profile)
                    profile_id = getattr(profile, 'profile_id', getattr(profile, 'id', f'profile_{i}'))
                    used_profile_ids.add(profile_id)
                    logger.info(f"Selected profile: {profile_id}")
                else:
                    logger.warning(f"Could not get profile {i+1}/{profile_count}")
                    break
            
            # Fallback: Use any available profiles
            if not profiles:
                logger.warning("No profiles from ProfileManager, using fallback")
                try:
                    available_profiles = list(getattr(self.profile_manager, 'dynamic_profiles', []))
                    if available_profiles:
                        # Take up to profile_count profiles
                        profiles = available_profiles[:profile_count]
                        logger.info(f"Using {len(profiles)} fallback profiles")
                    else:
                        logger.error("No dynamic profiles available")
                except Exception as e:
                    logger.error(f"Fallback profile selection failed: {e}")
            
        except Exception as e:
            logger.error(f"Profile selection error: {e}", exc_info=True)
        
        logger.info(f"Selected {len(profiles)} profiles for strike")
        return profiles
    
    def _convert_platform_safe(self, platform: PlatformType):
        """Safely convert PlatformType to CorePlatformEnum"""
        try:
            from src.profiles.enums import Platform as CorePlatformEnum
            
            # Platform mapping
            mapping = {
                PlatformType.FANSALE: getattr(CorePlatformEnum, 'FANSALE', CorePlatformEnum.GENERIC),
                PlatformType.TICKETMASTER: getattr(CorePlatformEnum, 'TICKETMASTER', CorePlatformEnum.GENERIC),
                PlatformType.VIVATICKET: getattr(CorePlatformEnum, 'VIVATICKET', CorePlatformEnum.GENERIC)
            }
            
            result = mapping.get(platform, CorePlatformEnum.GENERIC)
            return result
            
        except Exception as e:
            logger.warning(f"Platform conversion failed: {e}")
            # Final fallback - just return the original platform value as string
            return platform.value if hasattr(platform, 'value') else str(platform)
    
    async def _execute_single_strike(self,
                                   opportunity: EnhancedTicketOpportunity,
                                   profile: BrowserProfile,
                                   task_id: str,
                                   params: Dict[str, Any]) -> bool:
        """Execute single strike attempt with robust error handling"""
        start_time = time.time()
        profile_id = getattr(profile, 'profile_id', getattr(profile, 'id', 'unknown'))
        
        logger.info(f"🎯 Strike initiated: Profile {profile_id} -> {opportunity.event_name}")
        
        try:
            # Get browser context
            context = await self.browser_manager.get_stealth_context(profile, force_new=False)
            page = await context.new_page()
            
            try:
                # Execute platform strategy
                strategy = self.platform_strategies.get(opportunity.platform)
                if not strategy:
                    logger.error(f"No strategy for {opportunity.platform}")
                    return False
                
                success = await strategy(page, opportunity, profile)
                
                # Record usage if ProfileManager supports it
                elapsed = (time.time() - start_time) * 1000
                await self._record_usage_safe(profile, opportunity, success, elapsed, False)
                
                if success:
                    logger.critical(f"✅ STRIKE SUCCESS: Profile {profile_id} secured {opportunity.event_name}!")
                    
                    # Store successful profile ID if opportunity supports it
                    if hasattr(opportunity, 'selected_profile_id'):
                        opportunity.selected_profile_id = profile_id
                
                return success
                
            finally:
                # Always close the page
                try:
                    await page.close()
                except Exception as e:
                    logger.debug(f"Error closing page: {e}")
                
        except BlockedError as e:
            logger.warning(f"Strike blocked: Profile {profile_id} - {e}")
            elapsed = (time.time() - start_time) * 1000
            await self._record_usage_safe(profile, opportunity, False, elapsed, True)
            return False
        except Exception as e:
            logger.error(f"Strike error for profile {profile_id}: {e}", exc_info=True)
            elapsed = (time.time() - start_time) * 1000
            await self._record_usage_safe(profile, opportunity, False, elapsed, False)
            return False
    
    async def _record_usage_safe(self, profile: BrowserProfile, opportunity: EnhancedTicketOpportunity,
                               success: bool, elapsed_ms: float, detected: bool):
        """Safely record profile usage with fallbacks"""
        try:
            profile_id = getattr(profile, 'profile_id', getattr(profile, 'id', 'unknown'))
            core_platform = self._convert_platform_safe(opportunity.platform)
            
            # Try different record_usage method signatures
            if hasattr(self.profile_manager, 'record_usage'):
                try:
                    # Try full signature
                    await self.profile_manager.record_usage(
                        profile_id=profile_id,
                        platform=core_platform,
                        success=success,
                        response_time_ms=elapsed_ms,
                        detected=detected
                    )
                except TypeError:
                    # Try simpler signature
                    try:
                        await self.profile_manager.record_usage(
                            profile_id=profile_id,
                            success=success,
                            response_time_ms=elapsed_ms
                        )
                    except TypeError:
                        # Try basic signature
                        await self.profile_manager.record_usage(
                            profile_id=profile_id,
                            success=success
                        )
            else:
                logger.debug("ProfileManager doesn't have record_usage method")
                
        except Exception as e:
            logger.debug(f"Could not record usage: {e}")
    
    async def _strike_fansale(self,
                            page: 'PlaywrightPage',
                            opportunity: EnhancedTicketOpportunity,
                            profile: BrowserProfile) -> bool:
        """Enhanced FanSale strike implementation"""
        try:
            logger.info(f"🎯 FanSale strike: {opportunity.event_name}")
            
            # Navigate with optimized loading
            await page.goto(opportunity.offer_url, wait_until='domcontentloaded', timeout=30000)
            
            # Human-like delay
            await asyncio.sleep(random.uniform(1.0, 2.5))
            
            # Log page info
            title = await page.title()
            logger.info(f"📄 FanSale page loaded: {title}")
            
            # Enhanced buy button selectors
            buy_selectors = [
                'button:has-text("Acquista")', 'button:has-text("Compra")',
                'button:has-text("Buy")', 'button:has-text("Aggiungi al carrello")',
                'input[type="submit"][value*="Acquista"]', 'input[type="submit"][value*="Compra"]',
                'button.buy-button', 'button.purchase-button', 'button.btn-buy',
                '#buy-button', '#purchase-button', '.btn-primary',
                'a[href*="buy"]', 'a[href*="purchase"]', 'a[href*="acquista"]'
            ]
            
            clicked = False
            for selector in buy_selectors:
                try:
                    elements = await page.locator(selector).all()
                    for element in elements:
                        if await element.is_visible(timeout=2000):
                            logger.info(f"🎯 Found FanSale buy button: {selector}")
                            await element.hover()
                            await asyncio.sleep(random.uniform(0.2, 0.5))
                            await element.click()
                            clicked = True
                            logger.info(f"✅ Clicked FanSale button: {selector}")
                            break
                    if clicked:
                        break
                except Exception as e:
                    logger.debug(f"Failed to interact with {selector}: {e}")
                    continue
            
            if not clicked:
                logger.warning("❌ Could not find FanSale buy button")
                return False
            
            # Wait for result
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Enhanced success detection
            success_indicators = [
                'carrello', 'cart', 'checkout', 'conferma', 'confirmation',
                'pagamento', 'payment', 'ordine', 'order', 'ticket'
            ]
            
            current_url = page.url.lower()
            page_content = (await page.content()).lower()
            
            success = any(indicator in current_url or indicator in page_content
                         for indicator in success_indicators)
            
            if success:
                logger.critical(f"🎉 FanSale strike SUCCESS!")
            else:
                logger.warning(f"⚠️ FanSale strike unclear result")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ FanSale strike error: {e}")
            return False
    
    async def _strike_ticketmaster(self,
                                 page: 'PlaywrightPage',
                                 opportunity: EnhancedTicketOpportunity,
                                 profile: BrowserProfile) -> bool:
        """Enhanced Ticketmaster strike implementation"""
        try:
            logger.info(f"🎯 Ticketmaster strike: {opportunity.event_name}")
            
            # Navigate to the opportunity URL
            await page.goto(opportunity.offer_url, wait_until='domcontentloaded', timeout=30000)
            
            # Human-like delay
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
            # Log page title
            title = await page.title()
            logger.info(f"📄 Ticketmaster page: {title}")
            
            # Ticketmaster-specific selectors
            buy_selectors = [
                'button:has-text("Buy")', 'button:has-text("Purchase")',
                'button:has-text("Get Tickets")', 'button:has-text("Buy Tickets")',
                'button:has-text("Add to Cart")', 'button:has-text("Select")',
                '.buy-button', '.purchase-button', '.btn-primary', '.btn-buy',
                'input[value*="Buy"]', 'input[value*="Purchase"]', 'input[value*="Add"]',
                'a[href*="purchase"]', 'a[href*="buy"]', 'a[href*="cart"]',
                '[data-testid*="buy"]', '[data-testid*="purchase"]'
            ]
            
            clicked = False
            for selector in buy_selectors:
                try:
                    elements = await page.locator(selector).all()
                    for element in elements:
                        if await element.is_visible(timeout=3000):
                            logger.info(f"🎯 Found Ticketmaster buy button: {selector}")
                            await element.hover()
                            await asyncio.sleep(random.uniform(0.3, 0.7))
                            await element.click()
                            clicked = True
                            logger.info(f"✅ Clicked Ticketmaster button: {selector}")
                            break
                    if clicked:
                        break
                except Exception as e:
                    logger.debug(f"Failed to interact with {selector}: {e}")
                    continue
            
            if not clicked:
                logger.warning("❌ Could not find Ticketmaster buy button")
                return False
            
            # Wait for response
            await page.wait_for_load_state('networkidle', timeout=20000)
            
            # Success detection
            success_indicators = [
                'cart', 'checkout', 'payment', 'order', 'confirmation',
                'seat', 'ticket', 'purchase', 'billing', 'summary'
            ]
            
            current_url = page.url.lower()
            page_content = (await page.content()).lower()
            
            success = any(indicator in current_url or indicator in page_content
                         for indicator in success_indicators)
            
            if success:
                logger.critical(f"🎉 Ticketmaster strike SUCCESS!")
            else:
                logger.warning(f"⚠️ Ticketmaster strike unclear result")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Ticketmaster strike error: {e}")
            return False
    
    async def _strike_vivaticket(self,
                               page: 'PlaywrightPage',
                               opportunity: EnhancedTicketOpportunity,
                               profile: BrowserProfile) -> bool:
        """Enhanced Vivaticket strike implementation"""
        try:
            logger.info(f"🎯 Vivaticket strike: {opportunity.event_name}")
            
            # Navigate to the opportunity URL
            await page.goto(opportunity.offer_url, wait_until='domcontentloaded', timeout=30000)
            
            # Human-like delay
            await asyncio.sleep(random.uniform(1.0, 2.5))
            
            # Log page title
            title = await page.title()
            logger.info(f"📄 Vivaticket page: {title}")
            
            # Vivaticket-specific selectors
            buy_selectors = [
                'button:has-text("Acquista")', 'button:has-text("Compra")',
                'button:has-text("Buy")', 'button:has-text("Aggiungi al carrello")',
                'button:has-text("Seleziona")', 'button:has-text("Prenota")',
                '.buy-button', '.purchase-button', '.btn-buy', '.btn-primary',
                'input[value*="Acquista"]', 'input[value*="Compra"]', 'input[value*="Buy"]',
                'a[href*="buy"]', 'a[href*="purchase"]', 'a[href*="acquista"]',
                '[data-action*="buy"]', '[data-action*="purchase"]'
            ]
            
            clicked = False
            for selector in buy_selectors:
                try:
                    elements = await page.locator(selector).all()
                    for element in elements:
                        if await element.is_visible(timeout=3000):
                            logger.info(f"🎯 Found Vivaticket buy button: {selector}")
                            await element.hover()
                            await asyncio.sleep(random.uniform(0.2, 0.5))
                            await element.click()
                            clicked = True
                            logger.info(f"✅ Clicked Vivaticket button: {selector}")
                            break
                    if clicked:
                        break
                except Exception as e:
                    logger.debug(f"Failed to interact with {selector}: {e}")
                    continue
            
            if not clicked:
                logger.warning("❌ Could not find Vivaticket buy button")
                return False
            
            # Wait for response
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Success detection
            success_indicators = [
                'carrello', 'cart', 'checkout', 'pagamento', 'payment',
                'conferma', 'confirmation', 'ordine', 'order', 'biglietto',
                'ticket', 'riepilogo', 'summary'
            ]
            
            current_url = page.url.lower()
            page_content = (await page.content()).lower()
            
            success = any(indicator in current_url or indicator in page_content
                         for indicator in success_indicators)
            
            if success:
                logger.critical(f"🎉 Vivaticket strike SUCCESS!")
            else:
                logger.warning(f"⚠️ Vivaticket strike unclear result")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Vivaticket strike error: {e}")
            return False