# Domain Entity: Ticket
"""
Ticket and opportunity entities representing ticket listings and opportunities.
Pure domain objects with no external dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import hashlib


class PriorityLevel(Enum):
    """Priority levels for ticket opportunities"""
    CRITICAL = (1, 1.0, 0.1)  # (numeric_value, speed_multiplier, data_multiplier)
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


@dataclass
class Ticket:
    """Basic ticket information"""
    id: str
    event_name: str
    venue: str
    date: datetime
    section: str
    row: Optional[str] = None
    seat: Optional[str] = None
    price: float = 0.0
    currency: str = "EUR"
    quantity: int = 1


@dataclass
class TicketOpportunity:
    """Enhanced ticket opportunity with detection metadata"""
    # Core fields
    id: str
    platform: str  # Platform name as string
    event_name: str
    url: str
    offer_url: str
    
    # Ticket details
    section: str
    price: float
    quantity: int = 1
    
    # Metadata
    detected_at: datetime = field(default_factory=datetime.utcnow)
    priority: PriorityLevel = PriorityLevel.NORMAL
    detection_method: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Processing state
    processed: bool = False
    selected_profile_id: Optional[str] = None
    
    @property
    def fingerprint(self) -> str:
        """Generate unique fingerprint for deduplication"""
        key = f"{self.platform}:{self.event_name}:{self.section}:{self.price:.2f}"
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    @property
    def age_seconds(self) -> float:
        """Get age of opportunity in seconds"""
        return (datetime.utcnow() - self.detected_at).total_seconds()
    
    @property
    def is_fresh(self) -> bool:
        """Check if opportunity is still fresh (< 5 minutes old)"""
        return self.age_seconds < 300
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'platform': self.platform,
            'event_name': self.event_name,
            'url': self.url,
            'offer_url': self.offer_url,
            'section': self.section,
            'price': self.price,
            'quantity': self.quantity,
            'detected_at': self.detected_at.isoformat(),
            'priority': self.priority.name,
            'detection_method': self.detection_method,
            'metadata': self.metadata,
            'processed': self.processed,
            'selected_profile_id': self.selected_profile_id,
            'fingerprint': self.fingerprint
        }