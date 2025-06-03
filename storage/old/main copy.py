# src/main.py - v0.9
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

from dotenv import load_dotenv
load_dotenv()

import yaml

from core.browser_manager import StealthBrowserManager, BrowserProfile
from playwright.async_api import (
    Error as PlaywrightError,
    Page as PlaywrightPage,
    BrowserContext as PlaywrightContext,
    async_playwright, # For managing Playwright lifecycle
    Playwright # For type hinting
)
from core.errors import BlockedError

# Platform checkers
from platforms import ticketmaster
from platforms import vivaticket
from platforms import fansale

# Utility imports
from utils.tls_fingerprint import patch_ssl_for_fingerprint_evasion
# NEW: Import for advanced human behavior simulation
from utils.advanced_behavioral_simulation import simulate_advanced_human_behavior, BiometricProfile


if TYPE_CHECKING:
    import queue as threading_queue # For GUI bridge

CONFIG_FILE = Path("config/config.yaml")

# Global state for signal handling
_apa_instance_for_signal: Optional[AdvancedPurchaseArchitecture] = None
_stop_event_for_signal: Optional[asyncio.Event] = None
_active_monitoring_tasks_for_signal: List[asyncio.Task] = []

# --- Enums and Dataclasses ---
class PriorityLevel(Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

@dataclass
class TicketHit:
    platform: str
    event_name: str
    url: str # Monitoring URL
    offer_url: str # Specific URL for purchase action
    priority: PriorityLevel
    timestamp: float
    hit_data: Dict[str, Any] # Platform-specific details from checker
    retry_count: int = 0
    max_retries: int = 3 # Default, can be overridden by app_settings

    def __lt__(self, other: TicketHit) -> bool:
        if not isinstance(other, TicketHit):
            return NotImplemented
        # Higher priority (lower enum value) comes first, then earlier timestamp
        return (self.priority.value, self.timestamp) < (other.priority.value, other.timestamp)

@dataclass
class CircuitBreakerState:
    failure_count: int = 0
    last_failure_time: float = 0.0
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    failure_threshold: int = 5
    recovery_timeout: float = 300.0

# --- Helper Classes ---
class AdvancedNotifier:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg_notifications = cfg.get("notifications", {})
        self.console_alerts: bool = bool(self.cfg_notifications.get("console_alerts", True))
        self.logger = logging.getLogger("AdvancedNotifier")
        self.alert_history: deque = deque(maxlen=self.cfg_notifications.get("alert_history_size", 100))
        self.rate_limiter: Dict[str, float] = {} # key: category_level, value: last_alert_time
        self.alert_rate_limit_s = self.cfg_notifications.get("alert_rate_limit_s", 10.0) # Default 10s

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
            # Enhanced console alert formatting
            icon = "🚨" if level in ["CRITICAL", "ERROR"] else "⚠️" if level == "WARNING" else "ℹ️"
            log_method(f"{icon} [{category.upper()}] {message}")
        # TODO: Implement other notification channels (email, Pushover) if configured

class FingerprintRandomizer: # Kept for potential future use or more granular control
    @staticmethod
    async def randomize_page_fingerprint(page: PlaywrightPage) -> None:
        # This is a placeholder. True dynamic randomization is complex.
        # The primary fingerprint is set by the BrowserProfile and stealth_init.js.
        # This could add minor, page-specific variations if desired.
        logger = logging.getLogger("FingerprintRandomizer")
        try:
            await page.add_init_script(f"Math.random = () => {random.random()};") # Example: slightly alter Math.random behavior per page
            logger.debug("Applied minor dynamic fingerprint randomization to page.")
        except Exception as e:
            logger.error(f"Error applying dynamic fingerprint randomization: {e}")

class PlatformStealthManager: # Kept for potential future use
    @staticmethod
    async def apply_platform_specific_stealth(page: PlaywrightPage, platform: str):
        # This is a placeholder. Platform-specific JS tweaks can be added here.
        # Most heavy lifting is done by stealth_init.js based on the BrowserProfile.
        logger = logging.getLogger(f"PlatformStealth.{platform.lower()}")
        logger.debug(f"Applying platform-specific JS stealth (placeholder) for {platform} on page: {page.url[:80]}")
        # Example: if platform.lower() == "someplatform": await page.add_init_script("...")

# --- Main Application Architecture ---
class AdvancedPurchaseArchitecture:
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

        # Simplified: Only one primary StealthBrowserManager
        self.browser_manager: Optional[StealthBrowserManager] = None

        self.ticket_hit_queue: asyncio.PriorityQueue[TicketHit] = asyncio.PriorityQueue(
            maxsize=self.app_settings.get("ticket_hit_queue_size", 50)
        )
        self.purchase_workers: List[asyncio.Task] = []
        self.num_purchase_workers = self.app_settings.get("purchase_worker_count",
            self.app_settings.get("browser_pool",{}).get("target_size",1) # Default to 1 if pool not specified
        )
        if self.num_purchase_workers <= 0: self.num_purchase_workers = 1 # Ensure at least one worker

        self.circuit_breakers: Dict[str, CircuitBreakerState] = defaultdict(lambda: CircuitBreakerState(
            failure_threshold=self.app_settings.get("circuit_breaker_failure_threshold", 3), # Reduced default
            recovery_timeout=self.app_settings.get("circuit_breaker_recovery_timeout_s", 180.0) # Reduced default
        ))

        self.performance_metrics: Dict[str, Any] = defaultdict(float)
        self.performance_metrics.update({
            "hits_processed": 0, "successful_purchases": 0, "failed_purchases": 0, "blocks_detected":0,
            "api_calls": 0, "ui_interactions": 0
        })

        self.golden_profile_object: Optional[BrowserProfile] = None
        self.is_purchase_system_ready: bool = False # Tracks if golden profile is authenticated
        self._purchase_readiness_task: Optional[asyncio.Task] = None

        # Identify Golden Profile
        golden_profile_name: Optional[str] = self.app_settings.get("golden_profile_name_1")
        if golden_profile_name and all_available_profiles_for_apa_logic:
            self.golden_profile_object = next((p for p in all_available_profiles_for_apa_logic if p.name == golden_profile_name), None)
            if self.golden_profile_object:
                self.logger.info(f"Golden profile '{self.golden_profile_object.name}' identified for purchase system.")
            else:
                self.logger.error(f"Specified golden profile '{golden_profile_name}' not found in loaded profiles. Purchase system will be impaired.")
        elif not golden_profile_name:
            self.logger.warning("No 'golden_profile_name_1' configured in app_settings. Automated purchases and readiness checks using a golden profile will be disabled.")

        self.target_platform_for_purchase_system = self._detect_target_platform() # Based on main_purchase_url
        self._initialize_browser_manager(main_config_data) # Initialize the single browser manager

    def _detect_target_platform(self) -> str:
        main_purchase_url = self.app_settings.get("main_purchase_url", "").lower()
        if not main_purchase_url:
            self.logger.warning("Could not determine target platform: 'main_purchase_url' is not set in app_settings.")
            return "unknown"
        if "fansale" in main_purchase_url: return "FanSale"
        if "ticketmaster" in main_purchase_url: return "Ticketmaster"
        if "vivaticket" in main_purchase_url: return "Vivaticket"
        self.logger.warning(f"Could not determine target platform from main_purchase_url: '{main_purchase_url}'. Defaulting to 'unknown'.")
        return "unknown"

    def _prepare_config_for_browser_manager(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepares a configuration dictionary specifically for the StealthBrowserManager."""
        manager_cfg = json.loads(json.dumps(base_config)) # Deep copy
        self.logger.debug(f"Preparing BM Config for APA. Original base_config browser_launch_options: {base_config.get('browser_launch_options')}")

        manager_cfg.setdefault('browser_launch_options', {})
        manager_cfg['browser_launch_options']['use_persistent_user_data_dir_if_available'] = True
        # --------------------------------------------------------------------
        proxy_enabled = manager_cfg.get('proxy', {}).get('enabled', False)
        # Proxy settings for APA's manager instance should also be considered:
        # Does the golden profile need a specific proxy or no proxy for login/purchase?
        # This might require a separate proxy configuration block for the APA manager.
        self.logger.info(f"APA's BrowserManager proxy configured: {'ENABLED' if proxy_enabled else 'DISABLED'}")
        return manager_cfg

    def _initialize_browser_manager(self, main_config_data: Dict[str, Any]):
        """Initializes the single primary StealthBrowserManager."""
        try:
            manager_config = self._prepare_config_for_browser_manager(main_config_data)
            self.browser_manager = StealthBrowserManager(
                config=manager_config,
                playwright_instance=self.playwright
            )
            self.logger.info("Primary StealthBrowserManager (V2) instance created.")
        except Exception as e:
            self.logger.critical(f"FATAL ERROR initializing primary StealthBrowserManager: {e}", exc_info=True)
            self.browser_manager = None

    async def initialize_purchase_side_systems(self, gui_q: Optional[asyncio.Queue] = None) -> bool:
        """Initializes systems needed for purchasing, including readiness loop and workers."""
        if not self.browser_manager: # Check if the primary BM is available
            self.logger.error("Primary BrowserManager not available. Cannot initialize purchase systems.")
            self.is_purchase_system_ready = False
            return False

        if not self.golden_profile_object:
            self.logger.warning("Golden Profile not configured. Purchase readiness checks and automated purchases will be skipped.")
            self.is_purchase_system_ready = False
            # Still start workers, they just won't do anything if no golden profile
            await self._start_purchase_workers(gui_q)
            return True # System "initialized" but not ready for golden actions

        self.logger.info("Initializing APA purchase side systems...")
        try:
            await self._start_purchase_workers(gui_q)
            self._purchase_readiness_task = asyncio.create_task(
                self._maintain_purchase_readiness_loop(gui_q=gui_q),
                name="PurchaseReadinessCheckLoop"
            )
            self.logger.info("Purchase readiness check loop started (will use golden profile).")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing APA purchase side systems: {e}", exc_info=True)
            self.is_purchase_system_ready = False
            return False

    async def _start_purchase_workers(self, gui_q: Optional[asyncio.Queue] = None):
        self.purchase_workers.clear()
        for i in range(self.num_purchase_workers):
            worker_task_name = f"PurchaseWorker-{i}"
            worker = asyncio.create_task(
                self._purchase_worker(worker_id=i, gui_q=gui_q), name=worker_task_name
            )
            self.purchase_workers.append(worker)
        self.logger.info(f"Started {len(self.purchase_workers)} purchase worker(s).")

    async def _verify_authentication_on_page(self, page: PlaywrightPage, platform_to_check: str) -> bool:
        """Verifies if the user appears logged in on the given page for the platform."""
        effective_platform = platform_to_check.lower()
        # If platform_to_check is generic, use the one detected from main_purchase_url
        if effective_platform == "unknown" and self.target_platform_for_purchase_system != "unknown":
            effective_platform = self.target_platform_for_purchase_system.lower()

        self.logger.debug(f"Auth check for platform '{effective_platform}' on page {page.url[:80]}")
        if page.is_closed():
            self.logger.warning(f"Auth check: Page was closed. Assuming not authenticated.")
            return False

        # Selectors to indicate a logged-in state (these need to be robust)
        auth_selectors = {
            "fansale": "a[href*='myfansale'], a:has-text('Mio account'), a[data-qa='UserManuMyFanSALE'], div.is-logged-in, span.user-display-name",
            "ticketmaster": "button[data-testid='user-menu-button'], a[href*='account/overview'], button[aria-label*='Account'], div[data-testid='desktop-user-button'], button#profile-menu-trigger-button, a[href*='member'], [data-tm-icon='person'], span[data-automation='user-display-name']",
            "vivaticket": "a[href*='logout'], .user-name-display, div.userBoxLogged, a[href*='myvivaticket'], .is-logged-in, span.logged-user-name"
        }
        check_timeout = self.app_settings.get("auth_check_selector_timeout_ms", 7000) # ms

        if effective_platform in auth_selectors:
            try:
                for selector in auth_selectors[effective_platform].split(','):
                    trimmed_selector = selector.strip()
                    if not trimmed_selector: continue
                    # Use a short timeout for each selector check
                    if await page.locator(trimmed_selector).first.is_visible(timeout=check_timeout / len(auth_selectors[effective_platform].split(','))): # Distribute timeout
                        self.logger.info(f"Auth check PASSED for '{effective_platform}' (selector: '{trimmed_selector}' visible).")
                        return True
                self.logger.warning(f"Auth check FAILED for '{effective_platform}' (no configured login selectors were visible within timeout).")
                return False
            except PlaywrightError as e_auth_check: # Catches TimeoutError from is_visible
                self.logger.info(f"Auth check for '{effective_platform}' likely FAILED (selector not found or timed out): {str(e_auth_check)[:100]}")
                return False
            except Exception as e: # Catch any other unexpected errors
                self.logger.error(f"Unexpected error during auth check for '{effective_platform}': {e}", exc_info=True)
                return False
        else:
            self.logger.warning(f"No specific auth check selectors configured for platform '{effective_platform}'. Cannot verify authentication status.")
            return False # Assume not authenticated if no way to check

    async def _maintain_purchase_readiness_loop(self, gui_q: Optional[asyncio.Queue] = None):
        """Periodically checks if the golden profile is authenticated on the main purchase site."""
        if not self.browser_manager or not self.golden_profile_object:
            self.logger.error("ReadinessLoop: Primary BrowserManager or Golden Profile not available. Loop cannot run.")
            self.is_purchase_system_ready = False
            return

        await asyncio.sleep(random.uniform(3, 10)) # Initial random delay
        readiness_check_interval_s = self.app_settings.get("purchase_readiness_interval_s", 60.0)
        main_purchase_url = self.app_settings.get("main_purchase_url")

        if not main_purchase_url:
            self.logger.error("ReadinessLoop: 'main_purchase_url' not set in app_settings. Loop cannot run effectively.")
            self.is_purchase_system_ready = False
            return

        self.logger.info(f"Purchase Readiness Loop started for Golden Profile '{self.golden_profile_object.name}'. Interval: {readiness_check_interval_s}s. Target URL: {main_purchase_url}")

        persistent_context_for_golden: Optional[PlaywrightContext] = None
        page_for_check: Optional[PlaywrightPage] = None

        while not self._stop_event.is_set():
            current_auth_status = False
            try:
                self.logger.debug(f"ReadinessLoop: Getting PERSISTENT context for golden profile '{self.golden_profile_object.name}'.")
                # Get a persistent context for the golden profile
                persistent_context_for_golden = await self.browser_manager.get_persistent_context_for_profile(self.golden_profile_object)

                if not persistent_context_for_golden: # Should not happen if get_persistent_context_for_profile is robust
                    self.logger.error(f"ReadinessLoop: Failed to get persistent context for golden profile. Retrying later.")
                    self.is_purchase_system_ready = False
                    await asyncio.sleep(readiness_check_interval_s / 2) # Shorter retry if context fails
                    continue

                page_for_check = await persistent_context_for_golden.new_page()
                nav_timeout = self.app_settings.get("purchase_navigation_timeout_ms", 30000)
                await page_for_check.goto(main_purchase_url, wait_until="domcontentloaded", timeout=nav_timeout)

                # Apply advanced human behavior before auth check to mimic real user landing
                human_intensity = self.app_settings.get("readiness_check_human_intensity", "low")
                if human_intensity != "none":
                    biometric_cfg = self.golden_profile_object.extra_js_props.get("biometric_profile_config", {})
                    bio_profile = BiometricProfile(**biometric_cfg)
                    await simulate_advanced_human_behavior(page_for_check, intensity=human_intensity, profile=bio_profile)

                current_auth_status = await self._verify_authentication_on_page(page_for_check, self.target_platform_for_purchase_system)

                if current_auth_status:
                    if not self.is_purchase_system_ready: # Log only on change to ready
                        self.logger.info(f"ReadinessLoop: Golden profile '{self.golden_profile_object.name}' NOW AUTHENTICATED on {self.target_platform_for_purchase_system}.")
                        if gui_q: await gui_q.put(("log", (f"PURCHASE SYSTEM READY ({self.golden_profile_object.name} @ {self.target_platform_for_purchase_system})", "INFO")))
                    self.is_purchase_system_ready = True
                else:
                    if self.is_purchase_system_ready: # Log only on change to not ready
                        self.logger.warning(f"ReadinessLoop: Golden profile '{self.golden_profile_object.name}' NO LONGER AUTHENTICATED on {self.target_platform_for_purchase_system}.")
                        await self.notifier.alert(f"GOLDEN PROFILE '{self.golden_profile_object.name}' SESSION EXPIRED on {self.target_platform_for_purchase_system}!", level="ERROR", category="purchase_auth")
                        if gui_q: await gui_q.put(("log", (f"PURCHASE SYSTEM NOT READY - {self.golden_profile_object.name} LOGGED OUT!", "ERROR")))
                    else: # Still not ready
                        self.logger.warning(f"ReadinessLoop: Golden profile '{self.golden_profile_object.name}' REMAINS UNAUTHENTICATED on {self.target_platform_for_purchase_system}.")
                    self.is_purchase_system_ready = False

            except PlaywrightError as e_pw:
                self.logger.error(f"ReadinessLoop: Playwright error (Golden Profile: {self.golden_profile_object.name}): {e_pw}")
                self.is_purchase_system_ready = False # Assume not ready on error
            except Exception as e_gen:
                self.logger.error(f"ReadinessLoop: Unexpected error (Golden Profile: {self.golden_profile_object.name}): {e_gen}", exc_info=True)
                self.is_purchase_system_ready = False # Assume not ready on error
            finally:
                if page_for_check and not page_for_check.is_closed():
                    await page_for_check.close()
                # The persistent_context_for_golden itself is not closed here.
                # Its underlying browser is managed by self.browser_manager and closed on APA shutdown.

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=readiness_check_interval_s)
            except asyncio.TimeoutError: continue # Loop normally
            except asyncio.CancelledError: break # Exit loop if cancelled
        self.logger.info("Purchase Readiness Loop stopped.")
        self.is_purchase_system_ready = False # Ensure state is false on stop

    async def _purchase_worker(self, worker_id: int, gui_q: Optional[asyncio.Queue] = None):
        """Worker coroutine that processes ticket hits from the queue."""
        worker_logger = logging.getLogger(f"PurchaseWorker-{worker_id}")
        worker_logger.info(f"Worker {worker_id} started.")
        hit_being_processed: Optional[TicketHit] = None # To requeue on cancellation

        while not self._stop_event.is_set():
            hit_being_processed = None # Reset for each iteration
            try:
                # Wait for a short time to allow stop_event to be checked frequently
                hit_being_processed = await asyncio.wait_for(self.ticket_hit_queue.get(), timeout=1.0)
                worker_logger.info(f"Worker {worker_id}: Picked {hit_being_processed.priority.name} priority hit for '{hit_being_processed.event_name}'. Queue size now: {self.ticket_hit_queue.qsize()}")

                start_time = time.monotonic()
                # Pass the specific golden profile object to the purchase execution
                success = await self._execute_ultra_fast_purchase(hit_being_processed, worker_id, gui_q)
                processing_time_ms = (time.monotonic() - start_time) * 1000

                self.performance_metrics["hits_processed"] += 1
                if success:
                    self.performance_metrics["successful_purchases"] += 1
                    worker_logger.critical(f"W-{worker_id}: ✅ PURCHASE ACTION SUCCEEDED/HANDED OFF for '{hit_being_processed.event_name}' in {processing_time_ms:.0f}ms.")
                else:
                    self.performance_metrics["failed_purchases"] += 1
                    worker_logger.error(f"W-{worker_id}: ❌ PURCHASE ACTION FAILED for '{hit_being_processed.event_name}' in {processing_time_ms:.0f}ms.")

                self.ticket_hit_queue.task_done()
                hit_being_processed = None # Successfully processed or failed terminally

            except asyncio.TimeoutError:
                continue # No hit in queue, loop again
            except asyncio.CancelledError:
                worker_logger.info(f"Worker {worker_id} cancelled.")
                if hit_being_processed: # Requeue if cancelled mid-process
                    self.ticket_hit_queue.put_nowait(hit_being_processed)
                    worker_logger.info(f"Worker {worker_id}: Requeued '{hit_being_processed.event_name}' due to cancellation.")
                break # Exit worker loop
            except Exception as e:
                worker_logger.error(f"Worker {worker_id} encountered an unexpected error: {e}", exc_info=True)
                if hit_being_processed:
                    worker_logger.error(f"Error was during processing of: {hit_being_processed.event_name} ({hit_being_processed.offer_url})")
                    # Basic retry mechanism
                    if hit_being_processed.retry_count < hit_being_processed.max_retries:
                        hit_being_processed.retry_count += 1
                        worker_logger.info(f"Requeuing '{hit_being_processed.event_name}' (retry {hit_being_processed.retry_count}/{hit_being_processed.max_retries}).")
                        await self.ticket_hit_queue.put(hit_being_processed) # Use await for async queue
                    else:
                        worker_logger.error(f"Max retries reached for '{hit_being_processed.event_name}'. Discarding.")
                        self.performance_metrics["failed_purchases"] += 1 # Count as failed after max retries
                await asyncio.sleep(random.uniform(1,3)) # Brief pause after error
        worker_logger.info(f"Worker {worker_id} stopped.")

    async def _execute_ultra_fast_purchase(self, hit: TicketHit, worker_id: int, gui_q: Optional[asyncio.Queue] = None) -> bool:
        """Executes the purchase attempt using the golden profile's persistent context."""
        platform_lower = hit.platform.lower()
        worker_logger = logging.getLogger(f"PurchaseWorker-{worker_id}")

        if not self.golden_profile_object:
            worker_logger.error(f"Golden Profile not configured. Cannot attempt purchase for '{hit.event_name}'.")
            return False
        if not self.browser_manager: # Check if the primary BM is available
            worker_logger.error(f"Primary BrowserManager not available. Cannot attempt purchase for '{hit.event_name}'.")
            return False

        if not self.is_purchase_system_ready:
            worker_logger.warning(f"Purchase system not ready (golden profile not authenticated). Skipping purchase for '{hit.event_name}'.")
            await self.notifier.alert(f"Purchase for '{hit.event_name}' skipped: System NOT READY (Golden Profile Unauthenticated).", level="WARNING", category="purchase_skip")
            return False

        if not self._check_circuit_breaker(platform_lower): # Check circuit breaker for the platform
            worker_logger.warning(f"Circuit breaker for '{platform_lower}' is OPEN. Skipping purchase for '{hit.event_name}'.")
            return False

        page_for_purchase: Optional[PlaywrightPage] = None
        persistent_context_for_purchase: Optional[PlaywrightContext] = None
        action_succeeded = False

        try:
            worker_logger.info(f"Attempting purchase for: '{hit.event_name}' on offer URL '{hit.offer_url}' using Golden Profile: '{self.golden_profile_object.name}'.")
            if gui_q: await gui_q.put(("log", (f"W-{worker_id} buying: {hit.event_name[:20]}...", "ACTION")))

            # macOS Safari Handoff (if enabled and applicable)
            if platform_lower == "fansale" and platform_os.system() == "Darwin" and self.app_settings.get("enable_fansale_safari_handoff_macos", False):
                return await self._safari_handoff(hit, worker_id, gui_q)

            # Get the persistent context for the golden profile
            persistent_context_for_purchase = await self.browser_manager.get_persistent_context_for_profile(self.golden_profile_object)
            if not persistent_context_for_purchase:
                worker_logger.error(f"Failed to obtain persistent context for golden profile '{self.golden_profile_object.name}'. Purchase aborted for '{hit.event_name}'.")
                self._record_circuit_breaker_failure(platform_lower, is_critical=True)
                return False

            page_for_purchase = await persistent_context_for_purchase.new_page()

            # Apply advanced human behavior before critical actions
            human_intensity = self.app_settings.get("purchase_human_intensity", "medium")
            if human_intensity != "none":
                biometric_cfg = self.golden_profile_object.extra_js_props.get("biometric_profile_config", {})
                bio_profile = BiometricProfile(**biometric_cfg)
                await simulate_advanced_human_behavior(page_for_purchase, intensity=human_intensity, profile=bio_profile)

            nav_timeout = self.app_settings.get("purchase_navigation_timeout_ms", 30000) # Increased default
            nav_wait_until = self.app_settings.get("purchase_nav_wait_until", "domcontentloaded")
            worker_logger.info(f"W-{worker_id} navigating to offer: {hit.offer_url}")
            await page_for_purchase.goto(hit.offer_url, wait_until=nav_wait_until, timeout=nav_timeout)

            # Platform-specific action (e.g., add to cart, click buy)
            action_succeeded = await self._platform_specific_purchase_action(page_for_purchase, self.golden_profile_object, hit, platform_lower, worker_id)

            if action_succeeded:
                self._record_circuit_breaker_success(platform_lower)
                await self.notifier.alert(f"Purchase ACTION for '{hit.event_name}' SUCCEEDED or Handed Off. Review ASAP!", level="CRITICAL", category="purchase_success")
                if gui_q: await gui_q.put(("hit_success", (hit.event_name, hit.offer_url))) # Let GUI know
            else:
                self._record_circuit_breaker_failure(platform_lower)
                await self.notifier.alert(f"Purchase ACTION for '{hit.event_name}' FAILED.", level="ERROR", category="purchase_failure")
                if gui_q: await gui_q.put(("hit_fail", (hit.event_name, "Platform action failed")))
            return action_succeeded

        except PlaywrightError as e_pw:
            worker_logger.error(f"W-{worker_id}: Playwright error during purchase attempt for '{hit.event_name}': {e_pw}")
            self._record_circuit_breaker_failure(platform_lower, is_critical=isinstance(e_pw, BlockedError))
            if page_for_purchase and not page_for_purchase.is_closed() and self.app_settings.get("pause_on_purchase_error", True):
                worker_logger.info(f"Pausing browser due to error for '{hit.event_name}'.")
                try: await page_for_purchase.pause()
                except PlaywrightError: pass # Ignore if page is already closing
            return False
        except Exception as e_gen:
            worker_logger.error(f"W-{worker_id}: Unexpected error during purchase attempt for '{hit.event_name}': {e_gen}", exc_info=True)
            self._record_circuit_breaker_failure(platform_lower, is_critical=True) # Treat unexpected as critical
            if page_for_purchase and not page_for_purchase.is_closed() and self.app_settings.get("pause_on_purchase_error", True):
                worker_logger.info(f"Pausing browser due to unexpected error for '{hit.event_name}'.")
                try: await page_for_purchase.pause()
                except PlaywrightError: pass
            return False
        finally:
            if page_for_purchase and not page_for_purchase.is_closed():
                await page_for_purchase.close()
            # The persistent_context_for_purchase and its browser are kept alive by browser_manager
            worker_logger.debug(f"Finished purchase attempt for '{hit.event_name}' by W-{worker_id}. Success: {action_succeeded}")

    async def _safari_handoff(self, hit: TicketHit, worker_id: int, gui_q: Optional[asyncio.Queue] = None) -> bool:
        """Handles opening the URL in Safari on macOS."""
        worker_logger = logging.getLogger(f"PurchaseWorker-{worker_id}")
        worker_logger.warning(f"W-{worker_id}: Initiating SAFARI HANDOFF for '{hit.event_name}' to URL: {hit.offer_url}")
        try:
            # Ensure subprocess is run in a way that doesn't block the asyncio loop for too long
            process = await asyncio.create_subprocess_exec('open', '-a', 'Safari', hit.offer_url)
            await process.wait() # Wait for the command to execute
            if process.returncode == 0:
                self.logger.info(f"Safari handoff successful for '{hit.event_name}'.")
                if gui_q: await gui_q.put(("alert", (f"Safari Handoff (W-{worker_id})", f"{hit.event_name[:20]}...", hit.offer_url)))
                await self.notifier.alert(f"SAFARI HANDOFF initiated for '{hit.event_name}'. Please check Safari NOW!", category="purchase_handoff", level="CRITICAL")
                return True
            else:
                self.logger.error(f"Safari handoff command failed with code {process.returncode} for '{hit.event_name}'.")
                return False
        except Exception as e:
            worker_logger.error(f"W-{worker_id}: Safari handoff FAILED for '{hit.event_name}': {e}", exc_info=True)
            return False

    async def _platform_specific_purchase_action(self, page: PlaywrightPage, browser_profile: BrowserProfile, hit: TicketHit, platform_lower: str, worker_id: int) -> bool:
        """Performs the platform-specific purchase action (e.g., add to cart)."""
        action_logger = logging.getLogger(f"PurchaseAction.W{worker_id}.{platform_lower}")
        action_logger.info(f"Executing platform-specific purchase action for '{hit.event_name}' on {page.url[:70]}")
        target_cfg_for_hit = hit.hit_data.get('original_target_config', {}) # Get the original target_cfg

        try:
            if platform_lower == "ticketmaster":
                offer_id = hit.hit_data.get("offer_id") # This comes from check_ticketmaster_event's parsing
                if offer_id and hasattr(ticketmaster, 'add_to_basket'):
                    action_logger.info(f"Ticketmaster: Attempting API add_to_basket with offer_id '{offer_id}'. Event page URL for referer: {hit.url}")
                    # add_to_basket needs the event page URL for the Referer header
                    success, _ = await ticketmaster.add_to_basket(page.context, str(offer_id), event_page_url=hit.url)
                    action_logger.info(f"Ticketmaster add_to_basket API call result: {success}")
                    if success and self.app_settings.get("pause_after_successful_tm_api_add", True):
                        action_logger.warning(f"Ticketmaster: Successfully added to basket via API. PAUSING for manual checkout. Visit Ticketmaster basket.")
                        await page.pause() # Pause to allow manual checkout
                    return success
                else:
                    action_logger.warning(f"Ticketmaster: 'offer_id' missing in hit_data or 'add_to_basket' function not available. Hit data: {hit.hit_data}. Pausing for manual interaction.")
                    if not page.is_closed(): await page.pause()
                    return True # True because we paused for manual, not a script failure
            elif platform_lower == "vivaticket":
                action_logger.info("Vivaticket: Attempting generic 'buy' button click on offer page.")
                # Selectors for the offer detail page, might be different from listing page
                buy_selectors = target_cfg_for_hit.get("vivaticket_purchase_buy_selectors", # Use specific config if available
                                 "button[type='submit']:has-text('Acquista'), a.btn-buy, button.btn-checkout, input[type='submit'][value*='Acquista']") # More specific selectors
                for selector in buy_selectors.split(','):
                    try:
                        trimmed_selector = selector.strip()
                        if not trimmed_selector: continue
                        buy_button = page.locator(trimmed_selector).first
                        if await buy_button.is_visible(timeout=self.app_settings.get("vivaticket_click_timeout_ms", 7000)):
                            action_logger.info(f"Vivaticket: Clicking buy button with selector: '{trimmed_selector}'.")
                            await buy_button.click() # Consider more human-like click from advanced simulation if needed
                            action_logger.info(f"Vivaticket: Clicked element '{trimmed_selector}'. Pausing for manual checkout.")
                            if not page.is_closed(): await page.pause()
                            return True
                    except PlaywrightError:
                        action_logger.debug(f"Vivaticket: Buy selector '{trimmed_selector}' not found or not clickable quickly.")
                        continue
                action_logger.warning("Vivaticket: No 'buy' button found/clickable on offer page. Pausing.")
                if not page.is_closed(): await page.pause()
                return True # Paused for manual
            elif platform_lower == "fansale":
                action_logger.info("FanSale: Attempting specific ticket listing click and proceed.")
                if hasattr(fansale, 'click_specific_ticket_listing_and_proceed'):
                    # click_specific_ticket_listing_and_proceed expects hit_info to be the detailed hit data,
                    # and target_cfg to be the original target configuration for that event.
                    success = await fansale.click_specific_ticket_listing_and_proceed(page, browser_profile, hit.hit_data, target_cfg_for_hit)
                    action_logger.info(f"FanSale click_specific_ticket_listing_and_proceed result: {success}. (This function internally pauses)")
                    return success # This function already pauses
                else:
                    action_logger.warning("FanSale: 'click_specific_ticket_listing_and_proceed' function not found. Pausing.")
                    if not page.is_closed(): await page.pause()
                    return True # Paused for manual
            else:
                action_logger.warning(f"No specific purchase action defined for platform '{platform_lower}'. Pausing for manual intervention.")
                if not page.is_closed(): await page.pause()
                return True # Paused for manual
        except PlaywrightError as e_pw_action:
            action_logger.error(f"Playwright error during purchase action for '{hit.event_name}': {e_pw_action}")
            if not page.is_closed() and self.app_settings.get("pause_on_purchase_error", True): await page.pause()
            return False
        except Exception as e_action: # Catch any other unexpected error
            action_logger.error(f"Unexpected error during purchase action for '{hit.event_name}': {e_action}", exc_info=True)
            if not page.is_closed() and self.app_settings.get("pause_on_purchase_error", True): await page.pause()
            return False
        return False # Default to false if no action taken or error

    def _check_circuit_breaker(self, platform: str) -> bool:
        """Checks if the circuit breaker for the given platform allows operation."""
        breaker = self.circuit_breakers[platform]
        current_time = time.time()

        if breaker.state == "OPEN":
            if current_time - breaker.last_failure_time > breaker.recovery_timeout:
                breaker.state = "HALF_OPEN"
                breaker.failure_count = 0 # Reset failures for half-open test
                self.logger.info(f"CircuitBreaker for '{platform}' transitioned to HALF_OPEN state.")
                return True # Allow one attempt in HALF_OPEN
            self.logger.debug(f"CircuitBreaker for '{platform}' is OPEN. Purchase attempt blocked.")
            return False
        return True # CLOSED or HALF_OPEN (already allowed one attempt)

    def _record_circuit_breaker_success(self, platform: str):
        """Records a successful operation for the platform's circuit breaker."""
        breaker = self.circuit_breakers[platform]
        if breaker.state == "HALF_OPEN":
            self.logger.info(f"CircuitBreaker for '{platform}' successful in HALF_OPEN state. Transitioning to CLOSED.")
        breaker.failure_count = 0
        breaker.state = "CLOSED"

    def _record_circuit_breaker_failure(self, platform: str, is_critical: bool = False):
        """Records a failed operation for the platform's circuit breaker."""
        breaker = self.circuit_breakers[platform]
        breaker.failure_count += 1
        breaker.last_failure_time = time.time()

        if breaker.state == "HALF_OPEN" or breaker.failure_count >= breaker.failure_threshold or is_critical:
            if breaker.state != "OPEN": # Log only on transition to OPEN
                self.logger.warning(f"CircuitBreaker for '{platform}' OPENED due to failures reaching threshold ({breaker.failure_count}/{breaker.failure_threshold}) or critical error. Critical: {is_critical}")
            breaker.state = "OPEN"
        else: # Still CLOSED, but incrementing failures
            self.logger.debug(f"CircuitBreaker for '{platform}' recorded a failure. Count: {breaker.failure_count}/{breaker.failure_threshold}")

    async def add_ticket_hit(self, hit_data: Dict[str, Any], priority: PriorityLevel = PriorityLevel.HIGH):
        """Adds a discovered ticket hit to the prioritized processing queue."""
        offer_url = hit_data.get("offer_url", hit_data.get("url")) # Prefer offer_url if available
        if not offer_url:
            self.logger.error(f"Cannot add hit for event '{hit_data.get('event_name', 'N/A')}' - missing 'offer_url' or 'url' in hit_data.")
            return

        # Ensure max_retries is sourced from app_settings if not in hit_data
        max_retries_for_hit = hit_data.get("max_retries", self.app_settings.get("purchase_max_retries_per_hit", 3))

        hit = TicketHit(
            platform=hit_data.get("platform", "unknown"),
            event_name=hit_data.get("event_name", "Unknown Event"),
            url=hit_data.get("url", offer_url), # Original monitoring URL
            offer_url=offer_url,                # Specific URL for purchase
            priority=priority,
            timestamp=time.time(),
            hit_data=hit_data, # This contains all platform-specific details and original_target_config
            max_retries=max_retries_for_hit
        )
        try:
            queue_put_timeout = self.app_settings.get("ticket_hit_queue_put_timeout_s", 2.0)
            await asyncio.wait_for(self.ticket_hit_queue.put(hit), timeout=queue_put_timeout)
            self.logger.info(f"Added {priority.name} priority hit to queue: '{hit.event_name}'. Queue size: {self.ticket_hit_queue.qsize()}")
        except asyncio.TimeoutError:
            self.logger.error(f"HIT QUEUE PUT TIMEOUT! Could not add hit for '{hit.event_name}' after {queue_put_timeout}s. Hit DISCARDED.")
            await self.notifier.alert(f"HIT QUEUE TIMEOUT for {hit.event_name}. Ticket may be lost.", level="ERROR", category="queue_error")
        except asyncio.QueueFull: # Should ideally not happen if maxsize is large enough or processing is fast
            self.logger.error(f"HIT QUEUE IS FULL! Could not add hit for '{hit.event_name}'. Hit DISCARDED. Max size: {self.ticket_hit_queue.maxsize}")
            await self.notifier.alert(f"HIT QUEUE FULL for {hit.event_name}. System might be overwhelmed.", level="CRITICAL", category="queue_error")

    async def shutdown(self):
        """Gracefully shuts down the AdvancedPurchaseArchitecture."""
        self.logger.info("Shutting down AdvancedPurchaseArchitecture...")
        if not self._stop_event.is_set():
            self._stop_event.set() # Signal all loops and tasks to stop

        # Cancel and await purchase readiness task
        if self._purchase_readiness_task and not self._purchase_readiness_task.done():
            self.logger.debug("Cancelling purchase readiness task...")
            self._purchase_readiness_task.cancel()
            try:
                await self._purchase_readiness_task
            except asyncio.CancelledError:
                self.logger.info("Purchase readiness task successfully cancelled.")
            except Exception as e:
                self.logger.error(f"Error during purchase readiness task cancellation: {e}")
        self._purchase_readiness_task = None

        # Cancel and await purchase workers
        if self.purchase_workers:
            self.logger.debug(f"Cancelling {len(self.purchase_workers)} purchase worker(s)...")
            for worker_task in self.purchase_workers:
                if not worker_task.done():
                    worker_task.cancel()
            # Wait for all worker tasks to complete or be cancelled
            results = await asyncio.gather(*self.purchase_workers, return_exceptions=True)
            for i, res in enumerate(results):
                if isinstance(res, asyncio.CancelledError):
                    self.logger.info(f"Purchase worker {i} successfully cancelled.")
                elif isinstance(res, Exception):
                    self.logger.error(f"Purchase worker {i} raised an exception during shutdown: {res}")
            self.logger.info("All purchase workers stopped.")
        self.purchase_workers.clear()

        # Stop the browser manager
        if self.browser_manager:
            self.logger.info("Stopping Primary StealthBrowserManager (V2)...")
            await self.browser_manager.stop_manager() # This closes its browser pool and persistent golden browser
            self.browser_manager = None

        self.logger.info("AdvancedPurchaseArchitecture shutdown complete.")

# --- Monitoring Logic ---
async def monitor_target_enhanced(
    name: str, checker: Callable, target_cfg: Dict[str, Any],
    bm: StealthBrowserManager, # The single, primary browser manager
    apa: AdvancedPurchaseArchitecture,
    cancel_evt: asyncio.Event, gui_q: Optional[asyncio.Queue] = None,
):
    log = logging.getLogger(f"Monitor.{name.replace(' ', '_')[:30]}") # Ensure logger name isn't too long
    page_url_to_check = target_cfg.get("url")
    if not page_url_to_check:
        log.error(f"URL missing for target '{name}'. Skipping this target."); return

    # Interval calculation
    base_interval_s = float(target_cfg.get("interval_s", apa.app_settings.get("monitoring_interval_s", 60.0)))
    priority_multiplier = float(target_cfg.get("priority_multiplier", 1.0))
    # Ensure priority_multiplier doesn't lead to zero or negative interval
    effective_interval_s = base_interval_s / priority_multiplier if priority_multiplier > 0.1 else base_interval_s
    effective_interval_s = max(apa.app_settings.get("min_monitoring_interval_s", 5.0), effective_interval_s) # Enforce minimum

    log.info(f"Monitoring '{name}' (URL: {page_url_to_check[:60]}), Effective Interval: ~{effective_interval_s:.1f}s")
    # Initial random stagger for tasks
    await asyncio.sleep(random.uniform(1.0, min(5.0, effective_interval_s / 4 if effective_interval_s > 4 else 1.0)))

    consecutive_failures = 0
    last_success_time = time.monotonic() # Time of last successful check (no block/error)

    while not cancel_evt.is_set():
        page_instance_for_log: Optional[PlaywrightPage] = None # For logging in case of error
        active_profile_for_log: Optional[BrowserProfile] = None # For logging
        try:
            # Get a context from the browser manager's pool
            async with bm.get_context() as (ctx, profile_used): # bm is self.browser_manager
                active_profile_for_log = profile_used
                log.debug(f"[{name}] Starting check round with Profile: {profile_used.name}")
                if gui_q: await gui_q.put(("status", (name, f"Preparing (Profile: {profile_used.name[:12]})")))

                async with bm.get_page_from_context(ctx, url=None) as page: # Let monitor_target_enhanced handle initial goto
                    page_instance_for_log = page
                    # FingerprintRandomizer and PlatformStealthManager are placeholders,
                    # primary stealth comes from BrowserProfile and stealth_init.js via bm.get_context()
                    # await FingerprintRandomizer.randomize_page_fingerprint(page)
                    # current_platform = target_cfg.get("platform", "unknown")
                    # await PlatformStealthManager.apply_platform_specific_stealth(page, current_platform)

                    if gui_q: await gui_q.put(("status", (name, f"Checking (Prof: {profile_used.name[:10]}) URL: ...{page_url_to_check.split('/')[-1][:15]}")))
                    nav_timeout = apa.app_settings.get("monitoring_navigation_timeout_ms", 45000) # Increased default
                    nav_wait_until = apa.app_settings.get("monitoring_nav_wait_until", "domcontentloaded")
                    await page.goto(page_url_to_check, wait_until=nav_wait_until, timeout=nav_timeout)

                    # Apply advanced human behavior simulation
                    human_intensity = target_cfg.get("human_behavior_intensity", apa.app_settings.get("default_monitoring_human_intensity", "low"))
                    if human_intensity != "none":
                        biometric_cfg = profile_used.extra_js_props.get("biometric_profile_config", {})
                        bio_profile = BiometricProfile(**biometric_cfg) # Uses defaults if biometric_cfg is empty
                        await simulate_advanced_human_behavior(page, intensity=human_intensity, profile=bio_profile)

                    # Enhanced block detection (runs before main checker)
                    await _apa_enhanced_block_detection(page, name, target_cfg, apa.app_settings)

                    # Call the platform-specific checker function
                    hits_data_list = await checker(page=page, profile=profile_used, target_cfg=target_cfg, bm=bm, gui_q=gui_q)

                    if hits_data_list: # If checker returns a list of hits
                        log.critical(f"[{name}] HIT(S) DETECTED! (Profile: {profile_used.name}) Number of hits: {len(hits_data_list)}")
                        hit_priority_str = target_cfg.get("hit_priority", "HIGH").upper()
                        try:
                            hit_priority = PriorityLevel[hit_priority_str]
                        except KeyError:
                            log.warning(f"Invalid hit_priority '{hit_priority_str}' for '{name}'. Defaulting to HIGH.")
                            hit_priority = PriorityLevel.HIGH

                        for hit_detail in hits_data_list:
                            if not isinstance(hit_detail, dict):
                                log.warning(f"[{name}] Invalid hit_detail format: {type(hit_detail)}. Skipping.")
                                continue
                            hit_message_summary = hit_detail.get("message", f"Offer details: {str(hit_detail)[:70]}")
                            log.warning(f"[{name}] HIT DETAIL: {hit_message_summary}")

                            # Send alert via AdvancedNotifier
                            await apa.notifier.alert(f"HIT! Target: {name} (Profile: {profile_used.name}): {hit_message_summary}", level="WARNING", category="ticket_hit")
                            if gui_q: await gui_q.put(("hit", (name, f"HIT! ({profile_used.name}): {hit_message_summary}", page.url))) # GUI notification

                            # Prepare full hit information for the purchase queue
                            full_hit_info_for_queue = {
                                "platform": target_cfg.get("platform", "unknown"),
                                "url": page_url_to_check, # Original monitoring URL
                                "event_name": name,
                                "original_target_config": dict(target_cfg), # Pass target config for context
                                **hit_detail # Merge platform-specific hit data
                            }
                            await apa.add_ticket_hit(full_hit_info_for_queue, priority=hit_priority)

                        # Cooldown after finding hits for this target
                        post_hit_target_cooldown_s = float(target_cfg.get("post_hit_target_cooldown_s", random.uniform(60, 120)))
                        log.info(f"[{name}] Hit(s) processed. Target cooling down for {post_hit_target_cooldown_s:.1f}s.")
                        try:
                            await asyncio.wait_for(cancel_evt.wait(), timeout=post_hit_target_cooldown_s)
                        except asyncio.TimeoutError: pass # Timeout means cooldown passed
                        if cancel_evt.is_set(): break # Exit if cancelled during cooldown
                    else: # No hits
                        log.info(f"[{name}] No tickets found this round (Profile: {profile_used.name}).")
                        if gui_q: await gui_q.put(("status", (name, "No tickets.")))

                    consecutive_failures = 0 # Reset on successful check
                    last_success_time = time.monotonic()

        except BlockedError as e_block:
            log.warning(f"[{name}] Blocked (Profile: '{active_profile_for_log.name if active_profile_for_log else 'Unknown'}'): {e_block}.")
            apa.performance_metrics["blocks_detected"] +=1
            if gui_q: await gui_q.put(("blocked", (name, str(e_block), page_instance_for_log.url if page_instance_for_log else page_url_to_check )))
            consecutive_failures += 1
            # Dynamic backoff for blocks
            backoff_base = float(apa.app_settings.get("block_backoff_base_s", 30.0))
            max_backoff = float(apa.app_settings.get("block_max_backoff_s", 600.0))
            cooldown_s = min(max_backoff, (2 ** min(consecutive_failures, 5)) * backoff_base + random.uniform(0, backoff_base * 0.5)) # Cap exponent
            log.info(f"[{name}] Cooling down for {cooldown_s:.1f}s after block (Failures: {consecutive_failures}).")
            if gui_q: await gui_q.put(("status", (name, f"Blocked! CD {cooldown_s:.0f}s")))
            try: await asyncio.wait_for(cancel_evt.wait(), timeout=cooldown_s)
            except asyncio.TimeoutError: pass # Cooldown finished
            continue # Restart monitoring loop for this target
        except asyncio.CancelledError:
            log.info(f"[{name}] Monitoring task cancelled.")
            raise # Re-raise to allow cleanup
        except PlaywrightError as e_pw:
            log.error(f"[{name}] Playwright Error (Profile: {active_profile_for_log.name if active_profile_for_log else 'Unknown'}): {e_pw}")
            if gui_q: await gui_q.put(("error", (name, f"PW Error: {str(e_pw)[:45]}...", page_instance_for_log.url if page_instance_for_log else page_url_to_check )))
            consecutive_failures += 1
            err_cd_s = min(300, consecutive_failures * random.uniform(45,75)) # Error cooldown
            log.info(f"[{name}] Cooling down for {err_cd_s:.1f}s after Playwright error.")
            try: await asyncio.wait_for(cancel_evt.wait(), timeout=err_cd_s)
            except asyncio.TimeoutError: pass
            continue
        except Exception as e_gen: # Catch-all for other unexpected errors
            log.critical(f"[{name}] UNEXPECTED CRITICAL ERROR (Profile: {active_profile_for_log.name if active_profile_for_log else 'Unknown'}): {e_gen}", exc_info=True)
            if gui_q: await gui_q.put(("error", (name, f"General Error: {str(e_gen)[:45]}...", page_instance_for_log.url if page_instance_for_log else page_url_to_check)))
            consecutive_failures += 1
            gen_err_cd_s = min(450, consecutive_failures * random.uniform(60,90))
            log.warning(f"[{name}] Cooling down for {gen_err_cd_s:.1f}s after general error.")
            try: await asyncio.wait_for(cancel_evt.wait(), timeout=gen_err_cd_s)
            except asyncio.TimeoutError: pass
            continue

        # Dynamic interval adjustment
        current_target_interval_s = effective_interval_s
        # Increase interval on repeated failures
        if consecutive_failures >= apa.app_settings.get("consecutive_failure_threshold_for_interval_increase", 3):
            current_target_interval_s = min(current_target_interval_s * 1.5, apa.app_settings.get("max_monitoring_interval_s", 900.0))
        # Decrease interval if recently successful (but not too low)
        elif time.monotonic() - last_success_time < apa.app_settings.get("recent_success_window_s_for_interval_decrease", 300.0): # e.g. 5 mins
            current_target_interval_s = max(current_target_interval_s * 0.9, apa.app_settings.get("min_monitoring_interval_s", 10.0))

        # Add jitter to the calculated interval
        wait_time_s = current_target_interval_s * random.uniform(
            apa.app_settings.get("interval_jitter_min_factor", 0.85),
            apa.app_settings.get("interval_jitter_max_factor", 1.15)
        )
        wait_time_s = max(apa.app_settings.get("min_monitoring_interval_s", 5.0), wait_time_s) # Ensure min interval

        log.debug(f"[{name}] Next check in ~{wait_time_s:.1f}s (Base: {effective_interval_s:.1f}s, Current Adj: {current_target_interval_s:.1f}s).")
        if gui_q: await gui_q.put(("status", (name, f"Waiting {wait_time_s:.0f}s")))
        try:
            await asyncio.wait_for(cancel_evt.wait(), timeout=wait_time_s)
        except asyncio.TimeoutError:
            pass # Timeout means it's time for the next check
        except Exception as e_wait: # Catch other errors during wait
            log.error(f"[{name}] Error during interval wait: {e_wait}. Stopping monitoring for this target if not cancelled.")
            if not cancel_evt.is_set(): break # Exit loop for this target
    log.info(f"[{name}] Monitoring task for target has stopped.")


async def _apa_enhanced_block_detection(page: PlaywrightPage, target_name: str, target_cfg: Dict[str, Any], app_settings: Dict[str, Any]):
    """Performs enhanced block and CAPTCHA detection on the page."""
    logger_bd = logging.getLogger(f"BlockDetect.{target_name.replace(' ','_')[:20]}") # Shortened name
    try:
        content_scan_timeout_ms = app_settings.get("block_detect_content_scan_timeout_ms", 1500) # ms
        content_sample_js = "() => document.body ? document.body.innerText.toLowerCase().substring(0, 1500) : ''" # Increased sample
        content_sample = ""
        try:
            # Use asyncio.wait_for for a timeout on the evaluate call
            content_sample = await asyncio.wait_for(
                page.evaluate(content_sample_js),
                timeout=content_scan_timeout_ms / 1000.0 # Convert ms to s for asyncio.wait_for
            )
        except asyncio.TimeoutError:
            logger_bd.warning(f"[{target_name}] Timeout ({content_scan_timeout_ms}ms) getting page content for block detection.")
        except Exception as e_content: # Catch other Playwright or JS errors during evaluate
            logger_bd.warning(f"[{target_name}] Error getting page content for block detection: {e_content}")

        # Combine global and target-specific block indicators
        global_block_indicators = app_settings.get("global_block_page_indicators", ["access denied", "blocked", "pardon our interruption", "robot check", "are you a human"])
        target_specific_indicators = target_cfg.get("block_page_indicators", [])
        all_block_indicators = list(set(global_block_indicators + target_specific_indicators)) # Unique indicators

        if content_sample: # Only scan if content was retrieved
            for indicator_phrase in all_block_indicators:
                if indicator_phrase.lower() in content_sample:
                    logger_bd.warning(f"[{target_name}] BLOCK DETECTED (Content Indicator: '{indicator_phrase}') on URL: {page.url[:60]}")
                    raise BlockedError(f"Block indicator '{indicator_phrase}' found in page content.")

        # CAPTCHA detection (using selectors)
        global_captcha_selectors = app_settings.get("global_captcha_selectors", ["iframe[title*='recaptcha'i]", "div.g-recaptcha", "div.cf-turnstile"])
        target_captcha_selectors = target_cfg.get("captcha_selectors", [])
        all_captcha_selectors = list(set(global_captcha_selectors + target_captcha_selectors))
        captcha_check_timeout_ms = app_settings.get("block_detect_captcha_timeout_ms", 1000) # ms, short timeout per selector

        for selector in all_captcha_selectors:
            try:
                # Check if any element matching the selector is visible
                if await page.locator(selector).first.is_visible(timeout=captcha_check_timeout_ms):
                    logger_bd.warning(f"[{target_name}] CAPTCHA DETECTED (Selector: '{selector}') on URL: {page.url[:60]}")
                    raise BlockedError(f"CAPTCHA element with selector '{selector}' is visible.")
            except PlaywrightError: # TimeoutError from is_visible means not found/visible quickly
                continue # Try next selector
            except BlockedError: # Re-raise if it's already a BlockedError (from CAPTCHA detection)
                raise
            except Exception as e_sel_check: # Catch other errors during locator check
                logger_bd.debug(f"[{target_name}] Minor error checking CAPTCHA selector '{selector}': {e_sel_check}")

    except BlockedError: # Re-raise to be caught by monitor_target_enhanced
        raise
    except Exception as e_main_detect: # Catch-all for unexpected errors in this function
        logger_bd.error(f"[{target_name}] Unexpected error during enhanced block detection: {e_main_detect}", exc_info=True)
        # Do not raise BlockedError here, let the main check proceed if detection itself fails.

# --- Main Asynchronous Execution Logic ---
async def _async_main_refactored(config_data: Dict[str, Any], gui_q: Optional[asyncio.Queue] = None,
                                 stop_event_from_caller: Optional[asyncio.Event] = None) -> None:
    """Main asynchronous logic for the ticket monitor."""
    global _apa_instance_for_signal, _stop_event_for_signal, _active_monitoring_tasks_for_signal
    main_logger = logging.getLogger("AsyncMainRefactored")
    # Use the stop_event passed from the caller (CLI or GUI) or create a new one
    stop_event = stop_event_from_caller if stop_event_from_caller else asyncio.Event()
    _stop_event_for_signal = stop_event # Make it accessible to signal handler
    _active_monitoring_tasks_for_signal.clear() # Clear any stale tasks

    apa: Optional[AdvancedPurchaseArchitecture] = None

    try:
        main_logger.info("AsyncMainRefactored: Starting Playwright...")
        async with async_playwright() as p_instance: # Manage Playwright lifecycle
            # TLS Fingerprint Patching
            try:
                tls_profile_key = config_data.get("app_settings", {}).get("tls_fingerprint_profile")
                if tls_profile_key:
                    if patch_ssl_for_fingerprint_evasion(browser_profile_ja3_key=tls_profile_key):
                        main_logger.info(f"TLS fingerprint patch enabled for JA3 profile: '{tls_profile_key}'.")
                    else:
                        main_logger.warning(f"TLS fingerprint patch FAILED for JA3 profile: '{tls_profile_key}'. Check logs.")
                else:
                    main_logger.info("No 'tls_fingerprint_profile' found in app_settings; TLS settings not modified by patcher.")
            except Exception as e_tls_init:
                main_logger.error(f"Error during TLS fingerprint initialization: {e_tls_init}", exc_info=True)

            # Load all browser profiles (needed by APA to identify golden profile object)
            profiles_yaml_path_str = config_data.get('paths',{}).get('browser_profiles_yaml', str(CONFIG_FILE.parent / 'browser_profiles.yaml'))
            all_yaml_profiles = _load_browser_profiles_from_yaml(Path(profiles_yaml_path_str))
            if not all_yaml_profiles:
                main_logger.error(f"CRITICAL: No browser profiles loaded from '{profiles_yaml_path_str}'. The application may not function correctly.")
                # Depending on strictness, you might want to exit or use fallbacks in StealthBrowserManager.

            main_logger.info("Initializing AdvancedPurchaseArchitecture (APA)...")
            apa = AdvancedPurchaseArchitecture(
                main_config_data=config_data,
                all_available_profiles_for_apa_logic=all_yaml_profiles, # Pass all loaded profiles
                stop_event=stop_event,
                playwright_instance=p_instance
            )
            _apa_instance_for_signal = apa # Make APA instance globally accessible for signal handler

            # Start the primary browser manager (used for monitoring and golden profile persistent contexts)
            if apa.browser_manager:
                await apa.browser_manager.start_manager()
                main_logger.info("Primary StealthBrowserManager (V2) started.")
            else:
                main_logger.critical("Primary StealthBrowserManager failed to initialize. Cannot proceed.")
                return # Exit if BM is not up

            # Initialize purchase-side systems (workers, readiness loop for golden profile)
            await apa.initialize_purchase_side_systems(gui_q=gui_q)

            # Start monitoring tasks
            monitoring_tasks_local: List[asyncio.Task] = []
            if apa.browser_manager: # Ensure BM is available for monitoring
                targets_to_monitor = config_data.get("targets", [])
                platform_dispatch_checkers: Dict[str, Callable] = {
                    "Ticketmaster": ticketmaster.check_ticketmaster_event,
                    "FanSale": fansale.check_fansale_event,
                    "Vivaticket": vivaticket.check_vivaticket_event,
                }
                for idx, target_config_entry in enumerate(targets_to_monitor):
                    if not isinstance(target_config_entry, dict) or not target_config_entry.get("enabled", False):
                        continue # Skip disabled or malformed targets

                    platform_name = target_config_entry.get("platform")
                    checker_function = platform_dispatch_checkers.get(platform_name)
                    target_url = target_config_entry.get("url")

                    if not (checker_function and target_url and platform_name):
                        main_logger.error(f"Skipping invalid target configuration #{idx+1} ('{target_config_entry.get('event_name', 'N/A')}'). Missing platform, checker, or URL.")
                        continue

                    event_name_for_log = target_config_entry.get("event_name", f"{platform_name}_Event_{idx+1}")
                    task_unique_name = f"monitor_{event_name_for_log.replace(' ','_').replace('/','-')[:50]}" # Ensure unique and valid task name

                    task = asyncio.create_task(monitor_target_enhanced(
                        name=event_name_for_log, checker=checker_function, target_cfg=target_config_entry,
                        bm=apa.browser_manager, # Pass the single primary browser manager
                        apa=apa, cancel_evt=stop_event, gui_q=gui_q
                    ), name=task_unique_name)
                    monitoring_tasks_local.append(task)
                _active_monitoring_tasks_for_signal[:] = monitoring_tasks_local # Update global list for signal handler
            else: # Should not happen if previous check passed
                main_logger.error("Monitoring cannot start: Primary BrowserManager not available.")


            if not monitoring_tasks_local and not apa.purchase_workers: # Check if any work is being done
                main_logger.warning("No active monitoring tasks or purchase workers started. The application will idle until stopped.")
                await stop_event.wait() # Wait indefinitely if nothing to do
            elif monitoring_tasks_local:
                main_logger.info(f"{len(monitoring_tasks_local)} monitoring task(s) have been started.")
                await stop_event.wait() # Wait for stop signal while tasks run
            else: # Only purchase workers are active (e.g., no monitoring targets enabled)
                main_logger.info("Only purchase workers are active (no monitoring targets). Waiting for stop signal or hits.")
                await stop_event.wait()

            main_logger.info("Stop event received by main loop. Initiating shutdown sequence...")

    except RuntimeError as e_rt_main: # Catch specific RuntimeErrors, e.g., from Playwright startup
        main_logger.critical(f"FATAL RUNTIME ERROR in _async_main_refactored: {e_rt_main}", exc_info=True)
        if gui_q: await gui_q.put(("log", (f"FATAL CORE ERROR: {str(e_rt_main)[:90]}", "CRITICAL")))
        if not stop_event.is_set(): stop_event.set() # Ensure stop is signaled
    except Exception as e_unhandled_main: # Catch any other unhandled exceptions
        main_logger.critical(f"Unhandled CRITICAL error in _async_main_refactored: {e_unhandled_main}", exc_info=True)
        if gui_q: await gui_q.put(("log", (f"FATAL UNHANDLED ERROR: {str(e_unhandled_main)[:90]}", "CRITICAL")))
        if not stop_event.is_set(): stop_event.set() # Ensure stop is signaled
    finally:
        main_logger.info("_async_main_refactored 'finally' block: Cleaning up resources...")
        if not stop_event.is_set(): # If loop exited for other reason than stop_event
            stop_event.set()
            main_logger.debug("Stop event explicitly set in 'finally' block of _async_main_refactored.")

        # Cancel any still-running monitoring tasks
        if _active_monitoring_tasks_for_signal:
            main_logger.info(f"Cancelling {len(_active_monitoring_tasks_for_signal)} active monitoring task(s)...")
            for task_to_cancel in _active_monitoring_tasks_for_signal:
                if not task_to_cancel.done():
                    task_to_cancel.cancel()
            # Wait for tasks to acknowledge cancellation
            results = await asyncio.gather(*_active_monitoring_tasks_for_signal, return_exceptions=True)
            for i, res in enumerate(results):
                task_name = _active_monitoring_tasks_for_signal[i].get_name()
                if isinstance(res, asyncio.CancelledError):
                    main_logger.info(f"Monitoring task '{task_name}' successfully cancelled.")
                elif isinstance(res, Exception):
                     main_logger.error(f"Monitoring task '{task_name}' raised an exception during shutdown/cancellation: {res}")
            _active_monitoring_tasks_for_signal.clear()

        # Shutdown APA (which includes its browser manager and workers)
        if apa:
            await apa.shutdown()
        # Clear global instance if it was set to this APA instance
        if _apa_instance_for_signal is apa:
            _apa_instance_for_signal = None

        main_logger.info("_async_main_refactored cleanup finished.")

# --- Configuration and Logging Setup ---
def _load_yaml_config(file_path: Path) -> Dict[str, Any]:
    """Loads YAML configuration from the given file path."""
    if not file_path.is_file(): # More robust check
        logging.error(f"Configuration file {file_path} not found or is not a file.")
        return {}
    try:
        with file_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {} # Ensure it's a dict
    except yaml.YAMLError as ye:
        logging.error(f"Error parsing YAML configuration file {file_path}: {ye}", exc_info=True)
    except Exception as e:
        logging.error(f"Unexpected error loading YAML configuration {file_path}: {e}", exc_info=True)
    return {}

def _init_logging(level_str: str = "INFO", log_file_path_str: Optional[str] = None) -> None:
    """Initializes logging for the application."""
    log_level = getattr(logging, level_str.upper(), logging.INFO)
    if not isinstance(log_level, int): log_level = logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level) # Set level on the root logger

    # Remove any existing handlers to prevent duplication if this function is called multiple times
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        handler.close()

    log_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-7s] %(name)-30s :: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(log_level) # Set level on handler too
    root_logger.addHandler(console_handler)

    # File Handler
    if log_file_path_str:
        try:
            log_file_p = Path(log_file_path_str).resolve()
            log_file_p.parent.mkdir(parents=True, exist_ok=True)
            # Use logging.handlers.RotatingFileHandler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_p,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(log_formatter)
            file_handler.setLevel(log_level) # Set level on file handler
            root_logger.addHandler(file_handler)
            # Use print for this initial confirmation as logger might still be in flux by other parts of startup
            print(f"INFO: Logging to console and file: {log_file_p}")
        except Exception as e_fh:
            print(f"ERROR: Could not create or use log file '{log_file_path_str}': {e_fh}", file=sys.stderr)
            print("INFO: Logging to console only.")
    else:
        print("INFO: Logging to console only (no log file path provided).")

    # Silence noisy libraries after setting up our handlers
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("websockets.server").setLevel(logging.ERROR)
    logging.getLogger("websockets.protocol").setLevel(logging.ERROR)
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)
    # The explicit call to logging.info by the root logger will happen if _init_logging is called by cli_main
    # logging.getLogger().info(f"Logging initialized. Level: {logging.getLevelName(log_level)}. File: {log_file_path_str or 'Console only'}")

    # Get root logger and remove existing handlers to avoid duplication if re-initialized
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers): # Iterate over a copy
        root_logger.removeHandler(handler)
        handler.close() # Close handler before removing

    # Define formatter
    log_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-7s] %(name)-30s :: %(message)s", # Adjusted name width
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Setup handlers
    handlers_list: List[logging.Handler] = []

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    handlers_list.append(console_handler)

    # File Handler (if path is provided)
    if log_file_path_str:
        try:
            log_file_path = Path(log_file_path_str).resolve()
            log_file_path.parent.mkdir(parents=True, exist_ok=True) # Ensure log directory exists
            # Use RotatingFileHandler for better log management
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_path,
                maxBytes=10*1024*1024, # 10 MB per file
                backupCount=5,         # Keep 5 backup files
                encoding='utf-8'
            )
            file_handler.setFormatter(log_formatter)
            handlers_list.append(file_handler)
        except Exception as e_fh:
            # Use print for this critical error as logging might not be fully up
            print(f"ERROR: Could not create or use log file '{log_file_path_str}': {e_fh}", file=sys.stderr)

    # Apply configuration to root logger
    root_logger.setLevel(log_level)
    for handler_to_add in handlers_list:
        root_logger.addHandler(handler_to_add)

    # Set levels for noisy libraries
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("websockets.server").setLevel(logging.ERROR) # Common noisy library
    logging.getLogger("websockets.protocol").setLevel(logging.ERROR)
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING) # Pillow can be verbose

    logging.info(f"Logging initialized. Level: {logging.getLevelName(log_level)}. File: {log_file_path_str or 'Console only'}")

