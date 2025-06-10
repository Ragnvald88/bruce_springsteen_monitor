# stealthmaster/stealth/ml_resistant_behaviors.py
"""
ML-resistant human behavior simulation with advanced patterns.
Implements sophisticated behavioral patterns that evade ML-based detection systems.
"""

import asyncio
import random
import math
import time
from typing import Tuple, List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from playwright.async_api import Page, ElementHandle

import logging
logger = logging.getLogger(__name__)


class BehaviorProfile(Enum):
    """Different user behavior profiles."""
    FAST_PRECISE = "fast_precise"      # Young gamer type
    NORMAL = "normal"                  # Average user
    CAREFUL = "careful"                # Older/careful user
    MOBILE_LIKE = "mobile_like"        # Touch-screen habits
    POWER_USER = "power_user"          # Keyboard shortcuts, fast


@dataclass
class MouseCurve:
    """Represents a mouse movement curve."""
    points: List[Tuple[float, float]]
    duration: float
    acceleration_profile: str


class MLResistantBehaviors:
    """
    Advanced behavioral simulation that resists ML detection.
    Uses psychological models and biomechanics to create realistic patterns.
    """
    
    def __init__(self, profile: BehaviorProfile = BehaviorProfile.NORMAL):
        """Initialize with a specific behavior profile."""
        self.profile = profile
        self.profile_params = self._get_profile_params(profile)
        
        # Behavioral state
        self.fatigue_level = 0.0
        self.stress_level = 0.0
        self.attention_wandering = 0.0
        self.last_action_time = time.time()
        self.action_history = []
        
        # Mouse movement parameters
        self.mouse_speed_multiplier = self.profile_params["mouse_speed"]
        self.mouse_precision = self.profile_params["precision"]
        self.use_acceleration = self.profile_params["acceleration"]
        
        # Typing parameters
        self.typing_speed_wpm = self.profile_params["typing_wpm"]
        self.typo_rate = self.profile_params["typo_rate"]
        self.think_time = self.profile_params["think_time"]
        
        # Perlin noise for natural randomness
        self._noise_offset = random.random() * 1000
        
        logger.info(f"ML-Resistant behaviors initialized with {profile.value} profile")
    
    def _get_profile_params(self, profile: BehaviorProfile) -> Dict[str, Any]:
        """Get parameters for behavior profile."""
        profiles = {
            BehaviorProfile.FAST_PRECISE: {
                "mouse_speed": 1.5,
                "precision": 0.9,
                "acceleration": True,
                "typing_wpm": 80,
                "typo_rate": 0.01,
                "think_time": 0.5,
                "scroll_speed": 1.2,
                "attention_span": 0.8
            },
            BehaviorProfile.NORMAL: {
                "mouse_speed": 1.0,
                "precision": 0.7,
                "acceleration": True,
                "typing_wpm": 45,
                "typo_rate": 0.03,
                "think_time": 1.0,
                "scroll_speed": 1.0,
                "attention_span": 0.6
            },
            BehaviorProfile.CAREFUL: {
                "mouse_speed": 0.7,
                "precision": 0.5,
                "acceleration": False,
                "typing_wpm": 30,
                "typo_rate": 0.05,
                "think_time": 2.0,
                "scroll_speed": 0.8,
                "attention_span": 0.4
            },
            BehaviorProfile.MOBILE_LIKE: {
                "mouse_speed": 0.8,
                "precision": 0.4,
                "acceleration": False,
                "typing_wpm": 25,
                "typo_rate": 0.08,
                "think_time": 1.5,
                "scroll_speed": 1.5,
                "attention_span": 0.5
            },
            BehaviorProfile.POWER_USER: {
                "mouse_speed": 2.0,
                "precision": 0.95,
                "acceleration": True,
                "typing_wpm": 100,
                "typo_rate": 0.005,
                "think_time": 0.2,
                "scroll_speed": 2.0,
                "attention_span": 0.9
            }
        }
        return profiles[profile]
    
    def _perlin_noise(self, x: float) -> float:
        """Generate Perlin noise for natural randomness."""
        # Simplified Perlin noise implementation
        x = x + self._noise_offset
        fade = lambda t: t * t * t * (t * (t * 6 - 15) + 10)
        
        xi = int(x) & 255
        xf = x - int(x)
        
        u = fade(xf)
        
        # Simplified gradient calculation
        a = xi & 1
        b = (xi + 1) & 1
        
        return a * (1 - u) + b * u
    
    def _generate_mouse_curve(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        control_points: int = 3
    ) -> MouseCurve:
        """Generate a realistic mouse movement curve."""
        x1, y1 = start
        x2, y2 = end
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        # Duration based on Fitts' Law
        duration = 0.2 + (distance / 1000) * self.mouse_speed_multiplier
        
        # Generate control points with Perlin noise
        points = [(x1, y1)]
        
        # Add overshooting for realism (humans often overshoot targets)
        overshoot = 0.1 if self.profile == BehaviorProfile.FAST_PRECISE else 0.05
        
        for i in range(1, control_points + 1):
            t = i / (control_points + 1)
            
            # Base position
            base_x = x1 + (x2 - x1) * t
            base_y = y1 + (y2 - y1) * t
            
            # Add curve with Perlin noise
            noise_x = self._perlin_noise(t * 10) * 50 * (1 - self.mouse_precision)
            noise_y = self._perlin_noise(t * 10 + 100) * 50 * (1 - self.mouse_precision)
            
            # Add micro-jitter (hand tremor)
            jitter_x = (random.random() - 0.5) * 2
            jitter_y = (random.random() - 0.5) * 2
            
            points.append((base_x + noise_x + jitter_x, base_y + noise_y + jitter_y))
        
        # Add overshoot point if moving fast
        if self.use_acceleration and distance > 100:
            overshoot_x = x2 + (x2 - x1) * overshoot
            overshoot_y = y2 + (y2 - y1) * overshoot
            points.append((overshoot_x, overshoot_y))
        
        points.append((x2, y2))
        
        # Determine acceleration profile
        if self.use_acceleration:
            profile = "ease-in-out"  # Slow-fast-slow
        else:
            profile = "linear"
        
        return MouseCurve(points, duration, profile)
    
    async def move_mouse_human(
        self,
        page: Page,
        target_x: float,
        target_y: float,
        from_point: Optional[Tuple[float, float]] = None
    ) -> None:
        """Move mouse with human-like patterns."""
        # Get current position
        if from_point:
            current_x, current_y = from_point
        else:
            pos = await page.evaluate("() => ({ x: window.mouseX || 0, y: window.mouseY || 0 })")
            current_x, current_y = pos['x'], pos['y']
        
        # Generate movement curve
        curve = self._generate_mouse_curve((current_x, current_y), (target_x, target_y))
        
        # Execute movement
        start_time = time.time()
        
        for i in range(1, len(curve.points)):
            prev_x, prev_y = curve.points[i-1]
            curr_x, curr_y = curve.points[i]
            
            # Calculate timing based on acceleration profile
            progress = i / (len(curve.points) - 1)
            
            if curve.acceleration_profile == "ease-in-out":
                # Smooth acceleration and deceleration
                timing = 0.5 - 0.5 * math.cos(progress * math.pi)
            else:
                timing = progress
            
            # Move to point
            await page.mouse.move(curr_x, curr_y)
            
            # Calculate delay
            segment_duration = curve.duration / (len(curve.points) - 1)
            
            # Add variability to timing
            actual_delay = segment_duration * (0.8 + random.random() * 0.4)
            await asyncio.sleep(actual_delay)
        
        # Update fatigue based on movement
        self.fatigue_level = min(1.0, self.fatigue_level + 0.001)
    
    async def type_human(
        self,
        page: Page,
        text: str,
        field: Optional[ElementHandle] = None,
        think_first: bool = True
    ) -> None:
        """Type with realistic human patterns including muscle memory."""
        if field:
            await field.click()
            await asyncio.sleep(0.1 + random.random() * 0.2)
        
        # Initial thinking time
        if think_first:
            think_delay = self.think_time * (0.5 + random.random())
            await asyncio.sleep(think_delay)
        
        # Character pairs that are typed faster (muscle memory)
        common_pairs = ['th', 'he', 'in', 'er', 'an', 'ed', 'nd', 'to', 'en', 'ou',
                       'ng', 'ha', 'de', 're', 'or', 'it', 'is', 'at', 'on', 'es']
        
        i = 0
        while i < len(text):
            char = text[i]
            
            # Check for common pairs
            pair_typed = False
            if i < len(text) - 1:
                pair = text[i:i+2].lower()
                if pair in common_pairs:
                    # Type both characters quickly
                    await page.keyboard.type(text[i:i+2])
                    i += 2
                    pair_typed = True
                    # Faster delay for common pairs
                    await asyncio.sleep(random.uniform(0.03, 0.08))
            
            if not pair_typed:
                # Single character typing
                await page.keyboard.type(char)
                i += 1
                
                # Calculate delay based on WPM
                base_delay = 60.0 / (self.typing_speed_wpm * 5)  # 5 chars per word average
                
                # Add variability
                delay = base_delay * (0.5 + random.random())
                
                # Fatigue affects typing speed
                delay *= (1 + self.fatigue_level * 0.3)
                
                # Pause after punctuation
                if char in '.!?':
                    delay += random.uniform(0.3, 0.8)
                elif char in ',;:':
                    delay += random.uniform(0.1, 0.3)
                
                # Occasional longer pauses (thinking)
                if random.random() < 0.05:
                    delay += random.uniform(0.5, 2.0)
                
                await asyncio.sleep(delay)
            
            # Simulate typos
            if random.random() < self.typo_rate and i > 2 and i < len(text) - 2:
                # Common typo patterns
                typo_type = random.choice(['adjacent', 'double', 'transpose'])
                
                if typo_type == 'adjacent':
                    # Hit adjacent key
                    adjacent_keys = {
                        'a': 'sq', 'b': 'vghn', 'c': 'xdfv', 'd': 'serfcx',
                        'e': 'wrsdf', 'f': 'drtgvc', 'g': 'ftyhbv', 'h': 'gyujnb',
                        'i': 'ujko', 'j': 'huikmn', 'k': 'jiolm', 'l': 'kop',
                        'm': 'njk', 'n': 'bhjm', 'o': 'iklp', 'p': 'ol',
                        'q': 'wa', 'r': 'edft', 's': 'awedxz', 't': 'rfgy',
                        'u': 'yhji', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc',
                        'y': 'tghu', 'z': 'asx'
                    }
                    
                    if char.lower() in adjacent_keys:
                        wrong_key = random.choice(adjacent_keys[char.lower()])
                        await page.keyboard.type(wrong_key)
                        await asyncio.sleep(random.uniform(0.1, 0.3))
                        await page.keyboard.press('Backspace')
                        await asyncio.sleep(random.uniform(0.05, 0.15))
                
                elif typo_type == 'double' and i < len(text) - 1:
                    # Double tap
                    await page.keyboard.type(char)
                    await asyncio.sleep(random.uniform(0.2, 0.5))
                    await page.keyboard.press('Backspace')
                
                elif typo_type == 'transpose' and i < len(text) - 2:
                    # Transpose characters
                    await page.keyboard.type(text[i+1])
                    await asyncio.sleep(random.uniform(0.3, 0.8))
                    await page.keyboard.press('Backspace')
                    await page.keyboard.press('Backspace')
                    await asyncio.sleep(random.uniform(0.1, 0.2))
                    await page.keyboard.type(char)
        
        # Update fatigue
        self.fatigue_level = min(1.0, self.fatigue_level + len(text) * 0.0001)
    
    async def scroll_human(
        self,
        page: Page,
        direction: str = "down",
        distance: Optional[int] = None,
        smooth: bool = True
    ) -> None:
        """Scroll with human-like patterns including momentum."""
        if distance is None:
            distance = random.randint(200, 600)
        
        scroll_speed = self.profile_params["scroll_speed"]
        
        if smooth:
            # Smooth scrolling with momentum
            steps = random.randint(8, 15)
            
            # Generate scroll curve (ease-out for momentum)
            scroll_amounts = []
            for i in range(steps):
                progress = i / steps
                # Exponential decay for momentum effect
                amount = (1 - progress) ** 2
                scroll_amounts.append(amount)
            
            # Normalize to total distance
            total = sum(scroll_amounts)
            scroll_amounts = [int(distance * a / total) for a in scroll_amounts]
            
            for amount in scroll_amounts:
                if direction == "down":
                    await page.mouse.wheel(0, amount * scroll_speed)
                else:
                    await page.mouse.wheel(0, -amount * scroll_speed)
                
                # Variable delays for natural feel
                delay = random.uniform(0.01, 0.05)
                await asyncio.sleep(delay)
        else:
            # Chunky scrolling (like using arrow keys)
            chunks = random.randint(3, 7)
            for _ in range(chunks):
                chunk_size = distance // chunks + random.randint(-50, 50)
                
                if direction == "down":
                    await page.mouse.wheel(0, chunk_size * scroll_speed)
                else:
                    await page.mouse.wheel(0, -chunk_size * scroll_speed)
                
                await asyncio.sleep(random.uniform(0.1, 0.3))
    
    async def read_and_scroll(
        self,
        page: Page,
        duration: float = 5.0,
        pattern: str = "f-shaped"
    ) -> None:
        """Simulate reading patterns with scrolling."""
        start_time = time.time()
        viewport = await page.viewport_size()
        
        if not viewport:
            return
        
        while time.time() - start_time < duration:
            if pattern == "f-shaped":
                # F-shaped reading pattern (common for web)
                # Read across top
                await self.move_mouse_human(
                    page,
                    random.randint(100, viewport['width'] - 100),
                    random.randint(100, 200)
                )
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # Read down left side
                await self.move_mouse_human(
                    page,
                    random.randint(100, 300),
                    random.randint(200, 400)
                )
                await asyncio.sleep(random.uniform(0.3, 0.8))
                
                # Scroll down
                await self.scroll_human(page, "down", random.randint(100, 300))
                
            elif pattern == "z-shaped":
                # Z-shaped pattern
                # Top left to right
                await self.move_mouse_human(page, viewport['width'] - 200, 150)
                await asyncio.sleep(random.uniform(0.5, 1.0))
                
                # Diagonal to bottom left
                await self.move_mouse_human(page, 200, 400)
                await asyncio.sleep(random.uniform(0.3, 0.7))
                
                # Bottom left to right
                await self.move_mouse_human(page, viewport['width'] - 200, 400)
                await asyncio.sleep(random.uniform(0.5, 1.0))
                
                await self.scroll_human(page, "down")
            
            # Occasional attention wandering
            if random.random() < self.attention_wandering:
                # Look at random spot
                await self.move_mouse_human(
                    page,
                    random.randint(0, viewport['width']),
                    random.randint(0, viewport['height'])
                )
                await asyncio.sleep(random.uniform(1.0, 3.0))
            
            # Update attention wandering
            self.attention_wandering = min(1.0, self.attention_wandering + 0.05)
    
    async def hover_and_decide(
        self,
        page: Page,
        element: ElementHandle,
        decision_time: Optional[float] = None
    ) -> bool:
        """Hover over element and simulate decision making."""
        box = await element.bounding_box()
        if not box:
            return False
        
        # Move to element with some offset
        target_x = box['x'] + box['width'] * (0.3 + random.random() * 0.4)
        target_y = box['y'] + box['height'] * (0.3 + random.random() * 0.4)
        
        await self.move_mouse_human(page, target_x, target_y)
        
        # Decision time based on stress/fatigue
        if decision_time is None:
            base_time = random.uniform(0.3, 1.5)
            decision_time = base_time * (1 + self.stress_level * 0.5)
        
        # Micro-movements while deciding
        start_time = time.time()
        while time.time() - start_time < decision_time:
            # Small movements around the element
            micro_x = target_x + (random.random() - 0.5) * 20
            micro_y = target_y + (random.random() - 0.5) * 20
            
            await page.mouse.move(micro_x, micro_y)
            await asyncio.sleep(random.uniform(0.05, 0.15))
        
        # Decide whether to click (affected by stress)
        click_probability = 0.7 - self.stress_level * 0.3
        return random.random() < click_probability
    
    async def rage_click(self, page: Page, element: ElementHandle) -> None:
        """Simulate frustrated rapid clicking."""
        box = await element.bounding_box()
        if not box:
            return
        
        clicks = random.randint(2, 5)
        for _ in range(clicks):
            # Click with slight position variation
            x = box['x'] + box['width'] * (0.4 + random.random() * 0.2)
            y = box['y'] + box['height'] * (0.4 + random.random() * 0.2)
            
            await page.mouse.click(x, y)
            await asyncio.sleep(random.uniform(0.05, 0.15))
        
        # Increase stress level
        self.stress_level = min(1.0, self.stress_level + 0.2)
    
    async def idle_behavior(self, page: Page, duration: float = 2.0) -> None:
        """Simulate idle behavior like micro-movements."""
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Random micro-movement
            current = await page.evaluate("() => ({ x: window.mouseX || 0, y: window.mouseY || 0 })")
            
            # Small movement
            await page.mouse.move(
                current['x'] + (random.random() - 0.5) * 5,
                current['y'] + (random.random() - 0.5) * 5
            )
            
            await asyncio.sleep(random.uniform(0.5, 2.0))
    
    def update_behavioral_state(self, interaction_type: str) -> None:
        """Update behavioral state based on interactions."""
        current_time = time.time()
        time_since_last = current_time - self.last_action_time
        
        # Recovery from fatigue during breaks
        if time_since_last > 5.0:
            self.fatigue_level = max(0, self.fatigue_level - time_since_last * 0.01)
            self.stress_level = max(0, self.stress_level - time_since_last * 0.005)
            self.attention_wandering = max(0, self.attention_wandering - time_since_last * 0.002)
        
        # Update based on interaction
        if interaction_type == "intense_clicking":
            self.stress_level = min(1.0, self.stress_level + 0.1)
            self.fatigue_level = min(1.0, self.fatigue_level + 0.05)
        elif interaction_type == "long_typing":
            self.fatigue_level = min(1.0, self.fatigue_level + 0.1)
        elif interaction_type == "passive_reading":
            self.attention_wandering = min(1.0, self.attention_wandering + 0.05)
        
        self.last_action_time = current_time
        self.action_history.append({
            "type": interaction_type,
            "time": current_time,
            "fatigue": self.fatigue_level,
            "stress": self.stress_level
        })
        
        # Keep history size manageable
        if len(self.action_history) > 100:
            self.action_history = self.action_history[-50:]
    
    def get_behavioral_metrics(self) -> Dict[str, float]:
        """Get current behavioral metrics."""
        return {
            "fatigue_level": self.fatigue_level,
            "stress_level": self.stress_level,
            "attention_wandering": self.attention_wandering,
            "actions_performed": len(self.action_history),
            "time_since_last_action": time.time() - self.last_action_time
        }