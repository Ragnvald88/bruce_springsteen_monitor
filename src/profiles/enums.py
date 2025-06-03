# src/profiles/enums.py
"""Profile-related enumerations."""
from enum import Enum


class ProfileQuality(Enum):
    """Profile quality tiers with enhanced metadata."""
    LOW = (1, 0.1, 300)      # (tier, success_multiplier, cooldown_seconds)
    MEDIUM = (2, 0.5, 180)   
    HIGH = (3, 0.8, 120)     
    PREMIUM = (4, 1.0, 60)   
    
    @property
    def tier(self):
        return self.value[0]
    
    @property
    def success_multiplier(self):
        return self.value[1]
    
    @property
    def cooldown_seconds(self):
        return self.value[2]


class DataOptimizationLevel(Enum):
    """Data usage optimization levels."""
    OFF = "off"
    MINIMAL = "minimal"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class Platform(Enum):
    """Supported ticketing platforms."""
    FANSALE = "fansale"
    TICKETMASTER = "ticketmaster"
    VIVATICKET = "vivaticket"
    
    @property
    def login_url(self):
        urls = {
            "fansale": "https://www.fansale.it/login",
            "ticketmaster": "https://shop.ticketmaster.it/login",
            "vivaticket": "https://shop.vivaticket.com/login"
        }
        return urls.get(self.value, "")
    
    @property
    def stealth_requirements(self):
        """Platform-specific stealth requirements."""
        requirements = {
            "fansale": {
                "aggressive_stealth": False,
                "require_residential_proxy": False,
                "browser_preferences": ["Chrome", "Edge"]
            },
            "ticketmaster": {
                "aggressive_stealth": True,
                "require_residential_proxy": True,
                "browser_preferences": ["Chrome", "Edge"],
                "additional_headers": {
                    "sec-fetch-site": "same-origin",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-dest": "document"
                }
            },
            "vivaticket": {
                "aggressive_stealth": True,
                "require_residential_proxy": False,
                "browser_preferences": ["Chrome", "Firefox"]
            }
        }
        return requirements.get(self.value, {})