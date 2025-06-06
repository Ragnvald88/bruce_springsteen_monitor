# src/core/browser_profiles.py v1.0 - Enhanced for Ticket Bot Excellence
from __future__ import annotations
import asyncio
import dataclasses
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union, Tuple, Callable, Set, TypedDict
import random
import uuid
import logging
import json
import re
from datetime import datetime, timedelta
import hashlib
import copy
from enum import Enum
from pathlib import Path
import numpy as np
from collections import defaultdict
import yaml
import aiofiles
import base64
from cryptography.fernet import Fernet
import pickle
import zstandard as zstd
from playwright.async_api import BrowserContext, Cookie

# --- Imports from advanced_profile_system ---
try:
    from .advanced_profile_system import (
        DynamicProfile,
        MutationStrategy,
        ProfileState,
        DetectionEvent,
        FingerprintComponent,
        BehavioralModel
    )
except ImportError:
    from advanced_profile_system import (
        DynamicProfile,
        MutationStrategy,
        ProfileState,
        DetectionEvent,
        FingerprintComponent,
        BehavioralModel
    )

logger = logging.getLogger(__name__)

# ==============================================================================
# DEPRECATION NOTICE: Classes moved to unified profiles/ module
# ==============================================================================
# Import all classes from the unified profiles module to maintain compatibility
try:
    from ..profiles.enums import ProfileQuality, DataOptimizationLevel, Platform
    from ..profiles.types import SessionData
    from ..profiles.models import ProxyConfig, BrowserProfile
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from profiles.enums import ProfileQuality, DataOptimizationLevel, Platform
    from profiles.types import SessionData
    from profiles.models import ProxyConfig, BrowserProfile

# Skip to ProfileScoringConfig - BrowserProfile is imported from profiles.models

# --- Profile Scoring Configuration ---
    """Enhanced scoring configuration for profile selection"""
    base_score: float = 100.0
    
    # State-based modifiers
    state_modifiers: Dict[ProfileState, float] = field(default_factory=lambda: {
        ProfileState.PRISTINE: 20.0,
        ProfileState.HEALTHY: 30.0,
        ProfileState.SUSPICIOUS: -40.0,
        ProfileState.DORMANT: -20.0,
        ProfileState.COMPROMISED: -1000.0,
        ProfileState.EVOLVING: -500.0
    })
    
    # Platform-specific bonuses
    platform_bonuses: Dict[str, float] = field(default_factory=lambda: {
        'fansale': 10.0,      # Bonus for profiles successful on each platform
        'ticketmaster': 15.0,  # Ticketmaster is harder, so bigger bonus
        'vivaticket': 12.0
    })
    
    # Session-based scoring
    has_valid_session_bonus: float = 50.0  # Major bonus for having logged-in session
    session_age_penalty_per_hour: float = 0.5  # Penalty for old sessions
    
    # Performance metrics
    success_rate_weight: float = 40.0
    avg_response_time_weight: float = 20.0  # Faster is better
    consecutive_failure_penalty: float = 10.0
    
    # Risk assessment
    avg_risk_score_penalty_weight: float = 25.0
    drift_penalty: float = 50.0
    proxy_rotation_bonus: float = 15.0  # Bonus for fresh proxy
    
    # Time-based factors
    recency_bonus_max: float = 25.0
    recency_threshold_hours: float = 12.0
    peak_time_bonus: float = 20.0  # Bonus during ticket release times

# ==============================================================================
# IMPORTANT: ProfileManager and ProfileManagerConfig have been moved to:
# - src/profiles/manager.py (ProfileManager)
# - src/profiles/config.py (ProfileManagerConfig)
# This eliminates code duplication and ensures single source of truth.
# ==============================================================================

# Import the unified ProfileManager for backward compatibility
try:
    from ..profiles.manager import ProfileManager
    from ..profiles.config import ProfileManagerConfig
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from profiles.manager import ProfileManager
    from profiles.config import ProfileManagerConfig

__all__ = [
    'ProfileQuality', 'DataOptimizationLevel', 'Platform', 'SessionData',
    'ProxyConfig', 'BrowserProfile', 'ProfileScoringConfig',
    'ProfileManager', 'ProfileManagerConfig'
]
