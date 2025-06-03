# src/core/dynamic_profile_bridge.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
from .browser_profiles import BrowserProfile
from .advanced_profile_system import DynamicProfile, BehavioralModel, MutationSchedule

class DynamicProfileAdapter:
    """Adapts DynamicProfile to work with existing BrowserProfile infrastructure"""
    
    @staticmethod
    def dynamic_to_browser_profile(dynamic_profile: DynamicProfile) -> BrowserProfile:
        """Convert current state of DynamicProfile to BrowserProfile"""
        fingerprint = dynamic_profile.get_current_fingerprint()
        
        # Map dynamic fingerprint fields to BrowserProfile fields
        return BrowserProfile(
            name=fingerprint.get('name', f"Dynamic_{int(datetime.now().timestamp())}"),
            user_agent=fingerprint['user_agent'],
            viewport_width=fingerprint['viewport_width'],
            viewport_height=fingerprint['viewport_height'],
            screen_width=fingerprint['screen_width'],
            screen_height=fingerprint['screen_height'],
            sec_ch_ua=fingerprint['sec_ch_ua'],
            js_platform=fingerprint['js_platform'],
            timezone=fingerprint['timezone'],
            locale=fingerprint['locale'],
            webgl_vendor=fingerprint['webgl_vendor'],
            webgl_renderer=fingerprint['webgl_renderer'],
            webgl_version=fingerprint['webgl_version'],
            webgl_shading_language_version=fingerprint['webgl_shading_language_version'],
            connection_type=fingerprint['connection_type'],
            # Map optional fields
            battery_level=fingerprint.get('battery', {}).get('level'),
            battery_charging=fingerprint.get('battery', {}).get('charging'),
            canvas_noise_level=fingerprint.get('canvas_noise', {}).get('intensity', 0.00003),
            # Behavioral traits
            biometric_profile=dynamic_profile.behavioral_model.get_biometric_profile(),
            # Additional fields...
            extra_js_props=fingerprint
        )