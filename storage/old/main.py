# src/main.py - main.py v0.8a
from __future__ import annotations

import asyncio
import logging
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
# import hashlib # Not directly used in this refactored version unless TicketHit needs specific hashing
import json
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum

from dotenv import load_dotenv 
load_dotenv() 

import yaml

# Import V2 StealthBrowserManager and its BrowserProfile definition
from core.browser_manager import StealthBrowserManager, BrowserProfile

from playwright.async_api import (
    Error as PlaywrightError,
    Page as PlaywrightPage,
    BrowserContext as PlaywrightContext,
    async_playwright, # For managing Playwright lifecycle
    Playwright # For type hinting
)
from core.errors import BlockedError # Assuming this is still relevant

from platforms import ticketmaster
from platforms import vivaticket
from platforms import fansale

from utils.tls_fingerprint import patch_ssl_for_fingerprint_evasion
from utils.advanced_behavioral_simulation import simulate_advanced_human_behavior, BiometricProfile
# If your AdvancedBehavioralBiometrics class and other classes are also directly used:
# from utils.advanced_behavioral_simulation import (
#     simulate_advanced_human_behavior,
#     BiometricProfile,
#     AdvancedBehavioralBiometrics, # If you instantiate this directly in main
#     MouseDynamicsSimulator,       # If used directly
#     KeystrokeDynamicsSimulator,   # If used directly
#     AttentionModel                # If used directly
# )

if TYPE_CHECKING:
    import queue as threading_queue # For GUI bridge

CONFIG_FILE = Path("config/config.yaml")
# BROWSER_PROFILES_FILE path is now primarily read by V2 StealthBrowserManager via its config.
# APA might still load it to identify the golden profile if that logic remains.
# For simplicity, we can let APA get profile info from the config dict if needed.


# Global state for signal handling
_apa_instance_for_signal: Optional[AdvancedPurchaseArchitecture] = None
_stop_event_for_signal: Optional[asyncio.Event] = None
_active_monitoring_tasks_for_signal: List[asyncio.Task] = []

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
    max_retries: int = 3

    def __lt__(self, other: TicketHit) -> bool:
        if not isinstance(other, TicketHit):
            return NotImplemented
        return (self.priority.value, self.timestamp) < (other.priority.value, other.timestamp)

@dataclass
class CircuitBreakerState:
    failure_count: int = 0
    last_failure_time: float = 0.0
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    failure_threshold: int = 5 # Configurable
    recovery_timeout: float = 300.0  # 5 minutes, configurable

class AdvancedNotifier:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg_notifications = cfg.get("notifications", {})
        self.console_alerts: bool = bool(self.cfg_notifications.get("console_alerts", True))
        self.logger = logging.getLogger("AdvancedNotifier")
        self.alert_history: deque = deque(maxlen=100)
        self.rate_limiter: Dict[str, float] = {}

    async def alert(self, message: str, level: str = "CRITICAL", category: str = "general") -> None:
        current_time = time.time()
        rate_key = f"{category}_{level.lower()}"
        
        if current_time - self.rate_limiter.get(rate_key, 0) < self.cfg_notifications.get("alert_rate_limit_s", 10):
            self.logger.debug(f"Rate limit: Suppressed alert for {rate_key}: {message}")
            return
            
        self.rate_limiter[rate_key] = current_time
        self.alert_history.append((current_time, level, category, message))
        
        log_method = getattr(self.logger, level.lower(), self.logger.critical)
        if self.console_alerts:
            log_method(f"🚨 [{category.upper()}] {message}")

class FingerprintRandomizer:
    @staticmethod
    async def randomize_page_fingerprint(page: PlaywrightPage) -> None:
        try:
            await page.add_init_script("""
                const originalGetContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(type, ...args) {
                    const context = originalGetContext.apply(this, [type, ...args]);
                    if (type === '2d' && context) {
                        const originalFillText = context.fillText;
                        context.fillText = function(text, x, y, maxWidth) {
                            const noise = Math.random() * 0.1 - 0.05;
                            return originalFillText.call(this, text, x + noise, y + noise, maxWidth);
                        };
                    }
                    return context;
                };""")
            await page.add_init_script("""
                try {
                    const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === this.constructor.prototype.UNMASKED_VENDOR_WEBGL) { // 37445
                            const vendors = ['Intel Inc.', 'NVIDIA Corporation', 'AMD'];
                            return vendors[Math.floor(Math.random() * vendors.length)];
                        }
                        if (parameter === this.constructor.prototype.UNMASKED_RENDERER_WEBGL) { // 37446
                            const renderers = ['ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)', 'NVIDIA GeForce RTX 3090/PCIe/SSE2', 'AMD Radeon RX 6800 XT'];
                            return renderers[Math.floor(Math.random() * renderers.length)];
                        }
                        return originalGetParameter.call(this, parameter);
                    };
                } catch (e) { console.error('WebGL patch error:', e); }
            """)
            await page.add_init_script(f"""
                const timeOffset = {random.randint(-50, 50)};
                const originalPerformanceNow = performance.now;
                performance.now = () => originalPerformanceNow.call(performance) + timeOffset;
                const originalDateGetTime = Date.prototype.getTime;
                Date.prototype.getTime = function() {{ return originalDateGetTime.call(this) + timeOffset; }};
            """)
            logging.getLogger("FingerprintRandomizer").debug("Dynamic fingerprint patches applied.")
        except Exception as e:
            logging.getLogger("FingerprintRandomizer").error(f"Error applying dynamic fingerprint patches: {e}")

