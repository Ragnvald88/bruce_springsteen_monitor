# Domain Entities - Core business objects with no external dependencies
"""
Domain entities represent the core business concepts of the ticket monitoring system.
These are pure Python objects with no framework or infrastructure dependencies.
"""

from .platform import Platform, PlatformType
from .profile import BrowserProfile, ProfileQuality, ProfileState
from .ticket import Ticket, TicketOpportunity, PriorityLevel
from .proxy import ProxyConfig

__all__ = [
    'Platform', 'PlatformType',
    'BrowserProfile', 'ProfileQuality', 'ProfileState',
    'Ticket', 'TicketOpportunity', 'PriorityLevel',
    'ProxyConfig'
]