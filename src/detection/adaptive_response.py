"""
Adaptive Detection Response Engine

Analyzes detection patterns and dynamically adjusts evasion tactics
based on real-time feedback and machine learning.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import defaultdict, deque
import json
import logging

logger = logging.getLogger(__name__)


class DetectionType(Enum):
    """Types of detection events"""
    CAPTCHA = "captcha"
    RATE_LIMIT = "rate_limit"
    FINGERPRINT = "fingerprint"
    BEHAVIOR = "behavior"
    IP_BLOCK = "ip_block"
    SESSION_INVALID = "session_invalid"
    UNKNOWN = "unknown"
    

class ResponseStrategy(Enum):
    """Response strategies to detection"""
    SLOW_DOWN = "slow_down"
    CHANGE_PROXY = "change_proxy"
    ROTATE_FINGERPRINT = "rotate_fingerprint"
    ENHANCE_BEHAVIOR = "enhance_behavior"
    PAUSE_SESSION = "pause_session"
    SWITCH_PROFILE = "switch_profile"
    FULL_RESET = "full_reset"
    

@dataclass
class DetectionEvent:
    """Represents a detection event"""
    timestamp: datetime
    platform: str
    detection_type: DetectionType
    severity: float  # 0.0 - 1.0
    context: Dict[str, Any]
    session_id: Optional[str] = None
    proxy_used: Optional[str] = None
    fingerprint_id: Optional[str] = None
    

@dataclass
class AdaptiveResponse:
    """Response to detection event"""
    strategies: List[ResponseStrategy]
    parameters: Dict[str, Any]
    confidence: float
    estimated_success_rate: float
    

@dataclass
class PlatformProfile:
    """Detection profile for a specific platform"""
    platform: str
    detection_sensitivity: float = 0.5
    common_detection_types: List[DetectionType] = field(default_factory=list)
    effective_strategies: Dict[DetectionType, List[ResponseStrategy]] = field(default_factory=dict)
    detection_patterns: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    

class AdaptiveResponseEngine:
    """
    Analyzes detection patterns and adapts evasion strategies in real-time
    """
    
    def __init__(self):
        """Initialize adaptive response engine"""
        # Detection tracking
        self.detection_events: deque = deque(maxlen=10000)
        self.detection_patterns: Dict[str, List[Tuple[datetime, DetectionType]]] = defaultdict(list)
        
        # Platform profiles
        self.platform_profiles: Dict[str, PlatformProfile] = {}
        self._initialize_platform_profiles()
        
        # Strategy effectiveness tracking
        self.strategy_outcomes: Dict[Tuple[DetectionType, ResponseStrategy], List[bool]] = defaultdict(list)
        
        # Real-time metrics
        self.current_risk_scores: Dict[str, float] = defaultdict(float)
        self.active_mitigations: Dict[str, Set[ResponseStrategy]] = defaultdict(set)
        
        # ML components
        self.pattern_analyzer = PatternAnalyzer()
        
        # Start background analysis
        asyncio.create_task(self._analysis_loop())
        
        logger.info("Adaptive Response Engine initialized")
        
    def _initialize_platform_profiles(self) -> None:
        """Initialize known platform profiles"""
        # Fansale profile
        self.platform_profiles['fansale'] = PlatformProfile(
            platform='fansale',
            detection_sensitivity=0.7,
            common_detection_types=[
                DetectionType.FINGERPRINT,
                DetectionType.BEHAVIOR,
                DetectionType.RATE_LIMIT
            ],
            effective_strategies={
                DetectionType.FINGERPRINT: [
                    ResponseStrategy.ROTATE_FINGERPRINT,
                    ResponseStrategy.SWITCH_PROFILE
                ],
                DetectionType.BEHAVIOR: [
                    ResponseStrategy.ENHANCE_BEHAVIOR,
                    ResponseStrategy.SLOW_DOWN
                ],
                DetectionType.RATE_LIMIT: [
                    ResponseStrategy.SLOW_DOWN,
                    ResponseStrategy.CHANGE_PROXY
                ]
            }
        )
        
        # Ticketmaster profile
        self.platform_profiles['ticketmaster'] = PlatformProfile(
            platform='ticketmaster',
            detection_sensitivity=0.9,  # Very sensitive
            common_detection_types=[
                DetectionType.CAPTCHA,
                DetectionType.FINGERPRINT,
                DetectionType.IP_BLOCK,
                DetectionType.BEHAVIOR
            ],
            effective_strategies={
                DetectionType.CAPTCHA: [
                    ResponseStrategy.ENHANCE_BEHAVIOR,
                    ResponseStrategy.PAUSE_SESSION
                ],
                DetectionType.FINGERPRINT: [
                    ResponseStrategy.FULL_RESET,
                    ResponseStrategy.SWITCH_PROFILE
                ],
                DetectionType.IP_BLOCK: [
                    ResponseStrategy.CHANGE_PROXY
                ]
            }
        )
        
        # Vivaticket profile
        self.platform_profiles['vivaticket'] = PlatformProfile(
            platform='vivaticket',
            detection_sensitivity=0.6,
            common_detection_types=[
                DetectionType.RATE_LIMIT,
                DetectionType.SESSION_INVALID
            ],
            effective_strategies={
                DetectionType.RATE_LIMIT: [
                    ResponseStrategy.SLOW_DOWN,
                    ResponseStrategy.PAUSE_SESSION
                ],
                DetectionType.SESSION_INVALID: [
                    ResponseStrategy.FULL_RESET
                ]
            }
        )
        
    async def analyze_detection(
        self,
        platform: str,
        detection_signal: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdaptiveResponse:
        """
        Analyze a detection signal and recommend response
        
        Args:
            platform: Platform where detection occurred
            detection_signal: Detection information
            context: Current session context
            
        Returns:
            Adaptive response with strategies
        """
        # Classify detection type
        detection_type = self._classify_detection(detection_signal)
        severity = self._calculate_severity(detection_signal, platform)
        
        # Create detection event
        event = DetectionEvent(
            timestamp=datetime.now(),
            platform=platform,
            detection_type=detection_type,
            severity=severity,
            context=context,
            session_id=context.get('session_id'),
            proxy_used=context.get('proxy'),
            fingerprint_id=context.get('fingerprint_id')
        )
        
        # Record event
        self.detection_events.append(event)
        self.detection_patterns[platform].append((event.timestamp, detection_type))
        
        # Update risk score
        self._update_risk_score(platform, event)
        
        # Generate adaptive response
        response = self._generate_response(event)
        
        # Log response
        logger.info(f"Detection on {platform}: {detection_type.value} (severity: {severity:.2f})")
        logger.info(f"Response: {[s.value for s in response.strategies]}")
        
        return response
        
    def _classify_detection(self, detection_signal: Dict[str, Any]) -> DetectionType:
        """Classify the type of detection"""
        signal_text = str(detection_signal).lower()
        
        if any(word in signal_text for word in ['captcha', 'challenge', 'verify']):
            return DetectionType.CAPTCHA
        elif any(word in signal_text for word in ['rate', 'limit', 'too many', 'slow down']):
            return DetectionType.RATE_LIMIT
        elif any(word in signal_text for word in ['block', 'banned', 'forbidden']):
            return DetectionType.IP_BLOCK
        elif any(word in signal_text for word in ['session', 'expired', 'invalid']):
            return DetectionType.SESSION_INVALID
        elif any(word in signal_text for word in ['fingerprint', 'device', 'browser']):
            return DetectionType.FINGERPRINT
        elif any(word in signal_text for word in ['behavior', 'suspicious', 'bot']):
            return DetectionType.BEHAVIOR
        else:
            return DetectionType.UNKNOWN
            
    def _calculate_severity(self, detection_signal: Dict[str, Any], platform: str) -> float:
        """Calculate detection severity (0.0 - 1.0)"""
        base_severity = 0.5
        
        # Platform sensitivity factor
        if platform in self.platform_profiles:
            base_severity *= self.platform_profiles[platform].detection_sensitivity
            
        # Signal-based adjustments
        if detection_signal.get('hard_block'):
            base_severity = max(base_severity, 0.9)
        elif detection_signal.get('soft_challenge'):
            base_severity = min(base_severity, 0.6)
            
        # Recent detection frequency
        recent_detections = self._get_recent_detections(platform, minutes=10)
        if len(recent_detections) > 5:
            base_severity = min(1.0, base_severity + 0.1 * len(recent_detections))
            
        return min(1.0, max(0.0, base_severity))
        
    def _update_risk_score(self, platform: str, event: DetectionEvent) -> None:
        """Update platform risk score"""
        current_score = self.current_risk_scores[platform]
        
        # Exponential moving average
        alpha = 0.3
        new_score = alpha * event.severity + (1 - alpha) * current_score
        
        # Decay over time
        time_since_last = 0
        recent = self._get_recent_detections(platform, minutes=5)
        if recent:
            time_since_last = (datetime.now() - recent[-1][0]).total_seconds()
            decay_factor = 0.99 ** (time_since_last / 60)  # Decay per minute
            new_score *= decay_factor
            
        self.current_risk_scores[platform] = new_score
        
    def _generate_response(self, event: DetectionEvent) -> AdaptiveResponse:
        """Generate adaptive response to detection"""
        strategies = []
        parameters = {}
        
        # Get platform profile
        profile = self.platform_profiles.get(event.platform)
        
        # Base strategies from platform profile
        if profile and event.detection_type in profile.effective_strategies:
            base_strategies = profile.effective_strategies[event.detection_type]
            strategies.extend(base_strategies)
        else:
            # Generic strategies based on detection type
            strategies.extend(self._get_generic_strategies(event.detection_type))
            
        # Adjust based on severity
        if event.severity > 0.8:
            # High severity - more aggressive response
            if ResponseStrategy.FULL_RESET not in strategies:
                strategies.append(ResponseStrategy.FULL_RESET)
            parameters['wait_time'] = 300  # 5 minutes
        elif event.severity > 0.6:
            # Medium severity
            if ResponseStrategy.PAUSE_SESSION not in strategies:
                strategies.append(ResponseStrategy.PAUSE_SESSION)
            parameters['wait_time'] = 60  # 1 minute
        else:
            # Low severity
            if ResponseStrategy.SLOW_DOWN not in strategies:
                strategies.append(ResponseStrategy.SLOW_DOWN)
            parameters['speed_factor'] = 0.5
            
        # Check if strategies are already active
        active = self.active_mitigations[event.platform]
        new_strategies = [s for s in strategies if s not in active]
        
        # If all strategies are already active, escalate
        if not new_strategies and strategies:
            strategies = [ResponseStrategy.FULL_RESET]
            parameters['escalation'] = True
            
        # Calculate confidence based on historical effectiveness
        confidence = self._calculate_strategy_confidence(event.detection_type, strategies)
        
        # Estimate success rate
        success_rate = self._estimate_success_rate(event, strategies)
        
        # Update active mitigations
        for strategy in strategies:
            self.active_mitigations[event.platform].add(strategy)
            
        return AdaptiveResponse(
            strategies=strategies,
            parameters=parameters,
            confidence=confidence,
            estimated_success_rate=success_rate
        )
        
    def _get_generic_strategies(self, detection_type: DetectionType) -> List[ResponseStrategy]:
        """Get generic strategies for detection type"""
        strategy_map = {
            DetectionType.CAPTCHA: [ResponseStrategy.ENHANCE_BEHAVIOR, ResponseStrategy.SLOW_DOWN],
            DetectionType.RATE_LIMIT: [ResponseStrategy.SLOW_DOWN, ResponseStrategy.PAUSE_SESSION],
            DetectionType.FINGERPRINT: [ResponseStrategy.ROTATE_FINGERPRINT],
            DetectionType.BEHAVIOR: [ResponseStrategy.ENHANCE_BEHAVIOR],
            DetectionType.IP_BLOCK: [ResponseStrategy.CHANGE_PROXY],
            DetectionType.SESSION_INVALID: [ResponseStrategy.SWITCH_PROFILE],
            DetectionType.UNKNOWN: [ResponseStrategy.SLOW_DOWN]
        }
        return strategy_map.get(detection_type, [ResponseStrategy.SLOW_DOWN])
        
    def _calculate_strategy_confidence(
        self,
        detection_type: DetectionType,
        strategies: List[ResponseStrategy]
    ) -> float:
        """Calculate confidence in strategy effectiveness"""
        if not strategies:
            return 0.0
            
        confidences = []
        
        for strategy in strategies:
            key = (detection_type, strategy)
            outcomes = self.strategy_outcomes.get(key, [])
            
            if outcomes:
                # Success rate of this strategy
                success_rate = sum(outcomes) / len(outcomes)
                # Weight by number of samples
                weight = min(1.0, len(outcomes) / 10)
                confidence = success_rate * weight
            else:
                # No history - use default confidence
                confidence = 0.5
                
            confidences.append(confidence)
            
        return np.mean(confidences)
        
    def _estimate_success_rate(
        self,
        event: DetectionEvent,
        strategies: List[ResponseStrategy]
    ) -> float:
        """Estimate success rate of response strategies"""
        base_rate = 0.7  # Optimistic default
        
        # Adjust based on severity
        base_rate *= (1.0 - event.severity * 0.5)
        
        # Adjust based on platform patterns
        recent_success = self._get_recent_success_rate(event.platform)
        if recent_success is not None:
            base_rate = base_rate * 0.3 + recent_success * 0.7
            
        # Boost for combined strategies
        if len(strategies) > 1:
            base_rate *= 1.1
            
        return min(1.0, max(0.0, base_rate))
        
    def _get_recent_detections(
        self,
        platform: str,
        minutes: int = 10
    ) -> List[Tuple[datetime, DetectionType]]:
        """Get recent detections for platform"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [
            (ts, dt) for ts, dt in self.detection_patterns[platform]
            if ts > cutoff
        ]
        
    def _get_recent_success_rate(self, platform: str) -> Optional[float]:
        """Get recent success rate for platform"""
        recent_events = [
            e for e in self.detection_events
            if e.platform == platform and 
            e.timestamp > datetime.now() - timedelta(hours=1)
        ]
        
        if not recent_events:
            return None
            
        # Lower severity means more success
        avg_severity = np.mean([e.severity for e in recent_events])
        return 1.0 - avg_severity
        
    async def record_strategy_outcome(
        self,
        platform: str,
        detection_type: DetectionType,
        strategies: List[ResponseStrategy],
        success: bool
    ) -> None:
        """Record the outcome of applied strategies"""
        for strategy in strategies:
            key = (detection_type, strategy)
            self.strategy_outcomes[key].append(success)
            
            # Limit history
            if len(self.strategy_outcomes[key]) > 100:
                self.strategy_outcomes[key] = self.strategy_outcomes[key][-50:]
                
        # Update platform profile
        if platform in self.platform_profiles:
            profile = self.platform_profiles[platform]
            
            # Update effective strategies based on outcomes
            if success and detection_type not in profile.effective_strategies:
                profile.effective_strategies[detection_type] = strategies
            elif success:
                # Add successful strategies
                for strategy in strategies:
                    if strategy not in profile.effective_strategies[detection_type]:
                        profile.effective_strategies[detection_type].append(strategy)
                        
        # Clear active mitigations if successful
        if success:
            self.active_mitigations[platform].clear()
            self.current_risk_scores[platform] *= 0.5  # Reduce risk score
            
    async def _analysis_loop(self) -> None:
        """Background analysis of detection patterns"""
        while True:
            try:
                await asyncio.sleep(300)  # Analyze every 5 minutes
                
                # Analyze patterns for each platform
                for platform in self.platform_profiles:
                    await self._analyze_platform_patterns(platform)
                    
                # Clean old data
                self._cleanup_old_data()
                
            except Exception as e:
                logger.error(f"Analysis loop error: {e}")
                
    async def _analyze_platform_patterns(self, platform: str) -> None:
        """Analyze detection patterns for a platform"""
        recent_events = [
            e for e in self.detection_events
            if e.platform == platform and
            e.timestamp > datetime.now() - timedelta(hours=24)
        ]
        
        if not recent_events:
            return
            
        # Analyze detection frequency
        detection_counts = defaultdict(int)
        for event in recent_events:
            detection_counts[event.detection_type] += 1
            
        # Update platform profile
        profile = self.platform_profiles[platform]
        profile.common_detection_types = [
            dt for dt, _ in sorted(
                detection_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
        ]
        
        # Analyze time patterns
        hour_counts = defaultdict(int)
        for event in recent_events:
            hour_counts[event.timestamp.hour] += 1
            
        # Find peak detection hours
        peak_hours = [
            hour for hour, count in hour_counts.items()
            if count > np.mean(list(hour_counts.values()))
        ]
        
        # Store pattern
        profile.detection_patterns.append({
            'timestamp': datetime.now(),
            'peak_hours': peak_hours,
            'detection_types': dict(detection_counts),
            'avg_severity': np.mean([e.severity for e in recent_events])
        })
        
        # Limit pattern history
        if len(profile.detection_patterns) > 100:
            profile.detection_patterns = profile.detection_patterns[-50:]
            
        profile.last_updated = datetime.now()
        
    def _cleanup_old_data(self) -> None:
        """Clean up old detection data"""
        cutoff = datetime.now() - timedelta(days=7)
        
        # Clean detection patterns
        for platform in self.detection_patterns:
            self.detection_patterns[platform] = [
                (ts, dt) for ts, dt in self.detection_patterns[platform]
                if ts > cutoff
            ]
            
    def get_platform_risk_assessment(self, platform: str) -> Dict[str, Any]:
        """Get current risk assessment for platform"""
        profile = self.platform_profiles.get(platform)
        risk_score = self.current_risk_scores.get(platform, 0.0)
        
        recent_detections = self._get_recent_detections(platform, minutes=60)
        detection_rate = len(recent_detections) / 60  # Per minute
        
        assessment = {
            'platform': platform,
            'risk_score': risk_score,
            'risk_level': self._get_risk_level(risk_score),
            'detection_rate': detection_rate,
            'recent_detection_types': list(set(dt for _, dt in recent_detections[-10:])),
            'active_mitigations': list(self.active_mitigations[platform]),
            'recommended_actions': self._get_recommended_actions(platform, risk_score)
        }
        
        if profile:
            assessment.update({
                'sensitivity': profile.detection_sensitivity,
                'common_detections': [dt.value for dt in profile.common_detection_types],
                'last_pattern_analysis': profile.last_updated.isoformat()
            })
            
        return assessment
        
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to level"""
        if risk_score < 0.2:
            return "low"
        elif risk_score < 0.5:
            return "medium"
        elif risk_score < 0.8:
            return "high"
        else:
            return "critical"
            
    def _get_recommended_actions(self, platform: str, risk_score: float) -> List[str]:
        """Get recommended actions based on risk"""
        actions = []
        
        if risk_score > 0.8:
            actions.extend([
                "Pause all operations on this platform",
                "Switch to different proxy pool",
                "Reset all browser profiles"
            ])
        elif risk_score > 0.5:
            actions.extend([
                "Reduce operation frequency",
                "Enhance behavioral randomization",
                "Rotate fingerprints more frequently"
            ])
        elif risk_score > 0.2:
            actions.extend([
                "Monitor closely for increased detections",
                "Consider slowing down operations"
            ])
        else:
            actions.append("Continue normal operations")
            
        return actions
        
    def export_analytics(self, filepath: str) -> None:
        """Export detection analytics"""
        analytics = {
            'timestamp': datetime.now().isoformat(),
            'platforms': {},
            'detection_summary': self._get_detection_summary(),
            'strategy_effectiveness': self._get_strategy_effectiveness()
        }
        
        for platform, profile in self.platform_profiles.items():
            analytics['platforms'][platform] = {
                'risk_assessment': self.get_platform_risk_assessment(platform),
                'detection_patterns': profile.detection_patterns[-10:],
                'effective_strategies': {
                    dt.value: [s.value for s in strategies]
                    for dt, strategies in profile.effective_strategies.items()
                }
            }
            
        with open(filepath, 'w') as f:
            json.dump(analytics, f, indent=2, default=str)
            
    def _get_detection_summary(self) -> Dict[str, Any]:
        """Get overall detection summary"""
        total_detections = len(self.detection_events)
        if total_detections == 0:
            return {'total': 0}
            
        by_type = defaultdict(int)
        by_platform = defaultdict(int)
        
        for event in self.detection_events:
            by_type[event.detection_type.value] += 1
            by_platform[event.platform] += 1
            
        return {
            'total': total_detections,
            'by_type': dict(by_type),
            'by_platform': dict(by_platform),
            'avg_severity': np.mean([e.severity for e in self.detection_events])
        }
        
    def _get_strategy_effectiveness(self) -> Dict[str, Any]:
        """Get strategy effectiveness summary"""
        effectiveness = {}
        
        for (detection_type, strategy), outcomes in self.strategy_outcomes.items():
            if outcomes:
                key = f"{detection_type.value}_{strategy.value}"
                effectiveness[key] = {
                    'success_rate': sum(outcomes) / len(outcomes),
                    'sample_size': len(outcomes)
                }
                
        return effectiveness


class PatternAnalyzer:
    """Analyzes detection patterns using statistical methods"""
    
    def __init__(self):
        self.pattern_cache = {}
        
    def find_temporal_patterns(self, events: List[DetectionEvent]) -> Dict[str, Any]:
        """Find temporal patterns in detection events"""
        if not events:
            return {}
            
        # Extract timestamps
        timestamps = [e.timestamp for e in events]
        
        # Hour of day analysis
        hours = [ts.hour for ts in timestamps]
        hour_counts = defaultdict(int)
        for hour in hours:
            hour_counts[hour] += 1
            
        # Day of week analysis
        days = [ts.weekday() for ts in timestamps]
        day_counts = defaultdict(int)
        for day in days:
            day_counts[day] += 1
            
        # Inter-arrival times
        if len(timestamps) > 1:
            inter_arrival = []
            for i in range(1, len(timestamps)):
                delta = (timestamps[i] - timestamps[i-1]).total_seconds()
                inter_arrival.append(delta)
                
            avg_interval = np.mean(inter_arrival)
            std_interval = np.std(inter_arrival)
        else:
            avg_interval = 0
            std_interval = 0
            
        return {
            'peak_hours': [h for h, c in hour_counts.items() if c > np.mean(list(hour_counts.values()))],
            'peak_days': [d for d, c in day_counts.items() if c > np.mean(list(day_counts.values()))],
            'avg_interval_seconds': avg_interval,
            'interval_std': std_interval,
            'clustering_score': self._calculate_clustering_score(timestamps)
        }
        
    def _calculate_clustering_score(self, timestamps: List[datetime]) -> float:
        """Calculate how clustered events are (0=uniform, 1=highly clustered)"""
        if len(timestamps) < 3:
            return 0.0
            
        # Convert to seconds since first event
        first = timestamps[0]
        seconds = [(ts - first).total_seconds() for ts in timestamps]
        
        # Calculate variance
        variance = np.var(seconds)
        mean = np.mean(seconds)
        
        # Normalize
        if mean > 0:
            cv = np.sqrt(variance) / mean  # Coefficient of variation
            return min(1.0, cv)
        
        return 0.0


# Global instance
adaptive_response_engine = AdaptiveResponseEngine()