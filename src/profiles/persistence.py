"""
Browser Session Persistence Manager

Handles saving and restoring browser states across sessions to maintain
continuity and avoid re-authentication.
"""

import json
import pickle
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import aiofiles
import logging
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
import base64
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    """Represents a complete browser session state"""
    session_id: str
    platform: str
    profile_id: str
    created_at: datetime
    last_accessed: datetime
    
    # Browser state
    cookies: List[Dict[str, Any]]
    local_storage: Dict[str, str]
    session_storage: Dict[str, str]
    
    # Authentication
    auth_tokens: Dict[str, str]
    auth_expiry: Optional[datetime]
    
    # Fingerprint data
    fingerprint: Dict[str, Any]
    user_agent: str
    viewport: Dict[str, int]
    
    # Network state
    proxy_config: Optional[Dict[str, Any]]
    
    # Custom data
    custom_data: Dict[str, Any]
    
    # Session health
    is_valid: bool = True
    detection_score: float = 0.0
    

class SessionPersistence:
    """Manages browser session persistence with encryption"""
    
    def __init__(self, storage_path: str = "./session_data"):
        """Initialize session persistence manager"""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Generate or load encryption key
        self._init_encryption()
        
        # Session cache
        self._session_cache: Dict[str, SessionState] = {}
        
        # Cleanup old sessions on init
        asyncio.create_task(self._cleanup_old_sessions())
        
    def _init_encryption(self) -> None:
        """Initialize encryption for sensitive data"""
        key_file = self.storage_path / ".session_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Secure the key file
            key_file.chmod(0o600)
        
        self.cipher = Fernet(key)
        
    async def save_session(
        self,
        session_id: str,
        browser_context,
        platform: str,
        profile_id: str,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save browser session state
        
        Args:
            session_id: Unique session identifier
            browser_context: Playwright browser context
            platform: Platform name (e.g., 'fansale', 'ticketmaster')
            profile_id: Profile identifier
            custom_data: Additional custom data to store
            
        Returns:
            Success status
        """
        try:
            # Extract browser state
            cookies = await browser_context.cookies()
            
            # Get storage state (includes localStorage and sessionStorage)
            storage_state = await browser_context.storage_state()
            
            # Parse localStorage and sessionStorage
            local_storage = {}
            session_storage = {}
            
            for origin in storage_state.get('origins', []):
                origin_url = origin['origin']
                
                for item in origin.get('localStorage', []):
                    key = f"{origin_url}::{item['name']}"
                    local_storage[key] = item['value']
                    
                # Note: Playwright doesn't expose sessionStorage in storage_state
                # We'll need to extract it via JavaScript
                
            # Extract additional data via JavaScript
            pages = browser_context.pages
            if pages:
                page = pages[0]  # Use first page
                
                # Extract sessionStorage
                session_storage_data = await page.evaluate("""
                    () => {
                        const storage = {};
                        for (let i = 0; i < sessionStorage.length; i++) {
                            const key = sessionStorage.key(i);
                            storage[key] = sessionStorage.getItem(key);
                        }
                        return storage;
                    }
                """)
                
                session_storage = session_storage_data
                
                # Extract auth tokens if present
                auth_tokens = await page.evaluate("""
                    () => {
                        const tokens = {};
                        // Common token locations
                        const tokenKeys = ['access_token', 'auth_token', 'jwt', 'session_token'];
                        
                        // Check localStorage
                        tokenKeys.forEach(key => {
                            const value = localStorage.getItem(key);
                            if (value) tokens[key] = value;
                        });
                        
                        // Check cookies
                        const cookies = document.cookie.split(';');
                        cookies.forEach(cookie => {
                            const [name, value] = cookie.trim().split('=');
                            if (tokenKeys.includes(name)) {
                                tokens[name] = value;
                            }
                        });
                        
                        return tokens;
                    }
                """)
                
                # Get fingerprint data
                fingerprint = await page.evaluate("""
                    () => ({
                        screen: {
                            width: screen.width,
                            height: screen.height,
                            colorDepth: screen.colorDepth,
                            pixelDepth: screen.pixelDepth
                        },
                        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                        language: navigator.language,
                        platform: navigator.platform,
                        hardwareConcurrency: navigator.hardwareConcurrency,
                        deviceMemory: navigator.deviceMemory
                    })
                """)
                
                # Get viewport
                viewport = page.viewport_size
            else:
                auth_tokens = {}
                fingerprint = {}
                viewport = {"width": 1920, "height": 1080}
            
            # Create session state
            session_state = SessionState(
                session_id=session_id,
                platform=platform,
                profile_id=profile_id,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                cookies=cookies,
                local_storage=local_storage,
                session_storage=session_storage,
                auth_tokens=auth_tokens,
                auth_expiry=self._estimate_auth_expiry(cookies, auth_tokens),
                fingerprint=fingerprint,
                user_agent=await browser_context.evaluate("() => navigator.userAgent"),
                viewport=viewport,
                proxy_config=None,  # TODO: Extract from context if available
                custom_data=custom_data or {},
                is_valid=True,
                detection_score=0.0
            )
            
            # Encrypt sensitive data
            encrypted_state = self._encrypt_session_state(session_state)
            
            # Save to file
            session_file = self.storage_path / f"{platform}_{session_id}.session"
            async with aiofiles.open(session_file, 'wb') as f:
                await f.write(encrypted_state)
            
            # Update cache
            self._session_cache[session_id] = session_state
            
            logger.info(f"Saved session state for {platform}:{session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session state: {e}")
            return False
            
    async def restore_session(
        self,
        session_id: str,
        browser_context,
        platform: str
    ) -> Optional[SessionState]:
        """
        Restore browser session state
        
        Args:
            session_id: Session identifier
            browser_context: Playwright browser context to restore to
            platform: Platform name
            
        Returns:
            Restored session state or None if failed
        """
        try:
            # Check cache first
            if session_id in self._session_cache:
                session_state = self._session_cache[session_id]
                if self._is_session_valid(session_state):
                    logger.info(f"Using cached session for {platform}:{session_id}")
                else:
                    logger.warning(f"Cached session expired for {platform}:{session_id}")
                    del self._session_cache[session_id]
                    return None
            else:
                # Load from file
                session_file = self.storage_path / f"{platform}_{session_id}.session"
                
                if not session_file.exists():
                    logger.warning(f"Session file not found for {platform}:{session_id}")
                    return None
                
                async with aiofiles.open(session_file, 'rb') as f:
                    encrypted_data = await f.read()
                
                session_state = self._decrypt_session_state(encrypted_data)
                
                if not self._is_session_valid(session_state):
                    logger.warning(f"Session expired for {platform}:{session_id}")
                    return None
                
                # Cache it
                self._session_cache[session_id] = session_state
            
            # Restore cookies
            await browser_context.add_cookies(session_state.cookies)
            
            # Only restore localStorage/sessionStorage if we have items to restore
            if session_state.local_storage or session_state.session_storage:
                # Check if we need to create a page for restoration
                pages = browser_context.pages
                restore_page = None
                
                # Only navigate if we have storage to restore
                if session_state.local_storage:
                    # Group localStorage by domain
                    domains_to_restore = set()
                    for key in session_state.local_storage.keys():
                        if '::' in key:
                            domain = key.split('::', 1)[0]
                            domains_to_restore.add(domain)
                    
                    # For each domain, restore its localStorage
                    for domain in domains_to_restore:
                        if not restore_page:
                            restore_page = await browser_context.new_page()
                        
                        # Navigate to a minimal data: URL to set domain context
                        # This avoids loading the actual website
                        await restore_page.goto(f"{domain}/favicon.ico", wait_until='domcontentloaded', timeout=5000)
                        
                        # Restore localStorage for this domain
                        for key, value in session_state.local_storage.items():
                            if key.startswith(domain):
                                local_key = key.split('::', 1)[1] if '::' in key else key
                                await restore_page.evaluate(f"localStorage.setItem({json.dumps(local_key)}, {json.dumps(value)})")
                
                # Close the restore page if we created one
                if restore_page:
                    await restore_page.close()
            
            # Note: sessionStorage is tab-specific and will be lost between sessions
            # It's not practical to restore it without navigating to specific pages
            
            # Update last accessed time
            session_state.last_accessed = datetime.now()
            
            logger.info(f"Restored session state for {platform}:{session_id}")
            return session_state
            
        except Exception as e:
            logger.error(f"Failed to restore session state: {e}")
            return None
            
    def _encrypt_session_state(self, session_state: SessionState) -> bytes:
        """Encrypt session state for storage"""
        # Convert to dict
        state_dict = asdict(session_state)
        
        # Convert datetime objects to strings
        state_dict['created_at'] = state_dict['created_at'].isoformat()
        state_dict['last_accessed'] = state_dict['last_accessed'].isoformat()
        if state_dict['auth_expiry']:
            state_dict['auth_expiry'] = state_dict['auth_expiry'].isoformat()
        
        # Serialize and encrypt
        serialized = pickle.dumps(state_dict)
        encrypted = self.cipher.encrypt(serialized)
        
        return encrypted
        
    def _decrypt_session_state(self, encrypted_data: bytes) -> SessionState:
        """Decrypt session state from storage"""
        # Decrypt
        decrypted = self.cipher.decrypt(encrypted_data)
        state_dict = pickle.loads(decrypted)
        
        # Convert datetime strings back to objects
        state_dict['created_at'] = datetime.fromisoformat(state_dict['created_at'])
        state_dict['last_accessed'] = datetime.fromisoformat(state_dict['last_accessed'])
        if state_dict['auth_expiry']:
            state_dict['auth_expiry'] = datetime.fromisoformat(state_dict['auth_expiry'])
        
        return SessionState(**state_dict)
        
    def _is_session_valid(self, session_state: SessionState) -> bool:
        """Check if session is still valid"""
        # Check if session is marked as invalid
        if not session_state.is_valid:
            return False
        
        # Check detection score
        if session_state.detection_score > 0.8:
            return False
        
        # Check auth expiry
        if session_state.auth_expiry and datetime.now() > session_state.auth_expiry:
            return False
        
        # Check age (sessions older than 7 days are considered stale)
        if datetime.now() - session_state.created_at > timedelta(days=7):
            return False
        
        # Check cookie expiry
        valid_cookies = 0
        for cookie in session_state.cookies:
            if 'expires' in cookie:
                # Playwright uses seconds since epoch
                expiry = datetime.fromtimestamp(cookie['expires'])
                if expiry > datetime.now():
                    valid_cookies += 1
            else:
                # Session cookie, always valid
                valid_cookies += 1
        
        # Need at least some valid cookies
        return valid_cookies > 0
        
    def _estimate_auth_expiry(
        self,
        cookies: List[Dict[str, Any]],
        auth_tokens: Dict[str, str]
    ) -> Optional[datetime]:
        """Estimate when authentication will expire"""
        earliest_expiry = None
        
        # Check cookie expiry
        for cookie in cookies:
            if any(auth_key in cookie['name'].lower() 
                   for auth_key in ['auth', 'session', 'token']):
                if 'expires' in cookie:
                    expiry = datetime.fromtimestamp(cookie['expires'])
                    if earliest_expiry is None or expiry < earliest_expiry:
                        earliest_expiry = expiry
        
        # If we have JWT tokens, try to decode expiry
        for token_name, token_value in auth_tokens.items():
            if 'jwt' in token_name.lower() or '.' in token_value:
                # Simple JWT decode (not cryptographically verified)
                try:
                    parts = token_value.split('.')
                    if len(parts) == 3:
                        # Decode payload
                        payload = base64.urlsafe_b64decode(
                            parts[1] + '=' * (4 - len(parts[1]) % 4)
                        )
                        payload_data = json.loads(payload)
                        
                        # Check for expiry claim
                        if 'exp' in payload_data:
                            expiry = datetime.fromtimestamp(payload_data['exp'])
                            if earliest_expiry is None or expiry < earliest_expiry:
                                earliest_expiry = expiry
                except Exception:
                    pass
        
        # Default to 24 hours if no expiry found
        if earliest_expiry is None:
            earliest_expiry = datetime.now() + timedelta(hours=24)
        
        return earliest_expiry
        
    async def _cleanup_old_sessions(self) -> None:
        """Clean up old session files"""
        try:
            for session_file in self.storage_path.glob("*.session"):
                # Check file age
                file_stat = session_file.stat()
                file_age = datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_age > timedelta(days=30):
                    session_file.unlink()
                    logger.info(f"Cleaned up old session file: {session_file.name}")
                    
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
            
    async def get_valid_sessions(self, platform: str) -> List[SessionState]:
        """Get all valid sessions for a platform"""
        valid_sessions = []
        
        for session_file in self.storage_path.glob(f"{platform}_*.session"):
            try:
                async with aiofiles.open(session_file, 'rb') as f:
                    encrypted_data = await f.read()
                
                session_state = self._decrypt_session_state(encrypted_data)
                
                if self._is_session_valid(session_state):
                    valid_sessions.append(session_state)
                    
            except Exception as e:
                logger.error(f"Error loading session file {session_file}: {e}")
                
        return valid_sessions
        
    def invalidate_session(self, session_id: str) -> None:
        """Mark a session as invalid"""
        if session_id in self._session_cache:
            self._session_cache[session_id].is_valid = False
            
    def update_detection_score(self, session_id: str, score: float) -> None:
        """Update detection score for a session"""
        if session_id in self._session_cache:
            self._session_cache[session_id].detection_score = score
            
    async def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export session data for analysis or backup"""
        if session_id in self._session_cache:
            session_state = self._session_cache[session_id]
            return asdict(session_state)
        return None


# Global instance
session_persistence = SessionPersistence()