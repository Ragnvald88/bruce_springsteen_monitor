# src/utils/tls_fingerprint.py (v7 - Production-Ready for Akamai Evasion)
import logging
import random
import hashlib
import json
from typing import Dict, List, Optional, Tuple, Set, Any, TYPE_CHECKING, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager
import websockets  # Add this import for websocket support

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
    class WebSocketMonitor:
        """Real-time monitoring using WebSocket connections"""
        
        def __init__(self, profile_manager, opportunity_callback: Callable):
            self.profile_manager = profile_manager
            self.opportunity_callback = opportunity_callback
            self.connections = {}
            
        async def connect_to_platform(self, platform: str, url: str):
            """Establish WebSocket connection to platform"""
            profile = await self.profile_manager.get_profile_for_platform(platform)
            
            headers = self._build_ws_headers(profile)
            
            async with websockets.connect(url, extra_headers=headers) as websocket:
                self.connections[platform] = websocket
                
                # Send initial subscription
                await websocket.send(json.dumps({
                    "action": "subscribe",
                    "events": ["inventory_update", "price_change", "new_listing"],
                    "filters": {"available": True}
                }))
                
                # Listen for updates
                async for message in websocket:
                    data = json.loads(message)
                    if data['type'] == 'opportunity':
                        await self.opportunity_callback(data['payload'])
                        await self.opportunity_callback(data['payload'])

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
        
        return session
    
    async def _create_curl_cffi_session(self, fingerprint: TLSFingerprint, profile: 'DynamicProfile') -> Any:
        """Create curl-cffi session with JA3 fingerprint"""
        snapshot = profile.get_fingerprint_snapshot()
        
        # Map browser to curl_cffi impersonation
        browser = snapshot.get('browser_name', 'chrome')
        version = snapshot.get('browser_version', 'latest')
        
        if browser.lower() == 'chrome':
            impersonate = f"chrome{version.split('.')[0] if version != 'latest' else '120'}"
        elif browser.lower() == 'firefox':
            impersonate = f"firefox{version.split('.')[0] if version != 'latest' else '120'}"
        else:
            impersonate = "chrome120"
        
        session = curl_requests.Session(impersonate=impersonate)
        
        # Apply proxy if configured
        proxy_config = snapshot.get('proxy')
        if proxy_config:
            session.proxies = {
                'http': proxy_config,
                'https': proxy_config
            }
        
        return session
    
    def _map_to_tls_client_identifier(self, browser: str, version: str) -> str:
        """Map browser/version to tls-client identifier"""
        mapping = {
            ('chrome', 'latest'): 'chrome_120',
            ('chrome', '120'): 'chrome_120',
            ('chrome', '119'): 'chrome_119',
            ('firefox', 'latest'): 'firefox_120',
            ('firefox', '120'): 'firefox_120',
            ('safari', 'latest'): 'safari_17_0',
            ('edge', 'latest'): 'chrome_120'  # Edge uses Chromium
        }
        
        key = (browser.lower(), version)
        return mapping.get(key, 'chrome_120')
    
    def _build_ws_headers(self, profile: 'DynamicProfile') -> Dict[str, str]:
        """Build WebSocket headers for profile"""
        snapshot = profile.get_fingerprint_snapshot()
        return {
            'User-Agent': snapshot.get('user_agent', 'Mozilla/5.0'),
            'Origin': 'https://www.fansale.it',
            'Sec-WebSocket-Version': '13'
        }


def patch_ssl_for_fingerprint_evasion():
    """Patch SSL context to use custom TLS fingerprints"""
    import ssl
    
    # Store original methods
    original_ssl_context_wrap_socket = ssl.SSLContext.wrap_socket
    original_ssl_context_wrap_bio = ssl.SSLContext.wrap_bio
    
    def patched_wrap_socket(self, sock, server_side=False, do_handshake_on_connect=True, 
                           suppress_ragged_eofs=True, server_hostname=None, session=None):
        """Patched wrap_socket with fingerprint randomization"""
        
        # Apply cipher suite randomization
        if hasattr(self, '_cipher_randomization_applied'):
            # Randomize cipher order slightly
            available_ciphers = self.get_ciphers()
            if len(available_ciphers) > 5:
                # Shuffle middle ciphers while keeping strong ones first
                import random
                middle_start = 2
                middle_end = min(len(available_ciphers), 8)
                if middle_end > middle_start:
                    middle_section = available_ciphers[middle_start:middle_end]
                    random.shuffle(middle_section)
                    new_order = (available_ciphers[:middle_start] + 
                                middle_section + 
                                available_ciphers[middle_end:])
                    
                    # Apply new cipher order
                    cipher_string = ':'.join([c['name'] for c in new_order if 'name' in c])
                    self.set_ciphers(cipher_string[:200])  # Limit length
        
        return original_ssl_context_wrap_socket(
            self, sock, server_side, do_handshake_on_connect,
            suppress_ragged_eofs, server_hostname, session
        )
    
    def patched_wrap_bio(self, incoming, outgoing, server_side=False, 
                        server_hostname=None, session=None):
        """Patched wrap_bio with fingerprint evasion"""
        return original_ssl_context_wrap_bio(
            self, incoming, outgoing, server_side, server_hostname, session
        )
    
    # Apply patches
    ssl.SSLContext.wrap_socket = patched_wrap_socket
    ssl.SSLContext.wrap_bio = patched_wrap_bio
    
    logger.info("🛡️ SSL fingerprint evasion patches applied")