def _load_browser_profiles_from_yaml(file_path: Path) -> List[BrowserProfile]:
    """Loads BrowserProfile objects from a YAML file."""
    # This function is used by APA to identify its golden_profile_object.
    # StealthBrowserManager loads profiles independently based on its own config path.
    logger_profile_load = logging.getLogger("ProfileLoaderForAPA") # Specific logger
    profiles_data_dict = _load_yaml_config(file_path) # Use the robust YAML loader

    loaded_browser_profiles: List[BrowserProfile] = []
    if not profiles_data_dict or not isinstance(profiles_data_dict.get("browser_profiles"), list):
        logger_profile_load.warning(f"APA ProfileLoad: No 'browser_profiles' list found in '{file_path}', or file is empty/malformed. Returning empty list.")
        return []

    for idx, profile_definition_dict in enumerate(profiles_data_dict["browser_profiles"]):
        if not isinstance(profile_definition_dict, dict):
            logger_profile_load.warning(f"APA ProfileLoad: Skipping invalid profile entry #{idx+1} (not a dictionary) in '{file_path}'.")
            continue
        try:
            # Ensure BrowserProfile is defined and imported correctly where this is called
            # For main.py, it's imported from core.browser_manager
            loaded_browser_profiles.append(BrowserProfile(**profile_definition_dict))
        except TypeError as te: # Catches missing/unexpected fields for BrowserProfile dataclass
            logger_profile_load.error(f"APA ProfileLoad: TypeError creating BrowserProfile for '{profile_definition_dict.get('name', f'Unknown Profile #{idx+1}')}' from '{file_path}': {te}. Ensure all required fields are present and types match.", exc_info=True)
        except Exception as e_prof_load: # Catch other errors
            logger_profile_load.error(f"APA ProfileLoad: Unexpected error processing profile '{profile_definition_dict.get('name', f'Unknown Profile #{idx+1}')}' from '{file_path}': {e_prof_load}", exc_info=True)

    logger_profile_load.info(f"APA ProfileLoad: Successfully loaded {len(loaded_browser_profiles)} profiles from '{file_path}' for APA's internal logic (e.g., golden profile identification).")
    return loaded_browser_profiles

