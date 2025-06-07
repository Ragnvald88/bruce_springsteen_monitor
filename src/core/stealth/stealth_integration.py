# src/core/stealth_integration.py
"""
StealthMaster AI Integration Layer
Seamless integration bridge between StealthEngine and existing Bruce Springsteen monitoring system
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from playwright.async_api import BrowserContext, Page
from .stealth_engine import (
    StealthEngine, 
    DeviceProfile, 
    create_stealth_engine,
    StealthEngineIntegration
)

logger = logging.getLogger(__name__)

class BruceStealthIntegration:
    """
    Integration bridge for Bruce Springsteen ticket monitoring system
    Provides seamless StealthEngine integration with existing codebase
    """
    
    def __init__(self, live_status_logger=None):
        self.stealth_engine = create_stealth_engine()
        self.live_status_logger = live_status_logger
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Platform-specific configurations
        self.platform_configs = {
            'fansale': {
                'preferred_locales': ['it-IT', 'en-US'],
                'preferred_browsers': ['Chrome', 'Firefox', 'Safari'],
                'device_bias': 'balanced',  # mobile, desktop, balanced
                'stealth_level': 'high'
            },
            'ticketmaster': {
                'preferred_locales': ['en-US', 'en-GB'],
                'preferred_browsers': ['Chrome', 'Edge'],
                'device_bias': 'desktop',
                'stealth_level': 'ultra'
            },
            'vivaticket': {
                'preferred_locales': ['it-IT', 'en-US'],
                'preferred_browsers': ['Chrome', 'Firefox'],
                'device_bias': 'balanced',
                'stealth_level': 'high'
            }
        }
        
        logger.info("🛡️ BruceStealthIntegration initialized - StealthMaster AI ready!")
    
    def convert_legacy_profile_to_device_profile(self, legacy_profile: Dict[str, Any], platform: str = "generic") -> DeviceProfile:
        """
        Convert existing profile format to StealthEngine DeviceProfile
        """
        platform_config = self.platform_configs.get(platform, self.platform_configs['fansale'])
        
        # Extract values with intelligent defaults
        device_type = legacy_profile.get('device_type', 'desktop')
        os_name = legacy_profile.get('os', 'Windows 11')
        browser = legacy_profile.get('browser', platform_config['preferred_browsers'][0])
        
        # Smart screen resolution selection
        screen_width = legacy_profile.get('screen_width', 1920)
        screen_height = legacy_profile.get('screen_height', 1080)
        
        # Generate realistic viewport
        viewport_width = legacy_profile.get('viewport_width', screen_width - 100)
        viewport_height = legacy_profile.get('viewport_height', screen_height - 150)
        
        # Hardware intelligence
        cpu_cores = legacy_profile.get('hardware_concurrency', 8)
        memory_gb = legacy_profile.get('device_memory', 16)
        
        # GPU selection based on profile or intelligent defaults
        gpu_vendor = legacy_profile.get('gpu_vendor', 'NVIDIA')
        gpu_model = legacy_profile.get('gpu_model', 'GeForce RTX 3060')
        
        # Locale handling for platform optimization
        if platform == 'fansale' and not legacy_profile.get('locale'):
            locale = 'it-IT'
            languages = ['it-IT', 'it', 'en-US', 'en']
            timezone = 'Europe/Rome'
        else:
            locale = legacy_profile.get('locale', 'en-US')
            languages = legacy_profile.get('languages', [locale, 'en'])
            timezone = legacy_profile.get('timezone', 'America/New_York')
        
        # Browser version intelligence
        browser_version = legacy_profile.get('browser_version')
        if not browser_version:
            version_map = {
                'Chrome': '121.0.6167.85',
                'Firefox': '122.0',
                'Safari': '17.2.1',
                'Edge': '121.0.2277.83'
            }
            browser_version = version_map.get(browser, '121.0.6167.85')
        
        device_profile = DeviceProfile(
            device_type=device_type,
            os=os_name,
            os_version=self._get_os_version(os_name),
            browser=browser,
            browser_version=browser_version,
            screen_res=(screen_width, screen_height),
            viewport_size=(viewport_width, viewport_height),
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            gpu_vendor=gpu_vendor,
            gpu_model=gpu_model,
            timezone=timezone,
            locale=locale,
            languages=languages,
            platform_hints={'target': platform, 'legacy_profile_id': legacy_profile.get('id')}
        )
        
        if self.live_status_logger:
            self.live_status_logger.log_status(
                "SUCCESS", "PROFILE", 
                f"Converted legacy profile to StealthEngine DeviceProfile for {platform}",
                {"browser": browser, "os": os_name, "locale": locale}
            )
        
        return device_profile
    
    async def create_stealth_browser_context(self, 
                                           browser, 
                                           legacy_profile: Dict[str, Any], 
                                           platform: str = "generic") -> BrowserContext:
        """
        Create a fully protected browser context using StealthEngine
        Replaces existing browser context creation logic
        """
        if self.live_status_logger:
            self.live_status_logger.log_status(
                "PROGRESS", "BROWSER", 
                f"Creating stealth browser context for {platform}...",
                progress=25.0
            )
        
        try:
            # Convert legacy profile to DeviceProfile
            device_profile = self.convert_legacy_profile_to_device_profile(legacy_profile, platform)
            
            if self.live_status_logger:
                self.live_status_logger.log_status(
                    "PROGRESS", "BROWSER", 
                    "Applying advanced anti-detection...",
                    progress=50.0
                )
            
            # Create base context with basic options
            context_options = {
                'viewport': {
                    'width': device_profile.viewport_size[0],
                    'height': device_profile.viewport_size[1]
                },
                'user_agent': self._generate_user_agent(device_profile),
                'locale': device_profile.locale,
                'timezone_id': device_profile.timezone,
                'permissions': ['geolocation', 'notifications'],
                'extra_http_headers': {
                    'Accept-Language': ','.join(device_profile.languages[:3]),
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1'
                }
            }
            
            # Add Chrome-specific headers
            if device_profile.browser == 'Chrome':
                context_options['extra_http_headers'].update({
                    'sec-ch-ua': f'"Not_A Brand";v="8", "Chromium";v="{device_profile.browser_version.split(".")[0]}", "Google Chrome";v="{device_profile.browser_version.split(".")[0]}"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': f'"{device_profile.os.split()[0]}"'
                })
            
            # Create context
            context = await browser.new_context(**context_options)
            
            if self.live_status_logger:
                self.live_status_logger.log_status(
                    "PROGRESS", "BROWSER", 
                    "Injecting StealthMaster AI protection...",
                    progress=75.0
                )
            
            # Apply StealthEngine protection
            stealth_context = await self.stealth_engine.create_stealth_context(
                context, device_profile, platform
            )
            
            # Store session info for tracking
            session_id = f"{platform}_{device_profile.browser}_{int(asyncio.get_event_loop().time())}"
            self.active_sessions[session_id] = {
                'context': stealth_context,
                'device_profile': device_profile,
                'platform': platform,
                'created_at': asyncio.get_event_loop().time(),
                'success_count': 0,
                'detection_count': 0
            }
            
            if self.live_status_logger:
                self.live_status_logger.log_status(
                    "SUCCESS", "BROWSER", 
                    f"StealthMaster AI context ready for {platform}!",
                    {
                        "session_id": session_id,
                        "browser": device_profile.browser,
                        "os": device_profile.os,
                        "stealth_level": self.platform_configs.get(platform, {}).get('stealth_level', 'high')
                    },
                    progress=100.0
                )
            
            return stealth_context
            
        except Exception as e:
            if self.live_status_logger:
                self.live_status_logger.log_status(
                    "ERROR", "BROWSER", 
                    f"Failed to create stealth context: {str(e)}",
                    {"error": str(e), "platform": platform}
                )
            logger.error(f"StealthEngine context creation failed: {e}", exc_info=True)
            raise
    
    async def enhance_existing_context(self, 
                                     context: BrowserContext, 
                                     legacy_profile: Dict[str, Any], 
                                     platform: str = "generic") -> BrowserContext:
        """
        Enhance an existing browser context with StealthEngine protection
        For cases where context already exists
        """
        device_profile = self.convert_legacy_profile_to_device_profile(legacy_profile, platform)
        return await self.stealth_engine.create_stealth_context(context, device_profile, platform)
    
    def track_operation_success(self, platform: str, session_id: str, success: bool, details: Optional[Dict] = None):
        """
        Track success/failure for ML optimization and performance monitoring
        """
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            device_profile = session['device_profile']
            
            if success:
                session['success_count'] += 1
            else:
                session['detection_count'] += 1
            
            # Track with StealthEngine for ML optimization (if available)
            profile_id = f"{device_profile.browser}_{device_profile.os}_{device_profile.device_type}"
            detection_confidence = 0.1 if success else 0.8
            
            self.stealth_engine.track_success(
                profile_id=profile_id,
                platform=platform,
                success=success,
                detection_confidence=detection_confidence
            )
            
            if self.live_status_logger:
                status_level = "SUCCESS" if success else "WARNING"
                message = f"Operation {'succeeded' if success else 'failed'} on {platform}"
                self.live_status_logger.log_status(
                    status_level, "TRACKING", message,
                    {
                        "session_id": session_id,
                        "success_rate": session['success_count'] / (session['success_count'] + session['detection_count']),
                        "total_operations": session['success_count'] + session['detection_count'],
                        **(details or {})
                    }
                )
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get performance statistics for a session"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        device_profile = session['device_profile']
        total_ops = session['success_count'] + session['detection_count']
        
        return {
            'session_id': session_id,
            'platform': session['platform'],
            'browser': device_profile.browser,
            'os': device_profile.os,
            'success_rate': session['success_count'] / max(1, total_ops),
            'total_operations': total_ops,
            'uptime_seconds': asyncio.get_event_loop().time() - session['created_at'],
            'stealth_engine_success_rate': self.stealth_engine.get_success_rate(
                f"{device_profile.browser}_{device_profile.os}_{device_profile.device_type}",
                session['platform']
            )
        }
    
    def get_all_session_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all active sessions"""
        return [self.get_session_stats(sid) for sid in self.active_sessions.keys()]
    
    async def create_stealth_http_session(self, device_profile: DeviceProfile) -> Any:
        """
        Create HTTP session with advanced TLS fingerprinting
        Replaces existing TLS fingerprint functionality
        """
        return await self.stealth_engine.create_tls_session(device_profile)
    
    def _generate_user_agent(self, profile: DeviceProfile) -> str:
        """Generate user agent string for profile"""
        templates = {
            ('Chrome', 'Windows'): 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36',
            ('Chrome', 'macOS'): 'Mozilla/5.0 (Macintosh; Intel Mac OS X {mac_version}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36',
            ('Firefox', 'Windows'): 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{firefox_version}) Gecko/20100101 Firefox/{firefox_version}',
            ('Safari', 'macOS'): 'Mozilla/5.0 (Macintosh; Intel Mac OS X {mac_version}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safari_version} Safari/605.1.15',
        }
        
        template_key = (profile.browser, profile.os.split()[0])
        template = templates.get(template_key, templates[('Chrome', 'Windows')])
        
        os_version = '10.0' if 'Windows' in profile.os else None
        mac_version = profile.os_version.replace('.', '_') if 'macOS' in profile.os else None
        firefox_version = profile.browser_version.split('.')[0]
        safari_version = profile.browser_version
        
        return template.format(
            browser_version=profile.browser_version,
            mac_version=mac_version,
            firefox_version=firefox_version,
            safari_version=safari_version
        )
    
    def _get_os_version(self, os: str) -> str:
        """Get specific OS version"""
        versions = {
            'Windows 11': '10.0.22631',
            'Windows 10': '10.0.19045',
            'macOS': '14.2.1',
            'Ubuntu': '22.04'
        }
        return versions.get(os, '10.0')
    
    async def cleanup_session(self, session_id: str):
        """Clean up a session and its resources"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            try:
                await session['context'].close()
            except:
                pass
            del self.active_sessions[session_id]
            
            if self.live_status_logger:
                self.live_status_logger.log_status(
                    "INFO", "CLEANUP", 
                    f"Session {session_id} cleaned up",
                    {"session_id": session_id}
                )
    
    async def cleanup_all_sessions(self):
        """Clean up all active sessions"""
        session_ids = list(self.active_sessions.keys())
        for session_id in session_ids:
            await self.cleanup_session(session_id)
        
        if self.live_status_logger:
            self.live_status_logger.log_status(
                "INFO", "CLEANUP", 
                f"All {len(session_ids)} sessions cleaned up"
            )


# Global instance for easy access
_bruce_stealth_integration: Optional[BruceStealthIntegration] = None

def get_bruce_stealth_integration(live_status_logger=None) -> BruceStealthIntegration:
    """Get or create the global BruceStealthIntegration instance"""
    global _bruce_stealth_integration
    if _bruce_stealth_integration is None:
        _bruce_stealth_integration = BruceStealthIntegration(live_status_logger)
    return _bruce_stealth_integration

def init_bruce_stealth_integration(live_status_logger=None) -> BruceStealthIntegration:
    """Initialize the global BruceStealthIntegration instance"""
    global _bruce_stealth_integration
    _bruce_stealth_integration = BruceStealthIntegration(live_status_logger)
    return _bruce_stealth_integration