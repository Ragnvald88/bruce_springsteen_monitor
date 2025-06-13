"""
TLS Fingerprint Randomization Engine

This module implements advanced TLS fingerprint randomization to evade JA3/JA4 detection.
It randomizes cipher suites, TLS extensions, and other parameters to match real Chrome behavior.
"""

import random
import asyncio
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib

@dataclass
class TLSProfile:
    """Represents a TLS fingerprint profile"""
    cipher_suites: List[str]
    extensions: List[int]
    elliptic_curves: List[int]
    elliptic_curve_formats: List[int]
    tls_version: str
    alpn_protocols: List[str]
    signature_algorithms: List[int]
    
class TLSRandomizer:
    """Advanced TLS fingerprint randomization for Chrome 125+ emulation"""
    
    # Chrome 125+ cipher suites in realistic order variations
    CHROME_CIPHER_SUITES = [
        # TLS 1.3 cipher suites (always first in Chrome)
        ["0x1301", "0x1302", "0x1303"],  # TLS_AES_128_GCM_SHA256, TLS_AES_256_GCM_SHA384, TLS_CHACHA20_POLY1305_SHA256
        
        # TLS 1.2 cipher suites (various orderings seen in Chrome)
        [
            "0xc02b", "0xc02f", "0xc02c", "0xc030",  # ECDHE-ECDSA/RSA with AES GCM
            "0xcca9", "0xcca8", "0xc013", "0xc014",  # ECDHE with AES CBC
            "0x009c", "0x009d", "0x002f", "0x0035"   # RSA with AES
        ]
    ]
    
    # Chrome extension IDs and their valid orderings
    CHROME_EXTENSIONS = {
        "core": [0, 5, 10, 11, 13, 16, 18, 21, 23, 27, 35, 43, 45, 51],
        "variable": [17, 41, 44, 49, 50],  # These can appear in different positions
        "optional": [65037, 65281]  # GREASE values
    }
    
    # Elliptic curves Chrome supports
    CHROME_CURVES = [
        [0x001d, 0x0017, 0x0018],  # x25519, secp256r1, secp384r1
        [0x001d, 0x0018, 0x0017],  # Alternative ordering
        [0x0017, 0x001d, 0x0018],  # Another valid ordering
    ]
    
    def __init__(self):
        self.profiles_cache: Dict[str, TLSProfile] = {}
        self.session_profiles: Dict[str, TLSProfile] = {}
        
    def generate_chrome_profile(self, session_id: Optional[str] = None) -> TLSProfile:
        """Generate a realistic Chrome TLS fingerprint profile"""
        
        # Check if we have a cached profile for this session
        if session_id and session_id in self.session_profiles:
            return self.session_profiles[session_id]
            
        # Select cipher suite ordering
        tls13_ciphers = self.CHROME_CIPHER_SUITES[0]
        tls12_ciphers = self._randomize_cipher_order(self.CHROME_CIPHER_SUITES[1])
        all_ciphers = tls13_ciphers + tls12_ciphers
        
        # Generate extensions in Chrome-like order
        extensions = self._generate_extension_order()
        
        # Select elliptic curves ordering
        curves = random.choice(self.CHROME_CURVES)
        
        profile = TLSProfile(
            cipher_suites=all_ciphers,
            extensions=extensions,
            elliptic_curves=curves,
            elliptic_curve_formats=[0],  # uncompressed only in Chrome
            tls_version="771",  # TLS 1.2 (0x0303)
            alpn_protocols=["h2", "http/1.1"],
            signature_algorithms=self._get_signature_algorithms()
        )
        
        # Cache for session if provided
        if session_id:
            self.session_profiles[session_id] = profile
            
        return profile
        
    def _randomize_cipher_order(self, ciphers: List[str]) -> List[str]:
        """Randomize cipher order while maintaining Chrome patterns"""
        # Chrome groups certain ciphers together
        ecdhe_gcm = [c for c in ciphers if c in ["0xc02b", "0xc02f", "0xc02c", "0xc030"]]
        ecdhe_cbc = [c for c in ciphers if c in ["0xcca9", "0xcca8", "0xc013", "0xc014"]]
        rsa = [c for c in ciphers if c in ["0x009c", "0x009d", "0x002f", "0x0035"]]
        
        # Shuffle within groups
        random.shuffle(ecdhe_gcm)
        random.shuffle(ecdhe_cbc)
        random.shuffle(rsa)
        
        # Chrome always puts ECDHE-GCM first, then CBC, then RSA
        return ecdhe_gcm + ecdhe_cbc + rsa
        
    def _generate_extension_order(self) -> List[int]:
        """Generate Chrome-like extension ordering"""
        # Core extensions always present
        core = self.CHROME_EXTENSIONS["core"].copy()
        
        # Add GREASE values at random positions (Chrome behavior)
        grease_positions = random.sample(range(len(core)), 2)
        grease_values = self._generate_grease_values()
        
        # Insert GREASE
        for i, pos in enumerate(sorted(grease_positions, reverse=True)):
            core.insert(pos, grease_values[i])
            
        # Randomly include some variable extensions
        if random.random() > 0.3:
            variable = random.sample(self.CHROME_EXTENSIONS["variable"], 
                                   random.randint(1, 3))
            # Insert at Chrome-typical positions
            for ext in variable:
                pos = random.randint(len(core)//2, len(core))
                core.insert(pos, ext)
                
        return core
        
    def _generate_grease_values(self) -> List[int]:
        """Generate GREASE (Generate Random Extensions And Sustain Extensibility) values"""
        # GREASE values follow pattern: 0x0A0A, 0x1A1A, ..., 0xFAFA
        base_values = [0x0A, 0x1A, 0x2A, 0x3A, 0x4A, 0x5A, 0x6A, 0x7A, 0x8A, 0x9A, 0xAA, 0xBA, 0xCA, 0xDA, 0xEA]
        selected = random.sample(base_values, 2)
        return [(v << 8) | v for v in selected]
        
    def _get_signature_algorithms(self) -> List[int]:
        """Get Chrome signature algorithms in realistic order"""
        # Chrome 125+ signature algorithm preferences
        algorithms = [
            0x0403, 0x0503, 0x0603,  # ECDSA with SHA256/384/512
            0x0807, 0x0808, 0x0809,  # ED25519, ED448
            0x0804, 0x0805, 0x0806,  # RSA-PSS with SHA256/384/512
            0x0401, 0x0501, 0x0601,  # RSA with SHA256/384/512
        ]
        
        # Sometimes Chrome includes legacy algorithms
        if random.random() > 0.7:
            algorithms.extend([0x0201, 0x0203])  # SHA1 variants
            
        return algorithms
        
    def rotate_fingerprint(self, session_id: str) -> TLSProfile:
        """Rotate TLS fingerprint for a session while maintaining consistency"""
        # Generate new profile but keep some elements consistent
        old_profile = self.session_profiles.get(session_id)
        new_profile = self.generate_chrome_profile()
        
        if old_profile:
            # Keep ALPN consistent within session
            new_profile.alpn_protocols = old_profile.alpn_protocols
            # Keep TLS version consistent
            new_profile.tls_version = old_profile.tls_version
            
        self.session_profiles[session_id] = new_profile
        return new_profile
        
    def get_ja3_string(self, profile: TLSProfile) -> str:
        """Generate JA3 fingerprint string from profile"""
        # JA3 format: TLSVersion,Ciphers,Extensions,EllipticCurves,EllipticCurveFormats
        cipher_str = ",".join([str(int(c, 16)) for c in profile.cipher_suites])
        ext_str = ",".join([str(e) for e in profile.extensions])
        curve_str = ",".join([str(c) for c in profile.elliptic_curves])
        format_str = ",".join([str(f) for f in profile.elliptic_curve_formats])
        
        ja3_string = f"{profile.tls_version},{cipher_str},{ext_str},{curve_str},{format_str}"
        return ja3_string
        
    def get_ja3_hash(self, profile: TLSProfile) -> str:
        """Generate JA3 hash from profile"""
        ja3_string = self.get_ja3_string(profile)
        return hashlib.md5(ja3_string.encode()).hexdigest()
        
    async def apply_to_context(self, context, profile: Optional[TLSProfile] = None):
        """Apply TLS fingerprint to browser context"""
        if not profile:
            profile = self.generate_chrome_profile()
            
        # This would integrate with the browser's TLS stack
        # For now, we'll store it for reference
        context._tls_profile = profile
        
        # Log the fingerprint for debugging
        ja3_hash = self.get_ja3_hash(profile)
        print(f"Applied TLS fingerprint: {ja3_hash}")
        
        return profile

# Global instance
tls_randomizer = TLSRandomizer()