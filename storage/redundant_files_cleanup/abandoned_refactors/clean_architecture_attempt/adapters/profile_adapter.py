# Profile Adapter
"""
Adapter to bridge between old profile models and new domain entities.
"""
from typing import Any, Dict, Optional
from domain.entities import BrowserProfile, ProfileQuality, ProfileState, ProxyConfig


class ProfileAdapter:
    """Converts between different profile representations"""
    
    @staticmethod
    def from_old_profile(old_profile: Any) -> BrowserProfile:
        """Convert old profile model to new BrowserProfile entity"""
        # Create new profile
        profile = BrowserProfile()
        
        # Copy basic fields if they exist
        if hasattr(old_profile, 'profile_id'):
            profile.profile_id = old_profile.profile_id
        elif hasattr(old_profile, 'id'):
            profile.profile_id = old_profile.id
        
        # Browser info
        if hasattr(old_profile, 'browser'):
            profile.browser = old_profile.browser
        if hasattr(old_profile, 'browser_version'):
            profile.browser_version = old_profile.browser_version
        if hasattr(old_profile, 'os'):
            profile.os = old_profile.os
        if hasattr(old_profile, 'user_agent'):
            profile.user_agent = old_profile.user_agent
        
        # Display settings
        if hasattr(old_profile, 'viewport_width'):
            profile.viewport_width = old_profile.viewport_width
        if hasattr(old_profile, 'viewport_height'):
            profile.viewport_height = old_profile.viewport_height
        if hasattr(old_profile, 'screen_width'):
            profile.screen_width = old_profile.screen_width
        if hasattr(old_profile, 'screen_height'):
            profile.screen_height = old_profile.screen_height
        
        # Location settings
        if hasattr(old_profile, 'locale'):
            profile.locale = old_profile.locale
        if hasattr(old_profile, 'timezone'):
            profile.timezone = old_profile.timezone
        if hasattr(old_profile, 'accept_language'):
            profile.accept_language = old_profile.accept_language
        
        # Hardware
        if hasattr(old_profile, 'hardware_concurrency'):
            profile.hardware_concurrency = old_profile.hardware_concurrency
        if hasattr(old_profile, 'device_memory'):
            profile.device_memory = old_profile.device_memory
        if hasattr(old_profile, 'gpu_vendor'):
            profile.gpu_vendor = old_profile.gpu_vendor
        if hasattr(old_profile, 'gpu_model'):
            profile.gpu_model = old_profile.gpu_model
        
        # Quality and state
        if hasattr(old_profile, 'quality'):
            if isinstance(old_profile.quality, ProfileQuality):
                profile.quality = old_profile.quality
            else:
                # Try to convert from string or other format
                profile.quality = ProfileQuality.MEDIUM
        
        # Usage stats
        if hasattr(old_profile, 'use_count'):
            profile.use_count = old_profile.use_count
        if hasattr(old_profile, 'success_count'):
            profile.success_count = old_profile.success_count
        if hasattr(old_profile, 'failure_count'):
            profile.failure_count = old_profile.failure_count
        if hasattr(old_profile, 'last_used'):
            profile.last_used = old_profile.last_used
        if hasattr(old_profile, 'created_at'):
            profile.created_at = old_profile.created_at
        
        # Sessions
        if hasattr(old_profile, 'sessions'):
            profile.sessions = old_profile.sessions
        elif hasattr(old_profile, 'platform_sessions'):
            profile.sessions = old_profile.platform_sessions
        
        # Platforms
        if hasattr(old_profile, 'platforms'):
            if isinstance(old_profile.platforms, set):
                profile.platforms = {str(p) for p in old_profile.platforms}
            else:
                profile.platforms = set()
        
        # Proxy
        if hasattr(old_profile, 'proxy'):
            profile.proxy = ProfileAdapter._convert_proxy(old_profile.proxy)
        elif hasattr(old_profile, 'proxy_config'):
            profile.proxy = ProfileAdapter._convert_proxy(old_profile.proxy_config)
        
        return profile
    
    @staticmethod
    def _convert_proxy(old_proxy: Any) -> Optional[ProxyConfig]:
        """Convert old proxy configuration to new ProxyConfig"""
        if not old_proxy:
            return None
        
        if isinstance(old_proxy, ProxyConfig):
            return old_proxy
        
        if isinstance(old_proxy, dict):
            return ProxyConfig(
                host=old_proxy.get('host', ''),
                port=old_proxy.get('port', 0),
                username=old_proxy.get('username'),
                password=old_proxy.get('password'),
                proxy_type=old_proxy.get('proxy_type', 'http'),
                country_code=old_proxy.get('country_code'),
                proxy_provider=old_proxy.get('proxy_provider')
            )
        
        if hasattr(old_proxy, 'host'):
            return ProxyConfig(
                host=getattr(old_proxy, 'host', ''),
                port=getattr(old_proxy, 'port', 0),
                username=getattr(old_proxy, 'username', None),
                password=getattr(old_proxy, 'password', None),
                proxy_type=getattr(old_proxy, 'proxy_type', 'http'),
                country_code=getattr(old_proxy, 'country_code', None),
                proxy_provider=getattr(old_proxy, 'proxy_provider', None)
            )
        
        return None
    
    @staticmethod
    def to_context_params(profile: BrowserProfile) -> Dict[str, Any]:
        """Convert profile to Playwright context parameters"""
        params = {
            'viewport': {'width': profile.viewport_width, 'height': profile.viewport_height},
            'screen': {'width': profile.screen_width, 'height': profile.screen_height},
            'user_agent': profile.user_agent,
            'locale': profile.locale,
            'timezone_id': profile.timezone,
            'color_scheme': 'light',
            'device_scale_factor': 1.0,
            'has_touch': False,
            'is_mobile': profile.device_type == 'mobile',
        }
        
        # Proxy configuration
        if profile.proxy:
            proxy_url = profile.proxy.get_proxy_url()
            if proxy_url:
                params['proxy'] = {'server': proxy_url}
        
        # Headers
        headers = {
            'Accept-Language': profile.accept_language,
            'Accept-Encoding': 'gzip, deflate, br'
        }
        params['extra_http_headers'] = headers
        
        # Permissions
        params['permissions'] = ['geolocation']
        params['geolocation'] = {'latitude': 41.9028, 'longitude': 12.4964}  # Rome
        
        return params