# src/models/proxy.py
"""
Unified proxy configuration model
"""

from dataclasses import dataclass
from typing import Optional
import uuid


@dataclass
class ProxyConfig:
    """Enhanced proxy configuration with rotation support."""
    proxy_type: str = "http"
    host: str = ""
    port: int = 0
    username: Optional[str] = None
    password: Optional[str] = None
    rotation_endpoint: Optional[str] = None
    sticky_session: bool = True
    country_code: Optional[str] = None
    proxy_provider: Optional[str] = None  # brightdata, oxylabs, etc.
    
    def get_proxy_url(self, session_id: Optional[str] = None) -> Optional[str]:
        """Get formatted proxy URL with session support."""
        if not self.host or not self.port:
            return None
            
        auth = ""
        if self.username and self.password:
            username_parts = [self.username]
            if session_id and self.sticky_session:
                username_parts.append(f"session-{session_id}")
            if self.country_code:
                username_parts.append(f"country-{self.country_code}")
            
            final_username = "-".join(username_parts)
            auth = f"{final_username}:{self.password}@"
            
        return f"{self.proxy_type}://{auth}{self.host}:{self.port}"
    
    def rotate_session(self) -> str:
        """Generate new session ID for proxy rotation."""
        return str(uuid.uuid4())[:8]
    
    def to_httpx_proxy(self) -> Optional[str]:
        """Convert to httpx-compatible proxy URL."""
        return self.get_proxy_url()
    
    @property
    def protocol(self) -> str:
        """Alias for proxy_type for backward compatibility."""
        return self.proxy_type