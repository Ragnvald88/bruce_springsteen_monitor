# stealthmaster/network/session.py
"""Advanced session management with cookie handling and state persistence."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
import pickle
from collections import defaultdict
from urllib.parse import urlparse
import aiofiles

from playwright.async_api import Page, BrowserContext, Cookie
import httpx

from ..profiles.models import Profile, UserCredentials

logger = logging.getLogger(__name__)


class SessionState:
    """Represents a session state."""
    
    def __init__(self, session_id: str, platform: str, profile_id: str):
        """Initialize session state."""
        self.session_id = session_id
        self.platform = platform
        self.profile_id = profile_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.is_authenticated = False
        self.auth_tokens: Dict[str, str] = {}
        self.cookies: List[Cookie] = []
        self.headers: Dict[str, str] = {}
        self.metadata: Dict[str, Any] = {}
        self.request_count = 0
        self.error_count = 0
        
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
        self.request_count += 1
    
    def is_expired(self, max_age_minutes: int = 30) -> bool:
        """Check if session is expired."""
        age = datetime.now() - self.last_activity
        return age.total_seconds() > (max_age_minutes * 60)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "platform": self.platform,
            "profile_id": self.profile_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_authenticated": self.is_authenticated,
            "auth_tokens": self.auth_tokens,
            "cookies": [self._cookie_to_dict(c) for c in self.cookies],
            "headers": self.headers,
            "metadata": self.metadata,
            "request_count": self.request_count,
            "error_count": self.error_count
        }
    
    @staticmethod
    def _cookie_to_dict(cookie: Cookie) -> Dict[str, Any]:
        """Convert Playwright cookie to dict."""
        return {
            "name": cookie.get("name"),
            "value": cookie.get("value"),
            "domain": cookie.get("domain"),
            "path": cookie.get("path"),
            "expires": cookie.get("expires"),
            "httpOnly": cookie.get("httpOnly"),
            "secure": cookie.get("secure"),
            "sameSite": cookie.get("sameSite")
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """Create from dictionary."""
        session = cls(
            session_id=data["session_id"],
            platform=data["platform"],
            profile_id=data["profile_id"]
        )
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.last_activity = datetime.fromisoformat(data["last_activity"])
        session.is_authenticated = data["is_authenticated"]
        session.auth_tokens = data["auth_tokens"]
        session.cookies = data["cookies"]  # Already dict format
        session.headers = data["headers"]
        session.metadata = data["metadata"]
        session.request_count = data["request_count"]
        session.error_count = data["error_count"]
        return session


class SessionManager:
    """Manages browser sessions with persistence and rotation."""
    
    def __init__(self, data_dir: Path):
        """Initialize session manager."""
        self.data_dir = data_dir
        self.sessions_dir = data_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Active sessions
        self._sessions: Dict[str, SessionState] = {}
        self._session_locks: Dict[str, asyncio.Lock] = {}
        
        # Session pools by platform
        self._session_pools: Dict[str, List[SessionState]] = defaultdict(list)
        
        # Cookie management
        self._cookie_jar = CookieJar()
        
        # Session metrics
        self._metrics = SessionMetrics()
        
        # Load existing sessions
        self._load_task = asyncio.create_task(self._load_sessions())
    
    async def create_session(
        self,
        page: Page,
        platform: str,
        profile: Profile
    ) -> SessionState:
        """
        Create a new session.
        
        Args:
            page: Browser page
            platform: Platform name
            profile: User profile
            
        Returns:
            Created session
        """
        session_id = f"{platform}_{profile.id}_{datetime.now().timestamp()}"
        session = SessionState(
            session_id=session_id,
            platform=platform,
            profile_id=profile.id
        )
        
        # Store session
        self._sessions[session_id] = session
        self._session_locks[session_id] = asyncio.Lock()
        
        # Initialize cookies from profile if available
        cred = profile.get_credential(platform)
        if cred and cred.cookies:
            await self._restore_cookies(page, cred.cookies)
            session.cookies = cred.cookies
        
        # Add to pool
        self._session_pools[platform].append(session)
        
        logger.info(f"Created session {session_id} for {platform}")
        return session
    
    async def get_session(
        self,
        platform: str,
        profile_id: str
    ) -> Optional[SessionState]:
        """Get existing session for profile and platform."""
        # Look for active session
        for session in self._sessions.values():
            if session.platform == platform and session.profile_id == profile_id:
                if not session.is_expired():
                    session.update_activity()
                    return session
        
        # Look in pool
        for session in self._session_pools[platform]:
            if session.profile_id == profile_id and not session.is_expired():
                session.update_activity()
                return session
        
        return None
    
    async def update_session(
        self,
        session_id: str,
        page: Optional[Page] = None,
        authenticated: Optional[bool] = None,
        auth_tokens: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update session state.
        
        Args:
            session_id: Session ID
            page: Optional page to extract cookies from
            authenticated: Authentication status
            auth_tokens: Authentication tokens
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        
        async with self._session_locks[session_id]:
            session.update_activity()
            
            if authenticated is not None:
                session.is_authenticated = authenticated
            
            if auth_tokens:
                session.auth_tokens.update(auth_tokens)
            
            if metadata:
                session.metadata.update(metadata)
            
            # Extract cookies from page
            if page:
                context = page.context
                cookies = await context.cookies()
                session.cookies = cookies
                
                # Update cookie jar
                for cookie in cookies:
                    self._cookie_jar.add_cookie(cookie, session.platform)
            
            # Save session
            await self._save_session(session)
        
        return True
    
    async def rotate_session(
        self,
        platform: str,
        profile_id: str
    ) -> Optional[SessionState]:
        """
        Rotate to a new session for profile.
        
        Args:
            platform: Platform name
            profile_id: Profile ID
            
        Returns:
            New session or None
        """
        # Invalidate existing session
        old_session = await self.get_session(platform, profile_id)
        if old_session:
            await self.invalidate_session(old_session.session_id)
        
        # Create new session ID
        session_id = f"{platform}_{profile_id}_{datetime.now().timestamp()}"
        session = SessionState(
            session_id=session_id,
            platform=platform,
            profile_id=profile_id
        )
        
        # Reuse valid cookies from old session
        if old_session and old_session.cookies:
            valid_cookies = self._filter_valid_cookies(old_session.cookies)
            session.cookies = valid_cookies
        
        # Store new session
        self._sessions[session_id] = session
        self._session_locks[session_id] = asyncio.Lock()
        self._session_pools[platform].append(session)
        
        logger.info(f"Rotated session for {platform}/{profile_id}")
        return session
    
    async def invalidate_session(self, session_id: str) -> None:
        """Invalidate a session."""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            
            # Remove from pool
            if session in self._session_pools[session.platform]:
                self._session_pools[session.platform].remove(session)
            
            # Remove from active sessions
            del self._sessions[session_id]
            if session_id in self._session_locks:
                del self._session_locks[session_id]
            
            # Delete saved session
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
            
            logger.info(f"Invalidated session {session_id}")
    
    async def apply_session_to_page(
        self,
        page: Page,
        session: SessionState
    ) -> None:
        """
        Apply session state to a page.
        
        Args:
            page: Browser page
            session: Session state
        """
        # Apply cookies
        if session.cookies:
            await self._restore_cookies(page, session.cookies)
        
        # Apply headers via route interception
        if session.headers:
            async def add_headers(route):
                headers = {**route.request.headers, **session.headers}
                await route.continue_(headers=headers)
            
            await page.route("**/*", add_headers)
        
        # Apply auth tokens to local storage if needed
        if session.auth_tokens:
            for key, value in session.auth_tokens.items():
                await page.evaluate(f"""
                    localStorage.setItem('{key}', '{value}');
                """)
        
        logger.debug(f"Applied session {session.session_id} to page")
    
    async def extract_session_from_page(
        self,
        page: Page,
        session_id: str
    ) -> None:
        """Extract current session state from page."""
        if session_id not in self._sessions:
            return
        
        session = self._sessions[session_id]
        
        # Extract cookies
        context = page.context
        cookies = await context.cookies()
        session.cookies = cookies
        
        # Extract local storage tokens
        try:
            storage_data = await page.evaluate("""
                () => {
                    const data = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        if (key && (key.includes('token') || key.includes('auth'))) {
                            data[key] = localStorage.getItem(key);
                        }
                    }
                    return data;
                }
            """)
            session.auth_tokens.update(storage_data)
        except Exception as e:
            logger.debug(f"Failed to extract storage data: {e}")
        
        await self._save_session(session)
    
    async def _restore_cookies(
        self,
        page: Page,
        cookies: List[Dict[str, Any]]
    ) -> None:
        """Restore cookies to page."""
        context = page.context
        
        # Filter and clean cookies
        clean_cookies = []
        for cookie in cookies:
            # Ensure required fields
            if "name" in cookie and "value" in cookie:
                clean_cookie = {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie.get("domain", ""),
                    "path": cookie.get("path", "/"),
                }
                
                # Add optional fields
                if "expires" in cookie:
                    clean_cookie["expires"] = cookie["expires"]
                if "httpOnly" in cookie:
                    clean_cookie["httpOnly"] = cookie["httpOnly"]
                if "secure" in cookie:
                    clean_cookie["secure"] = cookie["secure"]
                if "sameSite" in cookie:
                    clean_cookie["sameSite"] = cookie["sameSite"]
                
                clean_cookies.append(clean_cookie)
        
        if clean_cookies:
            await context.add_cookies(clean_cookies)
            logger.debug(f"Restored {len(clean_cookies)} cookies")
    
    def _filter_valid_cookies(
        self,
        cookies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter out expired cookies."""
        valid_cookies = []
        now = datetime.now().timestamp()
        
        for cookie in cookies:
            # Check expiration
            if "expires" in cookie:
                if cookie["expires"] > now:
                    valid_cookies.append(cookie)
            else:
                # Session cookie, keep it
                valid_cookies.append(cookie)
        
        return valid_cookies
    
    async def _save_session(self, session: SessionState) -> None:
        """Save session to disk."""
        session_file = self.sessions_dir / f"{session.session_id}.json"
        
        try:
            async with aiofiles.open(session_file, 'w') as f:
                await f.write(json.dumps(session.to_dict(), indent=2))
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    async def _load_sessions(self) -> None:
        """Load saved sessions from disk."""
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                async with aiofiles.open(session_file, 'r') as f:
                    data = json.loads(await f.read())
                
                session = SessionState.from_dict(data)
                
                # Only load non-expired sessions
                if not session.is_expired(max_age_minutes=1440):  # 24 hours
                    self._sessions[session.session_id] = session
                    self._session_locks[session.session_id] = asyncio.Lock()
                    self._session_pools[session.platform].append(session)
                else:
                    # Delete expired session file
                    session_file.unlink()
                    
            except Exception as e:
                logger.error(f"Failed to load session {session_file}: {e}")
        
        logger.info(f"Loaded {len(self._sessions)} sessions")
    
    def get_platform_sessions(
        self,
        platform: str,
        authenticated_only: bool = False
    ) -> List[SessionState]:
        """Get all sessions for a platform."""
        sessions = self._session_pools.get(platform, [])
        
        if authenticated_only:
            sessions = [s for s in sessions if s.is_authenticated]
        
        # Filter expired
        valid_sessions = [s for s in sessions if not s.is_expired()]
        
        return valid_sessions
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics."""
        total_sessions = len(self._sessions)
        authenticated = sum(1 for s in self._sessions.values() if s.is_authenticated)
        
        by_platform = {}
        for platform, sessions in self._session_pools.items():
            valid = [s for s in sessions if not s.is_expired()]
            by_platform[platform] = {
                "total": len(valid),
                "authenticated": sum(1 for s in valid if s.is_authenticated)
            }
        
        return {
            "total_sessions": total_sessions,
            "authenticated_sessions": authenticated,
            "by_platform": by_platform,
            "cookie_stats": self._cookie_jar.get_statistics(),
            "metrics": self._metrics.get_summary()
        }
    
    async def cleanup_expired(self) -> int:
        """Clean up expired sessions."""
        expired = []
        
        for session_id, session in self._sessions.items():
            if session.is_expired():
                expired.append(session_id)
        
        for session_id in expired:
            await self.invalidate_session(session_id)
        
        logger.info(f"Cleaned up {len(expired)} expired sessions")
        return len(expired)
    
    async def shutdown(self) -> None:
        """Shutdown session manager and cleanup resources."""
        # Cancel load task if still running
        if hasattr(self, '_load_task') and not self._load_task.done():
            self._load_task.cancel()
            try:
                await self._load_task
            except asyncio.CancelledError:
                pass
        
        # Save all sessions
        await self._save_sessions()
        
        logger.info("Session manager shut down")


class CookieJar:
    """Manages cookies across domains and platforms."""
    
    def __init__(self):
        """Initialize cookie jar."""
        self._cookies: Dict[str, Dict[str, Cookie]] = defaultdict(dict)
        self._cookie_stats: Dict[str, int] = defaultdict(int)
    
    def add_cookie(self, cookie: Dict[str, Any], platform: str) -> None:
        """Add cookie to jar."""
        domain = cookie.get("domain", "")
        name = cookie.get("name", "")
        key = f"{domain}:{name}"
        
        self._cookies[platform][key] = cookie
        self._cookie_stats[platform] += 1
    
    def get_cookies_for_url(
        self,
        url: str,
        platform: str
    ) -> List[Dict[str, Any]]:
        """Get cookies applicable to URL."""
        parsed = urlparse(url)
        domain = parsed.netloc
        
        applicable_cookies = []
        
        for key, cookie in self._cookies.get(platform, {}).items():
            cookie_domain = cookie.get("domain", "")
            
            # Check if cookie applies to this domain
            if self._domain_matches(domain, cookie_domain):
                # Check path
                path = cookie.get("path", "/")
                if parsed.path.startswith(path):
                    applicable_cookies.append(cookie)
        
        return applicable_cookies
    
    def _domain_matches(self, request_domain: str, cookie_domain: str) -> bool:
        """Check if cookie domain matches request domain."""
        # Remove leading dot
        if cookie_domain.startswith("."):
            cookie_domain = cookie_domain[1:]
        
        # Exact match or subdomain match
        return (request_domain == cookie_domain or 
                request_domain.endswith(f".{cookie_domain}"))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cookie statistics."""
        return {
            "total_cookies": sum(len(cookies) for cookies in self._cookies.values()),
            "by_platform": dict(self._cookie_stats),
            "unique_domains": len(set(
                cookie.get("domain", "")
                for cookies in self._cookies.values()
                for cookie in cookies.values()
            ))
        }


