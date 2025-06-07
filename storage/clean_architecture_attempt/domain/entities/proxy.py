# Domain Entity: Proxy
"""
Proxy configuration entity for network requests.
Pure domain object with no external dependencies.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProxyConfig:
    """Proxy configuration with authentication and rotation support"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: str = "http"
    country_code: Optional[str] = None
    rotation_endpoint: Optional[str] = None
    sticky_session: bool = True
    proxy_provider: Optional[str] = None
    
    def get_proxy_url(self, session_id: Optional[str] = None) -> Optional[str]:
        """Get formatted proxy URL"""
        if not self.host or not self.port:
            return None
        
        auth = ""
        if self.username and self.password:
            username = self.username
            if session_id:
                username = f"{self.username}-session-{session_id}"
            if self.country_code:
                username = f"{username}-country-{self.country_code}"
            auth = f"{username}:{self.password}@"
        
        return f"{self.proxy_type}://{auth}{self.host}:{self.port}"
    
    @property
    def is_residential(self) -> bool:
        """Check if proxy is residential based on provider"""
        residential_providers = ['brightdata', 'oxylabs', 'smartproxy', 'iproyal']
        return self.proxy_provider in residential_providers if self.proxy_provider else False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'proxy_type': self.proxy_type,
            'country_code': self.country_code,
            'proxy_provider': self.proxy_provider,
            'sticky_session': self.sticky_session
        }