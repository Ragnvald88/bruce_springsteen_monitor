# src/profiles/scoring.py
"""Profile scoring logic for intelligent selection."""
import logging
from datetime import datetime
from typing import Optional

from .config import ProfileScoringConfig
from .enums import Platform
from .models import BrowserProfile
from src.core.advanced_profile_system import DynamicProfile, ProfileState

logger = logging.getLogger(__name__)


class ProfileScorer:
    """Calculate profile scores for selection."""
    
    def __init__(self, config: ProfileScoringConfig):
        self.config = config
    
    def calculate_score(
        self,
        dynamic_profile: DynamicProfile,
        static_profile: BrowserProfile,
        platform: Platform,
        require_session: bool
    ) -> float:
        """Calculate comprehensive profile score."""
        score = self.config.base_score
        
        # State modifier
        score += self.config.state_modifiers.get(dynamic_profile.state, 0)
        
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
            score += self.config.has_valid_session_bonus
            
            # Session age penalty
            session_age_hours = (
                datetime.utcnow() - datetime.fromisoformat(session['last_updated'])
            ).total_seconds() / 3600
            score -= session_age_hours * self.config.session_age_penalty_per_hour
            
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
            score += self.config.platform_bonuses.get(platform.value, 0)
            
            # Success rate
            success_rate = profile.get_success_rate(platform.value)
            score += (success_rate - 0.5) * self.config.success_rate_weight
            
            # Consecutive successes bonus
            consecutive = platform_stats.get('consecutive_successes', 0)
            score += min(consecutive * 2, 20)  # Cap at 20 points
        
        # Response time factor
        avg_response_time = platform_stats.get('avg_response_time_ms', 0)
        if avg_response_time > 0:
            normalized_speed = max(0, 1 - (avg_response_time / 5000))
            score += normalized_speed * self.config.avg_response_time_weight
        
        # Consecutive failures penalty
        score -= dynamic_profile.consecutive_failures * self.config.consecutive_failure_penalty
        
        # CAPTCHA penalty
        captcha_rate = platform_stats.get('captcha_solve_rate', 0)
        if captcha_rate < 0.7 and platform_stats.get('total_captchas', 0) > 5:
            score -= self.config.captcha_penalty
        
        return score
    
    def _apply_risk_scoring(self, score: float, dynamic_profile: DynamicProfile) -> float:
        """Apply risk-based scoring."""
        if dynamic_profile.component_risk_scores:
            avg_risk = sum(dynamic_profile.component_risk_scores.values()) / len(
                dynamic_profile.component_risk_scores
            )
            score -= avg_risk * self.config.avg_risk_score_penalty_weight
        
        # Drift penalty
        if hasattr(dynamic_profile, 'drift_detected') and dynamic_profile.drift_detected:
            score -= self.config.drift_penalty
        
        return score
    
    def _apply_quality_scoring(self, score: float, profile: BrowserProfile) -> float:
        """Apply quality-based scoring."""
        score *= profile.quality.success_multiplier
        
        # Proxy freshness bonus
        if profile.proxy_config and profile.should_rotate_proxy():
            score += self.config.proxy_rotation_bonus
        
        return score
    
    def _apply_time_scoring(self, score: float, profile: BrowserProfile) -> float:
        """Apply time-based scoring."""
        # Recency bonus
        time_since_used = (
            datetime.utcnow() - (profile.last_used or profile.created_at)
        ).total_seconds() / 3600
        
        if time_since_used < self.config.recency_threshold_hours:
            recency_factor = 1 - (time_since_used / self.config.recency_threshold_hours)
            score += recency_factor * self.config.recency_bonus_max
        
        # Peak time bonus
        current_hour = datetime.utcnow().hour
        if 9 <= current_hour <= 11 or 18 <= current_hour <= 20:
            score += self.config.peak_time_bonus
        
        return score
    
    def _apply_platform_adjustments(
        self,
        score: float,
        profile: BrowserProfile,
        platform: Platform
    ) -> float:
        """Apply platform-specific adjustments."""
        # Platform stealth requirements
        requirements = platform.stealth_requirements
        
        if requirements.get('aggressive_stealth') and not profile.cdp_stealth_enabled:
            score -= 20
        
        if requirements.get('require_residential_proxy'):
            if not profile.proxy_config:
                score -= 30
            elif profile.proxy_config.proxy_provider not in ['brightdata', 'oxylabs']:
                score -= 15
        
        # Browser preference matching
        browser_prefs = requirements.get('browser_preferences', [])
        if browser_prefs and not any(pref.lower() in profile.user_agent.lower() for pref in browser_prefs):
            score -= 10
        
        return score