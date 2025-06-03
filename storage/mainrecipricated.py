# src/main.py (Refactored for Beast Mode Integration)
from __future__ import annotations

import asyncio
import logging
import logging.handlers
import signal
import sys
from pathlib import Path
import argparse
from typing import Callable, Dict, List, Optional, TYPE_CHECKING, Any, Tuple
import platform as platform_os
import subprocess
import os
import random
import time
import json
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import copy # For deep merging configs
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

import yaml

# Your existing core imports
from core.browser_manager import StealthBrowserManager, BrowserProfile # BrowserProfile is already rich!
from playwright.async_api import (
    Error as PlaywrightError,
    Page as PlaywrightPage,
    BrowserContext as PlaywrightContext,
    async_playwright, # For managing Playwright lifecycle
    Playwright # For type hinting
)
from core.errors import BlockedError

# --- Beast Mode Import ---
from beast_mode import run_beast_mode, BeastModeOrchestrator # Import orchestrator for type hinting if needed

# Platform checkers (already present)
from platforms import ticketmaster
from platforms import vivaticket
from platforms import fansale

# Utility imports (already present)
from utils.tls_fingerprint import patch_ssl_for_fingerprint_evasion
from utils.advanced_behavioral_simulation import simulate_advanced_human_behavior, BiometricProfile


if TYPE_CHECKING:
    import queue as threading_queue # For GUI bridge

CONFIG_FILE = Path("config/config.yaml")
# Define path for beast mode specific config
BEAST_MODE_CONFIG_FILE = Path("config/beast_mode_config.yaml")


# Global state for signal handling (already present)
_apa_instance_for_signal: Optional[AdvancedPurchaseArchitecture] = None
_stop_event_for_signal: Optional[asyncio.Event] = None
_active_monitoring_tasks_for_signal: List[asyncio.Task] = [] # Used by existing stealth mode