class PlatformStealthManager:
    @staticmethod
    async def apply_platform_specific_stealth(page: PlaywrightPage, platform: str):
        platform_lower = platform.lower()
        logger = logging.getLogger(f"PlatformStealth.{platform_lower}")
        logger.debug(f"Applying specific stealth for platform: {platform_lower} on page: {page.url}")
        try:
            if platform_lower == "fansale":
                await page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
            elif platform_lower == "ticketmaster":
                await page.add_init_script("window._cf_chl_opt = window._cf_chl_opt || {};")
            elif platform_lower == "vivaticket":
                await page.add_init_script("window.vivaticketInternalAnalytics = { reportBotScore: () => {} };")
            logger.debug(f"Platform-specific JS stealth applied for {platform_lower}.")
        except Exception as e:
            logger.error(f"Error applying platform-specific JS for {platform_lower}: {e}")

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

        self.monitoring_bm: Optional[StealthBrowserManager] = None
        self.purchase_bm: Optional[StealthBrowserManager] = None
        
        self.ticket_hit_queue: asyncio.PriorityQueue[TicketHit] = asyncio.PriorityQueue(
            maxsize=self.app_settings.get("ticket_hit_queue_size", 50)
        )
        self.purchase_workers: List[asyncio.Task] = []
        self.num_purchase_workers = self.app_settings.get("purchase_worker_count", 
            self.app_settings.get("browser_pool",{}).get("target_size",2) # Default to pool size
        )

        self.circuit_breakers: Dict[str, CircuitBreakerState] = defaultdict(lambda: CircuitBreakerState(
            failure_threshold=self.app_settings.get("circuit_breaker_failure_threshold", 5),
            recovery_timeout=self.app_settings.get("circuit_breaker_recovery_timeout_s", 300.0)
        ))
        
        self.performance_metrics: Dict[str, Any] = defaultdict(float)
        self.performance_metrics.update({
            "hits_processed": 0, "successful_purchases": 0, "failed_purchases": 0, "blocks_detected":0
        })

        self.golden_profile_object: Optional[BrowserProfile] = None
        self.is_purchase_system_ready: bool = False
        self._purchase_readiness_task: Optional[asyncio.Task] = None

        golden_profile_name: Optional[str] = self.app_settings.get("golden_profile_name_1")
        if golden_profile_name and all_available_profiles_for_apa_logic:
            self.golden_profile_object = next((p for p in all_available_profiles_for_apa_logic if p.name == golden_profile_name), None)
            if self.golden_profile_object:
                self.logger.info(f"Golden profile '{self.golden_profile_object.name}' identified for purchase system.")
            else:
                self.logger.error(f"Specified golden profile '{golden_profile_name}' not found. Purchase system may not function correctly.")
        elif not golden_profile_name:
            self.logger.warning("No 'golden_profile_name_1' configured. Automated purchases disabled.")
            
        self.target_platform_for_purchase_system = self._detect_target_platform()
        self._initialize_browser_managers(main_config_data)

    def _detect_target_platform(self) -> str:
        main_purchase_url = self.app_settings.get("main_purchase_url", "").lower()
        if "fansale" in main_purchase_url: return "FanSale"
        if "ticketmaster" in main_purchase_url: return "Ticketmaster"
        if "vivaticket" in main_purchase_url: return "Vivaticket"
        self.logger.warning(f"Could not determine target platform from main_purchase_url: '{main_purchase_url}'.")
        return "unknown"

    def _prepare_config_for_v2_manager(self, base_config: Dict[str, Any], is_purchase_manager: bool) -> Dict[str, Any]:
        manager_cfg = json.loads(json.dumps(base_config)) # Deep copy

        if is_purchase_manager:
            manager_cfg.setdefault('browser_launch_options', {})['headless'] = False
            purchase_proxy_enabled = self.app_settings.get("purchase_manager_uses_proxy", 
                                                           manager_cfg.get('proxy', {}).get('enabled', False))
            manager_cfg.setdefault('proxy', {})['enabled'] = purchase_proxy_enabled
            self.logger.info(f"Purchase Manager V2 proxy configured: {'ENABLED' if purchase_proxy_enabled else 'DISABLED'}")

            if self.golden_profile_object:
                self.logger.info(f"Purchase manager (V2) being configured. To ensure it uses '{self.golden_profile_object.name}', "
                                 f"its 'browser_profiles_yaml' path (in config dict paths: {manager_cfg.get('paths', {}).get('browser_profiles_yaml')}) "
                                 "should ideally point to a YAML file containing *only* this golden profile, "
                                 "or the V2 manager needs a way to filter/prioritize it.")
            else:
                self.logger.warning("Purchase manager (V2) configured without a specific golden profile target.")
        else: # Monitoring manager
            monitor_proxy_enabled = manager_cfg.get('proxy', {}).get('enabled', False)
            self.logger.info(f"Monitoring Manager V2 proxy configured: {'ENABLED' if monitor_proxy_enabled else 'DISABLED'}")
        return manager_cfg

    def _initialize_browser_managers(self, main_config_data: Dict[str, Any]):
        try:
            monitoring_dict_cfg = self._prepare_config_for_v2_manager(main_config_data, is_purchase_manager=False)
            self.monitoring_bm = StealthBrowserManager(config=monitoring_dict_cfg, playwright_instance=self.playwright)
            self.logger.info("Monitoring StealthBrowserManager (V2) instance created.")

            if self.golden_profile_object:
                purchase_dict_cfg = self._prepare_config_for_v2_manager(main_config_data, is_purchase_manager=True)
                self.purchase_bm = StealthBrowserManager(config=purchase_dict_cfg, playwright_instance=self.playwright)
                self.logger.info(f"Purchase StealthBrowserManager (V2) instance created for golden profile '{self.golden_profile_object.name}'.")
            else:
                self.logger.warning("Golden profile not identified. Purchase BM (V2) not initialized.")
                self.purchase_bm = None
        except Exception as e:
            self.logger.critical(f"FATAL ERROR initializing V2 BMs: {e}", exc_info=True)
            self.monitoring_bm = self.purchase_bm = None


    async def initialize_purchase_side_systems(self, gui_q: Optional[asyncio.Queue] = None) -> bool:
        if not self.purchase_bm or not self.golden_profile_object:
            self.logger.warning("Purchase BM or Golden Profile not available. Skipping purchase system init.")
            self.is_purchase_system_ready = False
            return False

        self.logger.info("Initializing APA purchase side systems...")
        try:
            await self._start_purchase_workers(gui_q)
            self._purchase_readiness_task = asyncio.create_task(
                self._maintain_purchase_readiness_loop(gui_q=gui_q),
                name="PurchaseReadinessCheckLoop"
            )
            self.logger.info("Purchase readiness check loop started.")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing APA purchase side systems: {e}", exc_info=True)
            self.is_purchase_system_ready = False
            return False

    async def _start_purchase_workers(self, gui_q: Optional[asyncio.Queue] = None):
        if not self.purchase_bm:
            self.logger.warning("Purchase BM not initialized, cannot start purchase workers.")
            return

        self.purchase_workers.clear()
        for i in range(self.num_purchase_workers):
            worker_task_name = f"PurchaseWorker-{i}"
            worker = asyncio.create_task(
                self._purchase_worker(worker_id=i, gui_q=gui_q), name=worker_task_name
            )
            self.purchase_workers.append(worker)
        self.logger.info(f"Started {len(self.purchase_workers)} purchase worker(s).")

    async def _verify_authentication_on_page(self, page: PlaywrightPage, platform_to_check: str) -> bool:
        effective_platform = platform_to_check.lower()
        if effective_platform == "unknown" and self.target_platform_for_purchase_system != "unknown":
            effective_platform = self.target_platform_for_purchase_system.lower()
        
        self.logger.debug(f"Auth check for platform '{effective_platform}' on page {page.url[:80]}")
        if page.is_closed():
            self.logger.warning(f"Auth check: Page closed. Assuming not authenticated.")
            return False

        auth_selectors = {
            "fansale": "a[href*='myfansale'], a:has-text('Mio account'), a[data-qa='UserManuMyFanSALE'], div.is-logged-in",
            "ticketmaster": "button[data-testid='user-menu-button'], a[href*='account/overview'], button[aria-label*='Account'], div[data-testid='desktop-user-button'], button#profile-menu-trigger-button, a[href*='member'], [data-tm-icon='person']",
            "vivaticket": "a[href*='logout'], .user-name-display, div.userBoxLogged, a[href*='myvivaticket'], .is-logged-in"
        }
        check_timeout = self.app_settings.get("auth_check_selector_timeout_ms", 7000)

        if effective_platform in auth_selectors:
            try:
                for selector in auth_selectors[effective_platform].split(','):
                    trimmed_selector = selector.strip()
                    if not trimmed_selector: continue
                    if await page.locator(trimmed_selector).first.is_visible(timeout=check_timeout):
                        self.logger.info(f"Auth check PASSED for '{effective_platform}' (selector: '{trimmed_selector}' visible).")
                        return True
                self.logger.warning(f"Auth check FAILED for '{effective_platform}' (no login selectors visible).")
                return False
            except PlaywrightError as e_auth_check:
                self.logger.info(f"Auth check for '{effective_platform}' likely FAILED (selector not found/timeout: {str(e_auth_check)[:100]}).")
                return False
            except Exception as e:
                self.logger.error(f"Unexpected error during auth check for '{effective_platform}': {e}", exc_info=True)
                return False
        else:
            self.logger.debug(f"No specific auth check selectors for '{effective_platform}'. Assuming authenticated.")
            return True

    async def _maintain_purchase_readiness_loop(self, gui_q: Optional[asyncio.Queue] = None):
        if not self.purchase_bm or not self.golden_profile_object:
            self.logger.error("ReadinessLoop: Purchase BM or Golden Profile not available. Loop cannot run.")
            self.is_purchase_system_ready = False
            return

        await asyncio.sleep(random.uniform(5, 15)) # Stagger initial check
        readiness_check_interval_s = self.app_settings.get("purchase_readiness_interval_s", 60.0)
        main_purchase_url = self.app_settings.get("main_purchase_url")
        if not main_purchase_url:
            self.logger.warning("ReadinessLoop: 'main_purchase_url' not set. Using fallback.")
            main_purchase_url = f"https://www.{self.target_platform_for_purchase_system.lower()}.com"


        self.logger.info(f"Purchase Readiness Loop started. Interval: {readiness_check_interval_s}s.")
        while not self._stop_event.is_set():
            current_auth_status = False
            profile_name_used = "N/A"
            try:
                self.logger.debug(f"ReadinessLoop: Performing auth check for golden profile '{self.golden_profile_object.name}'.")
                async with self.purchase_bm.get_context() as (ctx, prof_used):
                    profile_name_used = prof_used.name
                    if prof_used.name != self.golden_profile_object.name:
                        self.logger.critical(f"ReadinessLoop: CRITICAL MISCONFIGURATION! Purchase BM yielded '{prof_used.name}' NOT golden profile '{self.golden_profile_object.name}'.")
                        self.is_purchase_system_ready = False
                        await asyncio.sleep(readiness_check_interval_s * 2)
                        continue
                    async with self.purchase_bm.get_page_from_context(ctx, url=main_purchase_url) as pge:
                        current_auth_status = await self._verify_authentication_on_page(pge, self.target_platform_for_purchase_system)
                
                if current_auth_status:
                    if not self.is_purchase_system_ready:
                        self.logger.info(f"ReadinessLoop: Golden profile '{self.golden_profile_object.name}' NOW AUTHENTICATED.")
                        if gui_q: await gui_q.put(("log", (f"PURCHASE SYSTEM READY ({self.golden_profile_object.name})", "INFO")))
                    self.is_purchase_system_ready = True
                else:
                    if self.is_purchase_system_ready:
                        self.logger.warning(f"ReadinessLoop: Golden profile '{self.golden_profile_object.name}' NO LONGER AUTHENTICATED.")
                        await self.notifier.alert(f"GOLDEN PROFILE '{self.golden_profile_object.name}' SESSION EXPIRED!", level="ERROR", category="purchase_auth")
                        if gui_q: await gui_q.put(("log", (f"PURCHASE SYSTEM NOT READY - {self.golden_profile_object.name} LOGGED OUT!", "ERROR")))
                    else:
                        self.logger.warning(f"ReadinessLoop: Golden profile '{self.golden_profile_object.name}' REMAINS UNAUTHENTICATED.")
                    self.is_purchase_system_ready = False
            except PlaywrightError as e_pw:
                self.logger.error(f"ReadinessLoop: Playwright error (Profile: {profile_name_used}): {e_pw}")
                self.is_purchase_system_ready = False
            except Exception as e_gen:
                self.logger.error(f"ReadinessLoop: Unexpected error (Profile: {profile_name_used}): {e_gen}", exc_info=True)
                self.is_purchase_system_ready = False
            
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=readiness_check_interval_s)
            except asyncio.TimeoutError: continue
            except asyncio.CancelledError: break
        self.logger.info("Purchase Readiness Loop stopped.")
        self.is_purchase_system_ready = False

    async def _purchase_worker(self, worker_id: int, gui_q: Optional[asyncio.Queue] = None):
        worker_logger = logging.getLogger(f"PurchaseWorker-{worker_id}")
        worker_logger.info(f"Worker {worker_id} started.")
        hit: Optional[TicketHit] = None
        while not self._stop_event.is_set():
            try:
                hit = await asyncio.wait_for(self.ticket_hit_queue.get(), timeout=1.0)
                worker_logger.info(f"Worker {worker_id}: Picked {hit.priority.name} hit for '{hit.event_name}'.")
                start_time = time.monotonic()
                success = await self._execute_ultra_fast_purchase(hit, worker_id, gui_q)
                proc_time_ms = (time.monotonic() - start_time) * 1000

                self.performance_metrics["hits_processed"] += 1
                if success:
                    self.performance_metrics["successful_purchases"] += 1
                    worker_logger.critical(f"W-{worker_id}: ✅ PURCHASE SUCCEEDED for '{hit.event_name}' in {proc_time_ms:.0f}ms.")
                else:
                    self.performance_metrics["failed_purchases"] += 1
                    worker_logger.error(f"W-{worker_id}: ❌ PURCHASE FAILED for '{hit.event_name}' in {proc_time_ms:.0f}ms.")
                
                total_hits = self.performance_metrics["hits_processed"]
                if total_hits > 0:
                    current_avg_ms = self.performance_metrics.get("average_response_time_ms", 0.0)
                    self.performance_metrics["average_response_time_ms"] = (current_avg_ms * (total_hits - 1) + proc_time_ms) / total_hits
                self.ticket_hit_queue.task_done()
            except asyncio.TimeoutError: continue
            except asyncio.CancelledError:
                worker_logger.info(f"Worker {worker_id} cancelled.")
                if hit: self.ticket_hit_queue.put_nowait(hit)
                break
            except Exception as e:
                worker_logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
                if hit:
                    worker_logger.error(f"Error processing: {hit.event_name} ({hit.offer_url})")
                    if hit.retry_count < hit.max_retries:
                        hit.retry_count += 1
                        worker_logger.info(f"Requeuing '{hit.event_name}' (retry {hit.retry_count}).")
                        await self.ticket_hit_queue.put(hit)
                    else:
                        worker_logger.error(f"Max retries for '{hit.event_name}'. Discarding.")
                        self.performance_metrics["failed_purchases"] += 1
                await asyncio.sleep(random.uniform(1,3))
        worker_logger.info(f"Worker {worker_id} stopped.")

    async def _execute_ultra_fast_purchase(self, hit: TicketHit, worker_id: int, gui_q: Optional[asyncio.Queue] = None) -> bool:
        platform_lower = hit.platform.lower()
        worker_logger = logging.getLogger(f"PurchaseWorker-{worker_id}")

        if not self.is_purchase_system_ready:
            worker_logger.warning(f"Purchase system not ready. Skipping '{hit.event_name}'.")
            await self.notifier.alert(f"Purchase for '{hit.event_name}' skipped: System NOT READY.", level="WARNING", category="purchase_skip")
            return False
        if not self._check_circuit_breaker(platform_lower):
            worker_logger.warning(f"Circuit breaker for '{platform_lower}' OPEN. Skipping '{hit.event_name}'.")
            return False
        if not self.purchase_bm or not self.golden_profile_object:
            worker_logger.error(f"Purchase BM or Golden Profile not configured. Cannot buy '{hit.event_name}'.")
            return False

        page_for_purchase: Optional[PlaywrightPage] = None
        action_succeeded = False
        try:
            worker_logger.info(f"Attempting purchase: '{hit.event_name}' on '{hit.offer_url}' (Golden: {self.golden_profile_object.name}).")
            if gui_q: await gui_q.put(("log", (f"W-{worker_id} buying: {hit.event_name[:20]}...", "ACTION")))

            if platform_lower == "fansale" and platform_os.system() == "Darwin" and self.app_settings.get("enable_fansale_safari_handoff_macos", True):
                return await self._safari_handoff(hit, worker_id, gui_q)

            async with self.purchase_bm.get_context() as (ctx, prof_used):
                if prof_used.name != self.golden_profile_object.name:
                    worker_logger.critical(f"CRITICAL MISCONFIG! W-{worker_id} Purchase BM yielded '{prof_used.name}' NOT golden '{self.golden_profile_object.name}'. Aborted '{hit.event_name}'.")
                    await self.notifier.alert(f"CRITICAL: Purchase attempt with WRONG PROFILE ({prof_used.name}) for {hit.event_name}!", level="CRITICAL", category="purchase_error")
                    self._record_circuit_breaker_failure(platform_lower, is_critical=True)
                    return False
                async with self.purchase_bm.get_page_from_context(ctx, url=None) as pge:
                    page_for_purchase = pge
                    await FingerprintRandomizer.randomize_page_fingerprint(page_for_purchase)
                    await PlatformStealthManager.apply_platform_specific_stealth(page_for_purchase, hit.platform)
                    
                    nav_timeout = self.app_settings.get("purchase_navigation_timeout_ms", 20000)
                    nav_wait_until = self.app_settings.get("purchase_nav_wait_until", "domcontentloaded")
                    worker_logger.info(f"W-{worker_id} navigating to offer: {hit.offer_url}")
                    await page_for_purchase.goto(hit.offer_url, wait_until=nav_wait_until, timeout=nav_timeout)
                    action_succeeded = await self._platform_specific_purchase_action(page_for_purchase, hit, platform_lower, worker_id)
            
            if action_succeeded:
                self._record_circuit_breaker_success(platform_lower)
                await self.notifier.alert(f"Purchase for '{hit.event_name}' SUCCEEDED/HandedOff.", level="WARNING", category="purchase_success")
                if gui_q: await gui_q.put(("hit_success", (hit.event_name, hit.offer_url)))
            else:
                self._record_circuit_breaker_failure(platform_lower)
                await self.notifier.alert(f"Purchase for '{hit.event_name}' FAILED.", level="ERROR", category="purchase_failure")
                if gui_q: await gui_q.put(("hit_fail", (hit.event_name, "Action failed")))
            return action_succeeded
        except PlaywrightError as e_pw:
            worker_logger.error(f"W-{worker_id}: Playwright error buying '{hit.event_name}': {e_pw}")
            self._record_circuit_breaker_failure(platform_lower)
            if page_for_purchase and not page_for_purchase.is_closed() and self.app_settings.get("pause_on_purchase_error", True):
                try: await page_for_purchase.pause()
                except PlaywrightError: pass
            return False
        except Exception as e_gen:
            worker_logger.error(f"W-{worker_id}: Unexpected error buying '{hit.event_name}': {e_gen}", exc_info=True)
            self._record_circuit_breaker_failure(platform_lower)
            if page_for_purchase and not page_for_purchase.is_closed() and self.app_settings.get("pause_on_purchase_error", True):
                try: await page_for_purchase.pause()
                except PlaywrightError: pass
            return False
        finally:
            worker_logger.debug(f"Finished purchase attempt for '{hit.event_name}' by W-{worker_id}.")

    async def _safari_handoff(self, hit: TicketHit, worker_id: int, gui_q: Optional[asyncio.Queue] = None) -> bool:
        worker_logger = logging.getLogger(f"PurchaseWorker-{worker_id}")
        worker_logger.warning(f"W-{worker_id}: SAFARI HANDOFF for '{hit.event_name}' to {hit.offer_url}")
        try:
            await asyncio.create_subprocess_exec('open', '-a', 'Safari', hit.offer_url)
            if gui_q: await gui_q.put(("alert", (f"Safari Handoff (W-{worker_id})", f"{hit.event_name[:20]}...", hit.offer_url)))
            await self.notifier.alert(f"SAFARI HANDOFF for '{hit.event_name}'. Check Safari NOW!", category="purchase_handoff", level="CRITICAL")
            return True
        except Exception as e:
            worker_logger.error(f"W-{worker_id}: Safari handoff FAILED for '{hit.event_name}': {e}", exc_info=True)
            return False

    async def _platform_specific_purchase_action(self, page: PlaywrightPage, hit: TicketHit, platform_lower: str, worker_id: int) -> bool:
        action_logger = logging.getLogger(f"PurchaseAction.W{worker_id}.{platform_lower}")
        action_logger.info(f"Platform action for '{hit.event_name}' on {page.url[:70]}")
        try:
            if platform_lower == "ticketmaster":
                offer_id = hit.hit_data.get("offer_id")
                if offer_id and hasattr(ticketmaster, 'add_to_basket'):
                    action_logger.info(f"TM add_to_basket with offer_id '{offer_id}'.")
                    success, msg = await ticketmaster.add_to_basket(page.context, str(offer_id))
                    action_logger.info(f"TM add_to_basket result: {success}, Msg: {msg}")
                    return success
                else:
                    action_logger.warning(f"TM: 'offer_id' missing or 'add_to_basket' not found. Hit: {hit.hit_data}")
                    if not page.is_closed(): await page.pause()
                    return True 
            elif platform_lower == "vivaticket":
                action_logger.info("Vivaticket generic 'buy' click.")
                buy_selectors = "button[class*='buy'], a[href*='buy'], .ticket-buy-button, button:has-text('Acquista')"
                for selector in buy_selectors.split(','):
                    try:
                        await page.locator(selector.strip()).first.click(timeout=self.app_settings.get("vivaticket_click_timeout_ms", 7000))
                        action_logger.info(f"Clicked Vivaticket element '{selector.strip()}'.")
                        if self.app_settings.get("pause_after_vivaticket_click", True) and not page.is_closed(): await page.pause()
                        return True
                    except PlaywrightError: continue
                action_logger.warning("Vivaticket: No 'buy' button found/clickable. Pausing.")
                if not page.is_closed(): await page.pause()
                return True
            elif platform_lower == "fansale":
                action_logger.info("FanSale specific ticket listing click.")
                if hasattr(fansale, 'click_specific_ticket_listing_and_proceed'):
                    original_cfg = hit.hit_data.get('original_target_config', {})
                    success = await fansale.click_specific_ticket_listing_and_proceed(page, hit.hit_data, original_cfg)
                    action_logger.info(f"FanSale click_specific_ticket_listing_and_proceed result: {success}")
                    return success
                else:
                    action_logger.warning("FanSale: 'click_specific_ticket_listing_and_proceed' not found. Pausing.")
                    if not page.is_closed(): await page.pause()
                    return True
            else:
                action_logger.warning(f"No specific action for '{platform_lower}'. Pausing.")
                if not page.is_closed(): await page.pause()
                return True
        except PlaywrightError as e_pw_action:
            action_logger.error(f"Playwright error during action for '{hit.event_name}': {e_pw_action}")
            if not page.is_closed(): await page.pause()
            return False
        except Exception as e_action:
            action_logger.error(f"Unexpected error during action for '{hit.event_name}': {e_action}", exc_info=True)
            if not page.is_closed(): await page.pause()
            return False

    def _check_circuit_breaker(self, platform: str) -> bool:
        breaker = self.circuit_breakers[platform]
        current_time = time.time()
        if breaker.state == "OPEN":
            if current_time - breaker.last_failure_time > breaker.recovery_timeout:
                breaker.state = "HALF_OPEN"
                breaker.failure_count = 0
                self.logger.info(f"CB for '{platform}' to HALF_OPEN.")
                return True
            self.logger.debug(f"CB for '{platform}' is OPEN. Blocked.")
            return False
        return True

    def _record_circuit_breaker_success(self, platform: str):
        breaker = self.circuit_breakers[platform]
        if breaker.state == "HALF_OPEN":
            self.logger.info(f"CB for '{platform}' successful in HALF_OPEN. To CLOSED.")
        breaker.failure_count = 0
        breaker.state = "CLOSED"

    def _record_circuit_breaker_failure(self, platform: str, is_critical: bool = False):
        breaker = self.circuit_breakers[platform]
        breaker.failure_count += 1
        breaker.last_failure_time = time.time()
        if breaker.state == "HALF_OPEN" or breaker.failure_count >= breaker.failure_threshold or is_critical:
            if breaker.state != "OPEN":
                self.logger.warning(f"CB for '{platform}' OPENED. Fails: {breaker.failure_count}/{breaker.failure_threshold}. Critical: {is_critical}")
            breaker.state = "OPEN"
        else:
            self.logger.debug(f"CB for '{platform}' recorded fail. Count: {breaker.failure_count}/{breaker.failure_threshold}")

    async def add_ticket_hit(self, hit_data: Dict[str, Any], priority: PriorityLevel = PriorityLevel.HIGH):
        offer_url = hit_data.get("offer_url", hit_data.get("url"))
        if not offer_url:
            self.logger.error(f"Cannot add hit for '{hit_data.get('event_name', 'N/A')}' - missing 'offer_url' and 'url'.")
            return
        hit = TicketHit(
            platform=hit_data.get("platform", "unknown"),
            event_name=hit_data.get("event_name", "Unknown Event"),
            url=hit_data.get("url", offer_url),
            offer_url=offer_url,
            priority=priority,
            timestamp=time.time(),
            hit_data=hit_data
        )
        try:
            queue_put_timeout = self.app_settings.get("ticket_hit_queue_put_timeout_s", 2.0)
            await asyncio.wait_for(self.ticket_hit_queue.put(hit), timeout=queue_put_timeout)
            self.logger.info(f"Added {priority.name} hit to queue: '{hit.event_name}'. QSize: {self.ticket_hit_queue.qsize()}")
        except asyncio.TimeoutError:
            self.logger.error(f"HIT QUEUE PUT TIMEOUT! Dropping '{hit.event_name}'.")
            await self.notifier.alert(f"HIT QUEUE TIMEOUT for {hit.event_name}.", level="ERROR", category="queue_error")
        except asyncio.QueueFull:
            self.logger.error(f"HIT QUEUE FULL! Dropping '{hit.event_name}'.")
            await self.notifier.alert(f"HIT QUEUE FULL for {hit.event_name}.", level="ERROR", category="queue_error")

    async def shutdown(self):
        self.logger.info("Shutting down APA...")
        if not self._stop_event.is_set(): self._stop_event.set()

        if self._purchase_readiness_task and not self._purchase_readiness_task.done():
            self.logger.debug("Cancelling purchase readiness task...")
            self._purchase_readiness_task.cancel()
            try: await self._purchase_readiness_task
            except asyncio.CancelledError: self.logger.info("Purchase readiness task cancelled.")
            except Exception as e: self.logger.error(f"Error cancelling readiness task: {e}")
        self._purchase_readiness_task = None

        if self.purchase_workers:
            self.logger.debug(f"Cancelling {len(self.purchase_workers)} purchase worker(s)...")
            for worker in self.purchase_workers:
                if not worker.done(): worker.cancel()
            await asyncio.gather(*self.purchase_workers, return_exceptions=True)
            self.logger.info("All purchase workers stopped.")
        self.purchase_workers.clear()

        if self.purchase_bm:
            self.logger.info("Stopping Purchase BM (V2)...")
            await self.purchase_bm.stop_manager()
            self.purchase_bm = None
        if self.monitoring_bm:
            self.logger.info("Stopping Monitoring BM (V2)...")
            await self.monitoring_bm.stop_manager()
            self.monitoring_bm = None
        self.logger.info("APA shutdown complete.")

