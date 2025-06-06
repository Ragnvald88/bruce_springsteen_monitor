# src/profiles/__init__.py
"""Browser profile management system."""

from .consolidated_models import (
    BrowserProfile, ProxyConfig, BrowserConfig,
    ProfileQuality, DataOptimizationLevel, Platform,
    SessionData, ProfileMetrics,
    create_optimized_profile, create_profiles_batch
)
from .manager import ProfileManager
from .utils import create_profile_manager_from_config

__all__ = [
    # Manager
    'ProfileManager',
    'create_profile_manager_from_config',
    
    # Models
    'BrowserProfile',
    'ProxyConfig',
    'BrowserConfig',
    
    # Enums
    'Platform',
    'ProfileQuality',
    'DataOptimizationLevel',
    
    # Types
    'SessionData',
    'ProfileMetrics',
    
    # Factories
    'create_optimized_profile',
    'create_profiles_batch',
]