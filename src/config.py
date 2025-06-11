# stealthmaster/config.py
"""Configuration models using Pydantic for type safety and validation."""

import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AppMode(str, Enum):
    """Application running modes."""
    STEALTH = "stealth"
    BEAST = "beast"
    ULTRA_STEALTH = "ultra_stealth"
    ADAPTIVE = "adaptive"
    HYBRID = "hybrid"


class Platform(str, Enum):
    """Supported ticketing platforms."""
    FANSALE = "fansale"
    TICKETMASTER = "ticketmaster"
    VIVATICKET = "vivaticket"


class ProxyType(str, Enum):
    """Proxy protocol types."""
    HTTP = "http"
    HTTPS = "https"
    SOCKS5 = "socks5"


class ProxyRotationStrategy(str, Enum):
    """Proxy rotation strategies."""
    INTELLIGENT = "intelligent"
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    STICKY = "sticky"


class MonitoringLevel(str, Enum):
    """Detection monitoring levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PARANOID = "paranoid"


# Sub-configuration models

class ModeConfig(BaseModel):
    """Mode-specific configuration."""
    max_concurrent_monitors: int = Field(ge=1, le=10)
    max_concurrent_strikes: int = Field(ge=1, le=10)
    max_connections: int = Field(ge=10, le=200)
    cache_size: int = Field(ge=100, le=5000)
    profile_rotation_interval: Optional[int] = Field(None, ge=60)
    min_quality_tier: Optional[int] = Field(None, ge=1, le=5)


class AppSettings(BaseModel):
    """Application settings."""
    mode: AppMode = AppMode.ADAPTIVE
    version: str = "2.0.0"
    dry_run: bool = False
    browser_open_mode: str = Field(default="both", pattern="^(default|automated|both)$")
    mode_configs: Dict[str, ModeConfig]


class MonitoringSettings(BaseModel):
    """Monitoring configuration."""
    default_interval_s: int = Field(default=30, ge=3)
    min_monitor_interval_s: int = Field(default=3, ge=1)
    cache_max_age_s: int = Field(default=300, ge=60)
    
    class QuantumOptimization(BaseModel):
        enabled: bool = True
        pattern_analysis_interval: int = 60
        resource_reallocation: bool = True
        predictive_burst_mode: bool = True
    
    quantum_optimization: QuantumOptimization = Field(default_factory=QuantumOptimization)


class BrowserOptions(BaseModel):
    """Browser configuration options."""
    headless: bool = True
    channel: str = Field(default="chrome", pattern="^(chrome|chromium|firefox|webkit)$")
    
    class StealthOptions(BaseModel):
        viewport_randomization: bool = True
        timezone_spoofing: bool = True
        webgl_noise: bool = True
        canvas_fingerprint_defender: bool = True
        audio_context_noise: bool = True
        font_fingerprint_defender: bool = True
    
    class CDPEvasion(BaseModel):
        enabled: bool = True
        runtime_enable_bypass: bool = True
        console_hook_bypass: bool = True
        error_stack_cleaning: bool = True
    
    stealth_options: StealthOptions = Field(default_factory=StealthOptions)
    cdp_evasion: CDPEvasion = Field(default_factory=CDPEvasion)


class StrikeSettings(BaseModel):
    """Strike force configuration."""
    coordination_strategy: str = Field(default="quantum", pattern="^(quantum|parallel|sequential)$")
    profile_selection: str = Field(default="ml_optimized", pattern="^(ml_optimized|round_robin|random)$")
    
    class TimeoutConfigs(BaseModel):
        navigation: int = Field(default=30000, ge=10000)
        strike_execution: int = Field(default=45000, ge=30000)
        queue_wait: int = Field(default=300000, ge=60000)
    
    timeout_configs: TimeoutConfigs = Field(default_factory=TimeoutConfigs)
    success_indicators: List[str] = Field(default_factory=lambda: [
        "reservation successful",
        "added to cart",
        "order confirmed",
        "pagamento",
        "conferma"
    ])


class PlatformAuth(BaseModel):
    """Platform authentication credentials."""
    username: str
    password: str
    
    @field_validator("username", "password")
    @classmethod
    def resolve_env_vars(cls, v):
        """Resolve environment variables."""
        if v.startswith("${") and v.endswith("}"):
            env_var = v[2:-1]
            env_value = os.getenv(env_var)
            if env_value is None:
                raise ValueError(f"Environment variable {env_var} is not set")
            return env_value
        return v


class Authentication(BaseModel):
    """Authentication configuration."""
    enabled: bool = True
    platforms: Dict[str, PlatformAuth] = Field(default_factory=dict)


class ProxyConfig(BaseModel):
    """Individual proxy configuration."""
    host: str
    port: Union[int, str]
    username: Optional[str] = None
    password: Optional[str] = None
    type: ProxyType = ProxyType.HTTP
    country: str = "IT"
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0)
    provider: Optional[str] = None
    
    @field_validator("host", "username", "password")
    @classmethod
    def resolve_env_vars(cls, v):
        """Resolve environment variables."""
        if v and v.startswith("${") and v.endswith("}"):
            env_var = v[2:-1]
            env_value = os.getenv(env_var)
            if env_value is None:
                # For optional fields like proxy username/password, return None
                if env_var.lower().endswith(("_username", "_password")):
                    return None
                raise ValueError(f"Environment variable {env_var} is not set")
            return env_value
        return v
    
    @field_validator("port")
    @classmethod
    def resolve_port_env(cls, v):
        """Resolve port from environment if needed."""
        if isinstance(v, str) and v.startswith("${"):
            env_var = v[2:-1]
            env_value = os.getenv(env_var)
            if env_value is None:
                raise ValueError(f"Environment variable {env_var} is not set")
            return int(env_value)
        return v


class ProxyRotationRules(BaseModel):
    """Proxy rotation rules."""
    rotate_on_block: bool = True
    rotate_interval_minutes: int = Field(default=30, ge=5)
    max_requests_per_proxy: int = Field(default=100, ge=10)
    cooldown_after_block_minutes: int = Field(default=120, ge=30)


class ProxyValidation(BaseModel):
    """Proxy validation settings."""
    test_url: HttpUrl = "https://httpbin.org/ip"
    timeout_seconds: int = Field(default=10, ge=5)
    validate_on_start: bool = True
    revalidate_interval_hours: int = Field(default=6, ge=1)


class ProxySettings(BaseModel):
    """Complete proxy configuration."""
    enabled: bool = True
    rotation_strategy: ProxyRotationStrategy = ProxyRotationStrategy.INTELLIGENT
    primary_pool: List[ProxyConfig] = Field(default_factory=list)
    backup_pool: List[ProxyConfig] = Field(default_factory=list)
    rotation_rules: ProxyRotationRules = Field(default_factory=ProxyRotationRules)
    platform_preferences: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    validation: ProxyValidation = Field(default_factory=ProxyValidation)


class ProfileSettings(BaseModel):
    """Profile management settings."""
    profile_count: int = Field(default=50, ge=1, le=500)
    rotation_strategy: str = "performance_based"
    
    class ProxyBinding(BaseModel):
        enabled: bool = True
        sticky_sessions: bool = True
        rotation_sync: bool = True
    
    class QualityDistribution(BaseModel):
        premium: int = 10
        high: int = 15
        medium: int = 15
        standard: int = 10
    
    class FingerprintMutation(BaseModel):
        enabled: bool = True
        mutation_interval: int = 3600
        mutation_factor: float = 0.15
    
    proxy_binding: ProxyBinding = Field(default_factory=ProxyBinding)
    quality_distribution: QualityDistribution = Field(default_factory=QualityDistribution)
    fingerprint_mutation: FingerprintMutation = Field(default_factory=FingerprintMutation)


class DataLimits(BaseModel):
    """Data usage limits and optimization."""
    global_limit_mb: int = Field(default=10000, ge=100)
    session_limit_mb: int = Field(default=2000, ge=100)
    
    class OptimizationThresholds(BaseModel):
        aggressive_trigger_percent: int = Field(default=70, ge=50, le=90)
        emergency_trigger_percent: int = Field(default=90, ge=80, le=95)
    
    class ResourceBlocking(BaseModel):
        images: bool = True
        media: bool = True
        fonts: bool = True
        trackers: bool = True
        analytics: bool = True
    
    optimization_thresholds: OptimizationThresholds = Field(default_factory=OptimizationThresholds)
    resource_blocking: ResourceBlocking = Field(default_factory=ResourceBlocking)


class BurstMode(BaseModel):
    """Burst mode configuration for targets."""
    enabled: bool = True
    min_interval_s: int = Field(default=3, ge=1)
    duration_s: int = Field(default=300, ge=60)
    trigger_on_activity: bool = True


class QueueConfig(BaseModel):
    """Queue handling configuration."""
    auto_join: bool = True
    maintain_presence: bool = True
    multi_tab_protection: bool = False


class Target(BaseModel):
    """Ticketing target configuration."""
    platform: Platform
    event_name: str
    url: HttpUrl
    enabled: bool = True
    priority: str = Field(default="NORMAL", pattern="^(LOW|NORMAL|HIGH|CRITICAL)$")
    interval_s: int = Field(default=30, ge=5)
    
    # Ticket preferences
    desired_sections: List[str] = Field(default_factory=list)
    max_price_per_ticket: float = Field(gt=0)
    min_ticket_quantity: int = Field(default=1, ge=1)
    max_ticket_quantity: int = Field(default=4, ge=1, le=10)
    fair_deal_only: bool = False
    certified_only: bool = False
    
    # Advanced configs
    burst_mode: Optional[BurstMode] = None
    queue_config: Optional[QueueConfig] = None
    
    @field_validator("max_ticket_quantity")
    @classmethod
    def validate_quantity_range(cls, v, info):
        """Ensure max >= min quantity."""
        if "min_ticket_quantity" in info.data and v < info.data["min_ticket_quantity"]:
            raise ValueError("max_ticket_quantity must be >= min_ticket_quantity")
        return v


class AntiDetection(BaseModel):
    """Anti-detection measures configuration."""
    
    class HumanSimulation(BaseModel):
        mouse_movements: bool = True
        keyboard_typing: bool = True
        scroll_patterns: bool = True
        reading_delays: bool = True
        micro_movements: bool = True
    
    class RequestPatterns(BaseModel):
        randomize_intervals: bool = True
        vary_user_agents: bool = True
        rotate_headers: bool = True
    
    class BlockRecovery(BaseModel):
        profile_rotation: bool = True
        cooldown_multiplier: float = Field(default=2.0, ge=1.0)
        max_retries: int = Field(default=3, ge=1)
    
    human_simulation: HumanSimulation = Field(default_factory=HumanSimulation)
    request_patterns: RequestPatterns = Field(default_factory=RequestPatterns)
    block_recovery: BlockRecovery = Field(default_factory=BlockRecovery)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_directory: Path = Field(default=Path("logs"))
    main_log_file: str = "stealthmaster.log"
    error_log_file: str = "errors.log"
    
    class PerformanceLogging(BaseModel):
        enabled: bool = True
        log_file: str = "performance.log"
    
    class DetectionLogging(BaseModel):
        enabled: bool = True
        log_file: str = "detection_events.log"
    
    class TicketLogging(BaseModel):
        enabled: bool = True
        log_file: str = "ticket_opportunities.log"
    
    performance_logging: PerformanceLogging = Field(default_factory=PerformanceLogging)
    detection_logging: DetectionLogging = Field(default_factory=DetectionLogging)
    ticket_logging: TicketLogging = Field(default_factory=TicketLogging)


class AdvancedFeatures(BaseModel):
    """Advanced feature toggles."""
    
    class MLOptimization(BaseModel):
        enabled: bool = True
        model_update_interval: int = 3600
        feature_extraction: bool = True
    
    class QuantumCoordination(BaseModel):
        enabled: bool = True
        entanglement_factor: float = Field(default=0.8, ge=0.0, le=1.0)
        superposition_states: int = Field(default=3, ge=1, le=5)
    
    class PredictiveAnalytics(BaseModel):
        enabled: bool = True
        pattern_recognition: bool = True
        demand_forecasting: bool = True
    
    class EmergencyProtocols(BaseModel):
        auto_switch_ultra_stealth: bool = False
        threat_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
        emergency_cooldown: int = Field(default=600, ge=60)
    
    ml_optimization: MLOptimization = Field(default_factory=MLOptimization)
    quantum_coordination: QuantumCoordination = Field(default_factory=QuantumCoordination)
    predictive_analytics: PredictiveAnalytics = Field(default_factory=PredictiveAnalytics)
    emergency_protocols: EmergencyProtocols = Field(default_factory=EmergencyProtocols)


class CaptchaSettings(BaseModel):
    """Captcha solving configuration."""
    enabled: bool = True
    service: str = Field(default="2captcha", pattern="^(2captcha|anticaptcha|capsolver)$")
    api_key: str = ""
    timeout: int = Field(default=120, ge=30, le=300)
    max_retries: int = Field(default=3, ge=1, le=10)
    
    @field_validator("api_key")
    @classmethod
    def resolve_env_vars(cls, v):
        """Resolve environment variables."""
        if v.startswith("${") and v.endswith("}"):
            env_var = v[2:-1]
            env_value = os.getenv(env_var)
            if env_value is None:
                # Return empty string if not set, captcha will be disabled
                return ""
            return env_value
        return v


class Settings(BaseModel):
    """Main application settings."""
    # Core settings
    app_settings: AppSettings
    monitoring_settings: MonitoringSettings
    browser_options: BrowserOptions
    strike_settings: StrikeSettings
    
    # Authentication & Network
    authentication: Authentication
    proxy_settings: ProxySettings
    captcha_settings: Optional[CaptchaSettings] = None
    
    # Profile & Data
    profile_settings: ProfileSettings
    data_limits: DataLimits
    
    # Targets
    targets: List[Target]
    
    # Security & Features
    anti_detection: AntiDetection
    logging: LoggingConfig
    advanced_features: AdvancedFeatures
    
    # Paths
    data_dir: Path = Field(default=Path("./data"))
    logs_dir: Path = Field(default=Path("./logs"))
    screenshots_dir: Path = Field(default=Path("./screenshots"))
    
    @field_validator("data_dir", "logs_dir", "screenshots_dir")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @model_validator(mode='after')
    def validate_mode_configs(self):
        """Ensure all modes have configs."""
        if self.app_settings:
            required_modes = ["ultra_stealth", "stealth", "adaptive", "hybrid", "beast"]
            for mode in required_modes:
                if mode not in self.app_settings.mode_configs:
                    raise ValueError(f"Missing configuration for mode: {mode}")
        return self
    
    model_config = {
        "use_enum_values": True,
        "validate_assignment": True
    }


def load_settings(config_path: Optional[Path] = None) -> Settings:
    """
    Load settings from YAML file or create defaults.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Settings object
    """
    if config_path and config_path.exists():
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
        
        # Convert nested configs to proper format
        if "targets" in data:
            for target in data["targets"]:
                # Ensure URL is string
                if "url" in target:
                    target["url"] = str(target["url"])
        
        return Settings(**data)
    
    # Return minimal defaults if no config
    return Settings(
        app_settings=AppSettings(
            mode_configs={
                "ultra_stealth": ModeConfig(max_concurrent_monitors=1, max_concurrent_strikes=1),
                "stealth": ModeConfig(max_concurrent_monitors=2, max_concurrent_strikes=2),
                "adaptive": ModeConfig(max_concurrent_monitors=3, max_concurrent_strikes=3),
                "hybrid": ModeConfig(max_concurrent_monitors=4, max_concurrent_strikes=4),
                "beast": ModeConfig(max_concurrent_monitors=8, max_concurrent_strikes=10),
            }
        ),
        monitoring_settings=MonitoringSettings(),
        browser_options=BrowserOptions(),
        strike_settings=StrikeSettings(),
        authentication=Authentication(),
        proxy_settings=ProxySettings(),
        profile_settings=ProfileSettings(),
        data_limits=DataLimits(),
        targets=[],
        anti_detection=AntiDetection(),
        logging=LoggingConfig(),
        advanced_features=AdvancedFeatures(),
    )