# --- GUI Integration Functions ---
def load_app_config_for_gui(config_path: Path = CONFIG_FILE) -> Dict[str, Any]:
    """Loads the main application configuration, typically for the GUI."""
    return _load_yaml_config(config_path)

async def main_loop_for_gui(config_data: Dict[str, Any], stop_event: asyncio.Event,
                            gui_threading_q: "threading_queue.Queue"):
    """
    Asynchronous main loop adapted for GUI integration.
    Uses an asyncio.Queue to bridge messages to the GUI's threading.Queue.
    """
    async_gui_q: asyncio.Queue[Tuple[str, Any]] = asyncio.Queue() # Queue for async domain
    gui_bridge_logger = logging.getLogger("GUIMessageBridge")

    async def message_bridge_task_fn():
        """Bridges messages from async_gui_q to gui_threading_q."""
        gui_bridge_logger.info("GUI message bridge task started.")
        stop_event_is_set = False
        while not stop_event_is_set:
            try:
                # Wait for either a message or the stop_event
                get_message_task = asyncio.create_task(async_gui_q.get())
                wait_for_stop_task = asyncio.create_task(stop_event.wait())

                done, pending = await asyncio.wait(
                    [get_message_task, wait_for_stop_task],
                    return_when=asyncio.FIRST_COMPLETED
                )

                if wait_for_stop_task in done: # stop_event was triggered
                    stop_event_is_set = True
                    if not get_message_task.done(): get_message_task.cancel() # Cancel message getter if stop came first
                    gui_bridge_logger.info("Bridge task: Stop event received.")

                if get_message_task in done:
                    try:
                        message_item = await get_message_task
                        gui_threading_q.put(message_item) # Put to GUI's thread-safe queue
                        async_gui_q.task_done()
                    except asyncio.CancelledError: # Can happen if stop_event triggered while waiting
                        gui_bridge_logger.debug("Bridge task: Message get cancelled.")
                        pass # Expected if stop_event came first

                # Cancel any pending task (the one that didn't complete first)
                for task_to_cancel in pending:
                    task_to_cancel.cancel()
                    try: await task_to_cancel # Await cancellation
                    except asyncio.CancelledError: pass

            except asyncio.CancelledError: # If bridge_task itself is cancelled
                stop_event_is_set = True
                gui_bridge_logger.info("GUI message bridge task was cancelled externally.")
                break
            except Exception as e_bridge: # Catch other errors in bridge loop
                gui_bridge_logger.error(f"GUI message bridge error: {e_bridge}", exc_info=True)
                await asyncio.sleep(0.1) # Avoid rapid looping on error

        # Process any remaining messages in async_gui_q after stop_event
        gui_bridge_logger.info("Bridge task: Processing any final messages from async queue...")
        while not async_gui_q.empty():
            try:
                final_item = async_gui_q.get_nowait()
                gui_threading_q.put(final_item)
                async_gui_q.task_done()
            except asyncio.QueueEmpty:
                break # Should not happen due to check
            except Exception as e_final_q:
                gui_bridge_logger.error(f"Error processing final queue item: {e_final_q}")
        gui_bridge_logger.info("GUI message bridge task stopped.")

    # Start the bridge task
    gui_message_bridge_task = asyncio.create_task(message_bridge_task_fn(), name="GuiMessageBridgeTask")

    try:
        # Run the main application logic, passing the async_gui_q for its messages
        await _async_main_refactored(config_data, gui_q=async_gui_q, stop_event_from_caller=stop_event)
    except Exception as e_main_loop_gui: # Catch errors from the main app logic
        gui_bridge_logger.critical(f"CRITICAL error in main_loop_for_gui (from _async_main_refactored): {e_main_loop_gui}", exc_info=True)
        # Try to send a final critical error to the GUI
        try:
            gui_threading_q.put(("log", (f"FATAL APPLICATION CORE ERROR: {str(e_main_loop_gui)[:90]}", "CRITICAL")))
        except Exception: pass # Ignore if queue itself is problematic
    finally:
        gui_bridge_logger.info("main_loop_for_gui 'finally' block: Ensuring bridge task is stopped.")
        if not stop_event.is_set(): # Ensure stop_event is set if main logic exits unexpectedly
            stop_event.set()
            gui_bridge_logger.debug("Stop event explicitly set in main_loop_for_gui 'finally'.")

        # Wait for the bridge task to finish processing and exit
        if gui_message_bridge_task and not gui_message_bridge_task.done():
            try:
                await asyncio.wait_for(gui_message_bridge_task, timeout=5.0) # Give bridge some time to flush
            except asyncio.TimeoutError:
                gui_bridge_logger.warning("Timeout waiting for GUI message bridge task to complete. Cancelling.")
                gui_message_bridge_task.cancel()
                try: await gui_message_bridge_task
                except asyncio.CancelledError: pass # Expected
            except Exception as e_bridge_await:
                 gui_bridge_logger.error(f"Error awaiting bridge task completion: {e_bridge_await}")
        gui_bridge_logger.info("main_loop_for_gui has finished.")

