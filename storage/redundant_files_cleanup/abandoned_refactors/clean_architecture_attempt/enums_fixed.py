# Core Enums - Fixed Version
"""
Core enums that bridge to the new domain entities.
This file provides backwards compatibility while using the new architecture.
"""
from enum import Enum
import sys
from pathlib import Path

# Add parent directory to path for domain imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from domain entities
from domain.entities import PlatformType as DomainPlatformType
from domain.entities import PriorityLevel, ProfileState


class OperationMode(Enum):
    """System operation modes with enhanced capabilities"""
    STEALTH = "stealth"
    BEAST = "beast"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"
    ULTRA_STEALTH = "ultra_stealth"


class PlatformType(Enum):
    """Supported ticketing platforms - wrapper around domain PlatformType"""
    FANSALE = "fansale"
    TICKETMASTER = "ticketmaster"
    VIVATICKET = "vivaticket"

    def to_core_platform(self):
        """Convert to domain PlatformType"""
        mapping = {
            PlatformType.FANSALE: DomainPlatformType.FANSALE,
            PlatformType.TICKETMASTER: DomainPlatformType.TICKETMASTER,
            PlatformType.VIVATICKET: DomainPlatformType.VIVATICKET
        }
        return mapping.get(self, DomainPlatformType.FANSALE)


class DetectionStatus(Enum):
    """Advanced detection states for opportunities"""
    MONITORING = "monitoring"
    DETECTED = "detected"
    VERIFIED = "verified"
    ATTEMPTING = "attempting"
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    DATA_LIMITED = "data_limited"


# Re-export domain enums for compatibility
Platform = DomainPlatformType
ProfileQuality = ProfileState  # Map to ProfileState for now


# Export all
__all__ = [
    'OperationMode',
    'PlatformType',
    'Platform',
    'PriorityLevel',
    'DetectionStatus',
    'ProfileState',
    'ProfileQuality'
]