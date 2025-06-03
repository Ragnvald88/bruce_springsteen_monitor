# src/utils/tls_fingerprint.py (v7 - Production-Ready for Akamai Evasion)
import logging
import random
import hashlib
import json
from typing import Dict, List, Optional, Tuple, Set, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager

# For actual TLS control, we need specialized libraries
try:
    import tls_client  # pip install tls-client
    HAS_TLS_CLIENT = True
except ImportError:
    HAS_TLS_CLIENT = False
    
try:
    from curl_cffi import requests as curl_requests  # pip install curl-cffi
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

if TYPE_CHECKING:
    from core.advanced_profile_system import DynamicProfile

logger = logging.getLogger(__name__)

@dataclass
class TLSFingerprint:
    """Complete TLS fingerprint representation"""
    ja3_string: str
    ja3_hash: str
    h2_settings: Dict[str, int] = field(default_factory=dict)
    h2_window_update: int = 15663105
    h2_priority_frames: List[Dict[str, Any]] = field(default_factory=list)
    pseudo_header_order: List[str] = field(default_factory=list)
    headers_order: List[str] = field(default_factory=list)
    
    # Session resumption behavior
    session_ticket_support: bool = True
    session_id_support: bool = True
    psk_support: bool = False
    
    # ALPS/ALPN details
    alpn_protocols: List[str] = field(default_factory=lambda: ['h2', 'http/1.1'])
    alps_support: bool = False
    
    # Additional Akamai-tracked features
    tls_compression: bool = False
    renegotiation_support: bool = True
    ocsp_stapling: bool = True
    sct_support: bool = True  # Certificate Transparency
    
    @classmethod
    def from_browser_profile(cls, browser: str, version: str, os: str) -> 'TLSFingerprint':
        """Generate authentic fingerprint for browser/OS combination"""
        fingerprints = TLS_FINGERPRINT_DATABASE.get(f"{browser}_{version}_{os}")
        if not fingerprints:
            # Fallback to generic Chrome
            fingerprints = TLS_FINGERPRINT_DATABASE.get("chrome_latest_windows")
        return cls(**fingerprints)
    
    def mutate(self, mutation_strength: float = 0.1) -> 'TLSFingerprint':
        """Create slightly mutated version maintaining consistency"""
        import copy
        mutated = copy.deepcopy(self)
        
        # Only mutate non-critical parameters slightly
        if random.random() < mutation_strength:
            # Safely mutate H2 settings
            if 'SETTINGS_HEADER_TABLE_SIZE' in mutated.h2_settings:
                mutated.h2_settings['SETTINGS_HEADER_TABLE_SIZE'] = random.choice([65536, 131072])
            
            # Slightly adjust window update (stay within browser ranges)
            mutated.h2_window_update = random.randint(15000000, 16000000)
        
        return mutated


