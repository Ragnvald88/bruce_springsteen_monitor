# src/core/advanced_profile_system.py v0.7
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
import random
import re # Ensure re is imported
from collections import defaultdict
import copy
import logging
# import numpy as np # Not strictly needed for the corrected _get_components_to_mutate, can use random.choices

# Set up logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- Enums (ProfileState, DetectionEvent) ---
class ProfileState(Enum):
    PRISTINE = "pristine"
    HEALTHY = "healthy"
    SUSPICIOUS = "suspicious"
    COMPROMISED = "compromised"
    DORMANT = "dormant"
    EVOLVING = "evolving"

class DetectionEvent(Enum):
    CAPTCHA_CHALLENGE = "captcha_challenge"
    RATE_LIMIT = "rate_limit"
    HARD_BLOCK = "hard_block"
    SUSPICIOUS_REDIRECT = "suspicious_redirect"
    SESSION_TERMINATED = "session_terminated"
    SUCCESS = "success"
    MANUAL_MUTATION_REQUEST = "manual_mutation_request"

# --- FingerprintComponent ---
@dataclass
class FingerprintComponent:
    name: str
    value: Any
    category: str
    dependencies: Set[str] = field(default_factory=set)
    mutation_weight: float = 1.0
    consistency_rules: List[Callable[['DynamicProfile'], None]] = field(default_factory=list)
    last_mutated_value: Any = field(init=False, default=None)

    def __post_init__(self):
        self.last_mutated_value = copy.deepcopy(self.value) # Ensure deep copy for mutable values

# --- BehavioralModel ---
@dataclass
class BehavioralModel:
    # Mirrored from BiometricProfile in advanced_behavioral_simulation.py for integration
    typing_speed_wpm: float = field(default_factory=lambda: random.uniform(45, 75))
    mouse_acceleration: float = field(default_factory=lambda: random.uniform(1.0, 1.8)) # Factor
    scroll_velocity_preference: float = field(default_factory=lambda: random.uniform(300, 700)) # px/action
    click_dwell_time_ms: float = field(default_factory=lambda: random.uniform(70, 140))
    movement_jitter_factor: float = field(default_factory=lambda: random.uniform(0.04, 0.12))
    pause_between_actions_s: float = field(default_factory=lambda: random.uniform(0.4, 1.5)) # Seconds
    reading_speed_wpm: float = field(default_factory=lambda: random.uniform(200, 320))
    attention_span_seconds: float = field(default_factory=lambda: random.uniform(15, 40))
    multitasking_tendency: float = field(default_factory=lambda: random.uniform(0.15, 0.55)) # Probability

    # Confidence can influence speeds, pauses, jitter
    confidence_level: float = field(default_factory=lambda: random.uniform(0.6, 0.9)) # 0.0 to 1.0

    def reset_patterns(self, full_reset: bool = False):
        self.typing_speed_wpm = random.uniform(45, 75)
        self.mouse_acceleration = random.uniform(1.0, 1.8)
        self.scroll_velocity_preference = random.uniform(300, 700)
        self.click_dwell_time_ms = random.uniform(70, 140)
        if full_reset:
            self.confidence_level = random.uniform(0.6, 0.9)
            self.movement_jitter_factor = random.uniform(0.04, 0.12)
            self.pause_between_actions_s = random.uniform(0.4, 1.5)


    def adapt_behavior(self, success: bool):
        if success:
            self.confidence_level = min(1.0, self.confidence_level * 1.05 + 0.02)
            self.typing_speed_wpm = min(self.typing_speed_wpm * (1.0 + (self.confidence_level - 0.5) * 0.05), 90)
            self.pause_between_actions_s = max(self.pause_between_actions_s * (1.0 - (self.confidence_level - 0.5) * 0.1), 0.2)
        else: # Failure or detection
            self.confidence_level = max(0.1, self.confidence_level * 0.90 - 0.05)
            self.typing_speed_wpm *= (0.9 + (self.confidence_level * 0.1)) # Slower if less confident
            self.pause_between_actions_s *= (1.1 - (self.confidence_level * 0.1)) # Longer pauses
            self.movement_jitter_factor = min(0.2, self.movement_jitter_factor * 1.1) # More jitter

    def get_biometric_profile_dict(self) -> Dict[str, Any]:
        # This maps to the BiometricProfile dataclass used by advanced_behavioral_simulation.py
        return {
            "typing_speed_wpm": self.typing_speed_wpm,
            "mouse_acceleration": self.mouse_acceleration,
            "scroll_velocity_preference": self.scroll_velocity_preference,
            "click_dwell_time_ms": self.click_dwell_time_ms,
            "movement_jitter_factor": self.movement_jitter_factor,
            "pause_between_actions": self.pause_between_actions_s, # Ensure key matches
            "reading_speed_wpm": self.reading_speed_wpm,
            "attention_span_seconds": self.attention_span_seconds,
            "multitasking_tendency": self.multitasking_tendency,
            # Add other fields if BiometricProfile in simulation expects them
        }

