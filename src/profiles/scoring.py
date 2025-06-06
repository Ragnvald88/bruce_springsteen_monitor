# src/profiles/scoring.py
"""Profile scoring logic for intelligent selection."""
import logging
from datetime import datetime
from typing import Optional

from .consolidated_models import Platform, BrowserProfile
from src.core.advanced_profile_system import DynamicProfile, ProfileState

logger = logging.getLogger(__name__)


class ProfileScorer:
    """Calculate profile scores for selection."""
    
    def __init__(self, config: dict = None):
        self.config = config or self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Get default scoring configuration"""
        return {
            'base_score': 50.0,
            'state_modifiers': {
                'PRISTINE': 10,
                'HEALTHY': 5,
                'WORN': -5,
                'COMPROMISED': -100,
                'EVOLVING': -20
            },
            'has_valid_session_bonus': 25,
            'session_age_penalty_per_hour': 0.5,
            'platform_bonuses': {
                'fansale': 10,
                'ticketmaster': 15,
                'vivaticket': 10
            },
            'success_rate_weight': 30,
            'avg_response_time_weight': 10,
            'consecutive_failure_penalty': 5,
            'captcha_penalty': 15,
            'avg_risk_score_penalty_weight': 20,
            'drift_penalty': 10,
            'proxy_rotation_bonus': 5,
            'recency_threshold_hours': 24,
            'recency_bonus_max': 10,
            'peak_time_bonus': 5
        }
    
    def calculate_score(
        self,
        dynamic_profile: DynamicProfile,
        static_profile: BrowserProfile,
        platform: Platform,
        require_session: bool
    ) -> float:
        """Calculate comprehensive profile score."""
        score = self.config.get('base_score', 50.0)
        
        # State modifier
        score += self.config.get('state_modifiers', {}).get(dynamic_profile.state.value if hasattr(dynamic_profile.state, 'value') else str(dynamic_profile.state), 0)
        
        # Session scoring
        score = self._apply_session_scoring(score, static_profile, platform, require_session)
        
        # Performance scoring
        score = self._apply_performance_scoring(score, static_profile, platform, dynamic_profile)
        
        # Risk and quality scoring
        score = self._apply_risk_scoring(score, dynamic_profile)
        score = self._apply_quality_scoring(score, static_profile)
        
        # Time-based scoring
        score = self._apply_time_scoring(score, static_profile)
        
        # Platform-specific adjustments
        score = self._apply_platform_adjustments(score, static_profile, platform)
        
        return max(0, score)
    
    def _apply_session_scoring(
        self,
        score: float,
        profile: BrowserProfile,
        platform: Platform,
        require_session: bool
    ) -> float:
        """Apply session-based scoring."""
        session = profile.platform_sessions.get(platform.value)
        
        if session and session.get('is_valid'):
            score += self.config.get('has_valid_session_bonus', 25)
            
            # Session age penalty
            session_age_hours = (
                datetime.utcnow() - datetime.fromisoformat(session['last_updated'])
            ).total_seconds() / 3600
            score -= session_age_hours * self.config.get('session_age_penalty_per_hour', 0.5)
            
            # Bonus for matching fingerprint
            if session.get('fingerprint_hash') == profile.fingerprint_hash:
                score += 10  # Consistency bonus
        elif require_session:
            score -= 100  # Heavy penalty if session required but not available
        
        return score
    
    def _apply_performance_scoring(
        self,
        score: float,
        profile: BrowserProfile,
        platform: Platform,
        dynamic_profile: DynamicProfile
    ) -> float:
        """Apply performance-based scoring."""
        platform_stats = profile.platform_stats.get(platform.value, {})
        
        # Platform success bonus
        if platform_stats.get('successes', 0) > 0:
            score += self.config.get('platform_bonuses', {}).get(platform.value, 0)
            
            # Success rate
            success_rate = profile.get_success_rate(platform.value)
            score += (success_rate - 0.5) * self.config.get('success_rate_weight', 30)
            
            # Consecutive successes bonus
            consecutive = platform_stats.get('consecutive_successes', 0)
            score += min(consecutive * 2, 20)  # Cap at 20 points
        
        # Response time factor
        avg_response_time = platform_stats.get('avg_response_time_ms', 0)
        if avg_response_time > 0:
            normalized_speed = max(0, 1 - (avg_response_time / 5000))
            score += normalized_speed * self.config.get('avg_response_time_weight', 10)
        
        # Consecutive failures penalty
        consecutive_failures = getattr(dynamic_profile, 'consecutive_failures', 0)
        score -= consecutive_failures * self.config.get('consecutive_failure_penalty', 5)
        
        # CAPTCHA penalty
        captcha_rate = platform_stats.get('captcha_solve_rate', 0)
        if captcha_rate < 0.7 and platform_stats.get('total_captchas', 0) > 5:
            score -= self.config.get('captcha_penalty', 15)
        
        return score
    
    def _apply_risk_scoring(self, score: float, dynamic_profile: DynamicProfile) -> float:
        """Apply risk-based scoring."""
        if hasattr(dynamic_profile, 'component_risk_scores') and dynamic_profile.component_risk_scores:
            avg_risk = sum(dynamic_profile.component_risk_scores.values()) / len(
                dynamic_profile.component_risk_scores
            )
            score -= avg_risk * self.config.get('avg_risk_score_penalty_weight', 20)
        
        # Drift penalty
        if hasattr(dynamic_profile, 'drift_detected') and dynamic_profile.drift_detected:
            score -= self.config.get('drift_penalty', 10)
        
        return score
    
    def _apply_quality_scoring(self, score: float, profile: BrowserProfile) -> float:
        """Apply quality-based scoring."""
        score *= profile.quality.success_rate
        
        # Proxy freshness bonus
        if hasattr(profile, 'proxy_config') and profile.proxy_config and hasattr(profile, 'should_rotate_proxy') and profile.should_rotate_proxy():
            score += self.config.get('proxy_rotation_bonus', 5)
        
        return score
    
    def _apply_time_scoring(self, score: float, profile: BrowserProfile) -> float:
        """Apply time-based scoring."""
        # Recency bonus
        time_since_used = (
            datetime.utcnow() - (profile.last_used or profile.created_at)
        ).total_seconds() / 3600
        
        recency_threshold = self.config.get('recency_threshold_hours', 24)
        if time_since_used < recency_threshold:
            recency_factor = 1 - (time_since_used / recency_threshold)
            score += recency_factor * self.config.get('recency_bonus_max', 10)
        
        # Peak time bonus
        current_hour = datetime.utcnow().hour
        if 9 <= current_hour <= 11 or 18 <= current_hour <= 20:
            score += self.config.get('peak_time_bonus', 5)
        
        return score
    
    def _apply_platform_adjustments(
        self,
        score: float,
        profile: BrowserProfile,
        platform: Platform
    ) -> float:
        """Apply platform-specific adjustments."""
        # Platform stealth requirements (simplified for consolidated system)
        if platform.requires_stealth:
            # Basic stealth check
            if not hasattr(profile, 'cdp_stealth_enabled') or not profile.cdp_stealth_enabled:
                score -= 20
        
        # Proxy requirements for high-security platforms
        if platform in [Platform.TICKETMASTER, Platform.VIVATICKET]:
            if not hasattr(profile, 'proxy_config') or not profile.proxy_config:
                score -= 30
        
        # Browser preference matching
        preferred_browsers = platform.preferred_browsers
        current_browser = getattr(profile, 'browser', profile.user_agent.split('/')[0] if '/' in profile.user_agent else 'Unknown')
        if current_browser not in preferred_browsers:
            score -= 10
        
        return score