class SessionMetrics:
    """Track session performance metrics."""
    
    def __init__(self):
        """Initialize metrics."""
        self._request_times: List[Tuple[datetime, float]] = []
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._success_counts: Dict[str, int] = defaultdict(int)
        self._auth_durations: List[float] = []
    
    def record_request(self, platform: str, duration: float, success: bool) -> None:
        """Record request metrics."""
        self._request_times.append((datetime.now(), duration))
        
        if success:
            self._success_counts[platform] += 1
        else:
            self._error_counts[platform] += 1
        
        # Keep only recent data
        cutoff = datetime.now() - timedelta(hours=1)
        self._request_times = [
            (t, d) for t, d in self._request_times
            if t > cutoff
        ]
    
    def record_auth_duration(self, duration: float) -> None:
        """Record authentication duration."""
        self._auth_durations.append(duration)
        
        # Keep only last 100
        if len(self._auth_durations) > 100:
            self._auth_durations = self._auth_durations[-100:]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        avg_request_time = 0.0
        if self._request_times:
            avg_request_time = sum(d for _, d in self._request_times) / len(self._request_times)
        
        avg_auth_time = 0.0
        if self._auth_durations:
            avg_auth_time = sum(self._auth_durations) / len(self._auth_durations)
        
        return {
            "avg_request_time_ms": avg_request_time * 1000,
            "avg_auth_time_s": avg_auth_time,
            "success_counts": dict(self._success_counts),
            "error_counts": dict(self._error_counts),
            "recent_requests": len(self._request_times)
        }