# --- CLI Signal Handling and Main Execution ---
def cli_signal_handler(sig, frame):
    """Handles SIGINT/SIGTERM for graceful shutdown in CLI mode."""
    global _stop_event_for_signal # Use the global stop event
    signal_name_str = getattr(signal.Signals, sig.name, f"Signal {sig}") # Get signal name if possible
    logging.getLogger("SignalHandler").warning(f"Signal {signal_name_str} received. Initiating graceful shutdown...")

    if _stop_event_for_signal:
        if not _stop_event_for_signal.is_set():
            _stop_event_for_signal.set()
            logging.getLogger("SignalHandler").info("Global stop event has been set by signal handler.")
        else: # Second interrupt
            logging.getLogger("SignalHandler").critical("Second interrupt signal received. Forcing exit immediately.")
            os._exit(1) # Force exit
    else:
        logging.getLogger("SignalHandler").critical("Global stop event not initialized for signal handler. Forcing exit immediately.")
        os._exit(1) # Force exit

async def async_cli_mode_operations(args: argparse.Namespace, config_data: Dict[str, Any], p_instance: Playwright):
    """Handles CLI-specific operations like warm-up or stealth testing."""
    cli_mode_logger = logging.getLogger("CLIModeOps")
    if args.warm_profile:
        start_url = args.start_url or config_data.get('app_settings', {}).get('warmup_default_start_url', 'https://www.google.com')
        cli_mode_logger.info(f"Running WARM-UP for profile: '{args.warm_profile}' on URL: '{start_url}'")
        await async_warm_profile_session(args.warm_profile, start_url, config_data, p_instance)
    elif args.test_stealth:
        cli_mode_logger.info(f"Running STEALTH TEST for profile: '{args.test_stealth}' on URL: '{args.test_url}'")
        await async_test_stealth_session(args.test_stealth, args.test_url, config_data, p_instance)