async def monitor_target_enhanced(
    name: str, checker: Callable, target_cfg: Dict[str, Any],
    bm: StealthBrowserManager, apa: AdvancedPurchaseArchitecture,
    cancel_evt: asyncio.Event, gui_q: Optional[asyncio.Queue] = None,
):
    log = logging.getLogger(f"Monitor.{name.replace(' ', '_')}") # Shortened logger name
    page_url_to_check = target_cfg.get("url")
    if not page_url_to_check:
        log.error(f"URL missing for '{name}'. Skipping."); return

    base_interval_s = float(target_cfg.get("interval_s", apa.app_settings.get("monitoring_interval_s", 60.0)))
    priority_multiplier = float(target_cfg.get("priority_multiplier", 1.0))
    effective_interval_s = base_interval_s / priority_multiplier if priority_multiplier > 0 else base_interval_s
    
    log.info(f"Monitoring '{name}' ({page_url_to_check[:60]}), Interval: ~{effective_interval_s:.1f}s")
    await asyncio.sleep(random.uniform(1.0, min(10.0, effective_interval_s / 5.0 if effective_interval_s > 5 else 1.0)))

    consecutive_failures = 0
    last_success_time = time.monotonic()

    while not cancel_evt.is_set():
        page_instance: Optional[PlaywrightPage] = None
        active_profile: Optional[BrowserProfile] = None
        try:
            async with bm.get_context() as (ctx, profile_used):
                active_profile = profile_used
                log.debug(f"[{name}] Round with Profile: {active_profile.name}")
                if gui_q: await gui_q.put(("status", (name, f"Prep (Prof: {active_profile.name[:12]})")))
                async with bm.get_page_from_context(ctx, url=None) as page:
                    page_instance = page
                    await FingerprintRandomizer.randomize_page_fingerprint(page)
                    current_platform = target_cfg.get("platform", "unknown")
                    await PlatformStealthManager.apply_platform_specific_stealth(page, current_platform)

                    if gui_q: await gui_q.put(("status", (name, f"Chk (Prof: {active_profile.name[:10]}) {page_url_to_check.split('/')[-1][:15]}...")))
                    nav_timeout = apa.app_settings.get("monitoring_navigation_timeout_ms", 30000)
                    nav_wait = apa.app_settings.get("monitoring_nav_wait_until", "domcontentloaded")
                    await page.goto(page_url_to_check, wait_until=nav_wait, timeout=nav_timeout)
                    
                    human_intensity = target_cfg.get("human_behavior_intensity", "medium") # Default to "medium" for the new script
                    if human_intensity != "none":
                        # --- Integration of new behavioral simulation ---
                        # Option A: Create a default BiometricProfile each time (simpler start)
                        # current_biometric_profile = BiometricProfile()
                        # Option B (Recommended): Load biometric parameters from your main BrowserProfile
                        # This assumes 'active_profile' is the BrowserProfile instance for the current monitoring iteration
                        biometric_params_from_config = {}
                        if active_profile and hasattr(active_profile, 'extra_js_props') and isinstance(active_profile.extra_js_props, dict):
                            biometric_params_from_config = active_profile.extra_js_props.get("biometric_profile_config", {})
                        else:
                            biometric_params_from_config = {}
                        current_biometric_profile = BiometricProfile(**biometric_params_from_config)
                        log.debug(f"[{name}] Applying advanced human behavior (Intensity: {human_intensity}) with BiometricProfile: {current_biometric_profile}")

                        await simulate_advanced_human_behavior(page, intensity=human_intensity, profile=current_biometric_profile)
                        # --- End of new behavioral simulation integration ---

                    
                    await _apa_enhanced_block_detection(page, name, target_cfg, apa.app_settings)
                    hits_data_list = await checker(page=page, profile=active_profile, target_cfg=target_cfg, bm=bm, gui_q=gui_q)

                    if hits_data_list:
                        log.critical(f"[{name}] HIT(S)! (Profile: {active_profile.name}) Count: {len(hits_data_list)}")
                        hit_priority_str = target_cfg.get("hit_priority", "HIGH").upper()
                        hit_priority = PriorityLevel[hit_priority_str] if hit_priority_str in PriorityLevel.__members__ else PriorityLevel.HIGH
                        for hit_detail in hits_data_list:
                            if not isinstance(hit_detail, dict): continue
                            hit_msg = hit_detail.get("message", f"Details: {str(hit_detail)[:70]}")
                            log.warning(f"[{name}] HIT DETAIL: {hit_msg}")
                            await apa.notifier.alert(f"HIT! {name} ({active_profile.name}): {hit_msg}", level="WARNING", category="ticket_hit")
                            if gui_q: await gui_q.put(("hit", (name, f"HIT! ({active_profile.name}): {hit_msg}", page.url)))
                            full_hit_info = {
                                "platform": current_platform, "url": page_url_to_check,
                                "event_name": name, "original_target_config": dict(target_cfg),
                                **hit_detail
                            }
                            await apa.add_ticket_hit(full_hit_info, priority=hit_priority)
                        
                        post_hit_delay_s = int(target_cfg.get("post_hit_delay_s", random.randint(75, 150)))
                        log.info(f"[{name}] Hit(s) processed. Target cooldown {post_hit_delay_s}s.")
                        try: await asyncio.wait_for(cancel_evt.wait(), timeout=float(post_hit_delay_s))
                        except asyncio.TimeoutError: pass
                        if cancel_evt.is_set(): break
                    else:
                        log.info(f"[{name}] No tickets (Profile {active_profile.name}).")
                        if gui_q: await gui_q.put(("status", (name, "No tickets.")))
                    consecutive_failures = 0
                    last_success_time = time.monotonic()
        except BlockedError as e_block:
            log.warning(f"[{name}] Blocked (Profile '{active_profile.name if active_profile else 'Unknown'}'): {e_block}.")
            apa.performance_metrics["blocks_detected"] +=1
            if gui_q: await gui_q.put(("blocked", (name, str(e_block), page_instance.url if page_instance else page_url_to_check )))
            consecutive_failures += 1
            backoff_base = float(apa.app_settings.get("block_backoff_base_s", 25))
            max_backoff = float(apa.app_settings.get("block_max_backoff_s", 500))
            cooldown_s = min(max_backoff, (2 ** consecutive_failures) * backoff_base + random.uniform(0, backoff_base/2))
            log.info(f"[{name}] Cooldown {cooldown_s:.1f}s after block.")
            if gui_q: await gui_q.put(("status", (name, f"Blocked! CD {cooldown_s:.0f}s")))
            try: await asyncio.wait_for(cancel_evt.wait(), timeout=cooldown_s)
            except asyncio.TimeoutError: pass
            continue
        except asyncio.CancelledError: log.info(f"[{name}] Task cancelled."); raise
        except PlaywrightError as e_pw:
            log.error(f"[{name}] PW Error (Profile {active_profile.name if active_profile else 'Unknown'}): {e_pw}")
            if gui_q: await gui_q.put(("error", (name, f"PW Error: {str(e_pw)[:45]}...", page_instance.url if page_instance else page_url_to_check )))
            consecutive_failures += 1; err_cd_s = min(250, consecutive_failures * random.uniform(40,65))
            log.info(f"[{name}] Cooldown {err_cd_s:.1f}s after PW error.")
            try: await asyncio.wait_for(cancel_evt.wait(), timeout=err_cd_s)
            except asyncio.TimeoutError: pass
            continue
        except Exception as e_gen:
            log.critical(f"[{name}] UNEXPECTED ERROR (Profile {active_profile.name if active_profile else 'Unknown'}): {e_gen}", exc_info=True)
            if gui_q: await gui_q.put(("error", (name, f"General Error: {str(e_gen)[:45]}...", page_instance.url if page_instance else page_url_to_check)))
            consecutive_failures += 1; gen_err_cd_s = min(400, consecutive_failures * random.uniform(55,80))
            log.warning(f"[{name}] Cooldown {gen_err_cd_s:.1f}s after general error.")
            try: await asyncio.wait_for(cancel_evt.wait(), timeout=gen_err_cd_s)
            except asyncio.TimeoutError: pass
            continue
        
        current_target_interval_s = effective_interval_s
        if consecutive_failures > apa.app_settings.get("consecutive_failure_threshold_for_interval_increase", 3):
            current_target_interval_s = min(current_target_interval_s * 1.5, apa.app_settings.get("max_monitoring_interval_s", 750))
        elif time.monotonic() - last_success_time < apa.app_settings.get("recent_success_window_s_for_interval_decrease", 250):
            current_target_interval_s = max(current_target_interval_s * 0.9, apa.app_settings.get("min_monitoring_interval_s", 15))
        
        wait_time_s = current_target_interval_s * random.uniform(0.85, 1.15)
        log.debug(f"[{name}] Next check in ~{wait_time_s:.1f}s.")
        if gui_q: await gui_q.put(("status", (name, f"Wait {wait_time_s:.0f}s")))
        try:
            await asyncio.wait_for(cancel_evt.wait(), timeout=wait_time_s)
        except asyncio.TimeoutError: pass
        except Exception as e_wait:
            log.error(f"[{name}] Error during interval wait: {e_wait}. Stopping if not cancelled.")
            if not cancel_evt.is_set(): break
    log.info(f"[{name}] Monitoring task stopped.")