# --- MutationStrategy ---
class MutationStrategy:
    def __init__(self):
        self._browser_data_cache: Optional[Dict] = None
        self._os_data_cache: Optional[Dict] = None
        self._hardware_profiles_cache: Optional[Dict] = None
        self._webgl_database_cache: Optional[Dict] = None
        self._font_database_cache: Optional[Dict[str, List[str]]] = None
        self._plugin_database_cache: Optional[Dict[str, List[Dict[str, Any]]]] = None
        self._common_locales_cache: Optional[Dict[str, List[str]]] = None
        self._common_timezones_cache: Optional[Dict[str, List[str]]] = None
        self._tls_database_cache: Optional[Dict[Tuple[str, str, str], str]] = None


    @property
    def browser_data(self) -> Dict:
        if self._browser_data_cache is None: self._browser_data_cache = self._load_browser_data()
        return self._browser_data_cache
    @property
    def os_data(self) -> Dict:
        if self._os_data_cache is None: self._os_data_cache = self._load_os_data()
        return self._os_data_cache
    @property
    def hardware_profiles(self) -> Dict:
        if self._hardware_profiles_cache is None: self._hardware_profiles_cache = self._load_hardware_profiles()
        return self._hardware_profiles_cache
    @property
    def webgl_database(self) -> Dict:
        if self._webgl_database_cache is None: self._webgl_database_cache = self._load_webgl_database()
        return self._webgl_database_cache
    @property
    def font_database(self) -> Dict[str, List[str]]:
        if self._font_database_cache is None: self._font_database_cache = self._load_font_database()
        return self._font_database_cache
    @property
    def plugin_database(self) -> Dict[str, List[Dict[str, Any]]]:
        if self._plugin_database_cache is None: self._plugin_database_cache = self._load_plugin_database()
        return self._plugin_database_cache
    @property
    def common_locales(self) -> Dict[str, List[str]]:
        if self._common_locales_cache is None: self._common_locales_cache = self._load_common_locales()
        return self._common_locales_cache
    @property
    def common_timezones(self) -> Dict[str, List[str]]:
        if self._common_timezones_cache is None: self._common_timezones_cache = self._load_common_timezones()
        return self._common_timezones_cache
    @property
    def tls_database(self) -> Dict[Tuple[str, str, str], str]: # (High Priority 3)
        if self._tls_database_cache is None: self._tls_database_cache = self._load_tls_database()
        return self._tls_database_cache


    def _load_browser_data(self) -> Dict: # (As before, but now accessed via property)
        return {
            'Chrome': {
                'versions': {
                    '124': {'full_versions': ['124.0.6367.60', '124.0.6367.119', '124.0.6367.201'], 'release_date': '2024-04-16', 'brands': [[('Chromium', '124'), ('Not-A.Brand', '99'), ('Google Chrome', '124')],[('Not_A Brand', '8'), ('Chromium', '124'), ('Google Chrome', '124')]]},
                    '125': {'full_versions': ['125.0.6422.60', '125.0.6422.112', '125.0.6422.141'], 'release_date': '2024-05-14', 'brands': [[('Not_A Brand', '24'), ('Chromium', '125'), ('Google Chrome', '125')],[('Chromium', '125'), ('Google Chrome', '125'), ('Not-A.Brand', '99')]]},
                    '126': {'full_versions': ['126.0.6478.56', '126.0.6478.114', '126.0.6478.126'], 'release_date': '2024-06-11', 'brands': [[('Not_A Brand', '8'), ('Chromium', '126'), ('Google Chrome', '126')],[('Chromium', '126'), ('Google Chrome', '126'), ('Not-A.Brand', '99')]]},
                    '127': {'full_versions': ['127.0.6533.72', '127.0.6533.88'], 'release_date': '2024-07-23', 'brands': [[('Not_A Brand', '8'), ('Chromium', '127'), ('Google Chrome', '127')],[('Chromium', '127'), ('Google Chrome', '127'), ('Not-A.Brand', '99')]]}
                },
                'ua_template_win': 'Mozilla/5.0 (Windows NT {os_nt_version}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36',
                'ua_template_mac': 'Mozilla/5.0 (Macintosh; Intel Mac OS X {os_platform_string_version}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36',
                'ua_template_linux': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36'
            },
        }
    def _load_os_data(self) -> Dict: # (As before)
        return {
            'Windows': {
                'versions': {
                    '10': {'builds': ['19045'], 'nt_version': '10.0', 'platform_string_version_part': '10.0', 'sec_ch_ua_platform': '"Windows"', 'sec_ch_ua_platform_versions': ['"10.0.0"', '"13.0.0"', '"14.0.0"', '"15.0.0"']},
                    '11': {'builds': ['22000', '22621', '22631', '26100'], 'nt_version': '10.0', 'platform_string_version_part': '10.0', 'sec_ch_ua_platform': '"Windows"', 'sec_ch_ua_platform_versions': ['"15.0.0"', '"16.0.0"', '"17.0.0"', '"18.0.0"']}
                }, 'js_platform': 'Win32', 'sec_ch_ua_arch': '"x86"', 'sec_ch_ua_bitness': '"64"', 'sec_ch_ua_wow64': '"?0"',
            },
            'macOS': {
                'versions': {
                    '13': {'builds': ['13.5', '13.6.7'], 'platform_string_version_part': '10_15_7', 'sec_ch_ua_platform': '"macOS"', 'sec_ch_ua_platform_versions': ['"13.0.0"', '"13.6.0"']},
                    '14': {'builds': ['14.3', '14.5.0'], 'platform_string_version_part': '10_15_7', 'sec_ch_ua_platform': '"macOS"', 'sec_ch_ua_platform_versions': ['"14.0.0"', '"14.3.0"', '"14.5.0"']},
                    '15': {'builds': ['15.0.0', '15.0.1'], 'platform_string_version_part': '10_15_7', 'sec_ch_ua_platform': '"macOS"', 'sec_ch_ua_platform_versions': ['"15.0.0"']}
                }, 'js_platform': 'MacIntel', 'sec_ch_ua_arch': '"arm"', 'sec_ch_ua_bitness': '"64"', 'sec_ch_ua_wow64': None,
            }
        }
    def _load_webgl_database(self) -> Dict: # (As before, ensure consistency with GPU classes)
        return {
            'Windows': {
                'Chrome': {
                    'NVIDIA_HighEnd': {'vendors': ['Google Inc. (NVIDIA)'], 'renderers': ['ANGLE (NVIDIA, NVIDIA GeForce RTX 4090 Direct3D11 vs_5_0 ps_5_0, D3D11)'], 'extensions': ['EXT_texture_filter_anisotropic', 'WEBGL_debug_renderer_info', 'KHR_parallel_shader_compile'], 'params': {'MAX_TEXTURE_SIZE': 32768, 'MAX_VERTEX_ATTRIBS': 16, 'STENCIL_BITS': 8}},
                    'AMD_MidRange': {'vendors': ['Google Inc. (AMD)'], 'renderers': ['ANGLE (AMD, AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)'], 'extensions': ['EXT_texture_filter_anisotropic', 'WEBGL_draw_buffers'], 'params': {'MAX_TEXTURE_SIZE': 16384, 'MAX_VERTEX_ATTRIBS': 16, 'STENCIL_BITS': 8}},
                    'Intel_Integrated': {'vendors': ['Google Inc. (Intel)'], 'renderers': ['ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)'], 'extensions': ['OES_vertex_array_object', 'WEBGL_lose_context'], 'params': {'MAX_TEXTURE_SIZE': 16384, 'STENCIL_BITS': 0}}
                }},
            'macOS': {
                'Chrome': {
                    'Apple_Silicon': {'vendors': ['Google Inc. (Apple)', 'Apple'], 'renderers': ['ANGLE (Apple, Apple M2 Pro, Unspecified Version)'], 'extensions': ['EXT_texture_filter_anisotropic', 'WEBGL_draw_buffers_indexed'], 'params': {'MAX_TEXTURE_SIZE': 16384, 'STENCIL_BITS': 8}},
                    'Intel_Mac': {'vendors': ['Google Inc. (Intel)', 'Intel'], 'renderers': ['ANGLE (Intel, Intel Iris Pro OpenGL Engine, Unspecified Version)'], 'extensions': ['WEBGL_depth_texture'], 'params': {'MAX_TEXTURE_SIZE': 16384, 'STENCIL_BITS': 8}}
                }}}
    def _load_hardware_profiles(self) -> Dict: # (As before)
        return {
            'Windows': {
                'high_end_desktop': {'cores': [12, 16, 24], 'memory': [16, 32, 64], 'screen_resolutions': [(2560, 1440), (3840, 2160)], 'dpr': [1.0, 1.25, 1.5], 'gpu_classes': ['NVIDIA_HighEnd', 'AMD_HighEnd']},
                'mid_range_laptop': {'cores': [6, 8, 12], 'memory': [8, 16], 'screen_resolutions': [(1920, 1080), (2560, 1440)], 'dpr': [1.0, 1.25], 'gpu_classes': ['NVIDIA_MidRange', 'AMD_MidRange', 'Intel_ModernIntegrated']},
            },
            'macOS': {
                'high_end_laptop': {'cores': [10, 12, 14, 16], 'memory': [16, 32, 64], 'screen_resolutions': [(3024, 1964), (3456, 2234)], 'dpr': [2.0], 'gpu_classes': ['Apple_Silicon']},
                'desktop': {'cores': [8, 12, 24], 'memory': [16, 32, 64], 'screen_resolutions': [(5120, 2880)], 'dpr': [2.0], 'gpu_classes': ['Apple_Silicon', 'AMD_HighEnd_Mac']}, # AMD_HighEnd_Mac for Mac Pro
            }}
    def _load_font_database(self) -> Dict[str, List[str]]: # (As before)
        return {
            "Windows": ["Arial", "Times New Roman", "Verdana", "Tahoma", "Calibri", "Segoe UI"],
            "macOS": ["Helvetica Neue", "Lucida Grande", "Arial", "SF Pro Text", "New York"],
            "Linux": ["DejaVu Sans", "Liberation Sans", "Ubuntu", "Noto Sans"] }
    def _load_plugin_database(self) -> Dict[str, List[Dict[str, Any]]]: # (As before)
        pdf_plugin = {"name": "PDF Viewer", "filename": "internal-pdf-viewer", "description": "Portable Document Format", "mimeTypes": [{"type": "application/pdf", "suffixes": "pdf", "description": "Portable Document Format"}]}
        chrome_pdf_plugin = {"name": "Chrome PDF Viewer", "filename": "internal-pdf-viewer", "description": "", "mimeTypes": [{"type": "application/pdf", "suffixes": "pdf", "description": ""}]}
        return { "Chrome_Windows": [pdf_plugin, chrome_pdf_plugin], "Chrome_macOS": [pdf_plugin, chrome_pdf_plugin], "Chrome_Linux": [pdf_plugin, chrome_pdf_plugin]}
    def _load_common_locales(self) -> Dict[str, List[str]]: # (As before)
        return { "en": ["en-US", "en-GB"], "de": ["de-DE"], "fr": ["fr-FR"], "es": ["es-ES"], "it": ["it-IT"], "nl": ["nl-NL"]}
    def _load_common_timezones(self) -> Dict[str, List[str]]: # (As before)
        return { "NorthAmerica": ["America/New_York", "America/Chicago", "America/Los_Angeles"], "Europe": ["Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Amsterdam"], "Asia": ["Asia/Tokyo", "Asia/Shanghai"]}

    def _load_tls_database(self) -> Dict[Tuple[str, str, str], str]: # (High Priority 3)
        # Key: (BrowserName, BrowserMajorVersion, OSName) -> JA3 String
        # This should be populated with real, verified JA3s.
        return {
            ('Chrome', '124', 'Windows'): '771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513-21,29-23-24,0',
            ('Chrome', '125', 'Windows'): '771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513-21,29-23-24,0', # Placeholder, likely different
            ('Chrome', '126', 'Windows'): '771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,65037-0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513-21,29-23-24,0', # Placeholder
            ('Chrome', '127', 'Windows'): '771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,65037-0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513-21,29-23-24,1', # Example different EC point format
            ('Chrome', '125', 'macOS'): '771,4865-4866-4867-49195-49203-49196-49204-52393-52392-49171-49172-156-157-47-53,45-10-13-18-5-27-16-65281-65037-17513-51-0-11-23-43-35,4588-29-23-24,0', # Example macOS
            # Add many more combinations
        }

    # --- Plausible Value Generators ---
    def generate_plausible_value(self, component_name: str, current_fingerprint_view: Dict[str, FingerprintComponent],
                                 target_os_name: Optional[str] = None, target_browser_name: Optional[str] = None,
                                 target_device_class: Optional[str] = None) -> Any:
        # ... (previous dispatcher logic is mostly fine, ensure it calls new/updated helpers) ...
        def get_current_val(key: str, default: Any = None) -> Any:
            comp = current_fingerprint_view.get(key)
            return comp.value if comp else default

        os_name = target_os_name or get_current_val('os_name', 'Windows')
        browser_name = target_browser_name or get_current_val('browser_name', 'Chrome')
        device_class = target_device_class or get_current_val('device_class', 'mid_range_laptop')
        browser_version = get_current_val('browser_version', '126.0.0.0') # Needed for many generators
        os_version = get_current_val('os_version', '10.0.19045') # Needed for some

        # Dispatcher
        if component_name == 'browser_version': return self._generate_browser_version(browser_name, browser_version)
        elif component_name == 'os_version': return self._generate_os_version(os_name, os_version)
        elif component_name == 'user_agent': return self._generate_user_agent(browser_name, browser_version, os_name, os_version)
        elif component_name == 'sec_ch_ua': return self._generate_sec_ch_ua(browser_name, browser_version)
        elif component_name == 'sec_ch_ua_full_version_list': return self._generate_sec_ch_ua_full_version_list(browser_name, browser_version)
        elif component_name == 'sec_ch_ua_platform': return self._generate_sec_ch_ua_platform(os_name)
        elif component_name == 'sec_ch_ua_platform_version': return self._generate_sec_ch_ua_platform_version(os_name, os_version)
        elif component_name == 'webgl_vendor': return self._generate_webgl_vendor(os_name, browser_name, device_class)
        elif component_name == 'webgl_renderer': return self._generate_webgl_renderer(os_name, browser_name, device_class, get_current_val('webgl_vendor'))
        elif component_name == 'webgl_extensions': return self._generate_webgl_extensions(os_name, browser_name, device_class)
        elif component_name == 'webgl_params': return self._generate_webgl_params(os_name, browser_name, device_class)
        elif component_name == 'hardware_concurrency': return self._generate_hardware_concurrency(os_name, device_class)
        elif component_name == 'device_memory': return self._generate_device_memory(os_name, device_class)
        elif component_name == 'screen_resolution': return self._calculate_screen_resolution(os_name, device_class) # Use new name
        elif component_name == 'viewport_dimensions': return self._calculate_viewport(get_current_val('screen_resolution',(1920,1080)), os_name, browser_name) # (Medium Prio 3)
        elif component_name == 'color_depth': return self._generate_color_depth(os_name, device_class)
        elif component_name == 'device_pixel_ratio': return self._generate_device_pixel_ratio(os_name, device_class)
        elif component_name == 'fonts_list': return self._generate_fonts_list(os_name)
        elif component_name == 'plugins_list': return self._generate_plugins_list(os_name, browser_name)
        elif component_name == 'locale': return self._generate_locale(get_current_val('languages', ['en-US'])[0])
        elif component_name == 'timezone': return self._generate_timezone(get_current_val('locale'))
        elif component_name == 'languages': return self._generate_languages(get_current_val('locale'))
        elif component_name == 'tls_ja3': return self._generate_tls_ja3(browser_name, browser_version, os_name) # (High Prio 3)
        elif component_name == 'canvas_params': return self._generate_canvas_params() # (High Prio 2)
        elif component_name == 'audio_context_params': return self._generate_audio_context_params() # (Stealth Gap 1)
        elif component_name == 'battery_status': return self._generate_battery_status(device_class) # (Stealth Gap 1)
        elif component_name == 'webrtc_ip_handling_mode': return self._generate_webrtc_mode() # (Medium Prio 2)

        current_comp = current_fingerprint_view.get(component_name)
        if current_comp: return current_comp.value
        raise ValueError(f"No generation strategy for component: {component_name}")

    def _generate_browser_version(self, browser_name: str, current_full_version: Optional[str]) -> str:
        # (Previous logic was good, ensure robustness for missing data)
        browser_info = self.browser_data.get(browser_name)
        if not browser_info: return current_full_version or "127.0.0.0" # Fallback

        major_versions = sorted(list(browser_info['versions'].keys()), key=int, reverse=True)
        if not major_versions: return current_full_version or "127.0.0.0"

        if current_full_version:
            current_major = current_full_version.split('.')[0]
            if random.random() < 0.8 and current_major in browser_info['versions']: # High chance to stay on same major
                possible_full_versions = browser_info['versions'][current_major]['full_versions']
                # Pick a different minor/patch, or same if only one option
                return random.choice([v for v in possible_full_versions if v != current_full_version] or [current_full_version])
            else: # Try to jump to a newer major or slightly older if at latest
                try:
                    current_major_idx = major_versions.index(current_major) # major_versions is sorted latest first
                    if current_major_idx == 0 and len(major_versions) > 1: # If current is latest, small chance to pick previous major
                        if random.random() < 0.2:
                             target_major = major_versions[1]
                             return random.choice(browser_info['versions'][target_major]['full_versions'])
                        else: # Stick to latest major, different build
                             return random.choice(browser_info['versions'][major_versions[0]]['full_versions'])
                    elif current_major_idx > 0: # Newer major exists (higher in list)
                        target_major = random.choice(major_versions[:current_major_idx])
                        return random.choice(browser_info['versions'][target_major]['full_versions'])
                except ValueError: pass # current_major not in our known list
        
        latest_major = major_versions[0]
        return random.choice(browser_info['versions'][latest_major]['full_versions'])

    def _generate_os_version(self, os_name: str, current_os_version_build: Optional[str]) -> str:
        # (Previous logic was good, ensure robustness)
        os_info = self.os_data.get(os_name)
        if not os_info: return current_os_version_build or "10.0.19045"

        major_os_versions = sorted(list(os_info['versions'].keys()), reverse=True) # Assuming keys are sortable (e.g. "10", "11" or "13", "14")
        if not major_os_versions: return current_os_version_build or "10.0.19045"

        if current_os_version_build:
            current_major_os = current_os_version_build.split('.')[0]
            if random.random() < 0.9 and current_major_os in os_info['versions']: # Very high chance to stay on same major OS
                return random.choice(os_info['versions'][current_major_os]['builds'])
            else: # Try to jump to a different major OS (could be newer or older)
                other_majors = [m for m in major_os_versions if m != current_major_os]
                if other_majors:
                    target_major_os = random.choice(other_majors)
                    return random.choice(os_info['versions'][target_major_os]['builds'])
        
        latest_major_os = major_os_versions[0]
        return random.choice(os_info['versions'][latest_major_os]['builds'])

    def _generate_user_agent(self, browser_name: str, browser_version: str, os_name: str, os_version_build: str) -> str:
        # (Previous logic was good, ensure robustness)
        browser_info = self.browser_data.get(browser_name)
        os_info = self.os_data.get(os_name)
        if not browser_info or not os_info:
            return f"Mozilla/5.0 (compatible; ProfileGenerator/2.0; {os_name}/{os_version_build}; {browser_name}/{browser_version})"

        ua_template_key = f'ua_template_{os_name.lower()}'
        ua_template = browser_info.get(ua_template_key, browser_info.get('ua_template_win')) # Default to Windows template

        os_major_key = os_version_build.split('.')[0]
        os_specific_data = os_info['versions'].get(os_major_key, {})
        
        # For macOS, UA often uses 10_15_7 regardless of actual OS version for compatibility
        # For Windows, it's usually Windows NT 10.0
        os_platform_string_version_part = os_specific_data.get('platform_string_version_part', '10_15_7' if os_name == 'macOS' else '10.0')
        if os_name == 'macOS': os_platform_string_version_part = os_platform_string_version_part.replace('.', '_')


        return ua_template.format(
            os_nt_version=os_specific_data.get('nt_version', '10.0'), # Primarily for Windows
            os_platform_string_version=os_platform_string_version_part, # Primarily for macOS
            version=browser_version
        )

    def _generate_sec_ch_ua(self, browser_name: str, browser_version: str) -> str:
        # (Previous logic was good, ensure robustness)
        browser_info = self.browser_data.get(browser_name)
        if not browser_info: return ''
        major_version_str = browser_version.split('.')[0]
        version_data = browser_info['versions'].get(major_version_str)
        if version_data and version_data.get('brands'):
            brands_tuple_list = random.choice(version_data['brands'])
            return ", ".join([f'"{brand}";v="{ver}"' for brand, ver in brands_tuple_list])
        return f'"Not_A Brand";v="8", "Chromium";v="{major_version_str}", "{browser_name}";v="{major_version_str}"'

    def _generate_sec_ch_ua_full_version_list(self, browser_name: str, browser_full_version: str) -> str:
        # (Previous logic was good, ensure robustness)
        browser_info = self.browser_data.get(browser_name)
        if not browser_info: return ''
        major_version_str = browser_full_version.split('.')[0]
        version_data = browser_info['versions'].get(major_version_str)
        if version_data and version_data.get('brands'):
            brands_tuple_list = random.choice(version_data['brands'])
            formatted_brands = []
            for brand_name_str, brand_major_ver_str in brands_tuple_list:
                ver_to_use = browser_full_version if browser_name in brand_name_str or "Chromium" in brand_name_str else f"{brand_major_ver_str}.0.0.0"
                formatted_brands.append(f'"{brand_name_str}";v="{ver_to_use}"')
            return ", ".join(formatted_brands)
        return f'"Not_A Brand";v="8.0.0.0", "Chromium";v="{browser_full_version}", "{browser_name}";v="{browser_full_version}"'

    def _generate_sec_ch_ua_platform(self, os_name: str) -> str:
        os_info = self.os_data.get(os_name)
        if os_info and os_info['versions']:
            # Get platform from the first available OS version entry (should be consistent)
            first_os_ver_key = list(os_info['versions'].keys())[0]
            return os_info['versions'][first_os_ver_key].get('sec_ch_ua_platform', f'"{os_name}"') # Fallback to OS name if not defined
        return f'"{os_name}"' # Fallback

    def _generate_sec_ch_ua_platform_version(self, os_name: str, os_version_build: str) -> str:
        # (Previous logic was good, ensure robustness)
        os_info = self.os_data.get(os_name)
        if not os_info: return '"0.0.0"'
        os_major_key = os_version_build.split('.')[0]
        os_ver_data = os_info['versions'].get(os_major_key)
        if os_ver_data and os_ver_data.get('sec_ch_ua_platform_versions'):
            return random.choice(os_ver_data['sec_ch_ua_platform_versions'])
        return '"0.0.0"'

    def _get_gpu_class_from_profile(self, os_name: str, device_class: str, current_renderer: Optional[str]=None) -> str:
        # Try to infer from current renderer if available
        if current_renderer:
            rs_lower = current_renderer.lower()
            if "nvidia" in rs_lower: return random.choice(['NVIDIA_HighEnd', 'NVIDIA_MidRange']) # Simplified
            if "amd" in rs_lower or "radeon" in rs_lower: return random.choice(['AMD_HighEnd', 'AMD_MidRange'])
            if "intel" in rs_lower: return 'Intel_Integrated' # Usually one main class for Intel integrated
            if "apple" in rs_lower or "m1" in rs_lower or "m2" in rs_lower or "m3" in rs_lower: return 'Apple_Silicon'
        
        # Fallback to device_class and os_name
        hw_profile = self.hardware_profiles.get(os_name, {}).get(device_class)
        if hw_profile and hw_profile.get('gpu_classes'):
            return random.choice(hw_profile['gpu_classes'])
        
        # Absolute fallback
        if os_name == "Windows": return random.choice(['NVIDIA_MidRange', 'AMD_MidRange', 'Intel_Integrated'])
        if os_name == "macOS": return 'Apple_Silicon'
        return 'Intel_Integrated' # Generic fallback


    def _generate_webgl_vendor(self, os_name: str, browser_name: str, device_class_or_gpu_class: str) -> str:
        # (Refined to use GPU class more directly if possible)
        db_os = self.webgl_database.get(os_name, self.webgl_database.get('Windows', {}))
        db_browser = db_os.get(browser_name, db_os.get('Chrome', {}))

        # If device_class_or_gpu_class is a known GPU class in db_browser
        if device_class_or_gpu_class in db_browser:
            gpu_class_to_use = device_class_or_gpu_class
        else: # Assume it's a device_class, try to map it to a GPU class
            gpu_class_to_use = self._get_gpu_class_from_profile(os_name, device_class_or_gpu_class, None)

        vendors_for_class = db_browser.get(gpu_class_to_use, {}).get('vendors')
        if vendors_for_class: return random.choice(vendors_for_class)
        return "Google Inc." # Fallback

    def _generate_webgl_renderer(self, os_name: str, browser_name: str, device_class_or_gpu_class: str, current_webgl_vendor: Optional[str]) -> str:
        # (Refined)
        db_os = self.webgl_database.get(os_name, self.webgl_database.get('Windows', {}))
        db_browser = db_os.get(browser_name, db_os.get('Chrome', {}))

        if device_class_or_gpu_class in db_browser: # If it's already a GPU class
            gpu_class_to_use = device_class_or_gpu_class
        else: # Assume it's a device_class, map it
            gpu_class_to_use = self._get_gpu_class_from_profile(os_name, device_class_or_gpu_class, None)
            # If current_webgl_vendor implies a different class, prefer that if consistent
            if current_webgl_vendor:
                inferred_gpu_class_from_vendor = self._get_gpu_class_from_profile(os_name, "generic", current_webgl_vendor) # "generic" device class
                if inferred_gpu_class_from_vendor != "generic" and inferred_gpu_class_from_vendor in db_browser:
                    gpu_class_to_use = inferred_gpu_class_from_vendor


        renderers_for_class = db_browser.get(gpu_class_to_use, {}).get('renderers')
        if renderers_for_class: return random.choice(renderers_for_class)
        
        all_renderers = [r for gc_data in db_browser.values() for r in gc_data.get('renderers', [])]
        return random.choice(all_renderers) if all_renderers else "Generic ANGLE Renderer"

    def _generate_webgl_extensions(self, os_name: str, browser_name: str, device_class_or_gpu_class: str) -> List[str]:
        # (Refined)
        db_os = self.webgl_database.get(os_name, self.webgl_database.get('Windows', {}))
        db_browser = db_os.get(browser_name, db_os.get('Chrome', {}))
        if device_class_or_gpu_class in db_browser: gpu_class_to_use = device_class_or_gpu_class
        else: gpu_class_to_use = self._get_gpu_class_from_profile(os_name, device_class_or_gpu_class, None)

        extensions_for_class = db_browser.get(gpu_class_to_use, {}).get('extensions')
        if extensions_for_class:
            num_to_select = random.randint(int(len(extensions_for_class)*0.85), len(extensions_for_class))
            return sorted(random.sample(extensions_for_class, num_to_select))
        return []

    def _generate_webgl_params(self, os_name: str, browser_name: str, device_class_or_gpu_class: str) -> Dict[str, Any]:
        # (Refined)
        db_os = self.webgl_database.get(os_name, self.webgl_database.get('Windows', {}))
        db_browser = db_os.get(browser_name, db_os.get('Chrome', {}))
        if device_class_or_gpu_class in db_browser: gpu_class_to_use = device_class_or_gpu_class
        else: gpu_class_to_use = self._get_gpu_class_from_profile(os_name, device_class_or_gpu_class, None)
        
        params_for_class = db_browser.get(gpu_class_to_use, {}).get('params')
        if params_for_class:
            # Add slight jitter
            return {k: (v + random.choice([-1,0,1]) if isinstance(v,int) and k == 'MAX_VERTEX_ATTRIBS' else v) for k,v in params_for_class.items()}
        return {'MAX_TEXTURE_SIZE': 16384, 'STENCIL_BITS': 0}

    def _generate_hardware_concurrency(self, os_name: str, device_class: str) -> int:
        # (Previous logic was good)
        hw_profile = self.hardware_profiles.get(os_name, {}).get(device_class)
        if hw_profile and hw_profile.get('cores'): return random.choice(hw_profile['cores'])
        return random.choice([4, 8, 12, 16])

    def _generate_device_memory(self, os_name: str, device_class: str) -> int:
        # (Previous logic was good, JS API capped at 8)
        hw_profile = self.hardware_profiles.get(os_name, {}).get(device_class)
        if hw_profile and hw_profile.get('memory'):
            actual_mem = random.choice(hw_profile['memory'])
            return min(8, 2**((actual_mem-1).bit_length())) # Rounds up to nearest power of 2, capped at 8
        return random.choice([4, 8])

    def _calculate_screen_resolution(self, os_name: str, device_class: str) -> Tuple[int, int]: # Renamed
        hw_profile = self.hardware_profiles.get(os_name, {}).get(device_class)
        if hw_profile and hw_profile.get('screen_resolutions'):
            return random.choice(hw_profile['screen_resolutions'])
        return (1920, 1080)

    def _calculate_viewport(self, screen_res: Tuple[int, int], os_name: str, browser_name: str) -> Tuple[int, int]: # (Medium Prio 3)
        screen_width, screen_height = screen_res
        # Approximate browser chrome sizes (top_chrome_height, side_borders_width)
        # These are very rough estimates and vary wildly.
        chrome_data = {
            ('Windows', 'Chrome'): {'top': 70, 'side': 0, 'bottom_os': 40}, # Taskbar
            ('macOS', 'Chrome'): {'top': 78, 'side': 0, 'bottom_os': 0},   # Menu bar handled by availHeight
            # Add more for Firefox, Safari, Edge...
        }
        default_chrome = {'top': 90, 'side': 0, 'bottom_os': 0}
        specific_chrome = chrome_data.get((os_name, browser_name), default_chrome)

        # Effective available height for viewport
        # On macOS, availHeight usually accounts for menu bar. On Windows, for taskbar.
        # This needs to be more robustly tied to how avail_height is set.
        # For now, assume screen_height is total, and we subtract OS chrome and browser chrome.
        
        # Simplified:
        vp_width = screen_width - specific_chrome['side']
        # Subtract browser top chrome and potential OS bottom chrome (taskbar)
        # A more robust approach would use the profile's avail_height and subtract browser top chrome.
        vp_height = screen_height - specific_chrome['top'] - specific_chrome['bottom_os']
        
        # Add some randomness for toolbars, etc.
        if random.random() < 0.2: vp_height -= random.choice([30, 50, 70]) # Bookmarks, extensions

        return (max(800, vp_width), max(600, vp_height)) # Ensure minimums


    def _generate_color_depth(self, os_name: str, device_class: str) -> int:
        # (Previous logic was good)
        hw_profile = self.hardware_profiles.get(os_name, {}).get(device_class)
        if hw_profile and hw_profile.get('color_depth'): return random.choice(hw_profile['color_depth'])
        return 24

    def _generate_device_pixel_ratio(self, os_name: str, device_class: str) -> float:
        # (Previous logic was good)
        hw_profile = self.hardware_profiles.get(os_name, {}).get(device_class)
        if hw_profile and hw_profile.get('dpr'): return random.choice(hw_profile['dpr'])
        return 1.0 if os_name == "Windows" else 2.0 # Common defaults

    def _generate_fonts_list(self, os_name: str) -> List[str]:
        # (Previous logic was good)
        base_fonts = self.font_database.get(os_name, self.font_database.get("Windows", []))
        if not base_fonts: return ["Arial", "Times New Roman"] # Absolute fallback
        num_fonts = random.randint(int(len(base_fonts) * 0.6), len(base_fonts))
        return sorted(random.sample(base_fonts, num_fonts))

    def _generate_plugins_list(self, os_name: str, browser_name: str) -> List[Dict[str, Any]]:
        # (Previous logic was good)
        key = f"{browser_name}_{os_name}"
        return copy.deepcopy(self.plugin_database.get(key, [])) # Return deepcopy to avoid modification

    def _generate_locale(self, primary_language_code: Optional[str]) -> str:
        # (Previous logic was good)
        if not primary_language_code: primary_language_code = "en"
        lang_prefix = primary_language_code.split('-')[0].lower()
        locales_for_lang = self.common_locales.get(lang_prefix)
        if locales_for_lang: return random.choice(locales_for_lang)
        return "en-US"

    def _generate_timezone(self, current_locale: Optional[str]) -> str:
        # (Previous logic was good)
        region = "Europe"
        if current_locale:
            lc = current_locale.lower()
            if any(x in lc for x in ["en-us", "es-mx", "fr-ca", "pt-br"]): region = "NorthAmerica" # Added pt-br
            elif any(x in lc for x in ["ja", "zh", "ko", "hi", "id"]): region = "Asia" # Added id
        timezones_for_region = self.common_timezones.get(region)
        if timezones_for_region: return random.choice(timezones_for_region)
        return "Etc/UTC" # Neutral fallback

    def _generate_languages(self, primary_locale: Optional[str]) -> List[str]:
        # (Previous logic was good)
        if not primary_locale: primary_locale = "en-US"
        languages = [primary_locale]
        lang_prefix = primary_locale.split('-')[0]
        related_locales = [loc for loc in self.common_locales.get(lang_prefix, []) if loc != primary_locale]
        if related_locales and random.random() < 0.8: languages.append(random.choice(related_locales))
        if lang_prefix != "en" and random.random() < 0.6: languages.append(random.choice(self.common_locales.get("en", ["en-US"])))
        return list(dict.fromkeys(languages))[:random.randint(1,3)] # 1 to 3 languages

    def _generate_tls_ja3(self, browser_name: str, browser_version: str, os_name: str) -> Optional[str]: # (High Prio 3)
        major_version = browser_version.split('.')[0]
        key = (browser_name, major_version, os_name)
        if key in self.tls_database: return self.tls_database[key]
        # Fallback: try same browser/OS, any version
        for (b, v, o), ja3 in self.tls_database.items():
            if b == browser_name and o == os_name: return ja3
        # Fallback: try same browser, any OS/version
        for (b, v, o), ja3 in self.tls_database.items():
            if b == browser_name: return ja3
        # Ultimate fallback (not ideal)
        return random.choice(list(self.tls_database.values())) if self.tls_database else None

    def _generate_canvas_params(self) -> Dict[str, Any]: # (High Prio 2)
        return {
            'noise_seed': random.randint(0, 2**32 - 1),
            'noise_intensity': round(random.uniform(0.00001, 0.00005), 7), # More precision
            'noise_r_shift': random.randint(0, 2),
            'noise_g_shift': random.randint(0, 2),
            'noise_b_shift': random.randint(0, 2),
            'text_angle_variation': round(random.uniform(-0.05, 0.05), 3), # Radians
            'text_baseline_variation': random.choice(['alphabetic', 'ideographic', 'bottom', 'top', 'middle']),
        }

    def _generate_audio_context_params(self) -> Dict[str, Any]: # (Stealth Gap 1)
        # Common sample rates, 44100 and 48000 are most frequent
        sample_rate = random.choice([44100, 48000, 44100, 48000, 32000, 96000])
        # DynamicsCompressorNode values often have slight variations
        return {
            'sample_rate': sample_rate,
            'base_latency': round(random.uniform(0.005, 0.030), 5), # e.g. for a 512 buffer at 48kHz ~0.01s
            'output_latency': round(random.uniform(0.010, 0.050), 5),
            'analyser_fft_size': random.choice([1024, 2048, 4096, 8192]),
            'compressor_threshold': round(random.uniform(-50, -40), 2),
            'compressor_knee': round(random.uniform(30, 40), 2),
            'compressor_ratio': round(random.uniform(10, 15), 2),
            'compressor_attack': round(random.uniform(0.001, 0.005), 4),
            'compressor_release': round(random.uniform(0.20, 0.30), 3),
        }

    def _generate_battery_status(self, device_class: str) -> Optional[Dict[str, Any]]: # (Stealth Gap 1)
        if "laptop" in device_class.lower() or "mobile" in device_class.lower(): # Assumes device_class indicates mobility
            charging = random.choice([True, False, False, True, False]) # More likely not charging
            level = round(random.uniform(0.15, 1.0), 2)
            charging_time = 0 if not charging or level == 1.0 else random.randint(600, 7200) # 10m to 2h
            discharging_time = float('inf') if charging or level == 0 else random.randint(3600, 28800) # 1h to 8h
            return {
                'charging': charging, 'level': level,
                'chargingTime': charging_time, 'dischargingTime': discharging_time
            }
        return None # No battery for desktops

    def _generate_webrtc_mode(self) -> str: # (Medium Prio 2)
        # These modes would be interpreted by stealth_init.js
        return random.choice([
            'default', # Allows all IPs (real, local, public via STUN)
            'default_public_interface_only', # Tries to only allow public IP from default route
            'disable_non_proxied_udp', # Advanced, tries to block UDP not via proxy
            'proxy_only_with_fallback', # Force proxy, fallback to public if proxy fails
            'disabled' # Completely disable WebRTC (highly detectable if feature is expected)
        ])


