# src/profiles/__init__.py
"""Browser profile management system."""

from .config import ProfileManagerConfig, ProfileScoringConfig
from .enums import Platform, ProfileQuality, DataOptimizationLevel
from .manager import ProfileManager
from .models import BrowserProfile, ProxyConfig
from .types import SessionData, ProfileMetrics

__all__ = [
    # Manager
    'ProfileManager',
    
    # Configuration
    'ProfileManagerConfig',
    'ProfileScoringConfig',
    
    # Models
    'BrowserProfile',
    'ProxyConfig',
    
    # Enums
    'Platform',
    'ProfileQuality',
    'DataOptimizationLevel',
    
    # Types
    'SessionData',
    'ProfileMetrics',
]