# Comprehensive TLS fingerprint database for real browsers
TLS_FINGERPRINT_DATABASE = {
    "chrome_latest_windows": {
        "ja3_string": "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,65037-0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513-21,29-23-24,0",
        "ja3_hash": "cd08e31494f9531f560d64c695473da9",
        "h2_settings": {
            "SETTINGS_HEADER_TABLE_SIZE": 65536,
            "SETTINGS_ENABLE_PUSH": 0,
            "SETTINGS_MAX_CONCURRENT_STREAMS": 1000,
            "SETTINGS_INITIAL_WINDOW_SIZE": 6291456,
            "SETTINGS_MAX_HEADER_LIST_SIZE": 262144
        },
        "h2_window_update": 15663105,
        "pseudo_header_order": [":method", ":authority", ":scheme", ":path"],
        "headers_order": ["cache-control", "sec-ch-ua", "sec-ch-ua-mobile", "sec-ch-ua-platform", 
                         "upgrade-insecure-requests", "user-agent", "accept", "sec-fetch-site", 
                         "sec-fetch-mode", "sec-fetch-user", "sec-fetch-dest", "accept-encoding", 
                         "accept-language", "cookie"],
        "session_ticket_support": True,
        "session_id_support": True,
        "alpn_protocols": ["h2", "http/1.1"],
        "ocsp_stapling": True,
        "sct_support": True
    },
    "firefox_latest_windows": {
        "ja3_string": "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-156-157-47-53-10,0-23-65281-10-11-35-16-5-13-51-45-43-27-21,29-23-24-25,0",
        "ja3_hash": "579ccef312d18482fc42e2b822ca2430", 
        "h2_settings": {
            "SETTINGS_HEADER_TABLE_SIZE": 65536,
            "SETTINGS_MAX_CONCURRENT_STREAMS": 100,
            "SETTINGS_INITIAL_WINDOW_SIZE": 131072,
            "SETTINGS_MAX_FRAME_SIZE": 16384,
            "SETTINGS_ENABLE_PUSH": 0
        },
        "h2_window_update": 12517377,
        "pseudo_header_order": [":method", ":path", ":authority", ":scheme"],
        "headers_order": ["user-agent", "accept", "accept-language", "accept-encoding", 
                         "host", "connection", "upgrade-insecure-requests", "sec-fetch-dest", 
                         "sec-fetch-mode", "sec-fetch-site", "te"],
        "session_ticket_support": True,
        "session_id_support": True,
        "alpn_protocols": ["h2", "http/1.1"],
        "ocsp_stapling": True,
        "sct_support": True
    }
}


class TLSFingerprintManager:
    """Production-ready TLS fingerprint management for Akamai evasion"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Any] = {}  # profile_id -> session
        self._session_lock = asyncio.Lock()
        
        # Verify we have proper TLS libraries
        if not HAS_TLS_CLIENT and not HAS_CURL_CFFI:
            raise RuntimeError(
                "No suitable TLS library found. Install tls-client or curl-cffi:\n"
                "pip install tls-client curl-cffi"
            )
    
    async def create_session_for_profile(self, profile: 'DynamicProfile') -> Any:
        """Create properly fingerprinted session for a profile"""
        async with self._session_lock:
            if profile.id in self.active_sessions:
                return self.active_sessions[profile.id]
            
            snapshot = profile.get_fingerprint_snapshot()
            browser = snapshot.get('browser_name', 'chrome')
            version = snapshot.get('browser_version', 'latest')
            os = snapshot.get('os_name', 'windows')
            
            # Get appropriate TLS fingerprint
            tls_fp = TLSFingerprint.from_browser_profile(browser, version, os)
            
            # Apply any profile-specific JA3 override
            if 'tls_ja3' in snapshot:
                tls_fp.ja3_string = snapshot['tls_ja3']
                tls_fp.ja3_hash = hashlib.md5(tls_fp.ja3_string.encode()).hexdigest()
            
            # Create session with proper implementation
            if HAS_TLS_CLIENT:
                session = await self._create_tls_client_session(tls_fp, profile)
            else:
                session = await self._create_curl_cffi_session(tls_fp, profile)
            
            self.active_sessions[profile.id] = session
            return session
    
    async def _create_tls_client_session(self, fingerprint: TLSFingerprint, profile: 'DynamicProfile') -> Any:
        """Create tls-client session with exact fingerprint"""
        # Map our fingerprint to tls-client identifier
        snapshot = profile.get_fingerprint_snapshot()
        client_identifier = self._map_to_tls_client_identifier(
            snapshot.get('browser_name', 'chrome'),
            snapshot.get('browser_version', 'latest')
        )
        
        # Create session with exact browser fingerprint
        session = tls_client.Session(
            client_identifier=client_identifier,
            ja3_string=fingerprint.ja3_string,
            h2_settings=fingerprint.h2_settings,
            h2_window_update=fingerprint.h2_window_update,
            pseudo_header_order=fingerprint.pseudo_header_order,
            header_order=fingerprint.headers_order,
            force_http1=False,
            catch_panics=True,
            debug=False
        )
        
        # Apply proxy if configured
        proxy_config = snapshot.get('proxy')
        if proxy_config:
            session.proxies = {
                'http': proxy_config,
                'https': proxy_config
            }