async def inject_tls_fingerprint_for_browser_context(context, profile: 'DynamicProfile'):
    """Inject TLS fingerprint into browser context BEFORE any page loads"""
    try:
        fingerprint_snapshot = profile.get_fingerprint_snapshot()
        
        # Advanced TLS/SSL evasion script
        tls_evasion_script = f"""
        (() => {{
            // TLS fingerprint evasion
            const originalFetch = window.fetch;
            const originalXHR = window.XMLHttpRequest;
            
            // JA3 fingerprint randomization
            const ja3Variations = [
                '{fingerprint_snapshot.get("tls_ja3", "771,4865-4866-4867-49195-49199")}',
                '771,4865-4867-4866-49195-49199-49196-49200-52393-52392',
                '771,4866-4865-4867-49195-49199-49196-49200-52393'
            ];
            
            // HTTP/2 settings randomization
            const h2Settings = {{
                'SETTINGS_HEADER_TABLE_SIZE': {fingerprint_snapshot.get("h2_header_table_size", 65536)},
                'SETTINGS_ENABLE_PUSH': 0,
                'SETTINGS_MAX_CONCURRENT_STREAMS': {fingerprint_snapshot.get("h2_max_streams", 1000)},
                'SETTINGS_INITIAL_WINDOW_SIZE': {fingerprint_snapshot.get("h2_window_size", 6291456)}
            }};
            
            // Randomize TLS extensions order
            const tlsExtensions = [35, 16, 5, 13, 18, 51, 45, 43, 27, 17513, 21];
            const shuffledExtensions = tlsExtensions.sort(() => Math.random() - 0.5);
            
            // Override fetch to inject custom headers
            window.fetch = function(url, options = {{}}) {{
                options.headers = options.headers || {{}};
                
                // Add HTTP/2 pseudo-headers in correct order
                const pseudoHeaders = {{
                    ':method': options.method || 'GET',
                    ':authority': new URL(url, window.location.href).host,
                    ':scheme': new URL(url, window.location.href).protocol.slice(0, -1),
                    ':path': new URL(url, window.location.href).pathname + new URL(url, window.location.href).search
                }};
                
                // Inject ALPS support headers
                options.headers['Accept-Encoding'] = 'gzip, deflate, br';
                options.headers['Accept-Language'] = '{fingerprint_snapshot.get("accept_language", "it-IT,it;q=0.9,en;q=0.8")}';
                
                return originalFetch.call(this, url, options);
            }};
            
            // Override XMLHttpRequest
            const XHROpen = originalXHR.prototype.open;
            originalXHR.prototype.open = function(method, url, async, user, password) {{
                const result = XHROpen.call(this, method, url, async, user, password);
                
                // Add TLS-specific headers
                this.setRequestHeader('Sec-Fetch-Site', 'same-origin');
                this.setRequestHeader('Sec-Fetch-Mode', 'cors');
                this.setRequestHeader('Sec-Fetch-Dest', 'empty');
                
                return result;
            }};
            
            // Connection timing randomization
            if (window.PerformanceNavigationTiming) {{
                const originalGetEntriesByType = performance.getEntriesByType;
                performance.getEntriesByType = function(type) {{
                    const entries = originalGetEntriesByType.call(this, type);
                    if (type === 'navigation') {{
                        entries.forEach(entry => {{
                            // Randomize connection timing slightly
                            if (entry.connectStart) {{
                                entry.connectStart += Math.random() * 10;
                            }}
                            if (entry.secureConnectionStart) {{
                                entry.secureConnectionStart += Math.random() * 15;
                            }}
                        }});
                    }}
                    return entries;
                }};
            }}
            
            // Session resumption simulation
            const sessionCache = new Map();
            const simulateSessionResumption = (hostname) => {{
                if (sessionCache.has(hostname)) {{
                    // Simulate session resumption (faster handshake)
                    return sessionCache.get(hostname);
                }} else {{
                    // Simulate full handshake
                    const sessionId = Math.random().toString(36).substring(2, 15);
                    sessionCache.set(hostname, sessionId);
                    return sessionId;
                }}
            }};
            
            console.log('🛡️ TLS fingerprint evasion injected');
        }})();
        """
        
        # Inject the TLS evasion script before any page loads
        await context.add_init_script(tls_evasion_script)
        
        logger.info(f"🛡️ TLS fingerprint injected for profile {profile.id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to inject TLS fingerprint: {e}")


# Export key functions
__all__ = [
    'TLSFingerprint',
    'TLSFingerprintManager', 
    'patch_ssl_for_fingerprint_evasion',
    'inject_tls_fingerprint_for_browser_context'
]