# src/profiles/config.py
"""Configuration classes for profile management."""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

# Imports from other modules in your project structure
from src.core.advanced_profile_system import ProfileState, DetectionEvent
from .models import ProxyConfig # For type hinting List[ProxyConfig]
from .enums import ProfileQuality # For type hinting quality_multipliers

@dataclass
class ProfileScoringConfig:
    """Enhanced scoring configuration for profile selection."""
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
        'fansale': 10.0,
        'ticketmaster': 15.0,
        'vivaticket': 12.0
    })
    
    # Session-based scoring
    has_valid_session_bonus: float = 50.0
    session_age_penalty_per_hour: float = 0.5
    
    # Performance metrics
    success_rate_weight: float = 40.0
    avg_response_time_weight: float = 20.0
    consecutive_failure_penalty: float = 10.0
    captcha_penalty: float = 30.0 # Used by ProfileScorer, sourced from utils.py
    
    # Risk assessment
    avg_risk_score_penalty_weight: float = 25.0
    drift_penalty: float = 50.0
    
    # Time-based factors
    recency_bonus_max: float = 25.0
    recency_threshold_hours: float = 12.0 # Time in hours
    peak_time_bonus: float = 20.0

    # Quality multipliers (mapping ProfileQuality enum names to float multipliers)
    quality_multipliers: Dict[str, float] = field(default_factory=lambda: {
        ProfileQuality.LOW.name: 0.5,
        ProfileQuality.MEDIUM.name: 0.8,
        ProfileQuality.HIGH.name: 1.0,
        ProfileQuality.PREMIUM.name: 1.2
    })

    # Advanced scoring from utils.py's parse_scoring_config
    proxy_rotation_bonus: float = 15.0
    tls_diversity_bonus: float = 10.0
    proxy_quality_bonus: float = 20.0
    min_unique_tls_fingerprints: int = 3


@dataclass
class ProfileManagerConfig:
    """Configuration for ProfileManager with session management."""
    # Pool settings
    num_target_profiles: int = 20
    profiles_per_platform: int = 5
    
    # Evolution settings
    evolution_interval_seconds: int = 900
    evolution_max_retries: int = 3
    evolution_retry_backoff_base_seconds: int = 60
    evolution_interval_jitter_factor: float = 0.2
    
    # Persistence settings
    persistence_filepath: str = "profiles_backup.json"
    session_backup_dir: str = "session_backups"
    enable_encrypted_storage: bool = True
    
    # Session settings
    session_validation_interval_seconds: int = 1800
    max_session_age_hours: int = 24
    auto_login_retry_limit: int = 3
    
    # Pool management
    compromise_threshold_pct: float = 0.20
    min_pool_size_for_replacement: int = 10
    max_pool_size_multiplier: float = 1.5
    
    # Proxy settings
    proxy_failure_threshold: int = 5
    proxy_configs: List[ProxyConfig] = field(default_factory=list)
    
    # Feature flags
    enable_tls_rotation: bool = True
    enable_behavioral_warmup: bool = True
    enable_session_preloading: bool = True
    enable_profile_cloning: bool = True
    enable_cdp_stealth: bool = True # This was in your original config.py's ProfileManagerConfig
    
    # Warmup settings
    warmup_sites: List[str] = field(default_factory=lambda: [
        "https://www.google.it",
        "https://www.repubblica.it",
        "https://www.corriere.it",
        "https://www.amazon.it"
    ])
    warmup_duration_seconds: Tuple[int, int] = field(default_factory=lambda: (60, 180))
    warmup_actions: List[str] = field(default_factory=lambda: ['scroll', 'click', 'hover', 'wait'])
    
    # Platform settings
    platform_priorities: Dict[str, float] = field(default_factory=lambda: {
        'ticketmaster': 1.0,
        'fansale': 0.8,
        'vivaticket': 0.7
    })
    platform_distribution: Dict[str, float] = field(default_factory=dict) # Populated from YAML
    
    # Metrics
    metrics_export_path: str = "metrics"
    
    # Scoring config
    scoring_config: ProfileScoringConfig = field(default_factory=ProfileScoringConfig)
    
    # Cooldowns
    cooldowns_seconds: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        DetectionEvent.HARD_BLOCK.value: (3600 * 4, 0.3),
        DetectionEvent.CAPTCHA_CHALLENGE.value: (1800, 0.3),
        DetectionEvent.RATE_LIMIT.value: (600, 0.3),
        DetectionEvent.SUCCESS.value: (30, 0.2),
        "post_mutation": (900, 0.3),
        "task_selection": (10, 0.2),
        "login_required": (300, 0.2),
    })

    # Anti-detection enhancements (These were in your original ProfileManagerConfig, keeping them)
    rotate_canvas_fingerprint: bool = True
    randomize_webgl_metadata: bool = True
    spoof_webrtc_ips: bool = True
    enable_timezone_spoofing: bool = True