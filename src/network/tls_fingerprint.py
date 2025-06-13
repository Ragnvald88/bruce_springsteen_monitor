# stealthmaster/network/tls_fingerprint.py
"""
TLS Fingerprint Rotator - Advanced TLS/JA3 fingerprint management for 2025.
Implements realistic browser TLS signatures to bypass AI-driven detection.
"""

import random
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import hashlib
import json
import struct

logger = logging.getLogger(__name__)


@dataclass
class TLSProfile:
    """Represents a complete TLS fingerprint profile"""
    name: str
    browser: str
    version: str
    platform: str
    
    # JA3 components
    tls_version: int
    cipher_suites: List[int]
    extensions: List[int]
    elliptic_curves: List[int]
    elliptic_curve_formats: List[int]
    
    # ALPN protocols
    alpn_protocols: List[str]
    
    # HTTP/2 settings
    h2_settings: Dict[str, int]
    h2_window_update: int
    h2_priority: Dict[str, Any]
    
    # Additional fingerprint components
    signature_algorithms: List[int]
    supported_versions: List[int]
    key_share_groups: List[int]
    psk_key_exchange_modes: List[int]
    
    # Metadata
    popularity_score: float = 1.0
    last_used: Optional[datetime] = None
    times_used: int = 0
    
    def get_ja3_string(self) -> str:
        """Generate JA3 fingerprint string"""
        # Format: TLSVersion,Ciphers,Extensions,EllipticCurves,EllipticCurveFormats
        components = [
            str(self.tls_version),
            '-'.join(map(str, self.cipher_suites)),
            '-'.join(map(str, self.extensions)),
            '-'.join(map(str, self.elliptic_curves)),
            '-'.join(map(str, self.elliptic_curve_formats))
        ]
        return ','.join(components)
    
    def get_ja3_hash(self) -> str:
        """Get JA3 MD5 hash"""
        ja3_string = self.get_ja3_string()
        return hashlib.md5(ja3_string.encode()).hexdigest()


