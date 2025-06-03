# src/session_manager.py
"""Session management for browser profiles."""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Optional, List

import aiofiles
import zstandard as zstd
from cryptography.fernet import Fernet
from playwright.async_api import BrowserContext

from .enums import Platform
from .models import BrowserProfile
from .types import SessionData

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage browser sessions across platforms."""
    
    def __init__(self, session_backup_dir: str = "session_backups"):
        self.session_backup_dir = Path(session_backup_dir)
        self.session_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Track session validity
        self.session_ready_profiles: Dict[str, Set[str]] = {
            platform.value: set() for platform in Platform
        }
        
        self._session_lock = asyncio.Lock()
    
    async def save_session(
        self,
        profile: BrowserProfile,
        platform: Platform,
        context: BrowserContext
    ) -> bool:
        """Save platform session data from browser context."""
        try:
            async with self._session_lock:
                # Get all cookies
                cookies = await context.cookies()
                
                # Get storage state
                storage_state = await context.storage_state()
                
                # Extract auth tokens and user info
                auth_tokens = self._extract_auth_tokens(cookies, storage_state)
                user_id = self._extract_user_id(cookies, storage_state, platform)
                
                session_data: SessionData = {
                    'platform': platform.value,
                    'cookies': cookies,
                    'local_storage': storage_state.get('origins', [{}])[0].get('localStorage', {}),
                    'session_storage': {},
                    'auth_tokens': auth_tokens,
                    'last_updated': datetime.utcnow().isoformat(),
                    'is_valid': True,
                    'user_id': user_id,
                    'fingerprint_hash': profile.fingerprint_hash
                }
                
                # Save to profile
                profile.platform_sessions[platform.value] = session_data
                
                # Mark as ready
                self.session_ready_profiles[platform.value].add(profile.profile_id)
                
                # Persist to disk if enabled
                if profile.persistent_context_dir:
                    await self._save_encrypted_session(profile, platform, session_data)
                
                logger.info(
                    f"Profile {profile.profile_id}: Saved session for {platform.value} "
                    f"(user: {user_id or 'unknown'})"
                )
                
                return True
                
        except Exception as e:
            logger.error(
                f"Profile {profile.profile_id}: Failed to save session for {platform.value}: {e}"
            )
            return False
    
    async def restore_session(
        self,
        profile: BrowserProfile,
        platform: Platform,
        context: BrowserContext
    ) -> bool:
        """Restore platform session to browser context."""
        try:
            async with self._session_lock:
                session_data = profile.platform_sessions.get(platform.value)
                
                if not session_data:
                    # Try loading from disk
                    session_data = await self._load_encrypted_session(profile, platform)
                    if session_data:
                        profile.platform_sessions[platform.value] = session_data
                
                if not session_data or not session_data.get('is_valid'):
                    return False
                
                # Check session age
                last_updated = datetime.fromisoformat(session_data['last_updated'])
                session_age_hours = (datetime.utcnow() - last_updated).total_seconds() / 3600
                
                if session_age_hours > 24:
                    logger.warning(
                        f"Profile {profile.profile_id}: Session for {platform.value} is too old "
                        f"({session_age_hours:.1f} hours)"
                    )
                    return False
                
                # Check fingerprint consistency
                if session_data.get('fingerprint_hash') != profile.fingerprint_hash:
                    logger.warning(
                        f"Profile {profile.profile_id}: Fingerprint mismatch for {platform.value} session"
                    )
                
                # Restore cookies
                if session_data.get('cookies'):
                    await context.add_cookies(session_data['cookies'])
                
                # Restore localStorage if possible
                # Note: Playwright doesn't directly support localStorage restoration
                # You'd need to navigate to the site first and then inject it via JavaScript
                
                logger.info(
                    f"Profile {profile.profile_id}: Restored session for {platform.value} "
                    f"(age: {session_age_hours:.1f} hours)"
                )
                
                return True
                
        except Exception as e:
            logger.error(
                f"Profile {profile.profile_id}: Failed to restore session for {platform.value}: {e}"
            )
            return False
    
    def invalidate_session(
        self,
        profile: BrowserProfile,
        platform: Platform
    ):
        """Invalidate a session."""
        if platform.value in profile.platform_sessions:
            profile.platform_sessions[platform.value]['is_valid'] = False
            self.session_ready_profiles[platform.value].discard(profile.profile_id)
            logger.warning(f"Invalidated session for profile {profile.profile_id} on {platform.value}")
    
    async def validate_sessions(
        self,
        profiles: Dict[str, BrowserProfile],
        max_age_hours: int = 24
    ):
        """Validate all sessions and mark stale ones."""
        async with self._session_lock:
            now = datetime.utcnow()
            
            for profile_id, profile in profiles.items():
                for platform, session in profile.platform_sessions.items():
                    if not session.get('is_valid'):
                        continue
                    
                    # Check age
                    last_updated = datetime.fromisoformat(session['last_updated'])
                    age_hours = (now - last_updated).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        session['is_valid'] = False
                        self.session_ready_profiles[platform].discard(profile_id)
                        logger.info(
                            f"Invalidated old session for profile {profile_id} on {platform} "
                            f"(age: {age_hours:.1f} hours)"
                        )
    
    def _extract_auth_tokens(
        self,
        cookies: List[Dict],
        storage_state: Dict
    ) -> Dict[str, str]:
        """Extract authentication tokens from cookies and storage."""
        tokens = {}
        
        # Common auth cookie patterns
        auth_patterns = [
            'auth_token', 'session_id', 'access_token', 'jwt', 'sid',
            'JSESSIONID', 'sessionid', 'auth', 'token', 'csrf'
        ]
        
        # Extract from cookies
        for cookie in cookies:
            cookie_name = cookie.get('name', '').lower()
            if any(pattern in cookie_name for pattern in auth_patterns):
                tokens[cookie['name']] = cookie['value']
        
        # Extract from localStorage
        for origin in storage_state.get('origins', []):
            for key, value in origin.get('localStorage', {}).items():
                key_lower = key.lower()
                if any(pattern in key_lower for pattern in auth_patterns):
                    tokens[key] = value
        
        return tokens
    
    def _extract_user_id(
        self,
        cookies: List[Dict],
        storage_state: Dict,
        platform: Platform
    ) -> Optional[str]:
        """Extract user ID based on platform."""
        # Platform-specific extraction
        if platform == Platform.TICKETMASTER:
            # Look for Ticketmaster-specific user identifiers
            for cookie in cookies:
                if 'member' in cookie.get('name', '').lower():
                    return cookie.get('value')
        
        elif platform == Platform.FANSALE:
            # Fansale patterns
            for cookie in cookies:
                if 'user' in cookie.get('name', '').lower():
                    return cookie.get('value')
        
        # Generic patterns
        for cookie in cookies:
            name = cookie.get('name', '').lower()
            if any(pattern in name for pattern in ['user_id', 'userid', 'uid', 'member_id']):
                return cookie.get('value')
        
        # Check localStorage
        for origin in storage_state.get('origins', []):
            local_storage = origin.get('localStorage', {})
            for key, value in local_storage.items():
                if 'user' in key.lower() and 'id' in key.lower():
                    return value
        
        return None
    
    async def _save_encrypted_session(
        self,
        profile: BrowserProfile,
        platform: Platform,
        session_data: SessionData
    ):
        """Save encrypted session data to disk."""
        try:
            session_file = self.session_backup_dir / f"{profile.profile_id}_{platform.value}.enc"
            
            # Compress and encrypt
            fernet = Fernet(profile._context_encryption_key)
            compressed = zstd.compress(json.dumps(session_data).encode())
            encrypted = fernet.encrypt(compressed)
            
            async with aiofiles.open(session_file, 'wb') as f:
                await f.write(encrypted)
                
        except Exception as e:
            logger.error(f"Failed to save encrypted session: {e}")
    
    async def _load_encrypted_session(
        self,
        profile: BrowserProfile,
        platform: Platform
    ) -> Optional[SessionData]:
        """Load encrypted session data from disk."""
        try:
            session_file = self.session_backup_dir / f"{profile.profile_id}_{platform.value}.enc"
            
            if not session_file.exists():
                return None
            
            async with aiofiles.open(session_file, 'rb') as f:
                encrypted = await f.read()
            
            # Decrypt and decompress
            fernet = Fernet(profile._context_encryption_key)
            compressed = fernet.decrypt(encrypted)
            decompressed = zstd.decompress(compressed)
            
            return json.loads(decompressed.decode())
            
        except Exception as e:
            logger.error(f"Failed to load encrypted session: {e}")
            return None