async def _apa_enhanced_block_detection(page: PlaywrightPage, target_name: str, target_cfg: Dict[str, Any], app_settings: Dict[str, Any]):
    logger = logging.getLogger(f"BlockDetect.{target_name}")
    try:
        content_scan_timeout_ms = app_settings.get("block_detect_content_scan_timeout_ms", 1200)
        content_sample = ""
        try:
            content_sample = await asyncio.wait_for(
                page.evaluate("() => document.body ? document.body.innerText.toLowerCase().substring(0, 1200) : ''"),
                timeout=content_scan_timeout_ms / 1000.0
            )
        except asyncio.TimeoutError: logger.warning(f"[{target_name}] Timeout getting content for block detection.")
        except Exception: logger.warning(f"[{target_name}] Error getting content for block detection.")

        global_block_indicators = app_settings.get("global_block_page_indicators", ["access denied", "blocked"])
        target_specific_indicators = target_cfg.get("block_page_indicators", [])
        all_block_indicators = list(set(global_block_indicators + target_specific_indicators))
        if content_sample:
            for indicator in all_block_indicators:
                if indicator.lower() in content_sample:
                    logger.warning(f"[{target_name}] BLOCK (Content: '{indicator}') on {page.url[:60]}")
                    raise BlockedError(f"Block indicator '{indicator}' in content.")

        global_captcha_selectors = app_settings.get("global_captcha_selectors", ["iframe[title*='recaptcha'i]"])
        target_captcha_selectors = target_cfg.get("captcha_selectors", [])
        all_captcha_selectors = list(set(global_captcha_selectors + target_captcha_selectors))
        captcha_check_timeout_ms = app_settings.get("block_detect_captcha_timeout_ms", 800)
        for selector in all_captcha_selectors:
            try:
                if await page.locator(selector).first.is_visible(timeout=captcha_check_timeout_ms):
                    logger.warning(f"[{target_name}] CAPTCHA (Selector: '{selector}') on {page.url[:60]}")
                    raise BlockedError(f"CAPTCHA selector '{selector}' visible.")
            except PlaywrightError: continue
            except BlockedError: raise
            except Exception as e_sel: logger.debug(f"[{target_name}] Minor error checking captcha '{selector}': {e_sel}")
    except BlockedError: raise
    except Exception as e: logger.error(f"[{target_name}] Unexpected error in block detection: {e}", exc_info=True)