async def async_warm_profile_session(profile_name_to_warm: str, start_url: str, config_data: Dict[str, Any], p_instance: Playwright):
    warm_logger = logging.getLogger(f"Warmup.{profile_name_to_warm.replace(' ','_')[:20]}")
    warm_logger.info(f"WARMUP SESSION for profile '{profile_name_to_warm}', starting at URL '{start_url}'.")

    temp_bm_config = json.loads(json.dumps(config_data))
    temp_bm_config.setdefault('browser_launch_options', {})['headless'] = False
    if "args" not in temp_bm_config['browser_launch_options']: # Ensure args list exists
        temp_bm_config['browser_launch_options']['args'] = []
    if "--auto-open-devtools-for-tabs" not in temp_bm_config['browser_launch_options']['args']: # Optional: devtools
         temp_bm_config['browser_launch_options']['args'].append("--auto-open-devtools-for-tabs")


    bm_for_warmup = StealthBrowserManager(
        config=temp_bm_config,
        playwright_instance=p_instance,
        use_only_profile_name=profile_name_to_warm
    )
    if not bm_for_warmup.profiles or bm_for_warmup.profiles[0].name != profile_name_to_warm:
        warm_logger.error(f"Failed to configure BM for warmup to use ONLY profile '{profile_name_to_warm}'. Aborting warmup.")
        return

    await bm_for_warmup.start_manager()
    persistent_ctx = None # Initialize
    try:
        profile_object_to_warm = bm_for_warmup.profiles[0]
        persistent_ctx = await bm_for_warmup.get_persistent_context_for_profile(profile_object_to_warm)

        if not persistent_ctx:
            warm_logger.error(f"Failed to get persistent context for profile '{profile_name_to_warm}'. Warmup aborted.")
            return

        page = await persistent_ctx.new_page()
        warm_logger.info(f"Navigating to {start_url} for manual interaction...")
        await page.goto(start_url, wait_until="domcontentloaded", timeout=60000)
        warm_logger.info(f"Page loaded: {page.url}. Please interact with the browser (login, accept cookies, etc.). Close the browser window OR stop this script (Ctrl+C) when finished warming up.")

        # More reliable way to wait for persistent context closure
        context_closed_event = asyncio.Event()
        def handle_context_close():
            warm_logger.info(f"Persistent context for '{profile_name_to_warm}' has been closed.")
            if not context_closed_event.is_set():
                context_closed_event.set()

        persistent_ctx.on("close", handle_context_close)

        # Keep the script alive while the user interacts.
        # The user closing the window will trigger the "close" event on the context.
        try:
            await asyncio.wait_for(context_closed_event.wait(), timeout=3 * 3600) # 3 hour timeout
            warm_logger.info(f"Warmup session for '{profile_name_to_warm}' ended (context closed by user action).")
        except asyncio.TimeoutError:
            warm_logger.warning(f"Warmup session for '{profile_name_to_warm}' timed out (3 hours). Please ensure you close the browser window.")
        except asyncio.CancelledError: # If main script is cancelled (e.g. Ctrl+C)
            warm_logger.info(f"Warmup session for '{profile_name_to_warm}' interrupted by script cancellation.")
            # Ensure context is closed if script is cancelled
            if persistent_ctx and not context_closed_event.is_set(): # Check if not already closed
                try:
                    await persistent_ctx.close()
                except Exception as e_close_cancel:
                    warm_logger.debug(f"Error closing persistent context during script cancellation: {e_close_cancel}")


    except Exception as e_warm:
        warm_logger.error(f"Error during warmup session for profile '{profile_name_to_warm}': {e_warm}", exc_info=True)
    finally:
        # stop_manager will try to close what's in _persistent_browsers (which are contexts)
        await bm_for_warmup.stop_manager()
        warm_logger.info(f"Warmup StealthBrowserManager for '{profile_name_to_warm}' stopped.")

    # (This duplicated except/finally block is removed; the correct one is already present above.)

