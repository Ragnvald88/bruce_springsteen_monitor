# src/models/enums.py
"""
Unified enums for the entire project
"""

from enum import Enum, auto


class Platform(Enum):
    """Unified platform enum - single source of truth"""
    FANSALE = "fansale"
    TICKETMASTER = "ticketmaster"
    VIVATICKET = "vivaticket"
    GENERIC = "generic"


class OperationMode(Enum):
    """System operation modes with enhanced capabilities"""
    STEALTH = "stealth"
    BEAST = "beast"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"
    ULTRA_STEALTH = "ultra_stealth"


class PriorityLevel(Enum):
    """Enhanced priority system with dynamic weighting"""
    # Value tuple: (numeric_value, speed_multiplier, data_multiplier)
    CRITICAL = (1, 1.0, 0.1)
    HIGH = (2, 0.8, 0.3)
    NORMAL = (3, 0.6, 0.5)
    LOW = (4, 0.4, 0.8)

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


class ProfileState(Enum):
    """Browser profile health states"""
    PRISTINE = "pristine"
    HEALTHY = "healthy"
    SUSPICIOUS = "suspicious"
    COMPROMISED = "compromised"
    QUARANTINE = "quarantine"


class DataOptimizationLevel(Enum):
    """Data usage optimization levels"""
    MINIMAL = "minimal"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    EXTREME = "extreme"


class ProfileQuality(Enum):
    """Profile quality tiers"""
    TIER_5 = 5  # Ultra Elite
    TIER_4 = 4  # Elite
    TIER_3 = 3  # Premium
    TIER_2 = 2  # Standard
    TIER_1 = 1  # Basic