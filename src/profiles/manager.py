# src/profiles/manager.py
"""Main profile manager implementation."""
import asyncio
import copy
import logging
import random
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Callable

import numpy as np

from .config import ProfileManagerConfig
from .enums import Platform, ProfileQuality
from .models import BrowserProfile, ProxyConfig
from .persistence import ProfilePersistence
from .scoring import ProfileScorer
from .session_manager import SessionManager
from ..core.advanced_profile_system import (
    DynamicProfile,
    MutationStrategy,
    ProfileState,
    DetectionEvent
)

logger = logging.getLogger(__name__)


class ProfileManager:
    """Advanced profile manager with session and platform management."""
    
    def __init__(
        self,
        config: Optional[ProfileManagerConfig] = None,
        base_profile_template: Optional[Dict] = None
    ):
        self.config = config or ProfileManagerConfig()
        self.dynamic_profiles: List[DynamicProfile] = []
        self.static_profiles: Dict[str, BrowserProfile] = {}
        self.mutation_strategy = MutationStrategy()
        
        # Initialize components
        self.scorer = ProfileScorer(self.config.scoring_config)
        self.session_manager = SessionManager(self.config.session_backup_dir)
        self.persistence = ProfilePersistence(
            self.config.persistence_filepath,
            enable_encryption=self.config.enable_encrypted_storage
        )
        
        # Cooldown management
        self.profile_cooldowns: Dict[str, datetime] = {}
        
        # Platform session pools
        self.platform_pools: Dict[str, List[str]] = defaultdict(list)
        
        # Base template
        self.base_profile_template = base_profile_template or self._get_default_base_template()
        
        # Task management
        self._evolution_task: Optional[asyncio.Task] = None
        self._session_validation_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._initialized = False
        
        # Locks
        self._profiles_lock = asyncio.Lock()
        self._cooldown_lock = asyncio.Lock()
        
        # TLS fingerprint rotation
        self._tls_fingerprints = self._load_tls_fingerprints()
        self._current_tls_index = 0
        
        logger.info(
            f"ProfileManager initialized. Target: {self.config.num_target_profiles} profiles, "
            f"{self.config.profiles_per_platform} per platform"
        )
    
    async def initialize(self, lazy_load: bool = True):
        """Initialize the profile manager with optional lazy loading."""
        if self._initialized:
            return
        
        if lazy_load:
            # Fast initialization - defer profile pool creation
            logger.info("ProfileManager fast initialization (lazy mode)")
            self._initialized = True
            # Start background tasks immediately for responsiveness
            await self.start_background_tasks()
            # Initialize profile pool in background
            asyncio.create_task(self._lazy_initialize_profile_pool())
        else:
            # Full initialization (original behavior)
            await self._initialize_profile_pool()
            await self.start_background_tasks()
            self._initialized = True
            logger.info("ProfileManager fully initialized")
    
    async def _lazy_initialize_profile_pool(self):
        """Initialize profile pool in background without blocking startup."""
        try:
            logger.info("Starting background profile pool initialization...")
            await self._initialize_profile_pool()
            logger.info("Background profile pool initialization complete")
        except Exception as e:
            logger.error(f"Background profile pool initialization failed: {e}")
            # Fallback to minimal profile creation
            await self._create_minimal_profile_pool()
    
    async def _create_minimal_profile_pool(self):
        """Create a minimal profile pool for immediate functionality."""
        try:
            from .enums import Platform
            platforms = [Platform.TICKETMASTER, Platform.FANSALE, Platform.VIVATICKET]
            
            # Create just one profile per platform for immediate functionality
            for platform in platforms:
                profile_id = f"{platform.value}_{random.randint(10000000, 99999999):08x}"
                
                # Create a basic dynamic profile
                from ..core.advanced_profile_system import DynamicProfile, ProfileState
                profile = DynamicProfile(
                    profile_id=profile_id,
                    platform=platform.value,
                    state=ProfileState.PRISTINE,
                    base_template=self._get_default_base_template()
                )
                
                self.dynamic_profiles.append(profile)
                
                # Add to platform pools
                if platform.value not in self.platform_pools:
                    self.platform_pools[platform.value] = []
                self.platform_pools[platform.value].append(profile_id)
            
            logger.info(f"Created minimal profile pool: {len(self.dynamic_profiles)} profiles")
            
        except Exception as e:
            logger.error(f"Failed to create minimal profile pool: {e}")
    
    async def shutdown(self):
        """Shutdown the profile manager."""
        await self.stop_background_tasks()
        logger.info("ProfileManager shutdown complete")
    
    def _get_default_base_template(self) -> Dict[str, Any]:
        """Get Italian-focused default template."""
        return {
            "os_name": "Windows",
            "browser_name": "Chrome",
            "device_class": "mid_range_desktop",
            "country": "IT",
            "language": "it-IT"
        }
    
    def _load_tls_fingerprints(self) -> List[Dict[str, Any]]:
        """Load realistic TLS fingerprints."""
        # In production, load from a comprehensive database
        return [
            {
                "ja3": "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0",
                "h2_settings": "1:65536,2:0,3:1000,4:6291456,6:262144",
                "h2_window_update": 15663105,
                "h2_priority": {"stream_id": 3, "exclusive": 1, "parent_stream_id": 0, "weight": 201}
            },
            {
                "ja3": "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0",
                "h2_settings": "1:65536,3:1000,4:6291456,6:262144",
                "h2_window_update": 15728640,
                "h2_priority": {"stream_id": 3, "exclusive": 1, "parent_stream_id": 0, "weight": 220}
            }
        ]
    
    async def _initialize_profile_pool(self):
        """Initialize profile pool with platform distribution."""
        async with self._profiles_lock:
            # Try loading from disk first
            loaded = await self.persistence.load_profiles(
                self.dynamic_profiles,
                self.static_profiles,
                self.mutation_strategy
            )
            
            if loaded:
                logger.info(f"Loaded {len(self.dynamic_profiles)} profiles from disk")
                # Rebuild platform pools
                for dp in self.dynamic_profiles:
                    sp = self.static_profiles.get(dp.id)
                    if sp:
                        for platform in Platform:
                            if platform.value in sp.platform_sessions:
                                self.platform_pools[platform.value].append(dp.id)
                                if sp.platform_sessions[platform.value].get('is_valid'):
                                    self.session_manager.session_ready_profiles[platform.value].add(dp.id)
            
            # Create new profiles if needed
            profiles_needed = self.config.num_target_profiles - len(self.dynamic_profiles)
            
            if profiles_needed > 0:
                logger.info(f"Creating {profiles_needed} new profiles")
                
                for i in range(profiles_needed):
                    platform_index = i % len(Platform)
                    platform = list(Platform)[platform_index]
                    
                    profile = await self._create_platform_optimized_profile(platform)
                    if profile:
                        self.dynamic_profiles.append(profile['dynamic'])
                        self.static_profiles[profile['dynamic'].id] = profile['static']
                        self.platform_pools[platform.value].append(profile['dynamic'].id)
            
            logger.info(f"Profile pool initialized. Distribution: {dict(self.platform_pools)}")
    
    async def get_profile_for_platform(
        self,
        platform: Platform,
        require_session: bool = True
    ) -> Optional[BrowserProfile]:
        """Get best profile for specific platform."""
        async with self._profiles_lock:
            async with self._cooldown_lock:
                now = datetime.utcnow()
                candidates = []
                
                # Get profiles assigned to this platform
                platform_profile_ids = self.platform_pools.get(platform.value, [])
                
                for profile_id in platform_profile_ids:
                    # Check if on cooldown
                    if profile_id in self.profile_cooldowns:
                        if now < self.profile_cooldowns[profile_id]:
                            continue
                    
                    dynamic_profile = next((p for p in self.dynamic_profiles if p.id == profile_id), None)
                    static_profile = self.static_profiles.get(profile_id)
                    
                    if not dynamic_profile or not static_profile:
                        continue
                    
                    # Skip compromised/evolving profiles
                    if dynamic_profile.state in [ProfileState.COMPROMISED, ProfileState.EVOLVING]:
                        continue
                    
                    # Calculate score
                    score = self.scorer.calculate_score(
                        dynamic_profile, static_profile, platform, require_session
                    )
                    
                    if score > 0:
                        candidates.append((score, static_profile))
                
                if not candidates:
                    logger.warning(f"No suitable profiles for {platform.value}")
                    # Try creating a new profile
                    new_profile = await self._create_platform_optimized_profile(platform)
                    if new_profile:
                        self.dynamic_profiles.append(new_profile['dynamic'])
                        self.static_profiles[new_profile['dynamic'].id] = new_profile['static']
                        self.platform_pools[platform.value].append(new_profile['dynamic'].id)
                        return new_profile['static']
                    return None
                
                # Select best profile
                candidates.sort(key=lambda x: x[0], reverse=True)
                selected_profile = candidates[0][1]
                
                # Apply cooldown
                cooldown_base, variance = self.config.cooldowns_seconds.get("task_selection", (10, 0.2))
                cooldown_seconds = self._calculate_cooldown_with_jitter(cooldown_base, variance)
                self.profile_cooldowns[selected_profile.profile_id] = now + timedelta(seconds=cooldown_seconds)
                
                # Update last used
                selected_profile.last_used = now
                
                # Check if proxy rotation needed
                if selected_profile.should_rotate_proxy():
                    selected_profile.rotate_proxy()
                    logger.info(f"Rotated proxy for profile {selected_profile.profile_id}")
                
                logger.info(
                    f"Selected profile {selected_profile.profile_id} for {platform.value} "
                    f"(score: {candidates[0][0]:.2f}, has_session: {platform.value in selected_profile.platform_sessions})"
                )
                
                return selected_profile
    
    async def record_feedback(
        self,
        profile_id: str,
        event: DetectionEvent,
        platform: str,
        metadata: Optional[Dict] = None,
        invalidate_session: bool = False
    ):
        """Record profile feedback with session management."""
        async with self._profiles_lock:
            async with self._cooldown_lock:
                # Update dynamic profile
                dynamic_profile = next((p for p in self.dynamic_profiles if p.id == profile_id), None)
                if dynamic_profile:
                    dynamic_profile.record_detection_event(event, metadata or {})
                
                # Update static profile
                static_profile = self.static_profiles.get(profile_id)
                if static_profile:
                    # Record usage
                    response_time = metadata.get('response_time_ms', 0) if metadata else 0
                    static_profile.record_usage(
                        success=(event == DetectionEvent.SUCCESS),
                        response_time_ms=response_time,
                        platform=platform,
                        error=metadata.get('error') if metadata else None,
                        detected=(event in [DetectionEvent.HARD_BLOCK, DetectionEvent.CAPTCHA_CHALLENGE]),
                        captcha_encountered=(event == DetectionEvent.CAPTCHA_CHALLENGE)
                    )
                    
                    # Invalidate session if needed
                    if invalidate_session:
                        self.session_manager.invalidate_session(
                            static_profile,
                            Platform(platform)
                        )
                
                # Apply cooldown based on event
                now = datetime.utcnow()
                cooldown_params = self.config.cooldowns_seconds.get(event.value)
                
                if cooldown_params:
                    base_duration, variance = cooldown_params
                    cooldown_seconds = self._calculate_cooldown_with_jitter(base_duration, variance)
                    self.profile_cooldowns[profile_id] = now + timedelta(seconds=cooldown_seconds)
                    logger.debug(
                        f"Profile {profile_id} on cooldown for {cooldown_seconds/60:.1f} minutes "
                        f"after {event.value}"
                    )
    
    async def warm_up_profile(
        self,
        profile: BrowserProfile,
        browser_manager: Any
    ) -> bool:
        """Warm up profile with realistic browsing."""
        if not self.config.enable_behavioral_warmup:
            return True
        
        logger.info(f"Warming up profile {profile.profile_id}")
        
        try:
            # Get context from browser manager
            context = await browser_manager.get_persistent_context_for_profile(profile)
            
            # Visit Italian sites
            sites_to_visit = random.sample(
                self.config.warmup_sites,
                k=min(3, len(self.config.warmup_sites))
            )
            
            for site in sites_to_visit:
                try:
                    page = await context.new_page()
                    
                    # Set realistic viewport
                    await page.set_viewport_size({
                        'width': profile.viewport_width,
                        'height': profile.viewport_height
                    })
                    
                    await page.goto(site, wait_until='domcontentloaded', timeout=30000)
                    
                    # Simulate human behavior
                    await asyncio.sleep(random.uniform(2, 5))
                    
                    # Random scrolling
                    for _ in range(random.randint(1, 3)):
                        scroll_amount = random.uniform(0.1, 0.5)
                        await page.evaluate(
                            f"window.scrollTo(0, document.body.scrollHeight * {scroll_amount})"
                        )
                        await asyncio.sleep(random.uniform(0.5, 2))
                    
                    # Maybe click something
                    if random.random() > 0.5:
                        links = await page.query_selector_all('a')
                        if links and len(links) > 5:
                            link = random.choice(links[:10])
                            try:
                                await link.click(timeout=5000)
                                await asyncio.sleep(random.uniform(1, 3))
                            except:
                                pass
                    
                    await page.close()
                    
                except Exception as e:
                    logger.warning(f"Warmup site {site} failed: {e}")
            
            # Mark profile as warmed up
            dynamic_profile = next(
                (p for p in self.dynamic_profiles if p.id == profile.profile_id),
                None
            )
            if dynamic_profile and dynamic_profile.state == ProfileState.PRISTINE:
                dynamic_profile.state = ProfileState.HEALTHY
            
            logger.info(f"Profile {profile.profile_id} warmed up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Profile warmup failed: {e}", exc_info=True)
            return False
        finally:
            if 'context' in locals():
                await context.close()
    
    async def ensure_platform_session(
        self,
        profile: BrowserProfile,
        platform: Platform,
        login_callback: Optional[Callable] = None
    ) -> bool:
        """Ensure profile has valid session for platform."""
        # Check existing session
        session = profile.platform_sessions.get(platform.value)
        if session and session.get('is_valid'):
            # Validate age
            session_age = (
                datetime.utcnow() - datetime.fromisoformat(session['last_updated'])
            ).total_seconds() / 3600
            if session_age < self.config.max_session_age_hours:
                return True
        
        # Need to login
        if not login_callback:
            logger.warning(f"No login callback provided for {platform.value}")
            return False
        
        logger.info(f"Profile {profile.profile_id} needs login for {platform.value}")
        
        try:
            # Execute login
            success = await login_callback(profile, platform)
            
            if success:
                self.session_manager.session_ready_profiles[platform.value].add(profile.profile_id)
                logger.info(
                    f"Profile {profile.profile_id} successfully logged into {platform.value}"
                )
            
            return success
            
        except Exception as e:
            logger.error(
                f"Login failed for profile {profile.profile_id} on {platform.value}: {e}"
            )
            return False
    
    async def _create_platform_optimized_profile(
        self,
        platform: Platform
    ) -> Optional[Dict[str, Any]]:
        """Create profile optimized for specific platform."""
        try:
            # Platform-specific optimizations
            base_template = copy.deepcopy(self.base_profile_template)
            requirements = platform.stealth_requirements
            
            # Browser selection based on platform requirements
            browser_prefs = requirements.get('browser_preferences', ['Chrome'])
            base_template['browser_name'] = random.choice(browser_prefs)
            
            # Device class selection
            if requirements.get('aggressive_stealth'):
                base_template['device_class'] = random.choice(['high_end_desktop', 'high_end_laptop'])
            else:
                base_template['device_class'] = random.choice(['mid_range_desktop', 'mid_range_laptop'])
            
            # Create dynamic profile
            profile_id = f"{platform.value}_{str(uuid.uuid4())[:8]}"
            dynamic_profile = DynamicProfile(
                mutation_strategy=self.mutation_strategy,
                base_profile_dict=base_template,
                profile_id=profile_id
            )
            
            # Create static profile
            static_profile = self._adapt_dynamic_to_static(dynamic_profile)
            
            # Platform-specific enhancements
            static_profile.timezone = "Europe/Rome"
            static_profile.locale = "it-IT"
            static_profile.languages_override = ["it-IT", "it", "en-US", "en"]
            
            # Enable CDP stealth for platforms that need it
            if requirements.get('aggressive_stealth'):
                static_profile.cdp_stealth_enabled = True
                static_profile.override_navigator_webdriver = True
                static_profile.mask_automation_indicators = True
            
            # Assign quality based on randomization
            static_profile.quality = random.choices(
                list(ProfileQuality),
                weights=[0.1, 0.3, 0.4, 0.2],  # Prefer HIGH quality
                k=1
            )[0]
            
            # Setup proxy if available
            if hasattr(self.config, 'proxy_configs') and self.config.proxy_configs:
                proxy_config = random.choice(self.config.proxy_configs)
                # Prefer residential proxies for aggressive platforms
                if requirements.get('require_residential_proxy'):
                    residential_proxies = [
                        p for p in self.config.proxy_configs
                        if p.proxy_provider in ['brightdata', 'oxylabs', 'smartproxy']
                    ]
                    if residential_proxies:
                        proxy_config = random.choice(residential_proxies)
                
                static_profile.proxy_config = proxy_config
                static_profile.proxy_session_id = proxy_config.rotate_session()
            
            # Add platform-specific headers
            if requirements.get('additional_headers'):
                static_profile.extra_http_headers.update(requirements['additional_headers'])
            
            # TLS fingerprint rotation
            if self.config.enable_tls_rotation and self._tls_fingerprints:
                tls_fingerprint = self._tls_fingerprints[self._current_tls_index]
                self._current_tls_index = (self._current_tls_index + 1) % len(self._tls_fingerprints)
                static_profile.extra_js_props['tls_fingerprint'] = tls_fingerprint
            
            return {
                'dynamic': dynamic_profile,
                'static': static_profile
            }
            
        except Exception as e:
            logger.error(f"Failed to create platform profile: {e}", exc_info=True)
            return None
    
    def _adapt_dynamic_to_static(self, dynamic_profile: DynamicProfile) -> BrowserProfile:
        """Convert DynamicProfile to BrowserProfile with enhancements."""
        js_data = dynamic_profile.get_stealth_init_js_profile_data()
        
        # Extract screen dimensions
        screen_res = js_data.get('screen_resolution', (1920, 1080))
        screen_width = screen_res[0] if isinstance(screen_res, tuple) else 1920
        screen_height = screen_res[1] if isinstance(screen_res, tuple) else 1080
        
        # Create static profile
        static_profile = BrowserProfile(
            name=f"{js_data.get('browser_name', 'Unknown')}_{dynamic_profile.device_class}",
            profile_id=dynamic_profile.id,
            user_agent=js_data.get('user_agent', ''),
            viewport_width=int(screen_width * 0.95),
            viewport_height=int(screen_height * 0.85),
            screen_width=screen_width,
            screen_height=screen_height,
            avail_width=js_data.get('avail_width', screen_width),
            avail_height=js_data.get('avail_height', screen_height - 40),
            device_pixel_ratio=float(js_data.get('device_pixel_ratio', 1.0)),
            color_depth=int(js_data.get('color_depth', 24)),
            pixel_depth=int(js_data.get('pixel_depth', 24)),
            js_platform=js_data.get('js_platform', 'Win32'),
            hardware_concurrency=int(js_data.get('hardware_concurrency', 8)),
            device_memory=js_data.get('device_memory', 8),
            timezone=js_data.get('timezone', 'Europe/Rome'),
            locale=js_data.get('locale', 'it-IT'),
            languages_override=js_data.get('languages_override', ['it-IT', 'it', 'en-US', 'en']),
            webgl_vendor=js_data.get('webgl_vendor'),
            webgl_renderer=js_data.get('webgl_renderer'),
            canvas_fingerprint=js_data.get('canvas_fingerprint'),
            audio_fingerprint=js_data.get('audio_fingerprint'),
            webrtc_ips=js_data.get('webrtc_ips', []),
            fonts_list=js_data.get('fonts', []),
            sec_ch_ua=js_data.get('sec_ch_ua'),
            sec_ch_ua_mobile=js_data.get('sec_ch_ua_mobile', '?0'),
            sec_ch_ua_platform=js_data.get('sec_ch_ua_platform'),
            sec_ch_ua_platform_version=js_data.get('sec_ch_ua_platform_version'),
            sec_ch_ua_full_version_list=js_data.get('sec_ch_ua_full_version_list'),
            extra_js_props=js_data.get('extra_js_props', {})
        )
        
        # Generate realistic Accept-Language header
        if static_profile.languages_override:
            parts = []
            q_values = [1.0, 0.9, 0.8, 0.7]
            for i, lang in enumerate(static_profile.languages_override[:4]):
                if i == 0:
                    parts.append(lang)
                else:
                    parts.append(f"{lang};q={q_values[min(i, len(q_values)-1)]:.1f}")
            static_profile.accept_language = ','.join(parts)
        
        return static_profile
    
    async def _periodic_profile_evolution_task(self):
        """Enhanced evolution with session awareness."""
        while not self._shutdown_event.is_set():
            try:
                # Jittered sleep
                sleep_duration = self._calculate_cooldown_with_jitter(
                    self.config.evolution_interval_seconds,
                    self.config.evolution_interval_jitter_factor
                )
                await asyncio.sleep(sleep_duration)
                
                if self._shutdown_event.is_set():
                    break
                
                async with self._profiles_lock:
                    # Evolve profiles
                    for dynamic_profile in list(self.dynamic_profiles):
                        if dynamic_profile.should_mutate():
                            changes = dynamic_profile.mutate()
                            if changes:
                                # Update static profile
                                static_profile = self._adapt_dynamic_to_static(dynamic_profile)
                                # Preserve session data
                                old_static = self.static_profiles.get(dynamic_profile.id)
                                if old_static:
                                    static_profile.platform_sessions = old_static.platform_sessions
                                    static_profile.platform_stats = old_static.platform_stats
                                    static_profile.proxy_config = old_static.proxy_config
                                    static_profile.proxy_session_id = old_static.proxy_session_id
                                
                                self.static_profiles[dynamic_profile.id] = static_profile
                                logger.info(
                                    f"Profile {dynamic_profile.id} evolved with {len(changes)} changes"
                                )
                    
                    # Replace compromised profiles
                    await self._replace_compromised_profiles()
                    
                    # Save state
                    await self.persistence.save_profiles(
                        self.dynamic_profiles,
                        self.static_profiles
                    )
                
            except Exception as e:
                logger.error(f"Evolution task error: {e}", exc_info=True)
    
    async def _periodic_session_validation(self):
        """Validate sessions periodically."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config.session_validation_interval_seconds)
                
                if self._shutdown_event.is_set():
                    break
                
                await self.session_manager.validate_sessions(
                    self.static_profiles,
                    self.config.max_session_age_hours
                )
                
            except Exception as e:
                logger.error(f"Session validation error: {e}")
    
    async def _replace_compromised_profiles(self):
        """Replace compromised profiles with platform awareness."""
        compromised_profiles = [
            p for p in self.dynamic_profiles
            if p.state == ProfileState.COMPROMISED
        ]
        
        if not compromised_profiles:
            return
        
        compromise_rate = len(compromised_profiles) / len(self.dynamic_profiles)
        
        if compromise_rate >= self.config.compromise_threshold_pct:
            logger.warning(f"Replacing {len(compromised_profiles)} compromised profiles")
            
            for profile in compromised_profiles:
                # Remove from all pools
                profile_id = profile.id
                self.dynamic_profiles.remove(profile)
                self.static_profiles.pop(profile_id, None)
                
                for platform_profiles in self.platform_pools.values():
                    if profile_id in platform_profiles:
                        platform_profiles.remove(profile_id)
                
                for session_profiles in self.session_manager.session_ready_profiles.values():
                    session_profiles.discard(profile_id)
                
                # Create replacement for same platform
                for platform, profile_ids in self.platform_pools.items():
                    if profile_id in profile_ids:
                        new_profile = await self._create_platform_optimized_profile(
                            Platform(platform)
                        )
                        if new_profile:
                            self.dynamic_profiles.append(new_profile['dynamic'])
                            self.static_profiles[new_profile['dynamic'].id] = new_profile['static']
                            self.platform_pools[platform].append(new_profile['dynamic'].id)
                        break
    
    def _calculate_cooldown_with_jitter(
        self,
        base_seconds: float,
        variance_factor: float = 0.3
    ) -> float:
        """Calculate cooldown with jitter."""
        if base_seconds <= 0:
            return 0.0
        jittered = np.random.normal(loc=base_seconds, scale=base_seconds * variance_factor)
        return max(base_seconds * 0.5, min(base_seconds * 2.0, jittered))
    
    async def start_background_tasks(self):
        """Start all background tasks."""
        self._shutdown_event.clear()
        
        # Start evolution
        self._evolution_task = asyncio.create_task(self._periodic_profile_evolution_task())
        
        # Start session validation
        if self.config.enable_session_preloading:
            self._session_validation_task = asyncio.create_task(self._periodic_session_validation())
        
        logger.info("Background tasks started")
    
    async def stop_background_tasks(self):
        """Stop all background tasks."""
        self._shutdown_event.set()
        
        tasks = [t for t in [self._evolution_task, self._session_validation_task] if t]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Final save
        await self.persistence.save_profiles(self.dynamic_profiles, self.static_profiles)
        
        logger.info("Background tasks stopped")
    
    def get_pool_metrics(self) -> Dict[str, Any]:
        """Get comprehensive pool metrics."""
        metrics = {
            'total_profiles': len(self.dynamic_profiles),
            'platform_distribution': {p: len(ids) for p, ids in self.platform_pools.items()},
            'session_ready': dict(self.session_manager.session_ready_profiles),
            'state_distribution': defaultdict(int),
            'quality_distribution': defaultdict(int),
            'avg_success_rates': {},
            'profiles_on_cooldown': len(self.profile_cooldowns),
            'active_profiles': 0,
            'detection_rate_24h': {}
        }
        
        # State and quality distribution
        for dynamic_profile in self.dynamic_profiles:
            metrics['state_distribution'][dynamic_profile.state.value] += 1
            
            static_profile = self.static_profiles.get(dynamic_profile.id)
            if static_profile:
                metrics['quality_distribution'][static_profile.quality.name] += 1
                if static_profile.last_used and (
                    datetime.utcnow() - static_profile.last_used
                ).total_seconds() < 3600:
                    metrics['active_profiles'] += 1
        
        # Platform success rates and detection rates
        for platform in Platform:
            total_attempts = 0
            total_successes = 0
            recent_detections = 0
            
            for static_profile in self.static_profiles.values():
                stats = static_profile.platform_stats.get(platform.value, {})
                total_attempts += stats.get('attempts', 0)
                total_successes += stats.get('successes', 0)
                
                # Count recent detections (last 24h)
                for event in stats.get('detection_events', []):
                    event_time = datetime.fromisoformat(event['timestamp'])
                    if (datetime.utcnow() - event_time).total_seconds() < 86400:
                        recent_detections += 1
            
            if total_attempts > 0:
                metrics['avg_success_rates'][platform.value] = total_successes / total_attempts
                metrics['detection_rate_24h'][platform.value] = recent_detections / total_attempts
        
        return metrics