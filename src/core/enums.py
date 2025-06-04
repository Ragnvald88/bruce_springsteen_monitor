# src/core/enums.py
from __future__ import annotations
from enum import Enum, auto

# Import CorePlatformEnum from your profiles package to be used by PlatformType
try:
    from src.profiles.enums import Platform as CorePlatformEnum
except ImportError:
    # Fallback or error handling if src.profiles.enums.Platform cannot be imported
    # This is critical for PlatformType.to_core_platform()
    print("CRITICAL ERROR: Could not import CorePlatformEnum from src.profiles.enums in core.enums")
    # Define a dummy if needed for the script to be parsable, but this indicates a setup issue
    class CorePlatformEnum(Enum):
        DUMMY = "dummy_platform"


class OperationMode(Enum):
    """System operation modes with enhanced capabilities"""
    STEALTH = "stealth"
    BEAST = "beast"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"
    ULTRA_STEALTH = "ultra_stealth"

class PlatformType(Enum):
    """Supported ticketing platforms - aligned with core.profiles.Platform"""
    FANSALE = "fansale"
    TICKETMASTER = "ticketmaster"
    VIVATICKET = "vivaticket"

    def to_core_platform(self) -> CorePlatformEnum:
        """Convert to core Platform enum from src.profiles.enums"""
        from src.profiles.enums import Platform as CorePlatformEnum
        mapping = {
            PlatformType.FANSALE: CorePlatformEnum.FANSALE,
            PlatformType.TICKETMASTER: CorePlatformEnum.TICKETMASTER,
            PlatformType.VIVATICKET: CorePlatformEnum.VIVATICKET
        }
        result = mapping.get(self)
        if result is None:
            # Fallback to GENERIC if mapping not found
            result = CorePlatformEnum.GENERIC

        return result
        


class PriorityLevel(Enum):
    """Enhanced priority system with dynamic weighting"""
    # Value tuple: (numeric_value, speed_multiplier, data_multiplier)
    CRITICAL = (1, 1.0, 0.1)
    HIGH = (2, 0.8, 0.3)
    NORMAL = (3, 0.6, 0.5)
    LOW = (4, 0.4, 0.8)

    # __init__ is implicitly handled for enums with values.
    # Properties are a good way to access tuple parts.
    @property
    def numeric_value(self) -> int:
        return self.value[0]

    @property
    def speed_multiplier(self) -> float:
        return self.value[1]

    @property
    def data_multiplier(self) -> float:
        return self.value[2]

class DetectionStatus(Enum):
    """Advanced detection states for opportunities"""
    MONITORING = auto()
    DETECTED = auto()
    VERIFIED = auto()
    ATTEMPTING = auto()
    SUCCESS = auto()
    FAILED = auto()
    BLOCKED = auto()
    RATE_LIMITED = auto()
    DATA_LIMITED = auto()
