"""Utility functions for profile management"""

import yaml
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from collections import defaultdict

from .consolidated_models import Platform, ProfileQuality, ProxyConfig
from .manager import ProfileManager
from dataclasses import dataclass, field
from ..core.advanced_profile_system import ProfileState

logger = logging.getLogger(__name__)


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
    captcha_penalty: float = 30.0
    
    # Risk assessment
    avg_risk_score_penalty_weight: float = 25.0
    drift_penalty: float = 50.0
    
    # Time-based factors
    recency_bonus_max: float = 25.0
    recency_threshold_hours: float = 12.0
    peak_time_bonus: float = 20.0
    proxy_rotation_bonus: float = 10.0
    
    # Quality multipliers  
    quality_multipliers: Dict[ProfileQuality, float] = field(default_factory=lambda: {
        ProfileQuality.PREMIUM: 2.0,
        ProfileQuality.HIGH: 1.5,
        ProfileQuality.MEDIUM: 1.0,
        ProfileQuality.LOW: 0.5
    })
    
    # Cooldown periods
    cooldown_periods: Dict[str, int] = field(default_factory=lambda: {
        'failure': 300,
        'captcha': 600,
        'success': 60
    })

def parse_proxy_configs(proxy_data: List[Dict[str, Any]]) -> List[ProxyConfig]:
    """Parse list of ProxyConfig from data, resolving environment variables."""
    configs = []
    if not proxy_data:
        logger.warning("No proxy data provided to parse_proxy_configs.")
        return configs

    logger.info(f"Attempting to parse {len(proxy_data)} proxy entries.")
    for i, proxy_dict in enumerate(proxy_data):
        try:
            logger.debug(f"Raw proxy entry #{i+1} from YAML: {proxy_dict}")

            raw_host = proxy_dict.get('host', '')
            raw_port = str(proxy_dict.get('port', '0')) 
            raw_username = proxy_dict.get('username', '')
            raw_password = proxy_dict.get('password', '')

            host_str = os.path.expandvars(raw_host)
            port_str = os.path.expandvars(raw_port)
            username_str = os.path.expandvars(raw_username)
            password_str = os.path.expandvars(raw_password)
            
            logger.debug(f"Expanded proxy entry #{i+1}: host='{host_str}', port='{port_str}', user='{username_str}'")

            parsed_port = int(port_str) if port_str.isdigit() else 0

            if not host_str or parsed_port <= 0:
                logger.warning(f"Skipping proxy entry #{i+1} due to missing/invalid host ('{host_str}') or port ({parsed_port}) after expansion.")
                continue
            
            config_instance = ProxyConfig(
                proxy_type=proxy_dict.get('type', 'http'),
                host=host_str,
                port=parsed_port,
                username=username_str if username_str else None,
                password=password_str if password_str else None,
                rotation_endpoint=proxy_dict.get('rotation_endpoint'),
                sticky_session=proxy_dict.get('sticky_session', True),
                country_code=proxy_dict.get('country_code'),
                proxy_provider=proxy_dict.get('provider')  # Corrected: maps 'provider' from YAML
            )
            configs.append(config_instance)
            logger.info(f"Successfully parsed proxy: {config_instance.host}:{config_instance.port}, Provider: {config_instance.proxy_provider}")
            
        except TypeError as te:
            logger.error(f"TypeError during ProxyConfig instantiation for entry: {proxy_dict}. Error: {te}. Ensure ProxyConfig fields match arguments.", exc_info=True)
        except Exception as e:
            logger.error(f"Failed to parse proxy config entry: {proxy_dict}. Error: {e}", exc_info=True)
    
    if not configs:
        logger.warning("Proxy parsing finished, but no valid proxy configurations were loaded.")
    else:
        logger.info(f"Successfully loaded {len(configs)} proxy configurations.")
    return configs


