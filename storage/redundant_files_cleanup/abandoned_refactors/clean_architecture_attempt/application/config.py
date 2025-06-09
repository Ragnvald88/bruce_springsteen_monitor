# Application Configuration
"""
Central configuration for the application layer.
Loads and validates configuration from various sources.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class MonitoringTarget:
    """Configuration for a monitoring target"""
    event_name: str
    url: str
    platform: str
    priority: str = "normal"
    check_interval: int = 60
    enabled: bool = True


@dataclass
class ApplicationConfig:
    """Main application configuration"""
    # Mode settings
    mode: str = "adaptive"
    dry_run: bool = False
    
    # Browser settings
    headless: bool = True
    browser_type: str = "chromium"
    
    # Monitoring settings
    targets: List[MonitoringTarget] = field(default_factory=list)
    max_concurrent_monitors: int = 10
    max_concurrent_strikes: int = 3
    
    # Profile settings
    num_profiles: int = 15
    profiles_per_platform: int = 3
    
    # Network settings
    data_limit_mb: float = 1000.0
    request_timeout: int = 30
    
    # Authentication
    fansale_email: Optional[str] = None
    fansale_password: Optional[str] = None
    
    # Proxy settings
    proxies: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_yaml(cls, config_path: str) -> 'ApplicationConfig':
        """Load configuration from YAML file"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Create instance
        config = cls()
        
        # Load settings
        if 'settings' in data:
            settings = data['settings']
            config.mode = settings.get('mode', config.mode)
            config.dry_run = settings.get('dry_run', config.dry_run)
            config.headless = settings.get('headless', config.headless)
            config.browser_type = settings.get('browser', config.browser_type)
        
        # Load strike settings
        if 'strike_settings' in data:
            strike = data['strike_settings']
            config.max_concurrent_strikes = strike.get('max_parallel', config.max_concurrent_strikes)
            config.request_timeout = strike.get('timeout', config.request_timeout)
        
        # Load targets
        if 'targets' in data:
            config.targets = [
                MonitoringTarget(**target) for target in data['targets']
            ]
        
        # Load authentication from environment
        config.fansale_email = os.getenv('FANSALE_EMAIL')
        config.fansale_password = os.getenv('FANSALE_PASSWORD')
        
        # Load proxies
        if 'profile_manager' in data and 'proxies' in data['profile_manager']:
            config.proxies = data['profile_manager']['proxies']
        
        # Load profile settings
        if 'profile_manager' in data:
            pm = data['profile_manager']
            config.num_profiles = pm.get('num_target_profiles', config.num_profiles)
            config.profiles_per_platform = pm.get('profiles_per_platform', config.profiles_per_platform)
        
        # Load data limits
        if 'data_usage' in data:
            config.data_limit_mb = data['data_usage'].get('global_limit_mb', config.data_limit_mb)
        
        return config
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Check targets
        if not self.targets:
            errors.append("No monitoring targets configured")
        
        # Check authentication
        if not self.fansale_email or not self.fansale_password:
            errors.append("FanSale credentials not configured (set FANSALE_EMAIL and FANSALE_PASSWORD)")
        
        # Check proxies
        if not self.proxies:
            errors.append("No proxies configured")
        
        return errors