# --- Enums and Dataclasses (PriorityLevel, TicketHit, CircuitBreakerState - already present) ---
class PriorityLevel(Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

@dataclass
class TicketHit: # Keep your existing TicketHit for APA's queue
    platform: str
    event_name: str
    url: str
    offer_url: str
    priority: PriorityLevel
    timestamp: float
    hit_data: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3

    def __lt__(self, other: TicketHit) -> bool:
        if not isinstance(other, TicketHit):
            return NotImplemented
        return (self.priority.value, self.timestamp) < (other.priority.value, other.timestamp)

@dataclass
class CircuitBreakerState: # Already present
    failure_count: int = 0
    last_failure_time: float = 0.0
    state: str = "CLOSED"
    failure_threshold: int = 5
    recovery_timeout: float = 300.0

# --- Helper Classes (AdvancedNotifier, FingerprintRandomizer, PlatformStealthManager - already present) ---
class AdvancedNotifier: # Your existing class
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg_notifications = cfg.get("notifications", {})
        self.console_alerts: bool = bool(self.cfg_notifications.get("console_alerts", True))
        self.logger = logging.getLogger("AdvancedNotifier")
        self.alert_history: deque = deque(maxlen=self.cfg_notifications.get("alert_history_size", 100))
        self.rate_limiter: Dict[str, float] = {}
        self.alert_rate_limit_s = self.cfg_notifications.get("alert_rate_limit_s", 10.0)

    async def alert(self, message: str, level: str = "CRITICAL", category: str = "general") -> None:
        current_time = time.time()
        rate_key = f"{category}_{level.lower()}"
        if current_time - self.rate_limiter.get(rate_key, 0) < self.alert_rate_limit_s:
            self.logger.debug(f"Rate limit: Suppressed alert for {rate_key}: {message}")
            return
        self.rate_limiter[rate_key] = current_time
        self.alert_history.append((current_time, level, category, message))
        log_method = getattr(self.logger, level.lower(), self.logger.critical)
        if self.console_alerts:
            icon = "🚨" if level in ["CRITICAL", "ERROR"] else "⚠️" if level == "WARNING" else "ℹ️"
            log_method(f"{icon} [{category.upper()}] {message}")

class FingerprintRandomizer: # Your existing class
    @staticmethod
    async def randomize_page_fingerprint(page: PlaywrightPage) -> None:
        logger_fp = logging.getLogger("FingerprintRandomizer")
        try:
            await page.add_init_script(f"Math.random = () => {random.random()};")
            logger_fp.debug("Applied minor dynamic fingerprint randomization to page.")
        except Exception as e:
            logger_fp.error(f"Error applying dynamic fingerprint randomization: {e}")

class PlatformStealthManager: # Your existing class
    @staticmethod
    async def apply_platform_specific_stealth(page: PlaywrightPage, platform: str):
        logger_ps = logging.getLogger(f"PlatformStealth.{platform.lower()}")
        logger_ps.debug(f"Applying platform-specific JS stealth (placeholder) for {platform} on page: {page.url[:80]}")

# --- Main Application Architecture (AdvancedPurchaseArchitecture - APA) ---
# This class is already well-defined in your src/main.py. We will primarily ensure
# its browser_manager is correctly initialized and can be used by Beast Mode.
# Key changes:
# 1. APA's browser_manager will be the ONE manager for both modes.
# 2. Profile stats update mechanism needs to be callable by Beast Mode.
class AdvancedPurchaseArchitecture: # Your existing class
    def __init__(self, main_config_data: Dict[str, Any],
                 all_available_profiles_for_apa_logic: List[BrowserProfile],
                 stop_event: asyncio.Event,
                 playwright_instance: Playwright):
        self.logger = logging.getLogger("AdvancedPurchaseArch")
        self.main_config_data = main_config_data
        self.app_settings = main_config_data.get("app_settings", {})
        self._stop_event = stop_event
        self.playwright: Playwright = playwright_instance
        self.notifier = AdvancedNotifier(main_config_data)
        self.browser_manager: Optional[StealthBrowserManager] = None # Will be initialized
        self.ticket_hit_queue: asyncio.PriorityQueue[TicketHit] = asyncio.PriorityQueue(
            maxsize=self.app_settings.get("ticket_hit_queue_size", 50)
        )
        self.purchase_workers: List[asyncio.Task] = []
        self.num_purchase_workers = self.app_settings.get("purchase_worker_count",
            self.app_settings.get("browser_pool",{}).get("target_size",1)
        )
        if self.num_purchase_workers <= 0: self.num_purchase_workers = 1

        self.circuit_breakers: Dict[str, CircuitBreakerState] = defaultdict(lambda: CircuitBreakerState(
            failure_threshold=self.app_settings.get("circuit_breaker_failure_threshold", 3),
            recovery_timeout=self.app_settings.get("circuit_breaker_recovery_timeout_s", 180.0)
        ))
        self.performance_metrics: Dict[str, Any] = defaultdict(float)
        self.performance_metrics.update({
            "hits_processed": 0, "successful_purchases": 0, "failed_purchases": 0, "blocks_detected":0,
            "api_calls": 0, "ui_interactions": 0
        })
        self.golden_profile_object: Optional[BrowserProfile] = None
        self.is_purchase_system_ready: bool = False
        self._purchase_readiness_task: Optional[asyncio.Task] = None

        golden_profile_name: Optional[str] = self.app_settings.get("golden_profile_name_1")
        if golden_profile_name and all_available_profiles_for_apa_logic:
            self.golden_profile_object = next((p for p in all_available_profiles_for_apa_logic if p.name == golden_profile_name), None)
            if self.golden_profile_object:
                self.logger.info(f"Golden profile '{self.golden_profile_object.name}' identified.")
            else:
                self.logger.error(f"Specified golden profile '{golden_profile_name}' not found.")
        elif not golden_profile_name:
            self.logger.warning("No 'golden_profile_name_1' configured.")

        self.target_platform_for_purchase_system = self._detect_target_platform()
        # Initialize the single browser manager - THIS IS KEY FOR BEAST MODE TOO
        self._initialize_browser_manager(main_config_data, all_available_profiles_for_apa_logic)


    def _detect_target_platform(self) -> str: # Your existing method
        main_purchase_url = self.app_settings.get("main_purchase_url", "").lower()
        if not main_purchase_url: return "unknown"
        if "fansale" in main_purchase_url: return "FanSale"
        if "ticketmaster" in main_purchase_url: return "Ticketmaster"
        if "vivaticket" in main_purchase_url: return "Vivaticket"
        return "unknown"

    def _prepare_config_for_browser_manager(self, base_config: Dict[str, Any]) -> Dict[str, Any]: # Your existing method
        manager_cfg = json.loads(json.dumps(base_config))
        manager_cfg.setdefault('browser_launch_options', {})
        manager_cfg['browser_launch_options']['use_persistent_user_data_dir_if_available'] = True
        return manager_cfg

    def _initialize_browser_manager(self, main_config_data: Dict[str, Any], all_profiles: List[BrowserProfile]):
        try:
            manager_config = self._prepare_config_for_browser_manager(main_config_data)
            # Pass ALL loaded profiles to StealthBrowserManager constructor.
            # StealthBrowserManager itself will load them from its configured path,
            # but having them here allows APA to link the golden_profile_object reference.
            # The StealthBrowserManager needs to be adapted or confirmed it can take a list of pre-loaded profiles
            # or that its internal loading makes them available via self.profiles for APA.
            # For now, we assume StealthBrowserManager internally loads profiles based on its 'config'.
            # The `all_profiles` list is used here for APA's logic to find the golden profile.
            # The `StealthBrowserManager` itself should load and manage its list of profiles
            # which will include these `all_profiles` if the YAML path is the same.

            self.browser_manager = StealthBrowserManager(
                config=manager_config, # This config should point to browser_profiles.yaml
                playwright_instance=self.playwright
                # StealthBrowserManager constructor in your provided code loads profiles internally
            )
            # After SBM initializes and loads its profiles, ensure APA can access them if needed,
            # particularly for beast_mode's profile selection.
            # If SBM's profiles are loaded and accessible as `self.browser_manager.profiles`,
            # then `all_available_profiles_for_apa_logic` was mainly for `golden_profile_object` identification.
            self.logger.info("Primary StealthBrowserManager (V2) instance created for APA.")
        except Exception as e:
            self.logger.critical(f"FATAL ERROR initializing primary StealthBrowserManager for APA: {e}", exc_info=True)
            self.browser_manager = None

    # Method to update profile stats - CALLED BY BEAST MODE
    async def update_profile_stats(self, profile_name: str, platform: str, success: bool):
        if not self.browser_manager or not self.browser_manager.profiles:
            self.logger.warning(f"Cannot update profile stats for {profile_name}: BrowserManager or profiles not available.")
            return

        profile_to_update = next((p for p in self.browser_manager.profiles if p.name == profile_name), None)
        if profile_to_update:
            profile_to_update.last_used = datetime.now()
            if success:
                profile_to_update.success_count += 1
                # platform_success_rate is not directly in your BrowserProfile dataclass
                # You might add a dict: platform_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)
                # e.g., profile_to_update.platform_stats.setdefault(platform, {'success':0, 'failure':0})['success'] += 1
                self.logger.info(f"Profile '{profile_name}' stats updated: success on {platform}.")
            else:
                profile_to_update.failure_count += 1
                self.logger.info(f"Profile '{profile_name}' stats updated: failure on {platform}.")
        else:
            self.logger.warning(f"Could not find profile '{profile_name}' in BrowserManager to update stats.")


    async def initialize_purchase_side_systems(self, gui_q: Optional[asyncio.Queue] = None) -> bool: # Your existing method
        if not self.browser_manager:
            self.logger.error("APA: BrowserManager not available. Cannot initialize purchase systems.")
            self.is_purchase_system_ready = False
            return False
        if not self.golden_profile_object:
            self.logger.warning("APA: Golden Profile not configured. Purchase readiness & auto-purchases skipped.")
            self.is_purchase_system_ready = False
            await self._start_purchase_workers(gui_q) # Start workers even if no golden profile
            return True

        self.logger.info("APA: Initializing purchase side systems...")
        try:
            await self._start_purchase_workers(gui_q)
            self._purchase_readiness_task = asyncio.create_task(
                self._maintain_purchase_readiness_loop(gui_q=gui_q), name="PurchaseReadinessLoop"
            )
            return True
        except Exception as e:
            self.logger.error(f"APA: Error initializing purchase side systems: {e}", exc_info=True)
            self.is_purchase_system_ready = False
            return False

    async def _start_purchase_workers(self, gui_q: Optional[asyncio.Queue] = None): # Your existing method
        self.purchase_workers.clear()
        for i in range(self.num_purchase_workers):
            worker_task_name = f"PurchaseWorker-{i}"
            worker = asyncio.create_task(
                self._purchase_worker(worker_id=i, gui_q=gui_q), name=worker_task_name
            )
            self.purchase_workers.append(worker)
        self.logger.info(f"APA: Started {len(self.purchase_workers)} purchase worker(s).")

    async def _verify_authentication_on_page(self, page: PlaywrightPage, platform_to_check: str) -> bool: # Your existing method
        effective_platform = platform_to_check.lower()
        if effective_platform == "unknown" and self.target_platform_for_purchase_system != "unknown":
            effective_platform = self.target_platform_for_purchase_system.lower()
        self.logger.debug(f"APA Auth check for '{effective_platform}' on {page.url[:80]}")
        if page.is_closed(): return False
        auth_selectors = {
            "fansale": "a[href*='myfansale'], a:has-text('Mio account'), div.is-logged-in",
            "ticketmaster": "button[data-testid='user-menu-button'], a[href*='member'], [data-tm-icon='person']",
            "vivaticket": "a[href*='logout'], .userBoxLogged, .is-logged-in"
        }
        timeout_per_selector_ms = self.app_settings.get("auth_check_selector_timeout_ms", 7000) / len(auth_selectors.get(effective_platform, "").split(',')) if auth_selectors.get(effective_platform) else 2000

        if effective_platform in auth_selectors:
            try:
                for selector in auth_selectors[effective_platform].split(','):
                    trimmed_selector = selector.strip()
                    if not trimmed_selector: continue
                    if await page.locator(trimmed_selector).first.is_visible(timeout=timeout_per_selector_ms):
                        self.logger.info(f"APA Auth PASSED for '{effective_platform}' (selector: '{trimmed_selector}')")
                        return True
                self.logger.warning(f"APA Auth FAILED for '{effective_platform}' (no selectors visible).")
                return False
            except PlaywrightError as e_auth_check:
                self.logger.info(f"APA Auth for '{effective_platform}' FAILED (timeout/error): {str(e_auth_check)[:100]}")
                return False
            except Exception as e:
                self.logger.error(f"APA Auth unexpected error for '{effective_platform}': {e}", exc_info=True)
                return False
        self.logger.warning(f"APA: No auth selectors for '{effective_platform}'.")
        return False

    async def _maintain_purchase_readiness_loop(self, gui_q: Optional[asyncio.Queue] = None): # Your existing method (can remain largely unchanged)
        if not self.browser_manager or not self.golden_profile_object:
            self.logger.error("APA ReadinessLoop: BrowserManager or Golden Profile not available.")
            self.is_purchase_system_ready = False
            return
        await asyncio.sleep(random.uniform(3,10))
        interval = self.app_settings.get("purchase_readiness_interval_s", 60.0)
        url = self.app_settings.get("main_purchase_url")
        if not url:
            self.logger.error("APA ReadinessLoop: 'main_purchase_url' not set.")
            self.is_purchase_system_ready = False
            return
        self.logger.info(f"APA ReadinessLoop started for Golden Profile '{self.golden_profile_object.name}'. Interval: {interval}s.")
        page_for_check: Optional[PlaywrightPage] = None
        while not self._stop_event.is_set():
            try:
                ctx = await self.browser_manager.get_persistent_context_for_profile(self.golden_profile_object)
                if not ctx:
                    self.logger.error("APA ReadinessLoop: Failed to get persistent context.")
                    self.is_purchase_system_ready = False
                    await asyncio.sleep(interval / 2); continue
                page_for_check = await ctx.new_page()
                await page_for_check.goto(url, wait_until="domcontentloaded", timeout=self.app_settings.get("purchase_navigation_timeout_ms", 30000))
                
                human_intensity = self.app_settings.get("readiness_check_human_intensity", "low")
                if human_intensity != "none" and self.golden_profile_object.extra_js_props: # Check extra_js_props
                    biometric_cfg = self.golden_profile_object.extra_js_props.get("biometric_profile_config", {})
                    bio_profile = BiometricProfile(**biometric_cfg) if biometric_cfg else BiometricProfile()
                    await simulate_advanced_human_behavior(page_for_check, intensity=human_intensity, profile=bio_profile)

                auth_status = await self._verify_authentication_on_page(page_for_check, self.target_platform_for_purchase_system)
                if auth_status:
                    if not self.is_purchase_system_ready: self.logger.info(f"APA ReadinessLoop: Golden profile NOW AUTHENTICATED.")
                    self.is_purchase_system_ready = True
                else:
                    if self.is_purchase_system_ready: self.logger.warning(f"APA ReadinessLoop: Golden profile NO LONGER AUTHENTICATED.")
                    else: self.logger.warning(f"APA ReadinessLoop: Golden profile REMAINS UNAUTHENTICATED.")
                    self.is_purchase_system_ready = False
            except Exception as e:
                self.logger.error(f"APA ReadinessLoop error: {e}", exc_info=True)
                self.is_purchase_system_ready = False
            finally:
                if page_for_check and not page_for_check.is_closed(): await page_for_check.close()
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError: continue
            except asyncio.CancelledError: break
        self.logger.info("APA Purchase Readiness Loop stopped.")
        self.is_purchase_system_ready = False

    async def _purchase_worker(self, worker_id: int, gui_q: Optional[asyncio.Queue] = None): # Your existing method (can remain largely unchanged)
        worker_logger = logging.getLogger(f"APAPurchaseWorker-{worker_id}")
        worker_logger.info(f"Worker {worker_id} started.")
        hit_being_processed: Optional[TicketHit] = None
        while not self._stop_event.is_set():
            hit_being_processed = None
            try:
                hit_being_processed = await asyncio.wait_for(self.ticket_hit_queue.get(), timeout=1.0)
                worker_logger.info(f"W-{worker_id}: Picked {hit_being_processed.priority.name} hit for '{hit_being_processed.event_name}'. Queue: {self.ticket_hit_queue.qsize()}")
                success = await self._execute_ultra_fast_purchase(hit_being_processed, worker_id, gui_q)
                self.performance_metrics["hits_processed"] += 1
                if success: self.performance_metrics["successful_purchases"] += 1
                else: self.performance_metrics["failed_purchases"] += 1
                self.ticket_hit_queue.task_done()
                hit_being_processed = None
            except asyncio.TimeoutError: continue
            except asyncio.CancelledError:
                if hit_being_processed: self.ticket_hit_queue.put_nowait(hit_being_processed)
                break
            except Exception as e:
                worker_logger.error(f"W-{worker_id} error: {e}", exc_info=True)
                if hit_being_processed:
                    if hit_being_processed.retry_count < hit_being_processed.max_retries:
                        hit_being_processed.retry_count += 1
                        await self.ticket_hit_queue.put(hit_being_processed)
                    else:
                        self.performance_metrics["failed_purchases"] += 1
                await asyncio.sleep(random.uniform(1,3))
        worker_logger.info(f"Worker {worker_id} stopped.")

    async def _execute_ultra_fast_purchase(self, hit: TicketHit, worker_id: int, gui_q: Optional[asyncio.Queue] = None) -> bool: # Your existing method (can remain largely unchanged)
        # This method uses self.golden_profile_object and self.browser_manager
        # The platform-specific actions call your existing platform modules.
        # This logic can be kept as is for "stealth mode" purchases if APA's queue is used.
        # Beast Mode's InstantStrike will have its own purchase attempt logic also using apa.browser_manager but with selected profiles.
        platform_lower = hit.platform.lower()
        worker_logger = logging.getLogger(f"APAPurchaseExec.W{worker_id}")
        if not self.golden_profile_object or not self.browser_manager: return False
        if not self.is_purchase_system_ready:
            worker_logger.warning(f"APA Purchase system not ready, skipping '{hit.event_name}'.")
            return False
        if not self._check_circuit_breaker(platform_lower): return False
        
        page_for_purchase: Optional[PlaywrightPage] = None
        action_succeeded = False
        try:
            worker_logger.info(f"APA W-{worker_id} purchasing: '{hit.event_name}' URL: {hit.offer_url}")
            if platform_lower == "fansale" and platform_os.system() == "Darwin" and self.app_settings.get("enable_fansale_safari_handoff_macos", False):
                return await self._safari_handoff(hit, worker_id, gui_q)

            ctx = await self.browser_manager.get_persistent_context_for_profile(self.golden_profile_object)
            if not ctx:
                self._record_circuit_breaker_failure(platform_lower, is_critical=True)
                return False
            page_for_purchase = await ctx.new_page()

            if self.golden_profile_object.extra_js_props: # Check extra_js_props
                biometric_cfg = self.golden_profile_object.extra_js_props.get("biometric_profile_config", {})
                bio_profile = BiometricProfile(**biometric_cfg) if biometric_cfg else BiometricProfile()
                await simulate_advanced_human_behavior(page_for_purchase, intensity=self.app_settings.get("purchase_human_intensity", "medium"), profile=bio_profile)

            await page_for_purchase.goto(hit.offer_url, wait_until=self.app_settings.get("purchase_nav_wait_until", "domcontentloaded"), timeout=self.app_settings.get("purchase_navigation_timeout_ms", 30000))
            action_succeeded = await self._platform_specific_purchase_action(page_for_purchase, self.golden_profile_object, hit, platform_lower, worker_id)
            if action_succeeded: self._record_circuit_breaker_success(platform_lower)
            else: self._record_circuit_breaker_failure(platform_lower)
            return action_succeeded
        except Exception as e:
            worker_logger.error(f"APA W-{worker_id} purchase error for '{hit.event_name}': {e}", exc_info=True)
            self._record_circuit_breaker_failure(platform_lower, is_critical=True)
            if page_for_purchase and not page_for_purchase.is_closed() and self.app_settings.get("pause_on_purchase_error", True):
                try: await page_for_purchase.pause()
                except PlaywrightError: pass
            return False
        finally:
            if page_for_purchase and not page_for_purchase.is_closed(): await page_for_purchase.close()

    async def _safari_handoff(self, hit: TicketHit, worker_id: int, gui_q: Optional[asyncio.Queue] = None) -> bool: # Your existing method
        worker_logger = logging.getLogger(f"APASafariHandoff.W{worker_id}")
        worker_logger.warning(f"SAFARI HANDOFF for '{hit.event_name}' to {hit.offer_url}")
        try:
            process = await asyncio.create_subprocess_exec('open', '-a', 'Safari', hit.offer_url)
            await process.wait()
            if process.returncode == 0:
                await self.notifier.alert(f"SAFARI HANDOFF for '{hit.event_name}'. Check Safari!", category="purchase_handoff", level="CRITICAL")
                return True
            return False
        except Exception as e:
            worker_logger.error(f"Safari handoff FAILED: {e}", exc_info=True)
            return False

    async def _platform_specific_purchase_action(self, page: PlaywrightPage, browser_profile: BrowserProfile, hit: TicketHit, platform_lower: str, worker_id: int) -> bool: # Your existing method
        # This method calls your platform modules (ticketmaster.py, fansale.py, etc.)
        # It can be used by APA's stealth mode. Beast Mode's InstantStrike will have its own
        # way of calling these platform modules or its simplified purchase logic.
        action_logger = logging.getLogger(f"APAPurchaseAction.W{worker_id}.{platform_lower}")
        action_logger.info(f"APA executing platform-specific purchase for '{hit.event_name}'")
        target_cfg_for_hit = hit.hit_data.get('original_target_config', {})
        try:
            if platform_lower == "ticketmaster":
                offer_id = hit.hit_data.get("offer_id")
                if offer_id and hasattr(ticketmaster, 'add_to_basket'):
                    success, _ = await ticketmaster.add_to_basket(page.context, str(offer_id), event_page_url=hit.url)
                    if success and self.app_settings.get("pause_after_successful_tm_api_add", True):
                        await page.pause()
                    return success
                else: await page.pause(); return True # Manual fallback
            elif platform_lower == "vivaticket": # Simplified from your code
                buy_selectors = target_cfg_for_hit.get("vivaticket_purchase_buy_selectors", "button[type='submit']:has-text('Acquista')")
                for selector in buy_selectors.split(','):
                    if await page.locator(selector.strip()).first.is_visible(timeout=7000):
                        await page.locator(selector.strip()).first.click()
                        await page.pause(); return True
                await page.pause(); return True # Manual fallback
            elif platform_lower == "fansale":
                if hasattr(fansale, 'click_specific_ticket_listing_and_proceed'):
                    return await fansale.click_specific_ticket_listing_and_proceed(page, browser_profile, hit.hit_data, target_cfg_for_hit)
                else: await page.pause(); return True # Manual fallback
            else: await page.pause(); return True # Manual fallback for unknown
        except Exception as e:
            action_logger.error(f"APA Platform action error for '{hit.event_name}': {e}", exc_info=True)
            if not page.is_closed() and self.app_settings.get("pause_on_purchase_error", True): await page.pause()
            return False

    def _check_circuit_breaker(self, platform: str) -> bool: # Your existing method
        breaker = self.circuit_breakers[platform]
        if breaker.state == "OPEN":
            if time.time() - breaker.last_failure_time > breaker.recovery_timeout:
                breaker.state = "HALF_OPEN"; breaker.failure_count = 0; return True
            return False
        return True

    def _record_circuit_breaker_success(self, platform: str): # Your existing method
        breaker = self.circuit_breakers[platform]
        if breaker.state == "HALF_OPEN": self.logger.info(f"CB '{platform}' to CLOSED.")
        breaker.failure_count = 0; breaker.state = "CLOSED"

    def _record_circuit_breaker_failure(self, platform: str, is_critical: bool = False): # Your existing method
        breaker = self.circuit_breakers[platform]
        breaker.failure_count += 1; breaker.last_failure_time = time.time()
        if breaker.state == "HALF_OPEN" or breaker.failure_count >= breaker.failure_threshold or is_critical:
            if breaker.state != "OPEN": self.logger.warning(f"CB '{platform}' OPENED.")
            breaker.state = "OPEN"

    async def add_ticket_hit(self, hit_data: Dict[str, Any], priority: PriorityLevel = PriorityLevel.HIGH): # Your existing method
        offer_url = hit_data.get("offer_url", hit_data.get("url"))
        if not offer_url: self.logger.error("APA Add Hit: Missing URL."); return
        max_retries = hit_data.get("max_retries", self.app_settings.get("purchase_max_retries_per_hit", 3))
        hit = TicketHit(platform=hit_data.get("platform", "unknown"),
                        event_name=hit_data.get("event_name", "Unknown"),
                        url=hit_data.get("url", offer_url), offer_url=offer_url,
                        priority=priority, timestamp=time.time(), hit_data=hit_data, max_retries=max_retries)
        try:
            await asyncio.wait_for(self.ticket_hit_queue.put(hit), timeout=2.0)
            self.logger.info(f"APA Added hit to queue: '{hit.event_name}'. Size: {self.ticket_hit_queue.qsize()}")
        except (asyncio.TimeoutError, asyncio.QueueFull):
            self.logger.error(f"APA HIT QUEUE ERROR for '{hit.event_name}'. DISCARDED.")

    async def shutdown(self): # Your existing method
        self.logger.info("APA Shutting down...")
        if not self._stop_event.is_set(): self._stop_event.set()
        if self._purchase_readiness_task and not self._purchase_readiness_task.done():
            self._purchase_readiness_task.cancel()
            try: await self._purchase_readiness_task
            except asyncio.CancelledError: pass
        if self.purchase_workers:
            for worker_task in self.purchase_workers:
                if not worker_task.done(): worker_task.cancel()
            await asyncio.gather(*self.purchase_workers, return_exceptions=True)
        if self.browser_manager: await self.browser_manager.stop_manager()
        self.logger.info("APA shutdown complete.")

# --- Monitoring Logic (monitor_target_enhanced, _apa_enhanced_block_detection - already present) ---
# These are used by your current "stealth mode". Beast Mode will have its own lightweight monitor.
async def monitor_target_enhanced( # Your existing stealth mode monitor
    name: str, checker: Callable, target_cfg: Dict[str, Any],
    bm: StealthBrowserManager, apa: AdvancedPurchaseArchitecture,
    cancel_evt: asyncio.Event, gui_q: Optional[asyncio.Queue] = None,
):
    log = logging.getLogger(f"StealthMonitor.{name.replace(' ', '_')[:20]}")
    page_url = target_cfg.get("url")
    if not page_url: log.error(f"URL missing for '{name}'."); return
    interval_s = float(target_cfg.get("interval_s", apa.app_settings.get("monitoring_interval_s", 60.0)))
    log.info(f"Stealth Monitoring '{name}', URL: {page_url[:60]}, Interval: ~{interval_s:.1f}s")
    await asyncio.sleep(random.uniform(1.0, 5.0)) # Stagger

    while not cancel_evt.is_set():
        try:
            async with bm.get_context() as (ctx, profile_used): # Uses the shared BM
                async with bm.get_page_from_context(ctx) as page: # Let checker handle goto
                    await _apa_enhanced_block_detection(page, name, target_cfg, apa.app_settings) # Your block detection
                    hits_data_list = await checker(page=page, profile=profile_used, target_cfg=target_cfg, bm=bm, gui_q=gui_q) # Call platform checker
                    if hits_data_list:
                        log.critical(f"[{name}] STEALTH HIT(S)! Profile: {profile_used.name}, Hits: {len(hits_data_list)}")
                        priority = PriorityLevel[target_cfg.get("hit_priority", "HIGH").upper()]
                        for hit_detail in hits_data_list:
                            full_hit_info = {"platform": target_cfg.get("platform"), "url": page_url, "event_name": name, "original_target_config": dict(target_cfg), **hit_detail}
                            await apa.add_ticket_hit(full_hit_info, priority=priority) # Add to APA's queue
            # ... (rest of your existing error handling and interval logic for stealth mode) ...
        except BlockedError as e_block: # Simplified for brevity
            log.warning(f"[{name}] Stealth Blocked: {e_block}. Cooldown.")
            await asyncio.sleep(random.uniform(60,120))
        except Exception as e:
            log.error(f"[{name}] Stealth Monitor Error: {e}", exc_info=True)
            await asyncio.sleep(random.uniform(30,60)) # Cooldown on general error

        try: await asyncio.wait_for(cancel_evt.wait(), timeout=interval_s * random.uniform(0.85, 1.15))
        except asyncio.TimeoutError: pass
    log.info(f"[{name}] Stealth Monitoring task stopped.")

async def _apa_enhanced_block_detection(page: PlaywrightPage, target_name: str, target_cfg: Dict[str, Any], app_settings: Dict[str, Any]): # Your existing method
    logger_bd = logging.getLogger(f"BlockDetect.{target_name.replace(' ','_')[:20]}")
    try:
        content_sample = await asyncio.wait_for(page.evaluate("() => document.body ? document.body.innerText.toLowerCase().substring(0,1500) : ''"), timeout=1.5)
        indicators = app_settings.get("global_block_page_indicators", []) + target_cfg.get("block_page_indicators", [])
        for ind in indicators:
            if ind.lower() in content_sample: raise BlockedError(f"Block: '{ind}' in content.")
        # CAPTCHA selectors (simplified)
        captcha_selectors = app_settings.get("global_captcha_selectors", []) + target_cfg.get("captcha_selectors", [])
        for sel in captcha_selectors:
            if await page.locator(sel).first.is_visible(timeout=1000): raise BlockedError(f"CAPTCHA: '{sel}' visible.")
    except BlockedError: raise
    except Exception as e: logger_bd.debug(f"Block detection minor error: {e}")


# --- Main Asynchronous Execution Logic (Refactored for Mode Switching) ---
async def _async_main_refactored(config_data: Dict[str, Any], gui_q: Optional[asyncio.Queue] = None,
                                 stop_event_from_caller: Optional[asyncio.Event] = None) -> None:
    global _apa_instance_for_signal, _stop_event_for_signal, _active_monitoring_tasks_for_signal
    main_logger = logging.getLogger("AsyncMainOrchestrator") # Renamed for clarity
    stop_event = stop_event_from_caller if stop_event_from_caller else asyncio.Event()
    _stop_event_for_signal = stop_event
    _active_monitoring_tasks_for_signal.clear()

    apa: Optional[AdvancedPurchaseArchitecture] = None # Will hold the APA instance

    try:
        main_logger.info("Orchestrator: Starting Playwright...")
        async with async_playwright() as p_instance:
            # TLS Fingerprint Patching (your existing logic)
            tls_profile_key = config_data.get("app_settings", {}).get("tls_fingerprint_profile")
            if tls_profile_key:
                if patch_ssl_for_fingerprint_evasion(browser_profile_ja3_key=tls_profile_key):
                    main_logger.info(f"TLS fingerprint patch enabled for: '{tls_profile_key}'.")
                else:
                    main_logger.warning(f"TLS fingerprint patch FAILED for: '{tls_profile_key}'.")

            # Load all browser profiles from YAML (used by APA to identify golden, and SBM loads them too)
            profiles_yaml_path_str = config_data.get('paths',{}).get('browser_profiles_yaml', str(CONFIG_FILE.parent / 'browser_profiles.yaml'))
            all_yaml_profiles = _load_browser_profiles_from_yaml(Path(profiles_yaml_path_str))
            if not all_yaml_profiles:
                main_logger.error(f"CRITICAL: No browser profiles loaded from '{profiles_yaml_path_str}'. Application might not function.")
                # Potentially exit or handle depending on how critical profiles are for all modes

            main_logger.info("Initializing AdvancedPurchaseArchitecture (APA)...")
            apa = AdvancedPurchaseArchitecture(
                main_config_data=config_data, # Pass the potentially merged config
                all_available_profiles_for_apa_logic=all_yaml_profiles,
                stop_event=stop_event,
                playwright_instance=p_instance
            )
            _apa_instance_for_signal = apa

            if not apa.browser_manager: # APA initializes its own browser_manager
                main_logger.critical("APA failed to initialize its BrowserManager. Cannot proceed.")
                return
            
            await apa.browser_manager.start_manager() # Start the SBM (pool, etc.)
            main_logger.info("APA's StealthBrowserManager started (used by both modes).")

            # --- MODE SWITCHING ---
            # 'mode' should ideally come from a beast_mode specific config section after merging
            # For example, if beast_mode_config.yaml has app_settings: { mode: "beast" }
            # and it's merged into config_data.
            # Default to 'stealth' if no mode is specified.
            operation_mode = config_data.get('app_settings', {}).get('mode', 'stealth').lower()

            if operation_mode == 'beast':
                main_logger.info("🔥 BEAST MODE ACTIVATED 🔥")
                main_logger.info("Beast Mode will use APA's StealthBrowserManager for browser operations.")

                # Pre-authenticate profiles if configured (uses APA's browser_manager)
                # Ensure 'pre_auth_all_profiles' and 'purchase_profiles' are in the merged config_data
                if config_data.get('app_settings', {}).get('pre_auth_all_profiles'):
                    main_logger.info("Beast Mode: Attempting pre-authentication...")
                    await _pre_authenticate_profiles(apa, config_data) # Pass APA and merged config
                else:
                    main_logger.info("Beast Mode: Pre-authentication not configured.")
                
                # Run beast mode
                # Beast mode needs its own config section. If `beast_mode_config.yaml` was merged
                # into `config_data` under a key like `beast_config_params`, pass that.
                # Otherwise, pass the relevant parts of `config_data`.
                # For simplicity now, pass the whole merged config; BeastModeOrchestrator will pick what it needs.
                await run_beast_mode(config_data, apa.browser_manager, stop_event)

            else: # Default to "stealth" mode (your existing APA-driven monitoring)
                main_logger.info("Running in STEALTH mode (APA-driven monitoring and purchase)...")
                # Initialize APA's purchase-side systems (workers, readiness loop)
                # This is part of your existing stealth mode flow.
                await apa.initialize_purchase_side_systems(gui_q=gui_q)

                # Start APA's monitoring tasks (your existing `monitor_target_enhanced`)
                monitoring_tasks_local: List[asyncio.Task] = []
                if apa.browser_manager: # Should always be true if APA init succeeded
                    targets_to_monitor = config_data.get("targets", [])
                    platform_dispatch_checkers: Dict[str, Callable] = {
                        "Ticketmaster": ticketmaster.check_ticketmaster_event,
                        "FanSale": fansale.check_fansale_event,
                        "Vivaticket": vivaticket.check_vivaticket_event,
                    }
                    for idx, target_config_entry in enumerate(targets_to_monitor):
                        if not target_config_entry.get("enabled", False): continue
                        platform_name = target_config_entry.get("platform")
                        checker_fn = platform_dispatch_checkers.get(platform_name)
                        if not checker_fn: continue
                        event_name = target_config_entry.get("event_name", f"Target_{idx+1}")
                        task = asyncio.create_task(monitor_target_enhanced(
                            name=event_name, checker=checker_fn, target_cfg=target_config_entry,
                            bm=apa.browser_manager, apa=apa, cancel_evt=stop_event, gui_q=gui_q
                        ), name=f"StealthMonitor_{event_name.replace(' ','_')}")
                        monitoring_tasks_local.append(task)
                    _active_monitoring_tasks_for_signal[:] = monitoring_tasks_local
                    if monitoring_tasks_local:
                         main_logger.info(f"Stealth Mode: {len(monitoring_tasks_local)} monitoring task(s) started.")
                    else:
                        main_logger.warning("Stealth Mode: No enabled monitoring targets found.")
                else:
                    main_logger.error("Stealth Mode: BrowserManager not available, cannot start monitoring.")
            
            # Common wait for stop event, regardless of mode
            if not (_active_monitoring_tasks_for_signal or operation_mode == 'beast'): # If no stealth tasks and not beast (e.g. only GUI)
                 main_logger.info("No active operational tasks (stealth or beast). Idling until stop signal.")
            await stop_event.wait()
            main_logger.info("Orchestrator: Stop event received. Initiating shutdown sequence...")

    except RuntimeError as e_rt_main:
        main_logger.critical(f"FATAL RUNTIME ERROR in Orchestrator: {e_rt_main}", exc_info=True)
    except Exception as e_unhandled_main:
        main_logger.critical(f"Unhandled CRITICAL error in Orchestrator: {e_unhandled_main}", exc_info=True)
    finally:
        main_logger.info("Orchestrator 'finally' block: Cleaning up resources...")
        if not stop_event.is_set(): stop_event.set()

        if operation_mode == 'stealth' and _active_monitoring_tasks_for_signal: # Only cancel stealth tasks if they were run
            main_logger.info(f"Cancelling {len(_active_monitoring_tasks_for_signal)} stealth monitoring task(s)...")
            for task_to_cancel in _active_monitoring_tasks_for_signal:
                if not task_to_cancel.done(): task_to_cancel.cancel()
            await asyncio.gather(*_active_monitoring_tasks_for_signal, return_exceptions=True)
            _active_monitoring_tasks_for_signal.clear()
        
        # APA shutdown handles its browser_manager and workers, which are used by both modes.
        # BeastMode's run_beast_mode should handle its own internal task cancellations when stop_event is set.
        if apa:
            await apa.shutdown()
        if _apa_instance_for_signal is apa: _apa_instance_for_signal = None
        main_logger.info("Orchestrator cleanup finished.")

# --- Pre-authentication function (as per your snippet, slightly adapted) ---
async def _pre_authenticate_profiles(apa: AdvancedPurchaseArchitecture, config: Dict[str, Any]) -> None:
    """Pre-authenticate profiles specified in config for Beast Mode."""
    logger_pre_auth = logging.getLogger("PreAuth")
    # 'purchase_profiles' should come from the merged beast_mode config section
    # e.g., config.get('beast_settings', {}).get('app_settings', {}).get('purchase_profiles', {})
    # For now, assume it's directly under 'app_settings' after merge
    purchase_profiles_config = config.get('app_settings', {}).get('purchase_profiles', {})

    if not purchase_profiles_config:
        logger_pre_auth.info("No 'purchase_profiles' configured for pre-authentication.")
        return
    if not apa.browser_manager:
        logger_pre_auth.error("BrowserManager not available in APA for pre-authentication.")
        return

    logger_pre_auth.info(f"Starting pre-authentication for {sum(len(names) for names in purchase_profiles_config.values())} profile-platform pairs...")

    for platform, profile_names in purchase_profiles_config.items():
        for profile_name in profile_names:
            profile_to_auth = next((p for p in apa.browser_manager.profiles if p.name == profile_name), None)
            if not profile_to_auth:
                logger_pre_auth.warning(f"Profile '{profile_name}' not found in BrowserManager. Skipping pre-auth for {platform}.")
                continue

            logger_pre_auth.info(f"Attempting pre-authentication for '{profile_name}' on platform '{platform}'.")
            context_for_auth: Optional[PlaywrightContext] = None
            page_for_auth: Optional[PlaywrightPage] = None
            try:
                context_for_auth = await apa.browser_manager.get_persistent_context_for_profile(profile_to_auth)
                if not context_for_auth:
                    logger_pre_auth.error(f"Failed to get persistent context for '{profile_name}'.")
                    continue
                
                page_for_auth = await context_for_auth.new_page()
                login_urls = { # Consider moving to config
                    'fansale': 'https://www.fansale.it/fansale/login.htm', # Adjusted
                    'ticketmaster': 'https://auth.ticketmaster.it/login', # Or country specific
                    'vivaticket': 'https://shop.vivaticket.com/it/registrazione' # Adjusted
                }
                login_url = login_urls.get(platform.lower())
                if not login_url:
                    logger_pre_auth.warning(f"No login URL defined for platform '{platform}'. Skipping pre-auth for {profile_name}.")
                    if page_for_auth and not page_for_auth.is_closed(): await page_for_auth.close()
                    continue

                await page_for_auth.goto(login_url, wait_until="domcontentloaded", timeout=30000)
                
                if await apa._verify_authentication_on_page(page_for_auth, platform):
                    logger_pre_auth.info(f"✓ Profile '{profile_name}' already authenticated on '{platform}'.")
                else:
                    logger_pre_auth.warning(f"✗ Profile '{profile_name}' needs login on '{platform}'. Pausing for manual login.")
                    if not page_for_auth.is_closed(): await page_for_auth.pause() # User manually logs in and resumes
                    # Optionally, re-verify auth after pause
                    if not page_for_auth.is_closed() and await apa._verify_authentication_on_page(page_for_auth, platform):
                         logger_pre_auth.info(f"✓ Profile '{profile_name}' now authenticated on '{platform}' after manual login.")
                    elif not page_for_auth.is_closed():
                         logger_pre_auth.warning(f"✗ Profile '{profile_name}' still not authenticated on '{platform}' after pause.")

            except PlaywrightError as e_pw:
                logger_pre_auth.error(f"Playwright error during pre-auth for '{profile_name}' on '{platform}': {e_pw}")
            except Exception as e:
                logger_pre_auth.error(f"Unexpected error during pre-auth for '{profile_name}' on '{platform}': {e}", exc_info=True)
            finally:
                if page_for_auth and not page_for_auth.is_closed():
                    await page_for_auth.close()
                # Persistent context itself is kept open by BrowserManager

    logger_pre_auth.info("Pre-authentication attempts finished.")


# --- Configuration and Logging Setup (Your existing _load_yaml_config, _init_logging, _load_browser_profiles_from_yaml) ---
# These functions are well-defined in your provided src/main.py and can be kept as is.
# Make sure BrowserProfile used in _load_browser_profiles_from_yaml matches the one from core.browser_manager
def _load_yaml_config(file_path: Path) -> Dict[str, Any]: # Your existing function
    if not file_path.is_file():
        logging.error(f"Config file {file_path} not found.")
        return {}
    try:
        with file_path.open("r", encoding="utf-8") as fh: data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logging.error(f"Error loading YAML {file_path}: {e}", exc_info=True)
        return {}

def _init_logging(level_str: str = "INFO", log_file_path_str: Optional[str] = None) -> None: # Your existing function (seems fine)
    log_level = getattr(logging, level_str.upper(), logging.INFO)
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers): root_logger.removeHandler(handler); handler.close()
    log_formatter = logging.Formatter("%(asctime)s [%(levelname)-7s] %(name)-30s :: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handlers: List[logging.Handler] = []
    console_handler = logging.StreamHandler(sys.stdout); console_handler.setFormatter(log_formatter); handlers.append(console_handler)
    if log_file_path_str:
        try:
            log_file_p = Path(log_file_path_str).resolve(); log_file_p.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(log_file_p, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
            file_handler.setFormatter(log_formatter); handlers.append(file_handler)
        except Exception as e: print(f"ERROR creating log file '{log_file_path_str}': {e}", file=sys.stderr)
    root_logger.setLevel(log_level)
    for handler in handlers: root_logger.addHandler(handler)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    # ... other library log level settings ...
    logging.info(f"Logging initialized. Level: {logging.getLevelName(log_level)}. File: {log_file_path_str or 'Console only'}")


def _load_browser_profiles_from_yaml(file_path: Path) -> List[BrowserProfile]: # Your existing function
    # Ensure this uses the BrowserProfile from core.browser_manager
    logger_profile_load = logging.getLogger("MainProfileLoader")
    profiles_data = _load_yaml_config(file_path)
    loaded_profiles: List[BrowserProfile] = []
    if not profiles_data or not isinstance(profiles_data.get("browser_profiles"), list):
        logger_profile_load.warning(f"No 'browser_profiles' list in '{file_path}'.")
        return []
    for idx, p_def in enumerate(profiles_data["browser_profiles"]):
        if not isinstance(p_def, dict): continue
        try:
            # Add defaults for new fields if not in YAML, or rely on dataclass defaults
            p_def.setdefault('success_count', 0)
            p_def.setdefault('failure_count', 0)
            p_def.setdefault('last_used', None) # Will be datetime or None
            # platform_success_rates might be initialized as empty dict if you add it
            loaded_profiles.append(BrowserProfile(**p_def))
        except Exception as e:
            logger_profile_load.error(f"Error creating BrowserProfile '{p_def.get('name', idx)}': {e}", exc_info=True)
    logger_profile_load.info(f"Loaded {len(loaded_profiles)} profiles from '{file_path}' for main app.")
    return loaded_profiles

# --- GUI Integration Functions (load_app_config_for_gui, main_loop_for_gui - already present) ---
# These can remain as is, they call _async_main_refactored.
def load_app_config_for_gui(config_path: Path = CONFIG_FILE) -> Dict[str, Any]: # Your existing function
    return _load_yaml_config(config_path)

async def main_loop_for_gui(config_data: Dict[str, Any], stop_event: asyncio.Event, gui_threading_q: "threading_queue.Queue"): # Your existing function
    async_gui_q: asyncio.Queue[Tuple[str, Any]] = asyncio.Queue()
    # ... (rest of your GUI message bridge logic, which calls _async_main_refactored) ...
    # Ensure it passes the merged config_data if GUI can also trigger Beast Mode
    await _async_main_refactored(config_data, gui_q=async_gui_q, stop_event_from_caller=stop_event)


# --- CLI Signal Handling and Main Execution (cli_signal_handler, async_cli_mode_operations, etc. - already present) ---
# Your existing CLI handling for warm-up, stealth-test, and main monitoring can be adapted.
# The key is how `config` is prepared if `--beast` is passed.
def cli_signal_handler(sig, frame): # Your existing function
    global _stop_event_for_signal
    signal_name = getattr(signal.Signals, sig.name, f"Signal {sig}")
    logging.getLogger("SignalHandler").warning(f"{signal_name} received. Shutdown...")
    if _stop_event_for_signal:
        if not _stop_event_for_signal.is_set(): _stop_event_for_signal.set()
        else: os._exit(1) # Force exit on second interrupt
    else: os._exit(1)

async def async_cli_mode_operations(args: argparse.Namespace, config_data: Dict[str, Any], p_instance: Playwright): # Your existing function
    # This is for --warm-profile, --test-stealth, not the main beast/stealth mode run
    cli_mode_logger = logging.getLogger("CLIModeOps")
    if args.warm_profile:
        start_url = args.start_url or config_data.get('app_settings', {}).get('warmup_default_start_url', 'https://www.google.com')
        cli_mode_logger.info(f"WARM-UP: '{args.warm_profile}' URL: '{start_url}'")
        await async_warm_profile_session(args.warm_profile, start_url, config_data, p_instance)
    # ... (rest of your test_stealth logic) ...

async def async_warm_profile_session(profile_name: str, url: str, config: Dict[str, Any], p: Playwright): # Your existing function, looks good
    # ... uses its own StealthBrowserManager instance ...
    pass
async def async_test_stealth_session(profile_name: str, url: str, config: Dict[str, Any], p: Playwright): # Your existing function, looks good
    # ... uses its own StealthBrowserManager instance ...
    pass


def deep_merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Deeply merges override_config into base_config."""
    merged = copy.deepcopy(base_config)
    for key, value in override_config.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = deep_merge_configs(merged[key], value)
        else:
            merged[key] = value
    return merged

def cli_main() -> None: # Adapted for Beast Mode
    parser = argparse.ArgumentParser(description="Advanced Ticket Monitor Bot (CLI Mode)")
    parser.add_argument("--warm-profile", type=str, help="Profile name to warm-up.")
    parser.add_argument("--start-url", type=str, help="Start URL for warm-up.")
    parser.add_argument("--test-stealth", type=str, help="Profile name for stealth testing.")
    parser.add_argument("--test-url", type=str, default="https://infoscan.io/", help="URL for stealth test.")
    # --- Beast Mode Argument ---
    parser.add_argument("--beast", action="store_true", help="Run in BEAST MODE with beast_mode_config.yaml overrides.")
    parser.add_argument("--config", type=str, default=str(CONFIG_FILE), help="Path to main config.yaml file.")
    parser.add_argument("--beast-config", type=str, default=str(BEAST_MODE_CONFIG_FILE), help="Path to beast_mode_config.yaml file.")


    cli_args_list = [arg for arg in sys.argv[1:] if arg != '--gui']
    args = parser.parse_args(cli_args_list)

    # Load main configuration
    main_config = _load_yaml_config(Path(args.config))
    if not main_config:
        print(f"CRITICAL: Main config '{args.config}' failed to load. Exiting.", file=sys.stderr)
        sys.exit(1)
    
    final_config = main_config

    # If Beast Mode is activated, load and merge its specific config
    if args.beast:
        print("INFO: --beast flag detected. Attempting to load and merge Beast Mode configuration.")
        beast_specific_config = _load_yaml_config(Path(args.beast_config))
        if beast_specific_config:
            final_config = deep_merge_configs(main_config, beast_specific_config)
            # Ensure the mode is explicitly set to "beast" in app_settings after merge
            final_config.setdefault('app_settings', {})['mode'] = 'beast'
            print(f"INFO: Beast Mode configuration '{args.beast_config}' merged successfully.")
        else:
            print(f"WARNING: Beast Mode config '{args.beast_config}' not found or empty. Running with main config (potentially still in beast mode if 'mode: beast' is set there).")
            # Still set mode to beast if flag is present, relying on main_config to have beast settings
            final_config.setdefault('app_settings', {})['mode'] = 'beast'


    # Initialize logging based on the final (potentially merged) configuration
    log_settings = final_config.get('logging', {}) # Use merged config for logging settings
    _init_logging(
        level_str=log_settings.get("level", "INFO"),
        log_file_path_str=log_settings.get("log_file_path", "logs/ticket_bot_main.log")
    )
    logging.info(f"Final configuration prepared. Operation mode: {final_config.get('app_settings', {}).get('mode', 'stealth')}")


    if args.warm_profile or args.test_stealth:
        # ... (your existing logic for these CLI ops using final_config) ...
        async def run_selected_cli_mode():
            async with async_playwright() as playwright_instance:
                await async_cli_mode_operations(args, final_config, playwright_instance)
        try:
            asyncio.run(run_selected_cli_mode())
        except Exception as e_cli_op_error:
            logging.critical(f"Error during CLI mode operation: {e_cli_op_error}", exc_info=True)
            sys.exit(1)
        return # Exit after these specific CLI modes

    logging.info("Starting Ticket Monitor Bot in main operational mode (CLI)...")
    global _stop_event_for_signal
    cli_stop_event = asyncio.Event()
    _stop_event_for_signal = cli_stop_event

    original_sigint = signal.signal(signal.SIGINT, cli_signal_handler)
    original_sigterm = signal.signal(signal.SIGTERM, cli_signal_handler)

    try:
        asyncio.run(_async_main_refactored(config_data=final_config, stop_event_from_caller=cli_stop_event))
    except KeyboardInterrupt:
        logging.info("CLI Main: KeyboardInterrupt.")
    # ... (rest of your existing cli_main finally block) ...
    finally:
        logging.info("CLI Main 'finally': Restoring signals and ensuring shutdown.")
        signal.signal(signal.SIGINT, original_sigint)
        signal.signal(signal.SIGTERM, original_sigterm)
        if not cli_stop_event.is_set(): cli_stop_event.set()
        logging.info("CLI application shutdown process finished.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)-7s] %(name)-20s :: %(message)s (PRE-CONFIG)", datefmt="%Y-%m-%d %H:%M:%S", force=True)
    if "--gui" in sys.argv:
        logging.info("GUI mode detected. Starting GUI...")
        try:
            from gui import start_gui # Assuming gui.py handles its own config for now
            start_gui()
        except Exception as e_gui:
            logging.critical(f"Failed to start GUI: {e_gui}", exc_info=True); sys.exit(1)
    else:
        cli_main()