# src/core/enums.py
from enum import Enum, auto

class OperationMode(Enum):
    """System operation modes"""
    STEALTH = "stealth"
    BEAST = "beast"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"
    ULTRA_STEALTH = "ultra_stealth"

class PlatformType(Enum):
    """Supported ticketing platforms"""
    FANSALE = "fansale"
    TICKETMASTER = "ticketmaster"
    VIVATICKET = "vivaticket"

class PriorityLevel(Enum):
    """Priority levels with multipliers"""
    CRITICAL = (1, 1.0, 0.1)
    HIGH = (2, 0.8, 0.3)
    NORMAL = (3, 0.6, 0.5)
    LOW = (4, 0.4, 0.8)
    
    @property
    def numeric_value(self):
        return self.value[0]
    
    @property
    def speed_multiplier(self):
        return self.value[1]
    
    @property
    def data_multiplier(self):
        return self.value[2]

class DetectionStatus(Enum):
    """Detection states"""
    MONITORING = auto()
    DETECTED = auto()
    VERIFIED = auto()
    ATTEMPTING = auto()
    SUCCESS = auto()
    FAILED = auto()
    BLOCKED = auto()
    RATE_LIMITED = auto()