def parse_profile_manager_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse ProfileManagerConfig from dict"""
    pm_settings = config_data.get('profile_manager', {})

    # Create scoring config
    scoring_config = parse_scoring_config(pm_settings.get('scoring', {}))

    # Parse proxy configs
    # Corrected line: Read 'proxies' from pm_settings (the 'profile_manager' section)
    pm_settings = config_data.get('profile_manager', {})
    proxy_configs = parse_proxy_configs(pm_settings.get('proxies', []))

    # Create main config
    config = {
        # Pool settings
        'num_target_profiles': pm_settings.get('num_target_profiles', 20),
        'profiles_per_platform': pm_settings.get('profiles_per_platform', 5),

        # Evolution settings
        'evolution_interval_seconds': pm_settings.get('evolution_interval_seconds', 900),
        'evolution_max_retries': pm_settings.get('evolution_max_retries', 3),
        'evolution_retry_backoff_base_seconds': pm_settings.get('evolution_retry_backoff_base_seconds', 60),
        'evolution_interval_jitter_factor': pm_settings.get('evolution_interval_jitter_factor', 0.2),

        # Persistence settings
        'persistence_filepath': pm_settings.get('persistence_filepath', 'storage/browser_profiles.yaml'),
        'session_backup_dir': pm_settings.get('session_backup_dir', 'session_backups'),
        'enable_encrypted_storage': bool(pm_settings.get('enable_encrypted_storage', False)),

        # Session settings
        'session_validation_interval_seconds': pm_settings.get('session_validation_interval_seconds', 1800),
        'max_session_age_hours': pm_settings.get('max_session_age_hours', 24),
        'auto_login_retry_limit': pm_settings.get('auto_login_retry_limit', 3),

        # Pool management
        'compromise_threshold_pct': pm_settings.get('compromise_threshold_pct', 0.20),
        'min_pool_size_for_replacement': pm_settings.get('min_pool_size_for_replacement', 10),
        'max_pool_size_multiplier': pm_settings.get('max_pool_size_multiplier', 1.5),

        # Proxy settings
        'proxy_failure_threshold': pm_settings.get('proxy_failure_threshold', 5),
        'proxy_configs': proxy_configs,

        # Feature flags
        'enable_tls_rotation': pm_settings.get('enable_tls_rotation', True),
        'enable_behavioral_warmup': pm_settings.get('enable_behavioral_warmup', True),
        'enable_session_preloading': pm_settings.get('enable_session_preloading', True),
        'enable_profile_cloning': pm_settings.get('enable_profile_cloning', True),

        # Warmup settings
        'warmup_sites': pm_settings.get('warmup_sites', [
            "https://www.google.it",
            "https://www.repubblica.it",
            "https://www.corriere.it",
            "https://www.amazon.it"
        ]),
        'warmup_duration_seconds': pm_settings.get('warmup_duration_seconds', (60, 180)),
        'warmup_actions': pm_settings.get('warmup_actions', ['scroll', 'click', 'hover', 'wait']),

        # Platform settings
        'platform_priorities': pm_settings.get('platform_priorities', {
            'ticketmaster': 1.0,
            'fansale': 0.8,
            'vivaticket': 0.7
        }),
        'platform_distribution': pm_settings.get('platform_distribution', {
            'ticketmaster': 0.4,
            'fansale': 0.3,
            'vivaticket': 0.3
        }),

        # Metrics
        'metrics_export_path': pm_settings.get('metrics_export_path', 'metrics'),

        # Scoring config
        'scoring_config': scoring_config,

        # Cooldowns
        'cooldowns_seconds': parse_cooldowns(pm_settings.get('cooldowns_seconds', {}))
    }

    return config


def parse_scoring_config(scoring_data: Dict[str, Any]) -> ProfileScoringConfig:
    """Parse ProfileScoringConfig from dict"""
    config = ProfileScoringConfig()
    
    # Base score
    if 'base_score' in scoring_data:
        config.base_score = scoring_data['base_score']
    
    # State modifiers
    if 'state_modifiers' in scoring_data:
        for state, modifier in scoring_data['state_modifiers'].items():
            if state in config.state_modifiers:
                config.state_modifiers[state] = modifier
    
    # Platform bonuses
    if 'platform_bonuses' in scoring_data:
        config.platform_bonuses.update(scoring_data['platform_bonuses'])
    
    # Session scoring
    if 'session_scoring' in scoring_data:
        session = scoring_data['session_scoring']
        config.has_valid_session_bonus = session.get('valid_bonus', 50.0)
        config.session_age_penalty_per_hour = session.get('age_penalty', 0.5)
    
    # Performance metrics
    if 'performance_weights' in scoring_data:
        perf = scoring_data['performance_weights']
        config.success_rate_weight = perf.get('success_rate', 40.0)
        config.avg_response_time_weight = perf.get('response_time', 20.0)
        config.consecutive_failure_penalty = perf.get('failure_penalty', 10.0)
    
    # Risk assessment
    if 'risk_weights' in scoring_data:
        risk = scoring_data['risk_weights']
        config.avg_risk_score_penalty_weight = risk.get('avg_risk', 25.0)
        config.drift_penalty = risk.get('drift', 50.0)
    
    # Time factors
    if 'time_factors' in scoring_data:
        time = scoring_data['time_factors']
        config.recency_bonus_max = time.get('recency_bonus', 25.0)
        config.recency_threshold_hours = time.get('recency_threshold', 12.0)
        config.peak_time_bonus = time.get('peak_bonus', 20.0)
    
    # Quality multipliers
    if 'quality_multipliers' in scoring_data:
        config.quality_multipliers = scoring_data['quality_multipliers']
    
    # Advanced scoring
    if 'advanced' in scoring_data:
        adv = scoring_data['advanced']
        config.proxy_rotation_bonus = adv.get('proxy_rotation_bonus', 15.0)
        config.tls_diversity_bonus = adv.get('tls_diversity_bonus', 10.0)
        config.proxy_quality_bonus = adv.get('proxy_quality_bonus', 20.0)
        config.min_unique_tls_fingerprints = adv.get('min_unique_tls', 3)
    
    return config

def parse_cooldowns(cooldown_data: Dict[str, Any]) -> Dict[str, Tuple[float, float]]:
    """Parse cooldown configurations"""
    default_cooldowns = {
        "hard_block": (14400, 0.3),  # 4 hours
        "captcha_challenge": (1800, 0.3),  # 30 minutes
        "rate_limit": (600, 0.3),  # 10 minutes
        "success": (30, 0.2),  # 30 seconds
        "post_mutation": (900, 0.3),  # 15 minutes
        "task_selection": (10, 0.2),  # 10 seconds
        "login_required": (300, 0.2),  # 5 minutes
    }
    
    cooldowns = {}
    
    for event, default in default_cooldowns.items():
        if event in cooldown_data:
            value = cooldown_data[event]
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                cooldowns[event] = (float(value[0]), float(value[1]))
            elif isinstance(value, (int, float)):
                cooldowns[event] = (float(value), default[1])
            else:
                cooldowns[event] = default
        else:
            cooldowns[event] = default
    
    return cooldowns


def generate_config_template(output_path: str = "config_template.yaml"):
    """Generate a config template file"""
    template = {
        'profile_manager': {
            'num_profiles': 20,
            'profiles_per_platform': 5,
            'evolution_interval': 900,
            'persistence_file': 'profiles_backup.json',
            'session_backup_dir': 'session_backups',
            'encryption_key_file': '.profile_key',
            
            'enable_tls_rotation': True,
            'enable_behavioral_warmup': True,
            'enable_session_preloading': True,
            'enable_profile_cloning': True,
            
            'warmup_sites': [
                "https://www.google.it",
                "https://www.repubblica.it",
                "https://www.corriere.it",
                "https://www.amazon.it"
            ],
            
            'platform_priorities': {
                'ticketmaster': 1.0,
                'fansale': 0.8,
                'vivaticket': 0.7
            },
            
            'scoring': {
                'base_score': 100.0,
                
                'state_modifiers': {
                    'pristine': 20.0,
                    'healthy': 30.0,
                    'suspicious': -40.0,
                    'dormant': -20.0,
                    'compromised': -1000.0,
                    'evolving': -500.0
                },
                
                'platform_bonuses': {
                    'fansale': 10.0,
                    'ticketmaster': 15.0,
                    'vivaticket': 12.0
                },
                
                'session_scoring': {
                    'valid_bonus': 50.0,
                    'age_penalty': 0.5
                },
                
                'performance_weights': {
                    'success_rate': 40.0,
                    'response_time': 20.0,
                    'failure_penalty': 10.0
                },
                
                'quality_multipliers': {
                    'LOW': 0.5,
                    'MEDIUM': 0.8,
                    'HIGH': 1.0,
                    'PREMIUM': 1.2
                }
            },
            
            'cooldowns': {
                'hard_block': [14400, 0.3],
                'captcha_challenge': [1800, 0.3],
                'rate_limit': [600, 0.3],
                'success': [30, 0.2],
                'task_selection': [10, 0.2],
                'login_required': [300, 0.2]
            }
        },
        
        'proxies': [
            {
                'type': 'http',
                'host': 'proxy.example.com',
                'port': 8080,
                'username': 'user',
                'password': 'pass',
                'country_code': 'IT',
                'provider': 'example_provider',
                'sticky_session': True,
                'rotation_interval': 30
            }
        ],
        
        'base_profile_template': {
            'os_name': 'Windows',
            'browser_name': 'Chrome',
            'device_class': 'mid_range_desktop',
            'country': 'IT',
            'language': 'it-IT',
            'timezone': 'Europe/Rome'
        }
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(template, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Generated config template at {output_path}")


def validate_profile_quality(profile: Any, platform: Platform) -> ProfileQuality:
    """Validate and suggest profile quality based on characteristics"""
    score = 0
    
    # Check user agent freshness
    if hasattr(profile, 'user_agent'):
        if 'Chrome/12' in profile.user_agent:  # Latest Chrome
            score += 20
        elif 'Chrome/11' in profile.user_agent:  # Recent Chrome
            score += 10
    
    # Check viewport dimensions
    if hasattr(profile, 'viewport_width'):
        if profile.viewport_width >= 1920:
            score += 20
        elif profile.viewport_width >= 1366:
            score += 10
    
    # Check proxy quality
    if hasattr(profile, 'proxy_config') and profile.proxy_config:
        if hasattr(profile.proxy_config, 'provider'):
            premium_providers = ['luminati', 'brightdata', 'oxylabs']
            if profile.proxy_config.provider in premium_providers:
                score += 30
            else:
                score += 10
    
    # Check session availability
    if hasattr(profile, 'platform_sessions'):
        if platform.value in profile.platform_sessions:
            score += 20
    
    # Platform-specific requirements
    if platform == Platform.TICKETMASTER:
        # Ticketmaster requires higher quality
        score -= 10
    
    # Determine quality
    if score >= 80:
        return ProfileQuality.PREMIUM
    elif score >= 60:
        return ProfileQuality.HIGH
    elif score >= 40:
        return ProfileQuality.MEDIUM
    else:
        return ProfileQuality.LOW


def merge_profile_stats(profiles: List[Any]) -> Dict[str, Any]:
    """Merge statistics from multiple profiles"""
    merged_stats = {
        'total_attempts': 0,
        'total_successes': 0,
        'total_failures': 0,
        'platform_breakdown': {},
        'quality_breakdown': {},
        'avg_response_times': {},
        'detection_events': []
    }
    
    platform_stats = defaultdict(lambda: {'attempts': 0, 'successes': 0, 'failures': 0})
    quality_stats = defaultdict(lambda: {'count': 0, 'successes': 0})
    response_times = defaultdict(list)
    
    for profile in profiles:
        if not hasattr(profile, 'platform_stats'):
            continue
        
        # Aggregate platform stats
        for platform, stats in profile.platform_stats.items():
            platform_stats[platform]['attempts'] += stats.get('attempts', 0)
            platform_stats[platform]['successes'] += stats.get('successes', 0)
            platform_stats[platform]['failures'] += stats.get('failures', 0)
            
            if 'avg_response_time_ms' in stats and stats['avg_response_time_ms'] > 0:
                response_times[platform].append(stats['avg_response_time_ms'])
            
            # Collect detection events
            if 'detection_events' in stats:
                merged_stats['detection_events'].extend(stats['detection_events'])
        
        # Quality stats
        if hasattr(profile, 'quality'):
            quality_name = profile.quality.name
            quality_stats[quality_name]['count'] += 1
            
            total_successes = sum(
                s.get('successes', 0) for s in profile.platform_stats.values()
            )
            quality_stats[quality_name]['successes'] += total_successes
    
    # Calculate totals
    for platform, stats in platform_stats.items():
        merged_stats['total_attempts'] += stats['attempts']
        merged_stats['total_successes'] += stats['successes']
        merged_stats['total_failures'] += stats['failures']
    
    # Format platform breakdown
    merged_stats['platform_breakdown'] = dict(platform_stats)
    
    # Format quality breakdown
    merged_stats['quality_breakdown'] = dict(quality_stats)
    
    # Calculate average response times
    for platform, times in response_times.items():
        if times:
            merged_stats['avg_response_times'][platform] = sum(times) / len(times)
    
    # Sort detection events by timestamp
    merged_stats['detection_events'].sort(
        key=lambda x: x.get('timestamp', ''),
        reverse=True
    )
    
    # Keep only recent detection events
    merged_stats['detection_events'] = merged_stats['detection_events'][:100]
    
    return merged_stats

def create_profile_manager_from_config(
    config_path: str,
    config_overrides: Optional[Dict[str, Any]] = None # Add the new parameter with a default
) -> ProfileManager:
    """Create ProfileManager from YAML config file, applying overrides if provided."""
    config_path_obj = Path(config_path)
    if not config_path_obj.exists():
        raise FileNotFoundError(f"Config file not found: {config_path_obj}")

    with open(config_path_obj, 'r') as f:
        # This is the configuration loaded from the base YAML file (e.g., config.yaml)
        base_config_data = yaml.safe_load(f)

    # Create a working copy of the configuration data to be parsed
    final_config_for_parsing = base_config_data.copy()

    # Apply the overrides to the 'profile_manager' section
    # The 'config_overrides' argument IS the dictionary of settings for the profile_manager.
    if config_overrides is not None:
        if 'profile_manager' not in final_config_for_parsing:
            final_config_for_parsing['profile_manager'] = {}
        final_config_for_parsing['profile_manager'].update(config_overrides)
        # This will overwrite keys in base_config_data['profile_manager'] with values
        # from config_overrides, or add new keys from config_overrides.

    # Parse the (potentially modified) configuration data
    # parse_profile_manager_config expects a dictionary that contains a 'profile_manager' key,
    # and potentially 'proxies', 'base_profile_template' etc. at its top level.
    pm_config_obj = parse_profile_manager_config(final_config_for_parsing)
    base_template = final_config_for_parsing.get('base_profile_template')

    return ProfileManager(config=pm_config_obj, base_profile_template=base_template)

def export_profile_health_report(profiles: List[Any], output_path: str):
    """Export detailed health report for all profiles"""
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'total_profiles': len(profiles),
        'profiles': []
    }
    
    for profile in profiles:
        if not hasattr(profile, 'profile_id'):
            continue
        
        health_score = calculate_profile_health_score(profile)
        
        profile_data = {
            'id': profile.profile_id,
            'quality': profile.quality.name if hasattr(profile, 'quality') else 'UNKNOWN',
            'health_score': health_score,
            'last_used': profile.last_used.isoformat() if hasattr(profile, 'last_used') and profile.last_used else None,
            'success_rate': profile.get_success_rate() if hasattr(profile, 'get_success_rate') else 0.0,
            'platform_sessions': list(profile.platform_sessions.keys()) if hasattr(profile, 'platform_sessions') else [],
            'proxy_configured': bool(getattr(profile, 'proxy_config', None)),
            'recommendations': generate_profile_recommendations(profile, health_score)
        }
        
        report['profiles'].append(profile_data)
    
    # Sort by health score
    report['profiles'].sort(key=lambda x: x['health_score'], reverse=True)
    
    # Generate summary
    report['summary'] = {
        'healthy_profiles': len([p for p in report['profiles'] if p['health_score'] >= 70]),
        'at_risk_profiles': len([p for p in report['profiles'] if 30 <= p['health_score'] < 70]),
        'unhealthy_profiles': len([p for p in report['profiles'] if p['health_score'] < 30]),
        'avg_health_score': sum(p['health_score'] for p in report['profiles']) / len(report['profiles']) if report['profiles'] else 0
    }
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Exported health report to {output_path}")


def calculate_profile_health_score(profile: Any) -> float:
    """Calculate health score for a profile (0-100)"""
    score = 100.0
    
    # Check success rate
    if hasattr(profile, 'get_success_rate'):
        success_rate = profile.get_success_rate()
        if success_rate < 0.3:
            score -= 40
        elif success_rate < 0.5:
            score -= 20
        elif success_rate < 0.7:
            score -= 10
    
    # Check last usage
    if hasattr(profile, 'last_used') and profile.last_used:
        hours_since_used = (datetime.utcnow() - profile.last_used).total_seconds() / 3600
        if hours_since_used > 72:  # 3 days
            score -= 20
        elif hours_since_used > 24:  # 1 day
            score -= 10
    else:
        score -= 30  # Never used
    
    # Check session validity
    if hasattr(profile, 'platform_sessions'):
        valid_sessions = sum(
            1 for session in profile.platform_sessions.values()
            if session.get('is_valid', False)
        )
        if valid_sessions == 0:
            score -= 20
    
    # Check proxy health
    if hasattr(profile, 'proxy_config') and not profile.proxy_config:
        score -= 10  # No proxy configured
    
    # Check quality tier
    if hasattr(profile, 'quality'):
        if profile.quality == ProfileQuality.LOW:
            score -= 20
        elif profile.quality == ProfileQuality.MEDIUM:
            score -= 10
    
    return max(0, min(100, score))


def generate_profile_recommendations(profile: Any, health_score: float) -> List[str]:
    """Generate recommendations for improving profile health"""
    recommendations = []
    
    if health_score < 30:
        recommendations.append("Consider retiring this profile")
    
    # Check success rate
    if hasattr(profile, 'get_success_rate'):
        if profile.get_success_rate() < 0.5:
            recommendations.append("Low success rate - needs behavior adjustment")
    
    # Check sessions
    if hasattr(profile, 'platform_sessions'):
        valid_sessions = sum(
            1 for session in profile.platform_sessions.values()
            if session.get('is_valid', False)
        )
        if valid_sessions == 0:
            recommendations.append("No valid sessions - requires login")
    
    # Check proxy
    if hasattr(profile, 'proxy_config'):
        if not profile.proxy_config:
            recommendations.append("Configure proxy for better anonymity")
        elif hasattr(profile, 'should_rotate_proxy') and profile.should_rotate_proxy():
            recommendations.append("Rotate proxy session")
    
    # Check last usage
    if hasattr(profile, 'last_used') and profile.last_used:
        hours_since_used = (datetime.utcnow() - profile.last_used).total_seconds() / 3600
        if hours_since_used > 24:
            recommendations.append("Profile idle - consider warming up")
    
    return recommendations


# Monitoring utilities

def create_profile_monitor(manager: ProfileManager) -> 'ProfileMonitor':
    """Create a profile monitor instance"""
    return ProfileMonitor(manager)


class ProfileMonitor:
    """Monitor profile health and performance"""
    
    def __init__(self, manager: ProfileManager):
        self.manager = manager
        self.alert_callbacks = []
    
    def add_alert_callback(self, callback: Callable):
        """Add callback for alerts"""
        self.alert_callbacks.append(callback)
    
    async def check_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        metrics = await self.manager.get_pool_metrics()
        
        alerts = []
        
        # Check pool size
        pool_size = metrics.get('pool_size', 0)
        if pool_size < self.manager.config.get('min_pool_size_for_replacement', 10):
            alerts.append({
                'level': 'warning',
                'message': f'Low pool size: {pool_size}'
            })
        
        # Check success rates
        for platform, rate in metrics.get('platform_success_rates', {}).items():
            if rate < 0.3:
                alerts.append({
                    'level': 'critical',
                    'message': f'Low success rate for {platform}: {rate:.2%}'
                })
        
        # Check compromised profiles
        state_dist = metrics.get('state_distribution', {})
        compromised = state_dist.get('compromised', 0)
        if compromised > 0:
            alerts.append({
                'level': 'warning',
                'message': f'{compromised} compromised profiles detected'
            })
        
        # Trigger alerts
        for alert in alerts:
            await self._trigger_alert(alert)
        
        return {
            'healthy': len(alerts) == 0,
            'alerts': alerts,
            'metrics': metrics
        }
    
    async def _trigger_alert(self, alert: Dict[str, Any]):
        """Trigger alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")