async def async_test_stealth_session(profile_name_to_test: str, test_url: str, config_data: Dict[str, Any], p_instance: Playwright):
    """Tests stealth for a specific profile using a temporary StealthBrowserManager."""
    test_logger = logging.getLogger(f"StealthTest.{profile_name_to_test.replace(' ','_')[:20]}")
    test_logger.info(f"STEALTH TEST SESSION for profile '{profile_name_to_test}', navigating to URL '{test_url}'.")

    temp_bm_config = json.loads(json.dumps(config_data))
    temp_bm_config.setdefault('browser_launch_options', {})['headless'] = False # Non-headless for observation

    bm_for_test = StealthBrowserManager(
        config=temp_bm_config,
        playwright_instance=p_instance,
        use_only_profile_name=profile_name_to_test
    )
    if not bm_for_test.profiles or bm_for_test.profiles[0].name != profile_name_to_test:
        test_logger.error(f"Failed to configure BM for stealth test to use ONLY profile '{profile_name_to_test}'. Aborting.")
        return

    await bm_for_test.start_manager()
    try:
        # For stealth testing, a regular pooled context is fine, as we are not testing persistence here,
        # but the fingerprint applied by the profile and stealth_init.js.
        async with bm_for_test.get_context() as (ctx, profile_used):
            # profile_used should be the one we specified due to use_only_profile_name
            if profile_used.name != profile_name_to_test:
                 test_logger.warning(f"BM for test provided profile '{profile_used.name}' though '{profile_name_to_test}' was requested. Proceeding with '{profile_used.name}'.")

            async with bm_for_test.get_page_from_context(ctx, url=test_url) as page: # Use built-in goto
                test_logger.info(f"Page loaded: {page.url}. Current title: '{await page.title()}'. Observe browser fingerprint and behavior. Close browser window to end test.")
                if page.context.browser and page.context.browser.is_connected():
                    await page.context.browser.wait_for_event("disconnected", timeout=3 * 3600 * 1000)
                    test_logger.info(f"Browser for stealth test of '{profile_name_to_test}' closed.")
                else:
                    test_logger.warning(f"Browser for test of '{profile_name_to_test}' was not connected or already closed.")
    except Exception as e_test:
        test_logger.error(f"Error during stealth test for profile '{profile_name_to_test}': {e_test}", exc_info=True)
    finally:
        await bm_for_test.stop_manager()
        test_logger.info(f"Stealth test StealthBrowserManager for '{profile_name_to_test}' stopped.")