async def _async_main_refactored(config_data: Dict[str, Any], gui_q: Optional[asyncio.Queue] = None,
                                 stop_event_from_caller: Optional[asyncio.Event] = None) -> None:
    global _apa_instance_for_signal, _stop_event_for_signal, _active_monitoring_tasks_for_signal
    main_logger = logging.getLogger("AsyncMainRefactored")
    stop_event = stop_event_from_caller or asyncio.Event()
    _stop_event_for_signal = stop_event
    _active_monitoring_tasks_for_signal.clear()
    apa: Optional[AdvancedPurchaseArchitecture] = None

    try:
        main_logger.info("AsyncMainRefactored: Starting Playwright...")
        async with async_playwright() as p_instance:
            try:
                tls_key = config_data.get("app_settings", {}).get("tls_fingerprint_profile")
                if tls_key:
                    if patch_ssl_for_fingerprint_evasion(browser_profile_ja3_key=tls_key):
                        main_logger.info(f"TLS patch enabled for JA3: '{tls_key}'.")
                    else: main_logger.warning(f"TLS patch FAILED for '{tls_key}'.")
                else: main_logger.info("No 'tls_fingerprint_profile'; TLS not modified.")
            except Exception as e_tls: main_logger.error(f"Error TLS init: {e_tls}", exc_info=True)

            profiles_yaml_path_str = config_data.get('paths',{}).get('browser_profiles_yaml', str(CONFIG_FILE.parent / 'browser_profiles.yaml'))
            all_yaml_profiles = _load_browser_profiles_from_yaml(Path(profiles_yaml_path_str))
            if not all_yaml_profiles:
                main_logger.warning(f"No profiles from '{profiles_yaml_path_str}'. APA may use fallbacks or V2 manager's internal list.")

            main_logger.info("Initializing APA...")
            apa = AdvancedPurchaseArchitecture(
                main_config_data=config_data,
                all_available_profiles_for_apa_logic=all_yaml_profiles,
                stop_event=stop_event,
                playwright_instance=p_instance
            )
            _apa_instance_for_signal = apa

            if apa.monitoring_bm: await apa.monitoring_bm.start_manager(); main_logger.info("Monitoring BM (V2) started.")
            if apa.purchase_bm: await apa.purchase_bm.start_manager(); main_logger.info("Purchase BM (V2) started.")
            
            await apa.initialize_purchase_side_systems(gui_q=gui_q)

            monitoring_tasks_local: List[asyncio.Task] = []
            if apa.monitoring_bm:
                targets = config_data.get("targets", [])
                dispatch_checkers: Dict[str, Callable] = {
                    "Ticketmaster": ticketmaster.check_ticketmaster_event,
                    "FanSale": fansale.check_fansale_event,
                    "Vivaticket": vivaticket.check_vivaticket_event,
                }
                for idx, target_cfg in enumerate(targets):
                    if not target_cfg.get("enabled", False): continue
                    platform, checker_fn, url = target_cfg.get("platform"), dispatch_checkers.get(target_cfg.get("platform")), target_cfg.get("url")
                    if not (checker_fn and url and platform):
                        main_logger.error(f"Skipping invalid target #{idx+1} ('{target_cfg.get('event_name', 'N/A')}').")
                        continue
                    evt_name = target_cfg.get("event_name", f"{platform}_Evt_{idx+1}")
                    task_name = f"monitor_{evt_name.replace(' ','_').replace('/','-')}"
                    task = asyncio.create_task(monitor_target_enhanced(
                        name=evt_name, checker=checker_fn, target_cfg=target_cfg,
                        bm=apa.monitoring_bm, apa=apa, cancel_evt=stop_event, gui_q=gui_q
                    ), name=task_name)
                    monitoring_tasks_local.append(task)
                _active_monitoring_tasks_for_signal[:] = monitoring_tasks_local
            
            if not monitoring_tasks_local and not apa.purchase_workers:
                main_logger.warning("No active monitoring/purchase tasks. Idling.")
                await stop_event.wait()
            elif monitoring_tasks_local:
                main_logger.info(f"{len(monitoring_tasks_local)} monitoring task(s) started.")
                await stop_event.wait()
            else: # Only purchase workers
                main_logger.info("Only purchase workers active. Waiting for stop.")
                await stop_event.wait()
            main_logger.info("Stop event received. Shutting down...")
    except RuntimeError as e_rt:
        main_logger.critical(f"FATAL RUNTIME ERROR in Main: {e_rt}", exc_info=True)
        if gui_q: await gui_q.put(("log", (f"FATAL CORE ERROR: {str(e_rt)[:90]}", "CRITICAL")))
        if not stop_event.is_set(): stop_event.set()
    except Exception as e_main:
        main_logger.critical(f"Unhandled CRITICAL error in Main: {e_main}", exc_info=True)
        if gui_q: await gui_q.put(("log", (f"FATAL UNHANDLED ERROR: {str(e_main)[:90]}", "CRITICAL")))
        if not stop_event.is_set(): stop_event.set()
    finally:
        main_logger.info("Main 'finally': Cleaning up...")
        if not stop_event.is_set(): stop_event.set(); main_logger.debug("Stop_event set in finally.")

        if _active_monitoring_tasks_for_signal:
            main_logger.info(f"Cancelling {len(_active_monitoring_tasks_for_signal)} monitoring task(s)...")
            for task in _active_monitoring_tasks_for_signal:
                if not task.done(): task.cancel()
            await asyncio.gather(*_active_monitoring_tasks_for_signal, return_exceptions=True)
            _active_monitoring_tasks_for_signal.clear()

        if apa: await apa.shutdown()
        if _apa_instance_for_signal is apa: _apa_instance_for_signal = None
        main_logger.info("Main cleanup finished.")