class TLSFingerprintRotator:
    """
    Manages TLS fingerprint rotation with 2025 browser profiles.
    Provides realistic TLS signatures matching actual browser behavior.
    Enhanced with GREASE values and dynamic randomization.
    """
    
    def __init__(self):
        """Initialize TLS fingerprint rotator"""
        self.profiles = self._load_tls_profiles()
        self.profile_weights = self._calculate_weights()
        self.usage_history: List[Tuple[str, datetime]] = []
        self.profile_map: Dict[str, TLSProfile] = {p.name: p for p in self.profiles}
        self.grease_cache: Dict[str, List[int]] = {}
        
        logger.info(f"TLS Fingerprint Rotator initialized with {len(self.profiles)} profiles")
    
    def _load_tls_profiles(self) -> List[TLSProfile]:
        """Load realistic TLS profiles for 2025 browsers"""
        profiles = [
            # Chrome 131 on Windows 11
            TLSProfile(
                name="Chrome_131_Win11",
                browser="Chrome",
                version="131.0.6778.85",
                platform="Windows",
                tls_version=771,  # TLS 1.2
                cipher_suites=[
                    4865, 4866, 4867,  # TLS_AES_128_GCM_SHA256, TLS_AES_256_GCM_SHA384, TLS_CHACHA20_POLY1305_SHA256
                    49195, 49199, 49196, 49200,  # ECDHE-ECDSA/RSA with AES GCM
                    52393, 52392,  # TLS_ECDHE_PSK
                    49171, 49172,  # ECDHE-ECDSA/RSA with AES CBC
                    156, 157, 47, 53  # Legacy support
                ],
                extensions=[
                    0,      # server_name
                    5,      # status_request
                    10,     # supported_groups
                    11,     # ec_point_formats
                    13,     # signature_algorithms
                    16,     # application_layer_protocol_negotiation
                    18,     # signed_certificate_timestamp
                    21,     # padding
                    23,     # extended_master_secret
                    27,     # compress_certificate
                    35,     # session_ticket
                    43,     # supported_versions
                    45,     # psk_key_exchange_modes
                    51,     # key_share
                    57,     # quic_transport_parameters
                    65281,  # renegotiation_info
                    17513   # application_settings
                ],
                elliptic_curves=[29, 23, 24, 25, 256, 257],  # X25519, secp256r1, secp384r1, secp521r1, ffdhe2048, ffdhe3072
                elliptic_curve_formats=[0],  # uncompressed
                alpn_protocols=["h2", "http/1.1"],
                h2_settings={
                    "HEADER_TABLE_SIZE": 65536,
                    "ENABLE_PUSH": 0,
                    "INITIAL_WINDOW_SIZE": 6291456,
                    "MAX_HEADER_LIST_SIZE": 262144,
                    "MAX_CONCURRENT_STREAMS": 1000,
                    "MAX_FRAME_SIZE": 16384
                },
                h2_window_update=15663105,
                h2_priority={
                    "weight": 256,
                    "depends_on": 0,
                    "exclusive": 1
                },
                signature_algorithms=[
                    1027, 1283, 1539,  # ECDSA with SHA256/384/512
                    2052, 2053, 2054,  # RSA-PSS with SHA256/384/512
                    1025, 1281, 1537   # RSA with SHA256/384/512
                ],
                supported_versions=[772, 771],  # TLS 1.3, 1.2
                key_share_groups=[29, 23, 24],  # X25519, secp256r1, secp384r1
                psk_key_exchange_modes=[1],  # PSK with (EC)DHE key establishment
                popularity_score=0.35  # Chrome has ~35% market share
            ),
            
            # Firefox 133 on Windows 11
            TLSProfile(
                name="Firefox_133_Win11",
                browser="Firefox",
                version="133.0",
                platform="Windows",
                tls_version=771,
                cipher_suites=[
                    4865, 4867, 4866,  # Different order than Chrome
                    49195, 49199, 52393, 52392,
                    49196, 49200, 49162, 49161,
                    49171, 49172, 51, 57, 47, 53, 10
                ],
                extensions=[
                    0, 23, 65281, 10, 11, 35, 16, 5, 51, 43, 13, 45, 28, 21
                ],
                elliptic_curves=[29, 23, 24, 25, 256, 257],
                elliptic_curve_formats=[0],
                alpn_protocols=["h2", "http/1.1"],
                h2_settings={
                    "HEADER_TABLE_SIZE": 65536,
                    "INITIAL_WINDOW_SIZE": 131072,
                    "MAX_FRAME_SIZE": 16777215,
                    "ENABLE_PUSH": 0,
                    "MAX_CONCURRENT_STREAMS": 100
                },
                h2_window_update=12517377,
                h2_priority={
                    "weight": 42,
                    "depends_on": 0,
                    "exclusive": 0
                },
                signature_algorithms=[
                    1027, 1283, 1539,
                    2052, 2053, 2054,
                    1025, 1281, 1537,
                    513, 515  # SHA224 variants
                ],
                supported_versions=[772, 771, 770],  # Also supports TLS 1.1
                key_share_groups=[29, 23, 24, 25],
                psk_key_exchange_modes=[1],
                popularity_score=0.08
            ),
            
            # Safari 18.2 on macOS Sequoia
            TLSProfile(
                name="Safari_18_macOS",
                browser="Safari",
                version="18.2",
                platform="macOS",
                tls_version=771,
                cipher_suites=[
                    4865, 4866, 4867,
                    49196, 49195, 52393,
                    49200, 49199, 52392,
                    49162, 49161, 49172,
                    49171, 157, 156, 53, 47,
                    49160, 49170, 10
                ],
                extensions=[
                    0, 23, 65281, 10, 11, 16, 5, 13, 18, 51, 45, 43, 27, 21
                ],
                elliptic_curves=[29, 23, 24, 25],
                elliptic_curve_formats=[0],
                alpn_protocols=["h2", "http/1.1"],
                h2_settings={
                    "HEADER_TABLE_SIZE": 4096,
                    "ENABLE_PUSH": 0,
                    "INITIAL_WINDOW_SIZE": 2097152,
                    "MAX_CONCURRENT_STREAMS": 100,
                    "MAX_FRAME_SIZE": 16384
                },
                h2_window_update=10485760,
                h2_priority={
                    "weight": 16,
                    "depends_on": 0,
                    "exclusive": 0
                },
                signature_algorithms=[
                    1027, 1283, 1539,
                    2052, 2053, 2054,
                    1025, 1281, 1537
                ],
                supported_versions=[772, 771],
                key_share_groups=[29, 23, 24],
                psk_key_exchange_modes=[1],
                popularity_score=0.15
            ),
            
            # Edge 131 on Windows 11 (Chromium-based)
            TLSProfile(
                name="Edge_131_Win11",
                browser="Edge",
                version="131.0.2903.63",
                platform="Windows",
                tls_version=771,
                cipher_suites=[
                    4865, 4866, 4867,
                    49195, 49199, 49196, 49200,
                    52393, 52392,
                    49171, 49172,
                    156, 157, 47, 53
                ],
                extensions=[
                    0, 5, 10, 11, 13, 16, 18, 21, 23, 27, 35, 43, 45, 51, 57, 65281, 17513
                ],
                elliptic_curves=[29, 23, 24, 25, 256, 257],
                elliptic_curve_formats=[0],
                alpn_protocols=["h2", "http/1.1"],
                h2_settings={
                    "HEADER_TABLE_SIZE": 65536,
                    "ENABLE_PUSH": 0,
                    "INITIAL_WINDOW_SIZE": 6291456,
                    "MAX_HEADER_LIST_SIZE": 262144,
                    "MAX_CONCURRENT_STREAMS": 1000,
                    "MAX_FRAME_SIZE": 16384
                },
                h2_window_update=15663105,
                h2_priority={
                    "weight": 256,
                    "depends_on": 0,
                    "exclusive": 1
                },
                signature_algorithms=[
                    1027, 1283, 1539,
                    2052, 2053, 2054,
                    1025, 1281, 1537
                ],
                supported_versions=[772, 771],
                key_share_groups=[29, 23, 24],
                psk_key_exchange_modes=[1],
                popularity_score=0.13
            ),
            
            # Chrome 131 on Android 14
            TLSProfile(
                name="Chrome_131_Android",
                browser="Chrome Mobile",
                version="131.0.6778.83",
                platform="Android",
                tls_version=771,
                cipher_suites=[
                    4865, 4866, 4867,
                    49195, 49199, 49196, 49200,
                    52393, 52392,
                    49171, 49172,
                    156, 157, 47, 53
                ],
                extensions=[
                    0, 5, 10, 11, 13, 16, 18, 21, 23, 27, 35, 43, 45, 51, 65281
                ],
                elliptic_curves=[29, 23, 24],
                elliptic_curve_formats=[0],
                alpn_protocols=["h2", "http/1.1"],
                h2_settings={
                    "HEADER_TABLE_SIZE": 65536,
                    "ENABLE_PUSH": 0,
                    "INITIAL_WINDOW_SIZE": 1048576,
                    "MAX_HEADER_LIST_SIZE": 262144,
                    "MAX_CONCURRENT_STREAMS": 100,
                    "MAX_FRAME_SIZE": 16384
                },
                h2_window_update=983041,
                h2_priority={
                    "weight": 220,
                    "depends_on": 0,
                    "exclusive": 1
                },
                signature_algorithms=[
                    1027, 1283, 1539,
                    2052, 2053, 2054,
                    1025, 1281, 1537
                ],
                supported_versions=[772, 771],
                key_share_groups=[29, 23, 24],
                psk_key_exchange_modes=[1],
                popularity_score=0.10
            ),
            
            # Brave 1.73 on Windows 11
            TLSProfile(
                name="Brave_173_Win11",
                browser="Brave",
                version="1.73.89",
                platform="Windows",
                tls_version=771,
                cipher_suites=[
                    4865, 4866, 4867,
                    49195, 49199, 49196, 49200,
                    52393, 52392,
                    49171, 49172,
                    156, 157, 47, 53
                ],
                extensions=[
                    0, 5, 10, 11, 13, 16, 18, 21, 23, 27, 35, 43, 45, 51, 57, 65281, 17513, 30032
                ],
                elliptic_curves=[29, 23, 24, 25, 256, 257],
                elliptic_curve_formats=[0],
                alpn_protocols=["h2", "http/1.1"],
                h2_settings={
                    "HEADER_TABLE_SIZE": 65536,
                    "ENABLE_PUSH": 0,
                    "INITIAL_WINDOW_SIZE": 6291456,
                    "MAX_HEADER_LIST_SIZE": 262144,
                    "MAX_CONCURRENT_STREAMS": 1000,
                    "MAX_FRAME_SIZE": 16384
                },
                h2_window_update=15663105,
                h2_priority={
                    "weight": 256,
                    "depends_on": 0,
                    "exclusive": 1
                },
                signature_algorithms=[
                    1027, 1283, 1539,
                    2052, 2053, 2054,
                    1025, 1281, 1537
                ],
                supported_versions=[772, 771],
                key_share_groups=[29, 23, 24],
                psk_key_exchange_modes=[1],
                popularity_score=0.02
            ),
            
            # Opera 114 on Windows 11
            TLSProfile(
                name="Opera_114_Win11",
                browser="Opera",
                version="114.0.5282.102",
                platform="Windows",
                tls_version=771,
                cipher_suites=[
                    4865, 4866, 4867,
                    49195, 49199, 49196, 49200,
                    52393, 52392,
                    49171, 49172,
                    156, 157, 47, 53
                ],
                extensions=[
                    0, 5, 10, 11, 13, 16, 18, 21, 23, 27, 35, 43, 45, 51, 65281, 17513
                ],
                elliptic_curves=[29, 23, 24, 25, 256, 257],
                elliptic_curve_formats=[0],
                alpn_protocols=["h2", "http/1.1"],
                h2_settings={
                    "HEADER_TABLE_SIZE": 65536,
                    "ENABLE_PUSH": 0,
                    "INITIAL_WINDOW_SIZE": 6291456,
                    "MAX_HEADER_LIST_SIZE": 262144,
                    "MAX_CONCURRENT_STREAMS": 1000,
                    "MAX_FRAME_SIZE": 16384
                },
                h2_window_update=15663105,
                h2_priority={
                    "weight": 256,
                    "depends_on": 0,
                    "exclusive": 1
                },
                signature_algorithms=[
                    1027, 1283, 1539,
                    2052, 2053, 2054,
                    1025, 1281, 1537
                ],
                supported_versions=[772, 771],
                key_share_groups=[29, 23, 24],
                psk_key_exchange_modes=[1],
                popularity_score=0.02
            ),
            
            # Chrome 131 on Ubuntu Linux
            TLSProfile(
                name="Chrome_131_Linux",
                browser="Chrome",
                version="131.0.6778.85",
                platform="Linux",
                tls_version=771,
                cipher_suites=[
                    4865, 4866, 4867,
                    49195, 49199, 49196, 49200,
                    52393, 52392,
                    49171, 49172,
                    156, 157, 47, 53
                ],
                extensions=[
                    0, 5, 10, 11, 13, 16, 18, 21, 23, 27, 35, 43, 45, 51, 57, 65281, 17513
                ],
                elliptic_curves=[29, 23, 24, 25, 256, 257],
                elliptic_curve_formats=[0],
                alpn_protocols=["h2", "http/1.1"],
                h2_settings={
                    "HEADER_TABLE_SIZE": 65536,
                    "ENABLE_PUSH": 0,
                    "INITIAL_WINDOW_SIZE": 6291456,
                    "MAX_HEADER_LIST_SIZE": 262144,
                    "MAX_CONCURRENT_STREAMS": 1000,
                    "MAX_FRAME_SIZE": 16384
                },
                h2_window_update=15663105,
                h2_priority={
                    "weight": 256,
                    "depends_on": 0,
                    "exclusive": 1
                },
                signature_algorithms=[
                    1027, 1283, 1539,
                    2052, 2053, 2054,
                    1025, 1281, 1537
                ],
                supported_versions=[772, 771],
                key_share_groups=[29, 23, 24],
                psk_key_exchange_modes=[1],
                popularity_score=0.05
            )
        ]
        
        return profiles
    
    def _calculate_weights(self) -> List[float]:
        """Calculate selection weights based on popularity"""
        return [p.popularity_score for p in self.profiles]
    
    def get_profile(self, user_agent: Optional[str] = None, session_id: Optional[str] = None) -> TLSProfile:
        """
        Get a TLS profile, optionally matching a user agent.
        Enhanced with GREASE values and dynamic randomization.
        
        Args:
            user_agent: Optional user agent to match
            session_id: Optional session ID for consistent profiles
            
        Returns:
            Selected TLS profile with dynamic randomization
        """
        if user_agent:
            # Try to match browser from user agent
            profile = self._match_user_agent(user_agent)
            if profile:
                return self._enhance_profile_with_randomization(profile, session_id)
        
        # Select based on weights with some randomization
        selected = random.choices(self.profiles, weights=self.profile_weights, k=1)[0]
        
        # Apply dynamic randomization
        enhanced = self._enhance_profile_with_randomization(selected, session_id)
        
        # Update usage stats
        enhanced.times_used += 1
        enhanced.last_used = datetime.now()
        self.usage_history.append((enhanced.name, datetime.now()))
        
        logger.debug(f"Selected TLS profile: {enhanced.name} (JA3: {enhanced.get_ja3_hash()})")
        return enhanced
    
    def _match_user_agent(self, user_agent: str) -> Optional[TLSProfile]:
        """Match TLS profile to user agent"""
        ua_lower = user_agent.lower()
        
        # Extract browser and version
        if "chrome" in ua_lower and "edg" not in ua_lower:
            version = self._extract_version(ua_lower, "chrome/")
            platform = self._extract_platform(ua_lower)
            
            # Find best matching Chrome profile
            for profile in self.profiles:
                if profile.browser == "Chrome" and profile.platform.lower() in platform:
                    return profile
        
        elif "firefox" in ua_lower:
            for profile in self.profiles:
                if profile.browser == "Firefox":
                    return profile
        
        elif "safari" in ua_lower and "chrome" not in ua_lower:
            for profile in self.profiles:
                if profile.browser == "Safari":
                    return profile
        
        elif "edg" in ua_lower:
            for profile in self.profiles:
                if profile.browser == "Edge":
                    return profile
        
        return None
    
    def _extract_version(self, ua: str, pattern: str) -> Optional[str]:
        """Extract version from user agent"""
        try:
            start = ua.find(pattern)
            if start != -1:
                start += len(pattern)
                end = ua.find(" ", start)
                if end == -1:
                    end = len(ua)
                return ua[start:end]
        except Exception:
            pass
        return None
    
    def _extract_platform(self, ua: str) -> str:
        """Extract platform from user agent"""
        if "windows" in ua:
            return "windows"
        elif "android" in ua:
            return "android"
        elif "mac os" in ua or "macintosh" in ua:
            return "macos"
        elif "linux" in ua:
            return "linux"
        return "unknown"
    
    def rotate(self) -> TLSProfile:
        """
        Rotate to a different TLS profile.
        
        Returns:
            New TLS profile
        """
        # Get least recently used profiles
        profile_last_used = {}
        for profile in self.profiles:
            if profile.last_used:
                profile_last_used[profile] = profile.last_used
            else:
                profile_last_used[profile] = datetime.min
        
        # Sort by last used (oldest first)
        sorted_profiles = sorted(profile_last_used.items(), key=lambda x: x[1])
        
        # Select from the least recently used half
        candidates = [p[0] for p in sorted_profiles[:len(sorted_profiles)//2]]
        
        # Weight by popularity
        weights = [p.popularity_score for p in candidates]
        selected = random.choices(candidates, weights=weights, k=1)[0]
        
        # Update usage
        selected.times_used += 1
        selected.last_used = datetime.now()
        self.usage_history.append((selected.name, datetime.now()))
        
        logger.info(f"Rotated to TLS profile: {selected.name}")
        return selected
    
    def get_profile_by_name(self, name: str) -> Optional[TLSProfile]:
        """Get specific profile by name"""
        return self.profile_map.get(name)
    
    def get_chrome_profile(self) -> TLSProfile:
        """Get a Chrome TLS profile"""
        chrome_profiles = [p for p in self.profiles if p.browser == "Chrome"]
        return random.choice(chrome_profiles)
    
    def get_firefox_profile(self) -> TLSProfile:
        """Get a Firefox TLS profile"""
        firefox_profiles = [p for p in self.profiles if p.browser == "Firefox"]
        return random.choice(firefox_profiles)
    
    def get_mobile_profile(self) -> TLSProfile:
        """Get a mobile browser TLS profile"""
        mobile_profiles = [p for p in self.profiles if p.platform in ["Android", "iOS"]]
        if mobile_profiles:
            return random.choice(mobile_profiles)
        return self.get_profile()  # Fallback to any profile
    
    def export_ja3_signatures(self) -> Dict[str, str]:
        """Export all JA3 signatures for debugging"""
        return {
            profile.name: {
                "ja3_string": profile.get_ja3_string(),
                "ja3_hash": profile.get_ja3_hash(),
                "browser": profile.browser,
                "platform": profile.platform
            }
            for profile in self.profiles
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get TLS rotation statistics"""
        total_uses = sum(p.times_used for p in self.profiles)
        
        return {
            "total_profiles": len(self.profiles),
            "total_rotations": total_uses,
            "profile_usage": {
                p.name: {
                    "times_used": p.times_used,
                    "last_used": p.last_used.isoformat() if p.last_used else None,
                    "browser": p.browser,
                    "platform": p.platform
                }
                for p in self.profiles
            },
            "recent_history": [
                {"profile": name, "timestamp": ts.isoformat()}
                for name, ts in self.usage_history[-10:]
            ],
            "most_used": max(self.profiles, key=lambda p: p.times_used).name if self.profiles else None,
            "least_used": min(self.profiles, key=lambda p: p.times_used).name if self.profiles else None
        }
    
    def reset_usage_stats(self):
        """Reset usage statistics"""
        for profile in self.profiles:
            profile.times_used = 0
            profile.last_used = None
        self.usage_history.clear()
        self.grease_cache.clear()
        logger.info("Reset TLS profile usage statistics")
    
    def _enhance_profile_with_randomization(self, profile: TLSProfile, session_id: Optional[str] = None) -> TLSProfile:
        """Enhance profile with dynamic randomization while maintaining browser consistency"""
        # Create a copy to avoid modifying the original
        import copy
        enhanced = copy.deepcopy(profile)
        
        # Apply cipher suite randomization within browser patterns
        enhanced.cipher_suites = self._randomize_cipher_suites(enhanced.cipher_suites, enhanced.browser)
        
        # Apply extension randomization with GREASE
        enhanced.extensions = self._randomize_extensions_with_grease(
            enhanced.extensions, enhanced.browser, session_id
        )
        
        # Randomize elliptic curves order (Chrome/Edge behavior)
        if enhanced.browser in ["Chrome", "Edge", "Brave", "Opera"]:
            enhanced.elliptic_curves = self._randomize_curve_order(enhanced.elliptic_curves)
        
        # Randomize signature algorithms within valid ranges
        enhanced.signature_algorithms = self._randomize_signature_algorithms(
            enhanced.signature_algorithms, enhanced.browser
        )
        
        return enhanced
    
    def _randomize_cipher_suites(self, ciphers: List[int], browser: str) -> List[int]:
        """Randomize cipher suite order while maintaining browser patterns"""
        # TLS 1.3 ciphers (always first)
        tls13 = [c for c in ciphers[:3] if c in [4865, 4866, 4867]]
        
        # TLS 1.2 ciphers
        tls12 = ciphers[3:]
        
        if browser in ["Chrome", "Edge", "Brave", "Opera"]:
            # Chrome-based browsers group ciphers by type
            ecdhe_gcm = [c for c in tls12 if c in [49195, 49199, 49196, 49200]]
            ecdhe_cbc = [c for c in tls12 if c in [49171, 49172, 52393, 52392]]
            rsa = [c for c in tls12 if c in [156, 157, 47, 53]]
            
            # Shuffle within groups
            random.shuffle(ecdhe_gcm)
            random.shuffle(ecdhe_cbc)
            random.shuffle(rsa)
            
            return tls13 + ecdhe_gcm + ecdhe_cbc + rsa
        
        elif browser == "Firefox":
            # Firefox has more random ordering
            random.shuffle(tls12)
            return tls13 + tls12
        
        # Safari keeps static order
        return ciphers
    
    def _randomize_extensions_with_grease(self, extensions: List[int], browser: str, session_id: Optional[str]) -> List[int]:
        """Add GREASE values to extensions at random positions"""
        # Create a copy
        ext_list = extensions.copy()
        
        # Generate or retrieve GREASE values for this session
        if session_id and session_id in self.grease_cache:
            grease_values = self.grease_cache[session_id]
        else:
            grease_values = self._generate_grease_values()
            if session_id:
                self.grease_cache[session_id] = grease_values
        
        # Chrome/Edge add 2-3 GREASE values
        if browser in ["Chrome", "Edge", "Brave", "Opera"]:
            # Remove existing GREASE values
            ext_list = [e for e in ext_list if not self._is_grease_value(e)]
            
            # Add GREASE at semi-random positions (Chrome pattern)
            positions = self._get_grease_positions(len(ext_list))
            for i, pos in enumerate(sorted(positions, reverse=True)):
                if i < len(grease_values):
                    ext_list.insert(pos, grease_values[i])
        
        # Randomize some variable extensions
        if browser in ["Chrome", "Edge"] and random.random() > 0.3:
            # Sometimes add/remove optional extensions
            optional_exts = [17, 41, 44, 49, 50]
            if random.random() > 0.5:
                # Add one
                to_add = random.choice([e for e in optional_exts if e not in ext_list])
                if to_add:
                    ext_list.insert(random.randint(len(ext_list)//2, len(ext_list)), to_add)
            else:
                # Remove one if present
                present = [e for e in optional_exts if e in ext_list]
                if present:
                    ext_list.remove(random.choice(present))
        
        return ext_list
    
    def _generate_grease_values(self) -> List[int]:
        """Generate GREASE (Generate Random Extensions And Sustain Extensibility) values"""
        # GREASE values follow pattern: 0x0A0A, 0x1A1A, ..., 0xFAFA
        base_values = [0x0A, 0x1A, 0x2A, 0x3A, 0x4A, 0x5A, 0x6A, 0x7A, 0x8A, 0x9A, 0xAA, 0xBA, 0xCA, 0xDA, 0xEA]
        
        # Select 2-3 random GREASE values
        num_grease = random.randint(2, 3)
        selected_bases = random.sample(base_values, num_grease)
        
        # Convert to full GREASE values
        return [(base << 8) | base for base in selected_bases]
    
    def _is_grease_value(self, value: int) -> bool:
        """Check if a value is a GREASE value"""
        # GREASE values have pattern 0xXAXA where X is same hex digit
        if value < 0x0A0A or value > 0xFAFA:
            return False
        
        high = (value >> 8) & 0xFF
        low = value & 0xFF
        
        return high == low and (high & 0x0F) == 0x0A
    
    def _get_grease_positions(self, num_extensions: int) -> List[int]:
        """Get positions for GREASE values following Chrome patterns"""
        # Chrome typically puts GREASE at:
        # - Near the beginning (position 1-3)
        # - Middle (around 40-60%)
        # - Near end (80-90%)
        
        positions = []
        
        # First GREASE near beginning
        positions.append(random.randint(1, min(3, num_extensions // 4)))
        
        # Second GREASE in middle
        middle_start = int(num_extensions * 0.4)
        middle_end = int(num_extensions * 0.6)
        if middle_end > middle_start:
            positions.append(random.randint(middle_start, middle_end))
        
        # Third GREASE (if used) near end
        if random.random() > 0.3:  # 70% chance of third GREASE
            end_start = int(num_extensions * 0.8)
            end_end = int(num_extensions * 0.9)
            if end_end > end_start:
                positions.append(random.randint(end_start, min(end_end, num_extensions - 1)))
        
        return positions
    
    def _randomize_curve_order(self, curves: List[int]) -> List[int]:
        """Randomize elliptic curve order (Chrome behavior)"""
        # Chrome uses these curves in varying orders
        curve_orders = [
            [29, 23, 24],  # x25519, secp256r1, secp384r1 (most common)
            [29, 24, 23],  # x25519, secp384r1, secp256r1
            [23, 29, 24],  # secp256r1, x25519, secp384r1
        ]
        
        # Keep the main curves but randomize order
        main_curves = [c for c in curves if c in [29, 23, 24]]
        other_curves = [c for c in curves if c not in [29, 23, 24]]
        
        # Pick a random ordering for main curves
        if main_curves:
            main_curves = random.choice(curve_orders)
        
        return main_curves + other_curves
    
    def _randomize_signature_algorithms(self, algorithms: List[int], browser: str) -> List[int]:
        """Randomize signature algorithm order within constraints"""
        # Group algorithms by type
        ecdsa = [a for a in algorithms if a in [1027, 1283, 1539]]  # ECDSA
        rsa_pss = [a for a in algorithms if a in [2052, 2053, 2054]]  # RSA-PSS
        rsa = [a for a in algorithms if a in [1025, 1281, 1537]]  # RSA
        others = [a for a in algorithms if a not in ecdsa + rsa_pss + rsa]
        
        if browser in ["Chrome", "Edge", "Brave"]:
            # Chrome prefers ECDSA, then RSA-PSS, then RSA
            # But sometimes swaps RSA-PSS and RSA
            if random.random() > 0.7:
                return ecdsa + rsa + rsa_pss + others
            else:
                return ecdsa + rsa_pss + rsa + others
        
        elif browser == "Firefox":
            # Firefox sometimes puts RSA-PSS first
            if random.random() > 0.6:
                return rsa_pss + ecdsa + rsa + others
            else:
                return ecdsa + rsa_pss + rsa + others
        
        # Default order
        return algorithms


class TLSValidator:
    """Validates TLS fingerprints against known patterns"""
    
    @staticmethod
    def validate_ja3(ja3_hash: str, known_good_hashes: List[str]) -> bool:
        """Check if JA3 hash matches known good browser fingerprints"""
        return ja3_hash in known_good_hashes
    
    @staticmethod
    def detect_anomalies(profile: TLSProfile) -> List[str]:
        """Detect anomalies in TLS profile"""
        anomalies = []
        
        # Check cipher suite ordering
        chrome_cipher_order = [4865, 4866, 4867]
        if profile.browser == "Chrome" and profile.cipher_suites[:3] != chrome_cipher_order:
            anomalies.append("Incorrect Chrome cipher suite order")
        
        # Check extension presence
        required_extensions = [0, 10, 11, 13, 16, 23, 43, 51]
        for ext in required_extensions:
            if ext not in profile.extensions:
                anomalies.append(f"Missing required extension: {ext}")
        
        # Check ALPN protocols
        if "h2" not in profile.alpn_protocols:
            anomalies.append("Missing HTTP/2 ALPN protocol")
        
        return anomalies
