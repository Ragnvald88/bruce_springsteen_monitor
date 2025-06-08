# src/core/adaptive_behavior_engine.py
"""
StealthMaster AI v3.0 - Adaptive Behavior Engine
ML-based dynamic behavior adaptation to evade detection
"""

import asyncio
import random
import time
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import logging

logger = logging.getLogger(__name__)


class BehaviorPattern(Enum):
    """Behavior pattern types"""
    CAUTIOUS = "cautious"      # Slow, methodical
    NORMAL = "normal"          # Average user
    EAGER = "eager"            # Fast but human
    ERRATIC = "erratic"        # Unpredictable
    ADAPTIVE = "adaptive"      # ML-based


@dataclass
class BehaviorMetrics:
    """Track behavior metrics for adaptation"""
    success_rate: float = 0.0
    detection_rate: float = 0.0
    avg_response_time: float = 0.0
    actions_per_minute: float = 0.0
    pattern_entropy: float = 0.0
    last_detection: Optional[datetime] = None
    consecutive_successes: int = 0
    consecutive_failures: int = 0


@dataclass
class ActionEvent:
    """Record of an action for pattern learning"""
    timestamp: datetime
    action_type: str
    duration: float
    success: bool
    detected: bool
    context: Dict[str, Any]


class AdaptiveBehaviorEngine:
    """
    Advanced behavior engine that learns and adapts
    Uses ML to find optimal patterns for each platform
    """
    
    def __init__(self, initial_pattern: BehaviorPattern = BehaviorPattern.NORMAL):
        self.current_pattern = initial_pattern
        self.metrics = BehaviorMetrics()
        
        # Action history for learning
        self.action_history: deque = deque(maxlen=1000)
        
        # Platform-specific patterns
        self.platform_patterns: Dict[str, Dict[str, Any]] = {}
        
        # Timing parameters (in milliseconds)
        self.timing_params = self._get_initial_timing_params()
        
        # Mouse movement parameters
        self.mouse_params = self._get_initial_mouse_params()
        
        # Decision weights
        self.decision_weights = {
            'speed': 0.5,
            'stealth': 0.5,
            'randomness': 0.3
        }
        
        # ML model simulation (in real implementation, use actual ML)
        self.pattern_scores: Dict[str, float] = {
            pattern.value: 0.5 for pattern in BehaviorPattern
        }
        
        # Callbacks
        self.adaptation_callbacks: List[Callable] = []
        
        logger.info(f"🧠 Adaptive Behavior Engine initialized with {initial_pattern.value} pattern")
    
    def _get_initial_timing_params(self) -> Dict[str, Tuple[float, float]]:
        """Get initial timing parameters based on pattern"""
        
        # Format: (min_ms, max_ms)
        base_timings = {
            BehaviorPattern.CAUTIOUS: {
                'click_delay': (800, 2000),
                'type_delay': (150, 400),
                'page_scan': (3000, 8000),
                'think_time': (2000, 5000),
                'scroll_delay': (1000, 3000),
                'mouse_move': (500, 1500)
            },
            BehaviorPattern.NORMAL: {
                'click_delay': (300, 800),
                'type_delay': (80, 200),
                'page_scan': (1500, 4000),
                'think_time': (1000, 3000),
                'scroll_delay': (500, 1500),
                'mouse_move': (200, 800)
            },
            BehaviorPattern.EAGER: {
                'click_delay': (150, 400),
                'type_delay': (40, 100),
                'page_scan': (800, 2000),
                'think_time': (500, 1500),
                'scroll_delay': (300, 800),
                'mouse_move': (100, 400)
            },
            BehaviorPattern.ERRATIC: {
                'click_delay': (100, 2000),
                'type_delay': (30, 300),
                'page_scan': (500, 5000),
                'think_time': (200, 4000),
                'scroll_delay': (200, 2000),
                'mouse_move': (50, 1000)
            }
        }
        
        return base_timings.get(self.current_pattern, base_timings[BehaviorPattern.NORMAL])
    
    def _get_initial_mouse_params(self) -> Dict[str, Any]:
        """Get initial mouse movement parameters"""
        
        return {
            'curve_complexity': 3 if self.current_pattern == BehaviorPattern.CAUTIOUS else 2,
            'overshoots': self.current_pattern == BehaviorPattern.ERRATIC,
            'acceleration': 1.5 if self.current_pattern == BehaviorPattern.EAGER else 1.0,
            'jitter_amount': 5 if self.current_pattern == BehaviorPattern.ERRATIC else 2,
            'pause_probability': 0.3 if self.current_pattern == BehaviorPattern.CAUTIOUS else 0.1
        }
    
    async def get_click_delay(self) -> float:
        """Get adaptive click delay in seconds"""
        
        min_ms, max_ms = self.timing_params['click_delay']
        
        # Add adaptation based on recent performance
        if self.metrics.consecutive_failures > 2:
            # Slow down if failing
            min_ms *= 1.5
            max_ms *= 1.5
        elif self.metrics.consecutive_successes > 5:
            # Speed up slightly if succeeding
            min_ms *= 0.9
            max_ms *= 0.9
        
        # Add human-like variation
        delay_ms = random.gauss((min_ms + max_ms) / 2, (max_ms - min_ms) / 6)
        delay_ms = max(min_ms, min(max_ms, delay_ms))  # Clamp to range
        
        # Occasionally add micro-pauses (human hesitation)
        if random.random() < 0.1:
            delay_ms += random.uniform(200, 500)
        
        return delay_ms / 1000  # Convert to seconds
    
    async def get_typing_delay(self) -> float:
        """Get delay between keystrokes"""
        
        min_ms, max_ms = self.timing_params['type_delay']
        
        # Simulate typing rhythm
        if hasattr(self, '_typing_rhythm'):
            # Continue rhythm
            base_delay = self._typing_rhythm
        else:
            # Start new rhythm
            self._typing_rhythm = random.uniform(min_ms, max_ms)
            base_delay = self._typing_rhythm
        
        # Add variation
        delay_ms = base_delay + random.gauss(0, 20)
        
        # Occasional pauses (thinking)
        if random.random() < 0.05:
            delay_ms += random.uniform(300, 800)
        
        # Fast burst typing occasionally
        if random.random() < 0.1:
            delay_ms *= 0.7
        
        return max(30, delay_ms) / 1000  # Minimum 30ms
    
    async def generate_mouse_path(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """Generate human-like mouse movement path"""
        
        points = []
        
        # Calculate distance
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = (dx**2 + dy**2)**0.5
        
        if distance < 50:
            # Short movement - straight line with slight curve
            steps = max(5, int(distance / 10))
            for i in range(steps + 1):
                t = i / steps
                # Add slight curve
                curve = np.sin(t * np.pi) * 0.1
                x = start[0] + dx * t + curve * dy * 0.3
                y = start[1] + dy * t - curve * dx * 0.3
                points.append((int(x), int(y)))
        else:
            # Long movement - bezier curve
            # Generate control points
            ctrl1_x = start[0] + dx * 0.25 + random.uniform(-50, 50)
            ctrl1_y = start[1] + dy * 0.25 + random.uniform(-50, 50)
            ctrl2_x = start[0] + dx * 0.75 + random.uniform(-50, 50)
            ctrl2_y = start[1] + dy * 0.75 + random.uniform(-50, 50)
            
            # Generate bezier curve
            steps = max(20, int(distance / 20))
            for i in range(steps + 1):
                t = i / steps
                
                # Bezier formula
                x = ((1-t)**3 * start[0] + 
                     3*(1-t)**2*t * ctrl1_x + 
                     3*(1-t)*t**2 * ctrl2_x + 
                     t**3 * end[0])
                
                y = ((1-t)**3 * start[1] + 
                     3*(1-t)**2*t * ctrl1_y + 
                     3*(1-t)*t**2 * ctrl2_y + 
                     t**3 * end[1])
                
                # Add jitter
                if self.mouse_params['jitter_amount'] > 0:
                    x += random.uniform(-self.mouse_params['jitter_amount'], 
                                      self.mouse_params['jitter_amount'])
                    y += random.uniform(-self.mouse_params['jitter_amount'], 
                                      self.mouse_params['jitter_amount'])
                
                points.append((int(x), int(y)))
            
            # Add overshoot if enabled
            if self.mouse_params['overshoots'] and random.random() < 0.3:
                overshoot_x = end[0] + dx * 0.1
                overshoot_y = end[1] + dy * 0.1
                points.append((int(overshoot_x), int(overshoot_y)))
                points.append(end)  # Return to target
        
        return points
    
    async def get_scroll_pattern(self) -> Dict[str, Any]:
        """Get human-like scroll pattern"""
        
        patterns = [
            {
                'direction': 'down',
                'amount': random.randint(100, 500),
                'duration': random.uniform(0.5, 1.5),
                'smooth': True
            },
            {
                'direction': 'up',
                'amount': random.randint(50, 200),
                'duration': random.uniform(0.3, 0.8),
                'smooth': True
            },
            {
                'direction': 'down',
                'amount': random.randint(300, 800),
                'duration': random.uniform(1.0, 2.0),
                'smooth': False  # Quick scroll
            }
        ]
        
        # Weight towards down scrolling
        weights = [0.6, 0.2, 0.2]
        pattern = random.choices(patterns, weights=weights)[0].copy()
        
        # Add variation
        pattern['amount'] = int(pattern['amount'] * random.uniform(0.8, 1.2))
        
        # Add pauses
        pattern['pause_after'] = random.uniform(0.5, 2.0)
        
        return pattern
    
    async def get_page_scan_pattern(self) -> List[Dict[str, Any]]:
        """Get pattern for scanning a page"""
        
        min_ms, max_ms = self.timing_params['page_scan']
        
        actions = []
        
        # Initial wait (page assessment)
        actions.append({
            'type': 'wait',
            'duration': random.uniform(min_ms/1000, max_ms/1000)
        })
        
        # Scroll pattern
        num_scrolls = random.randint(2, 5)
        for _ in range(num_scrolls):
            actions.append({
                'type': 'scroll',
                'pattern': await self.get_scroll_pattern()
            })
        
        # Look at specific areas
        if random.random() < 0.7:
            actions.append({
                'type': 'hover',
                'target': 'random_element',
                'duration': random.uniform(0.5, 1.5)
            })
        
        # Read time
        actions.append({
            'type': 'wait',
            'duration': random.uniform(1.0, 3.0)
        })
        
        return actions
    
    async def adapt_behavior(
        self,
        success: bool,
        detected: bool,
        response_time: float,
        platform: str
    ) -> None:
        """Adapt behavior based on outcomes"""
        
        # Update metrics
        self._update_metrics(success, detected, response_time)
        
        # Record event
        event = ActionEvent(
            timestamp=datetime.now(),
            action_type='navigation',
            duration=response_time,
            success=success,
            detected=detected,
            context={'platform': platform}
        )
        self.action_history.append(event)
        
        # Adapt pattern if needed
        if detected:
            await self._handle_detection(platform)
        elif success:
            await self._handle_success(platform)
        
        # Update ML scores
        self._update_pattern_scores()
        
        # Notify callbacks
        for callback in self.adaptation_callbacks:
            callback(self.current_pattern, self.metrics)
    
    def _update_metrics(self, success: bool, detected: bool, response_time: float) -> None:
        """Update behavior metrics"""
        
        # Update success/detection rates
        alpha = 0.1  # Exponential moving average factor
        
        self.metrics.success_rate = (1 - alpha) * self.metrics.success_rate + alpha * (1 if success else 0)
        self.metrics.detection_rate = (1 - alpha) * self.metrics.detection_rate + alpha * (1 if detected else 0)
        self.metrics.avg_response_time = (1 - alpha) * self.metrics.avg_response_time + alpha * response_time
        
        # Update consecutive counts
        if success and not detected:
            self.metrics.consecutive_successes += 1
            self.metrics.consecutive_failures = 0
        else:
            self.metrics.consecutive_failures += 1
            self.metrics.consecutive_successes = 0
        
        if detected:
            self.metrics.last_detection = datetime.now()
    
    async def _handle_detection(self, platform: str) -> None:
        """Handle detection event"""
        
        logger.warning(f"🚨 Detection on {platform}! Adapting behavior...")
        
        # Immediate response - slow down
        for key in self.timing_params:
            min_ms, max_ms = self.timing_params[key]
            self.timing_params[key] = (min_ms * 1.5, max_ms * 1.5)
        
        # Consider pattern change
        if self.metrics.consecutive_failures > 3:
            # Switch to more cautious pattern
            if self.current_pattern == BehaviorPattern.EAGER:
                await self.switch_pattern(BehaviorPattern.NORMAL)
            elif self.current_pattern == BehaviorPattern.NORMAL:
                await self.switch_pattern(BehaviorPattern.CAUTIOUS)
            elif self.current_pattern == BehaviorPattern.ERRATIC:
                await self.switch_pattern(BehaviorPattern.ADAPTIVE)
    
    async def _handle_success(self, platform: str) -> None:
        """Handle successful action"""
        
        # Gradual speed increase if consistent success
        if self.metrics.consecutive_successes > 10:
            for key in self.timing_params:
                min_ms, max_ms = self.timing_params[key]
                self.timing_params[key] = (min_ms * 0.95, max_ms * 0.95)
            
            # Consider pattern change
            if self.metrics.success_rate > 0.9 and self.metrics.detection_rate < 0.1:
                if self.current_pattern == BehaviorPattern.CAUTIOUS:
                    await self.switch_pattern(BehaviorPattern.NORMAL)
                elif self.current_pattern == BehaviorPattern.NORMAL:
                    await self.switch_pattern(BehaviorPattern.EAGER)
    
    def _update_pattern_scores(self) -> None:
        """Update ML pattern scores based on performance"""
        
        # Simple scoring based on recent performance
        current_score = (
            self.metrics.success_rate * 0.4 +
            (1 - self.metrics.detection_rate) * 0.4 +
            (1 / (1 + self.metrics.avg_response_time)) * 0.2
        )
        
        # Update current pattern score
        pattern_name = self.current_pattern.value
        alpha = 0.1
        self.pattern_scores[pattern_name] = (
            (1 - alpha) * self.pattern_scores[pattern_name] + 
            alpha * current_score
        )
    
    async def switch_pattern(self, new_pattern: BehaviorPattern) -> None:
        """Switch to a new behavior pattern"""
        
        logger.info(f"🔄 Switching behavior pattern: {self.current_pattern.value} → {new_pattern.value}")
        
        self.current_pattern = new_pattern
        self.timing_params = self._get_initial_timing_params()
        self.mouse_params = self._get_initial_mouse_params()
        
        # Reset some metrics
        self.metrics.consecutive_successes = 0
        self.metrics.consecutive_failures = 0
    
    async def get_decision_delay(self, complexity: str = "medium") -> float:
        """Get delay for decision making"""
        
        base_delays = {
            "simple": (500, 1000),
            "medium": (1000, 3000),
            "complex": (2000, 5000)
        }
        
        min_ms, max_ms = base_delays.get(complexity, base_delays["medium"])
        
        # Adjust based on pattern
        if self.current_pattern == BehaviorPattern.CAUTIOUS:
            min_ms *= 1.5
            max_ms *= 1.5
        elif self.current_pattern == BehaviorPattern.EAGER:
            min_ms *= 0.7
            max_ms *= 0.7
        
        delay_ms = random.gauss((min_ms + max_ms) / 2, (max_ms - min_ms) / 6)
        return max(min_ms, min(max_ms, delay_ms)) / 1000
    
    async def should_take_break(self) -> bool:
        """Determine if should take a break"""
        
        # Check action rate
        recent_actions = [a for a in self.action_history 
                         if (datetime.now() - a.timestamp).seconds < 300]
        
        actions_per_minute = len(recent_actions) / 5
        
        # Break if too active
        if actions_per_minute > 20:
            return True
        
        # Random breaks
        if self.current_pattern == BehaviorPattern.CAUTIOUS:
            return random.random() < 0.05  # 5% chance
        elif self.current_pattern == BehaviorPattern.NORMAL:
            return random.random() < 0.02  # 2% chance
        
        return False
    
    async def get_break_duration(self) -> float:
        """Get duration for a break"""
        
        if self.current_pattern == BehaviorPattern.CAUTIOUS:
            return random.uniform(30, 120)  # 30s to 2min
        elif self.current_pattern == BehaviorPattern.NORMAL:
            return random.uniform(15, 60)   # 15s to 1min
        else:
            return random.uniform(10, 30)   # 10s to 30s
    
    def get_adaptive_config(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific adaptive configuration"""
        
        # Base config
        config = {
            'timing': dict(self.timing_params),
            'mouse': dict(self.mouse_params),
            'pattern': self.current_pattern.value,
            'aggression': self._calculate_aggression_level()
        }
        
        # Platform-specific adjustments
        platform_adjustments = {
            'ticketmaster': {
                'timing_multiplier': 1.2,  # Slower for Ticketmaster
                'extra_caution': True
            },
            'fansale': {
                'timing_multiplier': 1.0,
                'extra_caution': False
            },
            'vivaticket': {
                'timing_multiplier': 1.1,
                'extra_caution': False
            }
        }
        
        if platform in platform_adjustments:
            adj = platform_adjustments[platform]
            
            # Apply timing multiplier
            for key in config['timing']:
                min_ms, max_ms = config['timing'][key]
                config['timing'][key] = (
                    min_ms * adj['timing_multiplier'],
                    max_ms * adj['timing_multiplier']
                )
            
            config['extra_caution'] = adj['extra_caution']
        
        return config
    
    def _calculate_aggression_level(self) -> float:
        """Calculate current aggression level (0-1)"""
        
        # Base on pattern
        pattern_aggression = {
            BehaviorPattern.CAUTIOUS: 0.2,
            BehaviorPattern.NORMAL: 0.5,
            BehaviorPattern.EAGER: 0.8,
            BehaviorPattern.ERRATIC: 0.6,
            BehaviorPattern.ADAPTIVE: 0.5
        }
        
        base = pattern_aggression[self.current_pattern]
        
        # Adjust based on performance
        if self.metrics.detection_rate > 0.3:
            base *= 0.7  # Reduce aggression
        elif self.metrics.success_rate > 0.8:
            base *= 1.2  # Increase aggression
        
        return max(0.1, min(0.9, base))
    
    def add_adaptation_callback(self, callback: Callable) -> None:
        """Add callback for adaptation events"""
        self.adaptation_callbacks.append(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get behavior statistics"""
        
        return {
            'current_pattern': self.current_pattern.value,
            'metrics': {
                'success_rate': round(self.metrics.success_rate, 3),
                'detection_rate': round(self.metrics.detection_rate, 3),
                'avg_response_time': round(self.metrics.avg_response_time, 2),
                'consecutive_successes': self.metrics.consecutive_successes,
                'consecutive_failures': self.metrics.consecutive_failures
            },
            'pattern_scores': self.pattern_scores,
            'aggression_level': self._calculate_aggression_level(),
            'action_history_size': len(self.action_history)
        }
    
    async def export_learned_patterns(self, filepath: str) -> None:
        """Export learned patterns for reuse"""
        
        data = {
            'patterns': self.platform_patterns,
            'scores': self.pattern_scores,
            'timing_params': self.timing_params,
            'metrics': {
                'success_rate': self.metrics.success_rate,
                'detection_rate': self.metrics.detection_rate
            },
            'exported_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"✅ Exported learned patterns to {filepath}")
    
    async def import_learned_patterns(self, filepath: str) -> None:
        """Import previously learned patterns"""
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.platform_patterns = data.get('patterns', {})
            self.pattern_scores = data.get('scores', self.pattern_scores)
            
            # Apply timing if recent
            exported_at = datetime.fromisoformat(data['exported_at'])
            if (datetime.now() - exported_at).days < 7:
                self.timing_params = data.get('timing_params', self.timing_params)
            
            logger.info(f"✅ Imported learned patterns from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to import patterns: {e}")


# Global instance
_behavior_engine: Optional[AdaptiveBehaviorEngine] = None

def get_behavior_engine(initial_pattern: BehaviorPattern = BehaviorPattern.NORMAL) -> AdaptiveBehaviorEngine:
    """Get or create global behavior engine"""
    global _behavior_engine
    
    if _behavior_engine is None:
        _behavior_engine = AdaptiveBehaviorEngine(initial_pattern)
    
    return _behavior_engine