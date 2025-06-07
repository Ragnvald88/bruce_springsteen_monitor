# Domain Service: Profile Scoring
"""
Profile scoring service implementing business rules for profile selection.
Pure business logic with no external dependencies.
"""
from datetime import datetime
from typing import Dict, Any
from ..entities import BrowserProfile, Platform, ProfileState, ProfileQuality


class ProfileScoringService:
    """Calculate profile scores for intelligent selection"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default scoring configuration"""
        return {
            'base_score': 50.0,
            'state_modifiers': {
                ProfileState.PRISTINE: 10,
                ProfileState.HEALTHY: 5,
                ProfileState.SUSPICIOUS: -20,
                ProfileState.DORMANT: -10,
                ProfileState.COMPROMISED: -100,
                ProfileState.EVOLVING: -50
            },
            'has_valid_session_bonus': 25,
            'session_age_penalty_per_hour': 0.5,
            'platform_bonuses': {
                'fansale': 10,
                'ticketmaster': 15,
                'vivaticket': 10
            },
            'success_rate_weight': 30,
            'consecutive_failure_penalty': 5,
            'recency_threshold_hours': 24,
            'recency_bonus_max': 10,
            'peak_time_bonus': 5,
            'quality_multipliers': {
                ProfileQuality.PREMIUM: 1.5,
                ProfileQuality.HIGH: 1.2,
                ProfileQuality.MEDIUM: 1.0,
                ProfileQuality.LOW: 0.7
            }
        }
    
    def calculate_score(
        self,
        profile: BrowserProfile,
        platform: Platform,
        require_session: bool = False
    ) -> float:
        """Calculate comprehensive profile score"""
        score = self.config['base_score']
        
        # State modifier
        state_modifiers = self.config['state_modifiers']
        score += state_modifiers.get(profile.state, 0)
        
        # Session scoring
        score = self._apply_session_scoring(score, profile, platform, require_session)
        
        # Performance scoring
        score = self._apply_performance_scoring(score, profile, platform)
        
        # Quality scoring
        score = self._apply_quality_scoring(score, profile)
        
        # Time-based scoring
        score = self._apply_time_scoring(score, profile)
        
        # Platform-specific adjustments
        score = self._apply_platform_adjustments(score, profile, platform)
        
        return max(0, score)
    
    def _apply_session_scoring(
        self,
        score: float,
        profile: BrowserProfile,
        platform: Platform,
        require_session: bool
    ) -> float:
        """Apply session-based scoring"""
        session = profile.sessions.get(platform.name)
        
        if session and session.is_valid:
            score += self.config['has_valid_session_bonus']
            
            # Session age penalty
            session_age_hours = (
                datetime.utcnow() - datetime.fromisoformat(session.last_updated)
            ).total_seconds() / 3600
            
            score -= session_age_hours * self.config['session_age_penalty_per_hour']
            
            # Bonus for valid session
            score += 10
        elif require_session:
            score -= 100  # Heavy penalty if session required but not available
        
        return score
    
    def _apply_performance_scoring(
        self,
        score: float,
        profile: BrowserProfile,
        platform: Platform
    ) -> float:
        """Apply performance-based scoring"""
        platform_bonuses = self.config['platform_bonuses']
        if platform.name in platform_bonuses:
            score += platform_bonuses[platform.name]
        
        # Success rate bonus
        if profile.success_rate > 0.5:
            success_weight = self.config['success_rate_weight']
            score += (profile.success_rate - 0.5) * success_weight
        
        # Consecutive successes bonus (simplified)
        if profile.success_count > 5:
            score += min(profile.success_count * 0.5, 20)  # Cap at 20 points
        
        # Failures penalty
        if profile.failure_count > 5:
            failure_penalty = self.config['consecutive_failure_penalty']
            score -= min(profile.failure_count * failure_penalty, 50)
        
        # Platform-specific session bonus
        if platform.name in profile.sessions and profile.sessions[platform.name].is_valid:
            score += 10  # Bonus for having valid session
        
        return score
    
    def _apply_quality_scoring(self, score: float, profile: BrowserProfile) -> float:
        """Apply quality-based scoring"""
        quality_multiplier = self.config['quality_multipliers'].get(
            profile.quality, 
            1.0
        )
        score *= quality_multiplier
        
        # Proxy bonus
        if profile.proxy:
            score += 5
        
        return score
    
    def _apply_time_scoring(self, score: float, profile: BrowserProfile) -> float:
        """Apply time-based scoring"""
        # Recency bonus
        time_since_used = (
            datetime.utcnow() - (profile.last_used or profile.created_at)
        ).total_seconds() / 3600
        
        recency_threshold = self.config['recency_threshold_hours']
        if time_since_used < recency_threshold:
            recency_factor = 1 - (time_since_used / recency_threshold)
            recency_bonus_max = self.config['recency_bonus_max']
            score += recency_factor * recency_bonus_max
        
        # Peak time bonus
        current_hour = datetime.utcnow().hour
        if 9 <= current_hour <= 11 or 18 <= current_hour <= 20:
            peak_bonus = self.config['peak_time_bonus']
            score += peak_bonus
        
        return score
    
    def _apply_platform_adjustments(
        self,
        score: float,
        profile: BrowserProfile,
        platform: Platform
    ) -> float:
        """Apply platform-specific adjustments"""
        # Platform stealth requirements
        if platform.requires_stealth:
            # Penalize if no proxy for high-security platforms
            if not profile.proxy:
                score -= 20
        
        # Browser preference matching
        if profile.browser not in platform.preferred_browsers:
            score -= 10
        
        return score