def _load_yaml_config(file_path: Path) -> Dict[str, Any]:
    if not file_path.exists(): logging.warning(f"Config file {file_path} not found."); return {}
    try:
        with file_path.open("r", encoding="utf-8") as fh: data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}
    except Exception as e: logging.error(f"Error loading YAML {file_path}: {e}"); return {}

def _init_logging(level_str: str = "INFO", log_file: Optional[str] = None) -> None:
    level = getattr(logging, level_str.upper(), logging.INFO)
    root = logging.getLogger()
    for h in list(root.handlers): root.removeHandler(h); h.close()
    handlers: List[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    formatter = logging.Formatter("%(asctime)s [%(levelname)-7s] %(name)-28s :: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    if log_file:
        try:
            p = Path(log_file).resolve(); p.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(p, encoding='utf-8', mode='a'); fh.setFormatter(formatter)
            handlers.append(fh)
        except Exception as e: print(f"ERROR: Could not create log file {log_file}: {e}", file=sys.stderr)
    logging.basicConfig(level=level, handlers=handlers, force=True, format="%(asctime)s [%(levelname)-7s] %(name)-28s :: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)

def _load_browser_profiles_from_yaml(file_path: Path) -> List[BrowserProfile]:
    # This is primarily for APA to identify its golden_profile_object.
    # V2 StealthBrowserManager loads profiles independently based on its own config path.
    logger = logging.getLogger("ProfileLoaderForAPA")
    profiles_data = _load_yaml_config(file_path)
    loaded_profiles: List[BrowserProfile] = []
    if not profiles_data or not isinstance(profiles_data.get("browser_profiles"), list):
        logger.warning(f"APA ProfileLoad: No 'browser_profiles' list in {file_path} or file not found/empty.")
        return []
    for i, prof_dict in enumerate(profiles_data["browser_profiles"]):
        if not isinstance(prof_dict, dict): continue
        try: loaded_profiles.append(BrowserProfile(**prof_dict)) # Assumes BrowserProfile is defined elsewhere (e.g. core.browser_manager)
        except Exception as e: logger.error(f"APA ProfileLoad: Error for profile '{prof_dict.get('name', i)}': {e}")
    logger.info(f"APA ProfileLoad: Loaded {len(loaded_profiles)} profiles from {file_path} for its internal logic.")
    return loaded_profiles

# GUI related functions (main_loop_for_gui, load_app_config_for_gui)
# These are similar to Version B, adapted to call _async_main_refactored.
def load_app_config_for_gui(config_path: Path = CONFIG_FILE) -> Dict[str, Any]:
    return _load_yaml_config(config_path)

async def main_loop_for_gui(config_data: Dict[str, Any], stop_event: asyncio.Event,
                            gui_threading_q: "threading_queue.Queue"):
    async_gui_q: asyncio.Queue[Tuple[str, Any]] = asyncio.Queue()
    log_bridge = logging.getLogger("GuiMessageBridge")

    async def message_bridge():
        log_bridge.info("GUI message bridge started.")
        stop_event_triggered = False
        while not stop_event_triggered:
            try:
                get_task = asyncio.create_task(async_gui_q.get())
                stop_task = asyncio.create_task(stop_event.wait())
                done, pending = await asyncio.wait([get_task, stop_task], return_when=asyncio.FIRST_COMPLETED)
                if stop_task in done: stop_event_triggered = True; get_task.cancel()
                if get_task in done:
                    try: item = await get_task; gui_threading_q.put(item); async_gui_q.task_done()
                    except asyncio.CancelledError: pass
                for p in pending: p.cancel() # Cancel other task if one completed
            except asyncio.CancelledError: stop_event_triggered = True; break
            except Exception as e: log_bridge.error(f"Bridge error: {e}", exc_info=True); await asyncio.sleep(0.1)
        
        log_bridge.info("Bridge: Processing final items...");
        while not async_gui_q.empty():
            try: gui_threading_q.put(async_gui_q.get_nowait()); async_gui_q.task_done()
            except asyncio.QueueEmpty: break
        log_bridge.info("GUI message bridge stopped.")

    bridge_task = asyncio.create_task(message_bridge(), name="GuiMessageBridgeTask")
    try:
        await _async_main_refactored(config_data, gui_q=async_gui_q, stop_event_from_caller=stop_event)
    except Exception as e_main_gui:
        log_bridge.critical(f"CRITICAL error in main_loop_for_gui from _async_main: {e_main_gui}", exc_info=True)
        try: gui_threading_q.put(("log", (f"FATAL CORE ERROR: {str(e_main_gui)[:90]}", "CRITICAL")))
        except Exception: pass # Ignore if queue is also broken
    finally:
        log_bridge.info("main_loop_for_gui 'finally': Stopping bridge...")
        if not stop_event.is_set(): stop_event.set()
        if bridge_task and not bridge_task.done():
            try: await asyncio.wait_for(bridge_task, timeout=3.0)
            except asyncio.TimeoutError: log_bridge.warning("Timeout stopping bridge. Cancelling."); bridge_task.cancel()
            except Exception: pass # Ignore other errors during final await
        log_bridge.info("main_loop_for_gui finished.")


# CLI Signal Handler and Main Execution
def cli_signal_handler(sig, frame):
    global _stop_event_for_signal
    signal_name = getattr(signal.Signals, sig.name, f"Signal {sig}")
    logging.warning(f"Signal {signal_name} received. Initiating graceful shutdown...")
    if _stop_event_for_signal:
        if not _stop_event_for_signal.is_set(): _stop_event_for_signal.set(); logging.info("Stop event set.")
        else: logging.critical("Second interrupt. Forcing exit."); os._exit(1)
    else: logging.critical("Stop event not init. Forcing exit."); os._exit(1)

# Placeholder warm-up/test functions (can be fleshed out similarly to Version A/B if needed)
async def async_warm_profile_session(profile_name: str, start_url: str, config_data: Dict[str, Any], p_instance: Playwright):
    # This would use a V2 StealthBrowserManager configured for warm-up
    warm_log = logging.getLogger(f"Warmup.{profile_name}")
    warm_log.info(f"WARMUP: Profile '{profile_name}', URL '{start_url}'. (V2 Manager Adaptation Needed)")
    # Create a specific config for the V2 manager for warming
    warmup_bm_config = json.loads(json.dumps(config_data)) # Deep copy
    warmup_bm_config.setdefault('browser_launch_options', {})['headless'] = False
    warmup_bm_config.setdefault('browser_launch_options', {}).setdefault('args', []).append("--auto-open-devtools-for-tabs")
    # Ensure V2 manager uses only the specified profile for this warm-up bm instance
    # This might mean setting warmup_bm_config['paths']['browser_profiles_yaml'] to a temp file
    # or modifying V2 manager to accept a 'use_only_profile_name' hint.
    warm_log.warning("Warm-up logic with V2 manager needs careful implementation of profile selection.")

    bm_for_warmup = StealthBrowserManager(config=warmup_bm_config, playwright_instance=p_instance)
    await bm_for_warmup.start_manager()
    try:
        async with bm_for_warmup.get_context() as (ctx, prof_used): # V2 manager selects profile
             if prof_used.name != profile_name:
                 warm_log.warning(f"V2 manager provided profile '{prof_used.name}' though '{profile_name}' was requested for warmup. Proceeding with '{prof_used.name}'.")
             async with bm_for_warmup.get_page_from_context(ctx, start_url) as page:
                warm_log.info(f"Page loaded: {page.url}. INTERACT MANUALLY. Close browser to finish.")
                if page.context.browser: await page.context.browser.wait_for_event("disconnected", timeout=3 * 3600 * 1000)
    except Exception as e: warm_log.error(f"Warmup error: {e}", exc_info=True)
    finally: await bm_for_warmup.stop_manager()


async def async_test_stealth_session(profile_name: str, test_url: str, config_data: Dict[str, Any], p_instance: Playwright):
    test_log = logging.getLogger(f"StealthTest.{profile_name}")
    test_log.info(f"STEALTH TEST: Profile '{profile_name}', URL '{test_url}'. (V2 Manager Adaptation Needed)")
    # Similar to warmup, configure V2 manager for testing this specific profile.
    test_bm_config = json.loads(json.dumps(config_data))
    test_bm_config.setdefault('browser_launch_options', {})['headless'] = False # Usually observe for test
    # Ensure V2 manager uses only the specified profile.

    bm_for_test = StealthBrowserManager(config=test_bm_config, playwright_instance=p_instance)
    await bm_for_test.start_manager()
    try:
        async with bm_for_test.get_context() as (ctx, prof_used):
            if prof_used.name != profile_name:
                 test_log.warning(f"V2 manager provided profile '{prof_used.name}' for test of '{profile_name}'.")
            async with bm_for_test.get_page_from_context(ctx, test_url) as page:
                test_log.info(f"Page loaded: {page.url}. OBSERVE STEALTH. Close browser to finish.")
                if page.context.browser: await page.context.browser.wait_for_event("disconnected", timeout=3 * 3600 * 1000)
    except Exception as e: test_log.error(f"Stealth test error: {e}", exc_info=True)
    finally: await bm_for_test.stop_manager()


def cli_main() -> None:
    parser = argparse.ArgumentParser(description="Enhanced Ticket Monitor Bot (V2 Manager Integrated)")
    parser.add_argument("--warm-profile", type=str, help="Profile name for warm-up session.")
    parser.add_argument("--start-url", type=str, help="Start URL for warm-up (default from config).")
    parser.add_argument("--test-stealth", type=str, help="Profile name for stealth testing.")
    parser.add_argument("--test-url", type=str, default="https://infoscan.io/", help="URL for stealth test.")

    cli_args = [arg for arg in sys.argv[1:] if arg != '--gui']
    args = parser.parse_args(cli_args)

    # Load main config first for logging setup
    config = _load_yaml_config(CONFIG_FILE)
    log_cfg_main = config.get('app_settings', {}).get('logging', config.get('logging', {}))
    _init_logging(
        level_str=log_cfg_main.get("level", "INFO"),
        log_file=log_cfg_main.get("file_path", "logs/ticket_bot_refactored.log") # Default log file
    )

    if not config: # After logging is up
        logging.critical(f"CRITICAL: Main config '{CONFIG_FILE}' failed to load. Exiting.")
        sys.exit(1)

    # Handle CLI modes (warmup, stealth test)
    if args.warm_profile or args.test_stealth:
        async def run_cli_mode():
            async with async_playwright() as p: # Playwright instance for these modes
                if args.warm_profile:
                    start_url = args.start_url or config.get('app_settings', {}).get('warmup_default_start_url', 'https://google.com')
                    await async_warm_profile_session(args.warm_profile, start_url, config, p)
                elif args.test_stealth:
                    await async_test_stealth_session(args.test_stealth, args.test_url, config, p)
        try:
            asyncio.run(run_cli_mode())
        except Exception as e_cli_mode:
            logging.critical(f"Error in CLI mode operation: {e_cli_mode}", exc_info=True)
            sys.exit(1)
        return # Exit after CLI mode completes

    # Main monitoring mode
    logging.info("Starting Refactored Ticket Monitor (CLI Mode)...")
    global _stop_event_for_signal # Ensure global is used by handler
    cli_stop_event = asyncio.Event()
    _stop_event_for_signal = cli_stop_event

    original_sigint = signal.signal(signal.SIGINT, cli_signal_handler)
    original_sigterm = signal.signal(signal.SIGTERM, cli_signal_handler)
    try:
        asyncio.run(_async_main_refactored(config_data=config, stop_event_from_caller=cli_stop_event))
    except KeyboardInterrupt: logging.info("CLI Main: KeyboardInterrupt. Stop event should be set.")
    except SystemExit as e_sys: logging.info(f"CLI Main: SystemExit with code {e_sys.code}.")
    except Exception as e_cli_run: logging.critical(f"CLI Main: Unhandled CRITICAL error: {e_cli_run}", exc_info=True); sys.exit(1)
    finally:
        logging.info("CLI Main: Restoring signal handlers and shutting down.")
        signal.signal(signal.SIGINT, original_sigint)
        signal.signal(signal.SIGTERM, original_sigterm)
        if not cli_stop_event.is_set(): cli_stop_event.set() # Ensure cleanup for graceful exit
        logging.info("CLI application shutdown process finished.")


if __name__ == "__main__":
    # Initial basicConfig for very early messages, _init_logging will refine it.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)-7s] %(name)-20s :: %(message)s", datefmt="%Y-%m-%d %H:%M:%S", force=True)

    if "--gui" in sys.argv:
        logging.info("Argument --gui detected. Attempting to start GUI mode...")
        try:
            from gui import start_gui # Assuming gui.py handles its own more specific logging if needed
            # GUI mode will also need config loading and a stop event.
            # start_gui might internally call main_loop_for_gui.
            start_gui()
        except ImportError as e_gui_imp:
            logging.critical(f"GUI components (gui.py) not found/imported: {e_gui_imp}. GUI mode not available.", exc_info=True)
            sys.exit(1)
        except Exception as e_gui_start:
            logging.critical(f"Unexpected error starting GUI: {e_gui_start}", exc_info=True)
            sys.exit(1)
    else:
        cli_main()