# --- DynamicProfile Class ---
class DynamicProfile:
    def __init__(self, mutation_strategy: MutationStrategy, base_profile_dict: Optional[Dict] = None, profile_id: Optional[str] = None):
        self.id = profile_id or self._generate_profile_id()
        self.mutation_strategy = mutation_strategy
        self.created_at = datetime.utcnow()
        self.last_active = datetime.utcnow()
        self.state = ProfileState.PRISTINE
        # Determine initial device_class more robustly
        self.device_class = (base_profile_dict.get('device_class') if base_profile_dict 
                             else self._determine_initial_device_class(base_profile_dict))

        self.fingerprint = self._initialize_fingerprint(base_profile_dict)
        self.behavioral_model = BehavioralModel()
        self.mutation_history: List[Dict] = []
        self.detection_history: List[Tuple[datetime, DetectionEvent, Dict]] = []
        self.success_count = 0
        self.failure_count = 0
        self.consecutive_failures = 0
        self.component_risk_scores: Dict[str, float] = defaultdict(float)
        self.mutation_cooldowns: Dict[str, datetime] = {}
        self.session_data: Dict[str, Any] = {}

    def _generate_profile_id(self) -> str: # (As before)
        return hashlib.sha256(str(random.random()).encode() + str(datetime.utcnow().timestamp()).encode()).hexdigest()[:16]

    def _determine_initial_device_class(self, base_profile_dict: Optional[Dict]) -> str: # (As before)
        if not base_profile_dict: return "mid_range_laptop"
        is_laptop = base_profile_dict.get('battery_status') is not None # Check for battery_status presence
        cores = base_profile_dict.get('hardware_concurrency', 8)
        if is_laptop:
            if cores >= 10: return "high_end_laptop"
            if cores >= 6: return "mid_range_laptop"
            return "low_end_laptop"
        else:
            if cores >= 12: return "high_end_desktop"
            return "mid_range_desktop"

    def _initialize_fingerprint(self, base_profile_dict: Optional[Dict]) -> Dict[str, FingerprintComponent]:
        fp: Dict[str, FingerprintComponent] = {}
        bp = base_profile_dict or {}
        ms = self.mutation_strategy # Alias for brevity

        # Initial primary choices (OS, Browser, Device Class)
        # These guide subsequent generations.
        os_name_val = bp.get('os_name', random.choice(list(ms.os_data.keys())))
        browser_name_val = bp.get('browser_name', random.choice(list(ms.browser_data.keys())))
        # device_class_val is self.device_class, already determined

        fp['os_name'] = FingerprintComponent(name='os_name', value=os_name_val, category='os', mutation_weight=0.02)
        fp['os_version'] = FingerprintComponent(name='os_version', value=bp.get('os_version', ms._generate_os_version(os_name_val, None)), category='os', dependencies={'os_name'}, mutation_weight=0.2)
        fp['device_class'] = FingerprintComponent(name='device_class', value=self.device_class, category='os', mutation_weight=0.05)

        fp['browser_name'] = FingerprintComponent(name='browser_name', value=browser_name_val, category='browser', mutation_weight=0.05)
        fp['browser_version'] = FingerprintComponent(name='browser_version', value=bp.get('browser_version', ms._generate_browser_version(browser_name_val, None)), category='browser', dependencies={'browser_name'}, mutation_weight=0.7)
        
        # Derived values based on initial choices
        # Pass the current state of fp (even if partially built) to generators that might need it
        # This is a bit tricky; ideally, generation should be top-down or iterative.
        # For now, generate primary ones, then derive others.
        
        # Screen and Viewport (Medium Prio 3 for viewport calculation)
        screen_res_val = bp.get('screen_resolution', ms._calculate_screen_resolution(os_name_val, self.device_class))
        fp['screen_resolution'] = FingerprintComponent(name='screen_resolution', value=screen_res_val, category='hardware', dependencies={'os_name', 'device_class'}, mutation_weight=0.1)
        viewport_val = bp.get('viewport_dimensions', ms._calculate_viewport(screen_res_val, os_name_val, browser_name_val))
        fp['viewport_dimensions'] = FingerprintComponent(name='viewport_dimensions', value=viewport_val, category='hardware', dependencies={'screen_resolution', 'os_name', 'browser_name'}, mutation_weight=0.1)


        # User Agent and Sec-CH-UA (dependent on many above)
        # Need to pass a view of fp for these generators
        temp_fp_view = {k:v for k,v in fp.items()} # Create a temporary view for generation
        
        ua_val = bp.get('user_agent', ms._generate_user_agent(browser_name_val, fp['browser_version'].value, os_name_val, fp['os_version'].value))
        fp['user_agent'] = FingerprintComponent(name='user_agent', value=ua_val, category='browser', dependencies={'browser_name', 'browser_version', 'os_name', 'os_version'}, mutation_weight=0.0)

        fp['sec_ch_ua'] = FingerprintComponent(name='sec_ch_ua', value=bp.get('sec_ch_ua', ms._generate_sec_ch_ua(browser_name_val, fp['browser_version'].value)), category='headers', dependencies={'browser_name', 'browser_version'}, mutation_weight=0.0)
        fp['sec_ch_ua_full_version_list'] = FingerprintComponent(name='sec_ch_ua_full_version_list', value=bp.get('sec_ch_ua_full_version_list', ms._generate_sec_ch_ua_full_version_list(browser_name_val, fp['browser_version'].value)), category='headers', dependencies={'browser_name', 'browser_version'}, mutation_weight=0.0)
        fp['sec_ch_ua_mobile'] = FingerprintComponent(name='sec_ch_ua_mobile', value=bp.get('sec_ch_ua_mobile', ("?1" if "mobile" in self.device_class.lower() or "tablet" in self.device_class.lower() else "?0")), category='headers', dependencies={'device_class'}, mutation_weight=0.01)
        fp['sec_ch_ua_platform'] = FingerprintComponent(name='sec_ch_ua_platform', value=bp.get('sec_ch_ua_platform', ms._generate_sec_ch_ua_platform(os_name_val)), category='headers', dependencies={'os_name'}, mutation_weight=0.0)
        fp['sec_ch_ua_platform_version'] = FingerprintComponent(name='sec_ch_ua_platform_version', value=bp.get('sec_ch_ua_platform_version', ms._generate_sec_ch_ua_platform_version(os_name_val, fp['os_version'].value)), category='headers', dependencies={'os_name', 'os_version'}, mutation_weight=0.0)
        # ... other Sec-CH-UA headers ...
        fp['sec_ch_ua_arch'] = FingerprintComponent(name='sec_ch_ua_arch', value=bp.get('sec_ch_ua_arch', ms.os_data.get(os_name_val, {}).get('sec_ch_ua_arch', '"x86"')), category='headers', dependencies={'os_name'}, mutation_weight=0.01)
        fp['sec_ch_ua_bitness'] = FingerprintComponent(name='sec_ch_ua_bitness', value=bp.get('sec_ch_ua_bitness', ms.os_data.get(os_name_val, {}).get('sec_ch_ua_bitness', '"64"')), category='headers', dependencies={'os_name'}, mutation_weight=0.01)
        fp['sec_ch_ua_model'] = FingerprintComponent(name='sec_ch_ua_model', value=bp.get('sec_ch_ua_model', '""'), category='headers', mutation_weight=0.01)
        fp['sec_ch_ua_wow64'] = FingerprintComponent(name='sec_ch_ua_wow64', value=bp.get('sec_ch_ua_wow64', ms.os_data.get(os_name_val, {}).get('sec_ch_ua_wow64')), category='headers', dependencies={'os_name', 'sec_ch_ua_arch'}, mutation_weight=0.0)


        # Hardware/Screen Category
        fp['color_depth'] = FingerprintComponent(name='color_depth', value=bp.get('color_depth', ms._generate_color_depth(os_name_val, self.device_class)), category='hardware', dependencies={'os_name', 'device_class'}, mutation_weight=0.05)
        fp['device_pixel_ratio'] = FingerprintComponent(name='device_pixel_ratio', value=bp.get('device_pixel_ratio', ms._generate_device_pixel_ratio(os_name_val, self.device_class)), category='hardware', dependencies={'os_name', 'device_class', 'screen_resolution'}, mutation_weight=0.05)
        fp['hardware_concurrency'] = FingerprintComponent(name='hardware_concurrency', value=bp.get('hardware_concurrency', ms._generate_hardware_concurrency(os_name_val, self.device_class)), category='hardware', dependencies={'os_name', 'device_class'}, mutation_weight=0.02, consistency_rules=[self._rule_hardware_vs_device_class])
        fp['device_memory'] = FingerprintComponent(name='device_memory', value=bp.get('device_memory', ms._generate_device_memory(os_name_val, self.device_class)), category='hardware', dependencies={'os_name', 'device_class'}, mutation_weight=0.02, consistency_rules=[self._rule_hardware_vs_device_class])

        # Rendering Category
        webgl_vendor_val = bp.get('webgl_vendor', ms._generate_webgl_vendor(os_name_val, browser_name_val, self.device_class))
        fp['webgl_vendor'] = FingerprintComponent(name='webgl_vendor', value=webgl_vendor_val, category='rendering', dependencies={'os_name', 'browser_name', 'device_class'}, mutation_weight=0.3)
        fp['webgl_renderer'] = FingerprintComponent(name='webgl_renderer', value=bp.get('webgl_renderer', ms._generate_webgl_renderer(os_name_val, browser_name_val, self.device_class, webgl_vendor_val)), category='rendering', dependencies={'webgl_vendor', 'os_name', 'browser_name', 'device_class'}, mutation_weight=0.4)
        fp['webgl_extensions'] = FingerprintComponent(name='webgl_extensions', value=bp.get('webgl_extensions', ms._generate_webgl_extensions(os_name_val, browser_name_val, self.device_class)), category='rendering', dependencies={'webgl_renderer'}, mutation_weight=0.1)
        fp['webgl_params'] = FingerprintComponent(name='webgl_params', value=bp.get('webgl_params', ms._generate_webgl_params(os_name_val, browser_name_val, self.device_class)), category='rendering', dependencies={'webgl_renderer'}, mutation_weight=0.05)
        fp['fonts_list'] = FingerprintComponent(name='fonts_list', value=bp.get('fonts_list', ms._generate_fonts_list(os_name_val)), category='rendering', dependencies={'os_name'}, mutation_weight=0.05)
        fp['plugins_list'] = FingerprintComponent(name='plugins_list', value=bp.get('plugins_list', ms._generate_plugins_list(os_name_val, browser_name_val)), category='rendering', dependencies={'os_name', 'browser_name'}, mutation_weight=0.01)

        # Canvas Params (High Prio 2)
        fp['canvas_params'] = FingerprintComponent(name='canvas_params', value=bp.get('canvas_params', ms._generate_canvas_params()), category='rendering', mutation_weight=0.2)

        # Audio Context Params (Stealth Gap 1)
        fp['audio_context_params'] = FingerprintComponent(name='audio_context_params', value=bp.get('audio_context_params', ms._generate_audio_context_params()), category='rendering', mutation_weight=0.1)

        # Localization Category
        locale_val = bp.get('locale', ms._generate_locale(None))
        fp['locale'] = FingerprintComponent(name='locale', value=locale_val, category='localization', mutation_weight=0.05)
        fp['timezone'] = FingerprintComponent(name='timezone', value=bp.get('timezone', ms._generate_timezone(locale_val)), category='localization', dependencies={'locale'}, mutation_weight=0.05)
        fp['languages'] = FingerprintComponent(name='languages', value=bp.get('languages', ms._generate_languages(locale_val)), category='localization', dependencies={'locale'}, mutation_weight=0.05)

        # Network Category
        fp['tls_ja3'] = FingerprintComponent(name='tls_ja3', value=bp.get('tls_ja3', ms._generate_tls_ja3(browser_name_val, fp['browser_version'].value, os_name_val)), category='network', dependencies={'browser_name', 'browser_version', 'os_name'}, mutation_weight=0.1)
        fp['webrtc_ip_handling_mode'] = FingerprintComponent(name='webrtc_ip_handling_mode', value=bp.get('webrtc_ip_handling_mode', ms._generate_webrtc_mode()), category='network', mutation_weight=0.02) # (Medium Prio 2)

        # Battery API (Stealth Gap 1)
        fp['battery_status'] = FingerprintComponent(name='battery_status', value=bp.get('battery_status', ms._generate_battery_status(self.device_class)), category='hardware', dependencies={'device_class'}, mutation_weight=0.05)
        
        # Add js_platform (often derived from os_name)
        fp['js_platform'] = FingerprintComponent(name='js_platform', value=bp.get('js_platform', ms.os_data.get(os_name_val, {}).get('js_platform', 'Win32')), category='os', dependencies={'os_name'}, mutation_weight=0.0)


        # Initial consistency pass for all components
        self._ensure_all_consistency(fp) # Pass the dict being built
        
        # Set last_mutated_value for all components after initialization
        for comp in fp.values():
            comp.last_mutated_value = copy.deepcopy(comp.value)
            
        return fp

    # --- Consistency Rules (Examples) ---
    def _rule_hardware_vs_device_class(self, current_fp_view: Dict[str, FingerprintComponent]):
        # This rule is now implicitly handled by _ensure_hardware_consistency
        # which calls generators that use device_class.
        # If more specific logic is needed, it can be added here.
        # For example, if device_class changes, it re-triggers generation of hardware_concurrency.
        pass


    def record_detection_event(self, event: DetectionEvent, metadata: Optional[Dict] = None): # (As before, good)
        metadata = metadata or {}
        self.detection_history.append((datetime.utcnow(), event, metadata))
        self.last_active = datetime.utcnow()
        if event == DetectionEvent.SUCCESS:
            self.success_count += 1; self.consecutive_failures = 0
            for comp_name in self.fingerprint.keys(): self.component_risk_scores[comp_name] = max(0, self.component_risk_scores[comp_name] - 0.05)
            if self.state == ProfileState.SUSPICIOUS and self.success_count > self.failure_count + 2: self.state = ProfileState.HEALTHY
        else:
            self.failure_count += 1; self.consecutive_failures +=1
            self._analyze_detection_cause(event, metadata)
        if event == DetectionEvent.HARD_BLOCK or self.consecutive_failures >= 3: self.state = ProfileState.COMPROMISED
        elif event != DetectionEvent.SUCCESS and self.state != ProfileState.COMPROMISED : self.state = ProfileState.SUSPICIOUS

    def _analyze_detection_cause(self, event: DetectionEvent, metadata: Dict): # (As before, good)
        base_risk_increase = 0.3 + (self.consecutive_failures * 0.1)
        for mr in self.mutation_history:
            if (datetime.utcnow() - mr['timestamp']).total_seconds() < 3600:
                for cn in mr['changed_components_dict'].keys(): self.component_risk_scores[cn] += 0.25 * base_risk_increase
        if event == DetectionEvent.CAPTCHA_CHALLENGE: self.component_risk_scores['behavioral_model'] += base_risk_increase # Conceptual
        elif event == DetectionEvent.HARD_BLOCK:
            for cn in ['user_agent', 'webgl_renderer', 'sec_ch_ua', 'tls_ja3', 'canvas_params']: self.component_risk_scores[cn] += base_risk_increase * 1.2


    def should_mutate(self, current_time: Optional[datetime] = None) -> bool: # (As before, good)
        now = current_time or datetime.utcnow()
        if self.state == ProfileState.COMPROMISED: return True
        if self.state == ProfileState.EVOLVING: return False
        hours_since_last_mutation = (now - (self.mutation_history[-1]['timestamp'] if self.mutation_history else self.created_at)).total_seconds() / 3600
        if hours_since_last_mutation > random.uniform(4*7*24, 8*7*24): return True # Natural browser update cycle
        if self.state == ProfileState.SUSPICIOUS and hours_since_last_mutation > random.uniform(0.5, 4): return True # Quicker for suspicious
        if self.state == ProfileState.HEALTHY and random.random() < 0.005 and hours_since_last_mutation > 24*3: return True # Small chance for healthy
        return False

    def mutate(self, force_level: Optional[str] = None) -> Dict[str, Any]: # (As before, good)
        original_state = self.state
        self.state = ProfileState.EVOLVING; self.last_active = datetime.utcnow()
        changed_summary: Dict[str, Dict[str,Any]] = {}
        if force_level == 'major' or original_state == ProfileState.COMPROMISED: changed_summary = self._major_evolution()
        elif force_level == 'moderate' or original_state == ProfileState.SUSPICIOUS: changed_summary = self._targeted_evolution()
        else: changed_summary = self._natural_evolution()
        self._record_mutation(force_level or original_state.value, changed_summary)
        if original_state == ProfileState.COMPROMISED:
            self.state = ProfileState.DORMANT; self.component_risk_scores.clear(); self.consecutive_failures = 0
        else:
            self.state = ProfileState.HEALTHY
            for cn in changed_summary.keys(): self.component_risk_scores[cn] = max(0, self.component_risk_scores[cn] * 0.5 - 0.1)
        return changed_summary

    def _get_components_to_mutate(self, num_components_to_change: int) -> List[str]: # (High Priority 1 - Corrected)
        now = datetime.utcnow()
        candidates = []
        for name, comp in self.fingerprint.items():
            cooldown_base = timedelta(hours=random.uniform(0.5, 12) / (self.component_risk_scores.get(name, 0) + 0.1)) # Shorter for high risk
            if name in self.mutation_cooldowns and (now - self.mutation_cooldowns[name]) < cooldown_base:
                continue
            
            # Ensure mutation_weight is positive to avoid issues with random.choices if all weights are zero
            effective_mutation_weight = max(0.001, comp.mutation_weight) # Smallest positive weight
            probability = effective_mutation_weight * (1 + self.component_risk_scores.get(name, 0.0) * 2.0) # Risk increases chance
            candidates.append({'name': name, 'probability': probability, 'component': comp})

        if not candidates: return []

        # Weighted sampling without replacement
        # Sort candidates by a random number biased by their probability (simulates weighted choice)
        # r**(1/weight) is a common technique. Higher weight -> higher chance of smaller r**(1/w) -> earlier in sort
        # To avoid issues with zero probability (which means zero weight):
        for cand in candidates:
            # Add a small epsilon to probability if it's zero to avoid division by zero or log(0)
            weight = max(cand['probability'], 1e-9) # Ensure weight is positive
            cand['sort_key'] = random.random() ** (1.0 / weight)
        
        candidates.sort(key=lambda x: x['sort_key'])
        
        selected_names = [c['name'] for c in candidates[:min(num_components_to_change, len(candidates))]]
        
        # Less frequently choose primary identifiers unless high risk
        final_choices = []
        primary_ids = {'os_name', 'browser_name', 'device_class'}
        for name in selected_names:
            if name in primary_ids and self.component_risk_scores.get(name,0) < 0.6 and random.random() > 0.05: # 5% chance if low risk
                continue
            final_choices.append(name)
        
        return final_choices[:num_components_to_change]


    def _natural_evolution(self) -> Dict[str, Any]: # (As before, good)
        # ... uses _get_components_to_mutate ...
        changed_components_summary = {}
        num_components_to_change = random.randint(1, 3)
        components_to_mutate = self._get_components_to_mutate(num_components_to_change)
        for comp_name in components_to_mutate:
            old_value = copy.deepcopy(self.fingerprint[comp_name].value)
            new_value = self.mutation_strategy.generate_plausible_value(comp_name, self.fingerprint)
            if json.dumps(new_value, sort_keys=True) != json.dumps(old_value, sort_keys=True): # Compare complex types
                self._apply_mutation(comp_name, new_value)
                changed_components_summary[comp_name] = {'old': old_value, 'new': new_value}
        if changed_components_summary: self._ensure_all_consistency(self.fingerprint)
        return changed_components_summary


    def _targeted_evolution(self) -> Dict[str, Any]: # (As before, good)
        # ... uses _get_components_to_mutate, prioritizes risky components ...
        changed_components_summary = {}
        sorted_risky_components = sorted(self.component_risk_scores.items(), key=lambda item: item[1], reverse=True)
        num_to_change = random.randint(2, 5)
        changed_count = 0
        mutated_this_cycle = set()

        for comp_name, risk_score in sorted_risky_components:
            if changed_count >= num_to_change: break
            if comp_name not in self.fingerprint or comp_name in mutated_this_cycle: continue
            if risk_score > 0.2 or random.random() < risk_score * 0.5: # Higher chance if risky
                old_value = copy.deepcopy(self.fingerprint[comp_name].value)
                new_value = self.mutation_strategy.generate_plausible_value(comp_name, self.fingerprint)
                if json.dumps(new_value, sort_keys=True) != json.dumps(old_value, sort_keys=True):
                    self._apply_mutation(comp_name, new_value)
                    changed_components_summary[comp_name] = {'old': old_value, 'new': new_value}
                    changed_count += 1
                    mutated_this_cycle.add(comp_name)
        
        if changed_count < num_to_change:
            additional_to_change = num_to_change - changed_count
            more_components = [c for c in self._get_components_to_mutate(additional_to_change + 5) if c not in mutated_this_cycle] # Get more candidates
            for comp_name in more_components[:additional_to_change]:
                old_value = copy.deepcopy(self.fingerprint[comp_name].value)
                new_value = self.mutation_strategy.generate_plausible_value(comp_name, self.fingerprint)
                if json.dumps(new_value, sort_keys=True) != json.dumps(old_value, sort_keys=True):
                    self._apply_mutation(comp_name, new_value)
                    changed_components_summary[comp_name] = {'old': old_value, 'new': new_value}
        
        if changed_components_summary: self._ensure_all_consistency(self.fingerprint)
        return changed_components_summary


    def _major_evolution(self) -> Dict[str, Any]: # (As before, good)
        # ... changes primary identifiers, then many others, then ensures all consistency ...
        changed_components_summary = {}
        evolution_path = random.choice(['os_change', 'browser_change', 'device_class_change', 'full_refresh'])
        
        # Store initial values of potentially changed core components
        initial_core_values = {
            'os_name': self.fingerprint['os_name'].value,
            'browser_name': self.fingerprint['browser_name'].value,
            'device_class': self.fingerprint['device_class'].value
        }

        target_os = initial_core_values['os_name']
        target_browser = initial_core_values['browser_name']
        target_device_class = initial_core_values['device_class']

        if evolution_path == 'os_change' or evolution_path == 'full_refresh':
            possible_os = list(self.mutation_strategy.os_data.keys())
            new_os = random.choice([os for os in possible_os if os != target_os] or [target_os])
            self._apply_mutation('os_name', new_os); target_os = new_os
            # Device class might need to change if OS changes dramatically (e.g. Win -> Mac)
            valid_device_classes = list(self.mutation_strategy.hardware_profiles.get(target_os, {}).keys())
            if valid_device_classes and target_device_class not in valid_device_classes:
                self._apply_mutation('device_class', random.choice(valid_device_classes)); target_device_class = self.fingerprint['device_class'].value


        if evolution_path == 'browser_change' or evolution_path == 'full_refresh':
            possible_browsers = list(self.mutation_strategy.browser_data.keys())
            new_browser = random.choice([b for b in possible_browsers if b != target_browser] or [target_browser])
            self._apply_mutation('browser_name', new_browser); target_browser = new_browser
            
        if evolution_path == 'device_class_change' or evolution_path == 'full_refresh':
             valid_device_classes = list(self.mutation_strategy.hardware_profiles.get(target_os, {}).keys())
             if valid_device_classes:
                new_device_class = random.choice([dc for dc in valid_device_classes if dc != target_device_class] or [target_device_class])
                self._apply_mutation('device_class', new_device_class); target_device_class = new_device_class

        # After primary changes, regenerate many dependent components
        # The _ensure_all_consistency will handle most of this.
        # We can also force-mutate a few more high-impact ones.
        high_impact_others = ['webgl_renderer', 'fonts_list', 'plugins_list', 'hardware_concurrency', 'screen_resolution', 'locale', 'tls_ja3']
        for comp_name in high_impact_others:
            if comp_name in self.fingerprint:
                 old_val = self.fingerprint[comp_name].value
                 new_val = self.mutation_strategy.generate_plausible_value(comp_name, self.fingerprint, target_os, target_browser, target_device_class)
                 if json.dumps(new_val, sort_keys=True) != json.dumps(old_val, sort_keys=True):
                     self._apply_mutation(comp_name, new_val)
        
        self._ensure_all_consistency(self.fingerprint)
        
        # Populate changed_components_summary by comparing current to last_mutated_value
        for name, comp in self.fingerprint.items():
            if json.dumps(comp.value, sort_keys=True) != json.dumps(comp.last_mutated_value, sort_keys=True):
                changed_components_summary[name] = {'old': comp.last_mutated_value, 'new': comp.value}
        
        return changed_components_summary

    def _apply_mutation(self, component_name: str, new_value: Any): # (As before, good)
        if component_name not in self.fingerprint: return
        component = self.fingerprint[component_name]
        component.last_mutated_value = copy.deepcopy(component.value)
        component.value = new_value
        self.mutation_cooldowns[component_name] = datetime.utcnow()
        for rule in component.consistency_rules: rule(self)

    def _record_mutation(self, mutation_type: str, changed_components_dict: Dict[str, Dict[str, Any]]): # (As before)
        self.mutation_history.append({'timestamp': datetime.utcnow(),'type': mutation_type,'changed_components_dict': changed_components_dict})
        if len(self.mutation_history) > 20: self.mutation_history.pop(0) # Limit history

    # --- Consistency Enforcement Methods ---
    def _ensure_all_consistency(self, fp_dict: Dict[str, FingerprintComponent]):
        # (Order matters. OS/Browser/DeviceClass first, then dependents)
        self._ensure_os_consistency(fp_dict)
        self._ensure_browser_consistency(fp_dict)
        self._ensure_device_class_consistency(fp_dict) # New: ensure device class aligns with OS
        
        self._ensure_hardware_consistency(fp_dict) # Depends on OS/DeviceClass
        self._ensure_screen_consistency(fp_dict)   # Depends on HW/DeviceClass
        
        self._ensure_user_agent_consistency(fp_dict) # Depends on Browser/OS versions
        self._ensure_sec_ch_ua_consistency(fp_dict)  # Depends on Browser/OS versions
        
        self.self_ensure_rendering_stack_consistency(fp_dict) # WebGL, Canvas, Audio, Fonts, Plugins
        self._ensure_localization_consistency(fp_dict)
        self._ensure_network_consistency(fp_dict) # TLS, WebRTC
        self._ensure_battery_consistency(fp_dict) # Depends on device_class

        # Final pass for any attached component rules
        for comp in fp_dict.values():
            for rule in comp.consistency_rules:
                rule(self)


    def _ensure_os_consistency(self, fp: Dict[str, FingerprintComponent]): # (As before)
        os_name_comp = fp['os_name']; os_ver_comp = fp['os_version']
        if os_name_comp.value != os_name_comp.last_mutated_value or not os_ver_comp.value: # If OS name changed or version is empty
            os_ver_comp.value = self.mutation_strategy._generate_os_version(os_name_comp.value, None)
        fp['js_platform'].value = self.mutation_strategy.os_data.get(os_name_comp.value, {}).get('js_platform', 'Win32')

    def _ensure_browser_consistency(self, fp: Dict[str, FingerprintComponent]): # (As before)
        browser_name_comp = fp['browser_name']; browser_ver_comp = fp['browser_version']
        if browser_name_comp.value != browser_name_comp.last_mutated_value or not browser_ver_comp.value:
            browser_ver_comp.value = self.mutation_strategy._generate_browser_version(browser_name_comp.value, None)

    def _ensure_device_class_consistency(self, fp: Dict[str, FingerprintComponent]):
        os_name = fp['os_name'].value
        device_class_comp = fp['device_class']
        valid_classes = list(self.mutation_strategy.hardware_profiles.get(os_name, {}).keys())
        if valid_classes and device_class_comp.value not in valid_classes:
            device_class_comp.value = random.choice(valid_classes)
            self.device_class = device_class_comp.value # Update instance attribute too


    def _ensure_user_agent_consistency(self, fp: Dict[str, FingerprintComponent]): # (As before)
        fp['user_agent'].value = self.mutation_strategy._generate_user_agent(fp['browser_name'].value, fp['browser_version'].value, fp['os_name'].value, fp['os_version'].value)

    def _ensure_sec_ch_ua_consistency(self, fp: Dict[str, FingerprintComponent]): # (As before, ensure all parts are updated)
        b_name = fp['browser_name'].value; b_ver = fp['browser_version'].value
        os_name = fp['os_name'].value; os_ver = fp['os_version'].value
        fp['sec_ch_ua'].value = self.mutation_strategy._generate_sec_ch_ua(b_name, b_ver)
        fp['sec_ch_ua_full_version_list'].value = self.mutation_strategy._generate_sec_ch_ua_full_version_list(b_name, b_ver)
        fp['sec_ch_ua_platform'].value = self.mutation_strategy._generate_sec_ch_ua_platform(os_name)
        fp['sec_ch_ua_platform_version'].value = self.mutation_strategy._generate_sec_ch_ua_platform_version(os_name, os_ver)
        os_data = self.mutation_strategy.os_data.get(os_name, {})
        fp['sec_ch_ua_arch'].value = os_data.get('sec_ch_ua_arch', '"x86"')
        fp['sec_ch_ua_bitness'].value = os_data.get('sec_ch_ua_bitness', '"64"')
        fp['sec_ch_ua_wow64'].value = os_data.get('sec_ch_ua_wow64') # Can be None
        is_mobile_device = "mobile" in self.device_class.lower() or "tablet" in self.device_class.lower()
        fp['sec_ch_ua_mobile'].value = "?1" if is_mobile_device else "?0"
        fp['sec_ch_ua_model'].value = '""' # Typically empty for non-mobile, or needs mobile model data

    def _ensure_hardware_consistency(self, fp: Dict[str, FingerprintComponent]):
        os_name = fp['os_name'].value; device_class = fp['device_class'].value
        fp['hardware_concurrency'].value = self.mutation_strategy._generate_hardware_concurrency(os_name, device_class)
        fp['device_memory'].value = self.mutation_strategy._generate_device_memory(os_name, device_class)

    def _ensure_screen_consistency(self, fp: Dict[str, FingerprintComponent]):
        os_name = fp['os_name'].value; device_class = fp['device_class'].value; browser_name = fp['browser_name'].value
        fp['screen_resolution'].value = self.mutation_strategy._calculate_screen_resolution(os_name, device_class)
        fp['color_depth'].value = self.mutation_strategy._generate_color_depth(os_name, device_class)
        fp['device_pixel_ratio'].value = self.mutation_strategy._generate_device_pixel_ratio(os_name, device_class)
        # Update viewport based on new screen resolution
        fp['viewport_dimensions'].value = self.mutation_strategy._calculate_viewport(fp['screen_resolution'].value, os_name, browser_name)


    def self_ensure_rendering_stack_consistency(self, fp: Dict[str, FingerprintComponent]):
        os_name = fp['os_name'].value; browser_name = fp['browser_name'].value; device_class = fp['device_class'].value
        # WebGL
        fp['webgl_vendor'].value = self.mutation_strategy._generate_webgl_vendor(os_name, browser_name, device_class)
        fp['webgl_renderer'].value = self.mutation_strategy._generate_webgl_renderer(os_name, browser_name, device_class, fp['webgl_vendor'].value)
        fp['webgl_extensions'].value = self.mutation_strategy._generate_webgl_extensions(os_name, browser_name, device_class)
        fp['webgl_params'].value = self.mutation_strategy._generate_webgl_params(os_name, browser_name, device_class)
        # Canvas, Audio
        fp['canvas_params'].value = self.mutation_strategy._generate_canvas_params()
        fp['audio_context_params'].value = self.mutation_strategy._generate_audio_context_params()
        # Fonts, Plugins
        fp['fonts_list'].value = self.mutation_strategy._generate_fonts_list(os_name)
        fp['plugins_list'].value = self.mutation_strategy._generate_plugins_list(os_name, browser_name)

    def _ensure_localization_consistency(self, fp: Dict[str, FingerprintComponent]): # (As before)
        locale_val = fp['locale'].value
        fp['languages'].value = self.mutation_strategy._generate_languages(locale_val)
        fp['timezone'].value = self.mutation_strategy._generate_timezone(locale_val)

    def _ensure_network_consistency(self, fp: Dict[str, FingerprintComponent]):
        fp['tls_ja3'].value = self.mutation_strategy._generate_tls_ja3(fp['browser_name'].value, fp['browser_version'].value, fp['os_name'].value)
        fp['webrtc_ip_handling_mode'].value = self.mutation_strategy._generate_webrtc_mode()

    def _ensure_battery_consistency(self, fp: Dict[str, FingerprintComponent]):
        fp['battery_status'].value = self.mutation_strategy._generate_battery_status(fp['device_class'].value)


    def get_fingerprint_snapshot(self) -> Dict[str, Any]: # (As before)
        return {name: component.value for name, component in self.fingerprint.items()}

    def get_platform_config(self, platform: str) -> Dict[str, Any]: # (High Priority 4)
        """Get platform-specific stealth configurations and behavioral hints."""
        # These are examples; they should be more dynamic or loaded from a config.
        # Values can be influenced by the profile's current state or behavioral model.
        base_locale = self.fingerprint.get('locale', FingerprintComponent('locale','en-US','','') ).value
        
        configs = {
            'fansale': {
                'viewport_scale_factor': random.uniform(0.96, 0.99), # e.g. for calculating viewport from screen
                'mouse_style': 'smooth_natural', # Hint for behavioral simulation
                'typing_variation_factor': round(1.0 + self.behavioral_model.confidence_level * 0.2, 2), # Faster if confident
                'extra_http_headers': {
                    'X-Requested-With': 'XMLHttpRequest', # Common for AJAX
                    'Accept-Language': base_locale.replace('_', '-') + ",en;q=0.8" # Platform specific lang pref
                },
                'click_humanization_params': { # For behavioral simulation
                    'pre_delay_ms_range': (int(80 * (2-self.behavioral_model.confidence_level)), int(250 * (2-self.behavioral_model.confidence_level))),
                    'hold_time_ms_range': (int(60 * self.behavioral_model.confidence_level), int(130 * self.behavioral_model.confidence_level)),
                },
                'dom_interaction_delay_ms_factor': round(1.0 + (1.0-self.behavioral_model.confidence_level)*0.5, 2) # Slower if less confident
            },
            'ticketmaster': {
                'queue_aware_behavior': True, # Hint for logic dealing with queues
                'viewport_scale_factor': 1.0,
                'strict_tls_profile_adherence': True, # Hint for network layer
                'captcha_interaction_mode': 'humanoid_slow', # Hint for captcha solver interaction
                'mouse_style': 'deliberate_precise',
                'request_delay_ms_range': (int(400 * (1.5-self.behavioral_model.confidence_level)), int(1800 * (1.5-self.behavioral_model.confidence_level))),
            },
            'vivaticket': {
                'locale_strict_check_expected': True, # Hint that site might be sensitive to locale/IP mismatch
                'timezone_consistency_check_expected': True,
                'viewport_scale_factor': random.uniform(0.94, 0.97),
                'font_enumeration_max_allowed': 60, # Site might check for too many fonts
                'plugin_count_max_allowed': 3, # Site might check for too many plugins
            }
        }
        default_config = {
            'viewport_scale_factor': 0.98, 'mouse_style': 'standard',
            'typing_variation_factor': 1.0, 'extra_http_headers': {}
        }
        return configs.get(platform.lower(), default_config)

    def update_behavioral_model(self, interaction_success: bool): # (Medium Prio 1)
        """Adapt behavioral patterns based on success/failure of an interaction."""
        self.behavioral_model.adapt_behavior(interaction_success)
        logger.debug(f"Behavioral model adapted. Success: {interaction_success}. New confidence: {self.behavioral_model.confidence_level:.2f}")


    def get_stealth_init_js_profile_data(self) -> Dict[str, Any]:
        fp_snapshot = self.get_fingerprint_snapshot()
        screen_w, screen_h = fp_snapshot.get('screen_resolution', (1920, 1080))
        vp_w, vp_h = fp_snapshot.get('viewport_dimensions', (int(screen_w*0.95), int(screen_h*0.85)))

        # This structure should closely match what `stealth_init.js` expects.
        # It's a conversion from our `FingerprintComponent` structure to the older `BrowserProfile` like dict.
        js_profile = {
            "name": self.id,
            "user_agent": fp_snapshot.get('user_agent'),
            "viewport_width": vp_w,
            "viewport_height": vp_h,
            "screen_width": screen_w,
            "screen_height": screen_h,
            # availWidth/Height should be screen - OS chrome (taskbar/menubar)
            # This needs a more robust calculation based on OS.
            "avail_width": screen_w,
            "avail_height": screen_h - random.choice([0, 25, 40, 48, 72, 80]), # Simplified OS chrome approximation
            "device_pixel_ratio": fp_snapshot.get('device_pixel_ratio'),
            "color_depth": fp_snapshot.get('color_depth'),
            "pixel_depth": fp_snapshot.get('color_depth'), # Often same

            "js_platform": fp_snapshot.get('js_platform'),
            "hardware_concurrency": fp_snapshot.get('hardware_concurrency'),
            "device_memory": fp_snapshot.get('device_memory'), # JS API caps at 8
            "timezone": fp_snapshot.get('timezone'),
            "locale": fp_snapshot.get('locale'),
            
            "extra_js_props": {
                # Navigator overrides
                "navigator_languages_override": fp_snapshot.get('languages'),
                "navigator_vendor": "Google Inc." if "Chrome" in fp_snapshot.get('browser_name','') else "Apple Computer, Inc." if "Safari" in fp_snapshot.get('browser_name','') else "",
                "navigator_appName": "Netscape", # Common legacy value
                "navigator_product": "Gecko",    # Common legacy value
                "maxTouchPoints": 0 if "desktop" in self.device_class else random.choice([1,2,5,10]), # Basic touch points
                "pdfViewerEnabled": True, # Most browsers have this

                # WebGL - stealth_init.js needs these if it's doing fine-grained WebGL spoofing
                "webgl_vendor": fp_snapshot.get('webgl_vendor'),
                "webgl_renderer": fp_snapshot.get('webgl_renderer'),
                "webgl_extensions": fp_snapshot.get('webgl_extensions'),
                "webgl_parameters": fp_snapshot.get('webgl_params'),

                # Canvas
                "canvas_fp_noise": fp_snapshot.get('canvas_params'), # Pass the whole dict

                # Audio - Pass the whole dict for stealth_init.js to use
                "audio_context_details": fp_snapshot.get('audio_context_params'),

                # Battery
                "battery": fp_snapshot.get('battery_status'),

                # Plugins
                "plugins": fp_snapshot.get('plugins_list'),
                
                # Fonts (if stealth_init.js does font list spoofing, otherwise not needed here)
                # "system_fonts": fp_snapshot.get('fonts_list'),

                # WebRTC
                "webrtc_ip_handling_mode": fp_snapshot.get('webrtc_ip_handling_mode'),

                # Other specific values stealth_init.js might expect
                # Ensure all relevant components from fp_snapshot are mapped or included here
            }
        }
        # For any component in fp_snapshot not explicitly mapped, add it to extra_js_props
        # to ensure stealth_init.js has access if it needs it.
        for key, value in fp_snapshot.items():
            if key not in js_profile and key not in js_profile["extra_js_props"]:
                js_profile["extra_js_props"][key] = value
        
        return js_profile