def cli_main() -> None:
    """Main entry point for CLI operations."""
    parser = argparse.ArgumentParser(description="Advanced Ticket Monitor Bot (CLI Mode)")
    parser.add_argument("--warm-profile", type=str, help="Name of the browser profile to warm-up (must exist in browser_profiles.yaml).")
    parser.add_argument("--start-url", type=str, help="Start URL for the warm-up session. Defaults to a common site if not provided.")
    parser.add_argument("--test-stealth", type=str, help="Name of the browser profile for stealth testing.")
    parser.add_argument("--test-url", type=str, default="https://infoscan.io/", help="URL to navigate to for stealth testing (default: infoscan.io).")
    # Add other CLI arguments as needed

    # Filter out --gui if present, as it's handled before calling cli_main
    cli_args_list = [arg for arg in sys.argv[1:] if arg != '--gui']
    args = parser.parse_args(cli_args_list)

    # Load main configuration first to set up logging properly
    config = _load_yaml_config(CONFIG_FILE)
    if not config: # If config loading failed
        # Use print for this very early error as logging might not be up
        print(f"CRITICAL: Main configuration file '{CONFIG_FILE}' failed to load or is empty. Cannot continue.", file=sys.stderr)
        sys.exit(1)

    # Initialize logging based on the loaded configuration
    log_settings = config.get('app_settings', {}).get('logging', config.get('logging', {})) # Check both locations
    _init_logging(
        level_str=log_settings.get("level", "INFO"), # Default to INFO if not specified
        log_file_path_str=log_settings.get("log_file_path", "logs/ticket_bot_main.log") # Consistent name
    )

    # Handle CLI-specific modes (warm-up, stealth test) before starting main monitoring
    if args.warm_profile or args.test_stealth:
        async def run_selected_cli_mode():
            async with async_playwright() as playwright_instance: # Manage Playwright lifecycle for these modes
                await async_cli_mode_operations(args, config, playwright_instance)
        try:
            asyncio.run(run_selected_cli_mode())
        except Exception as e_cli_op_error:
            logging.critical(f"Error during CLI mode operation ('{args.warm_profile or args.test_stealth}'): {e_cli_op_error}", exc_info=True)
            sys.exit(1) # Exit after the CLI operation
        return # Important: Exit after CLI mode completes, don't fall through to main monitoring

    # --- Main Monitoring Mode ---
    logging.info("Starting Ticket Monitor Bot in main monitoring mode (CLI)...")
    global _stop_event_for_signal # Ensure the global event is used by the signal handler
    cli_mode_stop_event = asyncio.Event()
    _stop_event_for_signal = cli_mode_stop_event # Assign to the global var for signal handler

    # Setup signal handlers for graceful shutdown
    original_sigint_handler = signal.signal(signal.SIGINT, cli_signal_handler)
    original_sigterm_handler = signal.signal(signal.SIGTERM, cli_signal_handler)

    try:
        # Run the main asynchronous application logic
        asyncio.run(_async_main_refactored(config_data=config, stop_event_from_caller=cli_mode_stop_event))
    except KeyboardInterrupt: # This should ideally be handled by the signal setting the event
        logging.info("CLI Main: KeyboardInterrupt received. Stop event should already be set by handler.")
    except SystemExit as e_sysexit: # e.g., from sys.exit()
        logging.info(f"CLI Main: SystemExit caught with code {e_sysexit.code}.")
    except Exception as e_cli_run_main: # Catch any other unhandled errors from _async_main_refactored
        logging.critical(f"CLI Main: Unhandled CRITICAL error during main execution: {e_cli_run_main}", exc_info=True)
        sys.exit(1) # Exit with error status
    finally:
        logging.info("CLI Main 'finally' block: Restoring original signal handlers and ensuring shutdown processes.")
        # Restore original signal handlers
        signal.signal(signal.SIGINT, original_sigint_handler)
        signal.signal(signal.SIGTERM, original_sigterm_handler)

        # Ensure the stop event is set if it wasn't already (e.g., if asyncio.run completed without interrupt)
        if not cli_mode_stop_event.is_set():
            cli_mode_stop_event.set()
            logging.debug("CLI Main: Stop event explicitly set in 'finally' to ensure cleanup.")
        logging.info("CLI application shutdown process has finished.")

if __name__ == "__main__":
    # Initial, very basic logging config for messages before _init_logging is called.
    # _init_logging will then reconfigure it properly based on config.yaml.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-7s] %(name)-20s :: %(message)s (PRE-CONFIG)",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True # Override any existing basicConfig from imports
    )

    if "--gui" in sys.argv:
        logging.info("Argument --gui detected. Attempting to start GUI mode...")
        try:
            # Assuming gui.py contains start_gui() and handles its own specific setup
            from gui import start_gui
            start_gui() # This function should handle its own config loading and asyncio loop management
        except ImportError as e_gui_module_import:
            logging.critical(f"GUI components (gui.py) could not be imported: {e_gui_module_import}. GUI mode is not available.", exc_info=True)
            sys.exit(1)
        except Exception as e_gui_init_error:
            logging.critical(f"An unexpected error occurred while trying to start the GUI: {e_gui_init_error}", exc_info=True)
            sys.exit(1)
    else:
        # Proceed with CLI mode
        cli_main()