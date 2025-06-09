# Platform Adapter
"""
Adapter to bridge between old platform enums and new domain entities.
"""
from typing import Union, Any
from domain.entities import Platform, PlatformType


class PlatformAdapter:
    """Converts between different platform representations"""
    
    @staticmethod
    def from_string(platform_str: str) -> Platform:
        """Convert string to Platform entity"""
        platform_str = platform_str.lower()
        
        if platform_str == "fansale":
            return Platform(PlatformType.FANSALE)
        elif platform_str == "ticketmaster":
            return Platform(PlatformType.TICKETMASTER)
        elif platform_str == "vivaticket":
            return Platform(PlatformType.VIVATICKET)
        else:
            # Default to fansale
            return Platform(PlatformType.FANSALE)
    
    @staticmethod
    def from_old_enum(old_platform: Any) -> Platform:
        """Convert old platform enum to new Platform entity"""
        # Handle various old enum types
        if hasattr(old_platform, 'value'):
            platform_str = old_platform.value
        elif hasattr(old_platform, 'name'):
            platform_str = old_platform.name.lower()
        else:
            platform_str = str(old_platform).lower()
        
        return PlatformAdapter.from_string(platform_str)
    
    @staticmethod
    def to_string(platform: Union[Platform, PlatformType]) -> str:
        """Convert Platform to string"""
        if isinstance(platform, Platform):
            return platform.name
        elif isinstance(platform, PlatformType):
            return platform.value
        else:
            return str(platform).lower()