# Domain Entity: Platform
"""
Platform entity representing supported ticketing platforms.
This is a core domain concept with no external dependencies.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Any


class PlatformType(Enum):
    """Supported ticketing platforms"""
    FANSALE = "fansale"
    TICKETMASTER = "ticketmaster"
    VIVATICKET = "vivaticket"


@dataclass
class Platform:
    """Platform configuration and requirements"""
    platform_type: PlatformType
    
    @property
    def name(self) -> str:
        return self.platform_type.value
    
    @property
    def requires_stealth(self) -> bool:
        """Check if platform needs enhanced stealth"""
        return self.platform_type in [PlatformType.TICKETMASTER, PlatformType.VIVATICKET]
    
    @property
    def preferred_browsers(self) -> List[str]:
        """Get preferred browsers for platform"""
        preferences = {
            PlatformType.FANSALE: ["Chrome", "Firefox", "Edge"],
            PlatformType.TICKETMASTER: ["Chrome", "Edge"],
            PlatformType.VIVATICKET: ["Chrome", "Firefox"],
        }
        return preferences.get(self.platform_type, ["Chrome"])
    
    @property
    def stealth_requirements(self) -> Dict[str, Any]:
        """Get stealth requirements for platform"""
        requirements = {
            PlatformType.FANSALE: {
                "aggressive_stealth": False,
                "browser_preferences": ["Chrome", "Firefox", "Edge"],
                "requires_referrer": True,
                "supports_mobile": False,
                "min_viewport_width": 1280,
                "preferred_locale": "it-IT"
            },
            PlatformType.TICKETMASTER: {
                "aggressive_stealth": True,
                "browser_preferences": ["Chrome", "Edge"],
                "requires_referrer": True,
                "supports_mobile": False,
                "min_viewport_width": 1366,
                "preferred_locale": "en-US",
                "requires_webgl": True,
                "requires_canvas": True
            },
            PlatformType.VIVATICKET: {
                "aggressive_stealth": True,
                "browser_preferences": ["Chrome", "Firefox"],
                "requires_referrer": True,
                "supports_mobile": False,
                "min_viewport_width": 1280,
                "preferred_locale": "it-IT"
            }
        }
        return requirements.get(self.platform_type, requirements[PlatformType.FANSALE])
    
    def __hash__(self):
        return hash(self.platform_type)
    
    def __eq__(self, other):
        if isinstance(other, Platform):
            return self.platform_type == other.platform_type
        return False