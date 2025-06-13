# stealthmaster/stealth/behaviors.py
"""Human behavior simulation for anti-detection."""

import asyncio
import random
import math
import time
from typing import Tuple, List, Optional, Dict, Any
from playwright.async_api import Page, ElementHandle
from dataclasses import dataclass
from enum import Enum
import numpy as np
import logging

logger = logging.getLogger(__name__)


# from .ml_resistant_behaviors import MLResistantBehaviors, BehaviorProfile

# Enhanced behavior profiles with detailed characteristics
class BehaviorProfile(Enum):
    NORMAL = "normal"
    CAUTIOUS = "cautious"
    AGGRESSIVE = "aggressive"
    TIRED = "tired"
    FOCUSED = "focused"
    DISTRACTED = "distracted"

@dataclass
class BehaviorMetrics:
    """Track behavior metrics for adaptation"""
    typing_speed_wpm: float = 45.0
    mouse_speed: float = 1.0
    error_rate: float = 0.02
    attention_span: float = 1.0
    fatigue_level: float = 0.0
    focus_level: float = 0.7
    last_break_time: float = 0.0
    actions_since_break: int = 0


class HumanBehavior:
    """Advanced human behavior simulation with 2025 ML-resistant patterns."""
    
    def __init__(self):
        """Initialize behavior simulator."""
        self.last_action_time = time.time()
        self.action_count = 0
        self.behavior_profile = BehaviorProfile.NORMAL
        self.metrics = BehaviorMetrics()
        
        # Advanced tracking
        self.mouse_history: List[Tuple[float, float, float]] = []  # x, y, timestamp
        self.typing_rhythm: List[float] = []  # Inter-key delays
        self.attention_zones: List[Dict[str, Any]] = []  # Areas of interest
        self.session_start = time.time()
        
        # Physiological parameters
        self.tremor_amplitude = random.uniform(0.5, 2.0)  # Mouse micro-movements
        self.reaction_time_base = random.uniform(0.15, 0.25)  # Base reaction time
    
    async def initialize(self, page: Page) -> None:
        """Initialize human behavior for a page."""
        # Add mouse movement tracking
        await page.evaluate("""
            window.mouseX = 0;
            window.mouseY = 0;
            document.addEventListener('mousemove', (e) => {
                window.mouseX = e.clientX;
                window.mouseY = e.clientY;
            });
        """)
        
    async def human_delay(self, min_ms: int = 100, max_ms: int = 300) -> None:
        """Add human-like delay between actions."""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    async def move_mouse_naturally(
        self,
        page: Page,
        start: Tuple[int, int],
        end: Tuple[int, int],
        steps: int = None
    ) -> None:
        """Advanced mouse movement with human-like trajectories."""
        x1, y1 = start
        x2, y2 = end
        
        # Calculate distance and adjust steps
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if steps is None:
            steps = max(20, int(distance / 10))  # More steps for longer movements
        
        # Generate multiple control points for cubic bezier curve
        # This creates more natural, less predictable movements
        deviation = min(distance * 0.3, 100)  # Deviation based on distance
        
        # Control points with human-like overshooting and correction
        ctrl1_x = x1 + (x2 - x1) * 0.25 + random.uniform(-deviation, deviation)
        ctrl1_y = y1 + (y2 - y1) * 0.25 + random.uniform(-deviation, deviation)
        
        ctrl2_x = x1 + (x2 - x1) * 0.75 + random.uniform(-deviation/2, deviation/2)
        ctrl2_y = y1 + (y2 - y1) * 0.75 + random.uniform(-deviation/2, deviation/2)
        
        # Add slight overshoot for realism (humans often overshoot targets)
        if random.random() < 0.3:
            overshoot_factor = 1.05 + random.random() * 0.1
            ctrl2_x = x1 + (x2 - x1) * overshoot_factor
            ctrl2_y = y1 + (y2 - y1) * overshoot_factor
        
        # Variable speed based on distance (Fitts's law)
        base_speed = 0.005 if distance < 100 else 0.003
        
        for i in range(steps):
            t = i / steps
            
            # Cubic bezier curve for more natural movement
            x = ((1-t)**3 * x1 + 
                 3*(1-t)**2*t * ctrl1_x + 
                 3*(1-t)*t**2 * ctrl2_x + 
                 t**3 * x2)
            
            y = ((1-t)**3 * y1 + 
                 3*(1-t)**2*t * ctrl1_y + 
                 3*(1-t)*t**2 * ctrl2_y + 
                 t**3 * y2)
            
            # Add micro-tremors (physiological tremor)
            if self.metrics.fatigue_level > 0.3:
                tremor_x = random.gauss(0, self.tremor_amplitude * self.metrics.fatigue_level)
                tremor_y = random.gauss(0, self.tremor_amplitude * self.metrics.fatigue_level)
                x += tremor_x
                y += tremor_y
            
            # Movement with acceleration/deceleration
            speed_factor = 1.0
            if t < 0.2:  # Acceleration phase
                speed_factor = t * 5
            elif t > 0.8:  # Deceleration phase
                speed_factor = (1 - t) * 5
            
            await page.mouse.move(x, y)
            
            # Variable delay based on movement phase
            delay = base_speed / (speed_factor * self.metrics.mouse_speed)
            await asyncio.sleep(delay + random.gauss(0, delay * 0.1))
        
        # Record movement for pattern analysis
        self.mouse_history.append((x2, y2, time.time()))
        if len(self.mouse_history) > 1000:
            self.mouse_history = self.mouse_history[-500:]  # Keep last 500 points
    
    async def human_type(
        self,
        page: Page,
        text: str,
        element: Optional[ElementHandle] = None
    ) -> None:
        """Advanced typing simulation with muscle memory and fatigue effects."""
        if element:
            await self.click_with_hesitation(page, element, 0.3)
            await asyncio.sleep(random.uniform(0.1, 0.3))  # Focus delay
        
        # Calculate base typing speed from WPM
        chars_per_minute = self.metrics.typing_speed_wpm * 5  # Average 5 chars per word
        base_delay = 60.0 / chars_per_minute
        
        # Common bigrams/trigrams type faster (muscle memory)
        common_sequences = ['th', 'he', 'in', 'er', 'an', 'the', 'ing', 'and', 'ion']
        
        i = 0
        while i < len(text):
            # Check for common sequences
            typed_fast = False
            for seq in common_sequences:
                if text[i:i+len(seq)].lower() == seq and i + len(seq) <= len(text):
                    # Type sequence quickly
                    for char in text[i:i+len(seq)]:
                        await page.keyboard.type(char)
                        await asyncio.sleep(base_delay * random.uniform(0.6, 0.8))
                    i += len(seq)
                    typed_fast = True
                    break
            
            if not typed_fast:
                char = text[i]
                
                # Fatigue affects typing speed
                fatigue_factor = 1.0 + (self.metrics.fatigue_level * 0.5)
                
                # Calculate delay based on key distance (simplified)
                delay = base_delay * fatigue_factor
                
                # Different delays for different character types
                if char.isupper():
                    delay *= random.uniform(1.2, 1.5)  # Shift key coordination
                elif char in '!@#$%^&*()_+':
                    delay *= random.uniform(1.3, 1.8)  # Special characters take longer
                elif char == ' ':
                    delay *= random.uniform(0.8, 1.0)  # Space bar is fast
                
                # Thinking pauses
                if char in '.!?' or (i > 0 and text[i-1] == ' ' and random.random() < 0.15):
                    delay += random.uniform(0.3, 1.2) * (1 + self.metrics.focus_level)
                
                # Typos based on fatigue and error rate
                if random.random() < self.metrics.error_rate * (1 + self.metrics.fatigue_level):
                    # Common typo patterns
                    typo_patterns = {
                        'a': 's', 's': 'a', 'd': 'f', 'f': 'd',
                        'g': 'h', 'h': 'g', 'j': 'k', 'k': 'j',
                        'i': 'o', 'o': 'i', 'n': 'm', 'm': 'n'
                    }
                    
                    if char.lower() in typo_patterns and random.random() < 0.7:
                        # Adjacent key typo
                        wrong_char = typo_patterns[char.lower()]
                        if char.isupper():
                            wrong_char = wrong_char.upper()
                    else:
                        # Random typo
                        wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                    
                    await page.keyboard.type(wrong_char)
                    await asyncio.sleep(random.uniform(0.1, 0.4))  # Recognition delay
                    
                    # Correction
                    await page.keyboard.press('Backspace')
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                
                # Type the character
                await page.keyboard.type(char)
                
                # Add delay with natural variation
                await asyncio.sleep(delay + random.gauss(0, delay * 0.15))
                
                # Record typing rhythm
                self.typing_rhythm.append(delay)
                if len(self.typing_rhythm) > 100:
                    self.typing_rhythm = self.typing_rhythm[-50:]
                
                i += 1
        
        # Update metrics
        self.action_count += len(text)
        self._update_fatigue()
    
    async def human_scroll(
        self,
        page: Page,
        direction: str = "down",
        amount: int = None
    ) -> None:
        """Scroll page with human-like pattern."""
        if amount is None:
            amount = random.randint(100, 500)
        
        # Scroll in small increments
        increments = random.randint(3, 8)
        for _ in range(increments):
            scroll_amount = amount // increments + random.randint(-20, 20)
            
            if direction == "down":
                await page.mouse.wheel(0, scroll_amount)
            else:
                await page.mouse.wheel(0, -scroll_amount)
            
            await asyncio.sleep(random.uniform(0.05, 0.15))
    
    async def random_mouse_movement(self, page: Page) -> None:
        """Add random mouse movements to simulate reading/thinking."""
        viewport = await page.viewport_size()
        if not viewport:
            return
        
        movements = random.randint(2, 5)
        for _ in range(movements):
            x = random.randint(100, viewport['width'] - 100)
            y = random.randint(100, viewport['height'] - 100)
            
            current_pos = await page.evaluate("() => ({ x: window.mouseX || 0, y: window.mouseY || 0 })")
            await self.move_mouse_naturally(
                page,
                (current_pos['x'], current_pos['y']),
                (x, y)
            )
            
            await asyncio.sleep(random.uniform(0.5, 2.0))
    
    async def reading_pattern(self, page: Page, duration: float = 3.0) -> None:
        """Advanced reading simulation with multiple patterns."""
        start_time = time.time()
        viewport = await page.viewport_size()
        if not viewport:
            return
        
        # Select reading pattern based on content type
        patterns = ['f_pattern', 'z_pattern', 'layer_cake', 'spotted']
        pattern = random.choice(patterns)
        
        while time.time() - start_time < duration:
            if pattern == 'f_pattern':
                # F-pattern: scan across top, then down left side
                # Top horizontal scan
                for x in range(100, viewport['width'] - 100, 50):
                    await page.mouse.move(x, 150)
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                
                # Vertical scan down left
                for y in range(150, min(viewport['height'] - 100, 600), 30):
                    await page.mouse.move(150, y)
                    await asyncio.sleep(random.uniform(0.05, 0.1))
                
                # Occasional horizontal scans
                if random.random() < 0.4:
                    y_pos = random.randint(200, min(400, viewport['height'] - 100))
                    for x in range(150, viewport['width'] // 2, 40):
                        await page.mouse.move(x, y_pos)
                        await asyncio.sleep(random.uniform(0.03, 0.08))
            
            elif pattern == 'z_pattern':
                # Z-pattern: top left to right, diagonal to bottom left, then right
                await self.move_mouse_naturally(page, (100, 100), (viewport['width'] - 100, 100))
                await asyncio.sleep(random.uniform(0.2, 0.4))
                
                await self.move_mouse_naturally(page, 
                    (viewport['width'] - 100, 100), 
                    (100, min(viewport['height'] - 100, 500)))
                await asyncio.sleep(random.uniform(0.2, 0.4))
                
                await self.move_mouse_naturally(page,
                    (100, min(viewport['height'] - 100, 500)),
                    (viewport['width'] - 100, min(viewport['height'] - 100, 500)))
            
            elif pattern == 'layer_cake':
                # Layer cake: read in horizontal bands
                band_height = 150
                current_y = 150
                
                while current_y < min(viewport['height'] - 100, 600):
                    # Scan across
                    direction = 1 if random.random() > 0.5 else -1
                    start_x = 100 if direction == 1 else viewport['width'] - 100
                    end_x = viewport['width'] - 100 if direction == 1 else 100
                    
                    for x in range(start_x, end_x, 30 * direction):
                        await page.mouse.move(x, current_y)
                        await asyncio.sleep(random.uniform(0.02, 0.06))
                    
                    current_y += band_height + random.randint(-20, 20)
            
            else:  # spotted pattern
                # Jump to points of interest
                interest_points = random.randint(3, 6)
                for _ in range(interest_points):
                    x = random.randint(100, viewport['width'] - 100)
                    y = random.randint(100, min(viewport['height'] - 100, 600))
                    
                    current_pos = await page.evaluate("() => ({ x: window.mouseX || 0, y: window.mouseY || 0 })")
                    await self.move_mouse_naturally(page, 
                        (current_pos['x'], current_pos['y']), (x, y))
                    
                    # Dwell time (fixation)
                    await asyncio.sleep(random.uniform(0.2, 0.8) * self.metrics.attention_span)
            
            # Natural scrolling
            if random.random() < 0.7:
                scroll_amount = random.randint(50, 200)
                await self.human_scroll(page, "down", scroll_amount)
            
            # Attention drift
            if random.random() < (0.2 / self.metrics.focus_level):
                await self.random_mouse_movement(page)
            
            # Micro-breaks in reading
            if random.random() < 0.1:
                await asyncio.sleep(random.uniform(1, 3))
    
    async def click_with_hesitation(
        self,
        page: Page,
        element: ElementHandle,
        hesitation: float = 0.5
    ) -> None:
        """Click element with natural hesitation."""
        # Move to element area first
        box = await element.bounding_box()
        if not box:
            await element.click()
            return
        
        # Target slightly off-center
        target_x = box['x'] + box['width'] * (0.3 + random.random() * 0.4)
        target_y = box['y'] + box['height'] * (0.3 + random.random() * 0.4)
        
        # Move mouse naturally
        current_pos = await page.evaluate("() => ({ x: window.mouseX || 0, y: window.mouseY || 0 })")
        await self.move_mouse_naturally(
            page,
            (current_pos['x'], current_pos['y']),
            (target_x, target_y)
        )
        
        # Hesitate before clicking
        await asyncio.sleep(hesitation + random.uniform(-0.2, 0.5))
        
        # Click
        await page.mouse.click(target_x, target_y)
    
    def is_active(self, page: Page) -> bool:
        """Check if human behavior is active for this page."""
        return self.behavior_profile is not None
    
    def _update_fatigue(self) -> None:
        """Update fatigue level based on activity."""
        current_time = time.time()
        session_duration = (current_time - self.session_start) / 60  # Minutes
        
        # Fatigue increases over time
        base_fatigue = min(session_duration / 60, 0.8)  # Max 0.8 after 1 hour
        
        # Actions increase fatigue
        action_fatigue = min(self.action_count / 1000, 0.3)
        
        # Breaks reduce fatigue
        time_since_break = (current_time - self.metrics.last_break_time) / 60
        break_factor = max(0, 1 - (time_since_break / 30))  # 30 min break cycle
        
        self.metrics.fatigue_level = base_fatigue + action_fatigue - (break_factor * 0.3)
        self.metrics.fatigue_level = max(0, min(1, self.metrics.fatigue_level))
        
        # Update other metrics based on fatigue
        self.metrics.mouse_speed = 1.0 - (self.metrics.fatigue_level * 0.3)
        self.metrics.error_rate = 0.02 + (self.metrics.fatigue_level * 0.03)
        self.metrics.attention_span = 1.0 - (self.metrics.fatigue_level * 0.4)
        
        # Take a break if too fatigued
        if self.metrics.fatigue_level > 0.7 and time_since_break > 15:
            self.metrics.last_break_time = current_time
            self.metrics.actions_since_break = 0
    
    async def simulate_micro_break(self, page: Page) -> None:
        """Simulate a micro-break in activity."""
        # Move mouse to rest position
        viewport = await page.viewport_size()
        if viewport:
            rest_x = random.choice([50, viewport['width'] - 50])
            rest_y = random.randint(viewport['height'] // 2, viewport['height'] - 100)
            
            current_pos = await page.evaluate("() => ({ x: window.mouseX || 0, y: window.mouseY || 0 })")
            await self.move_mouse_naturally(page, 
                (current_pos['x'], current_pos['y']), (rest_x, rest_y))
        
        # Pause
        break_duration = random.uniform(2, 8)
        await asyncio.sleep(break_duration)
        
        # Update metrics
        self.metrics.last_break_time = time.time()
        self.metrics.fatigue_level *= 0.9  # Slight recovery
    
    async def attention_shift(self, page: Page, target_area: Dict[str, int]) -> None:
        """Simulate attention shift to a specific area."""
        # Look around target area with saccadic movements
        base_x, base_y = target_area['x'], target_area['y']
        width, height = target_area.get('width', 100), target_area.get('height', 100)
        
        # Multiple quick glances
        for _ in range(random.randint(2, 4)):
            offset_x = random.randint(-width//4, width//4)
            offset_y = random.randint(-height//4, height//4)
            
            current_pos = await page.evaluate("() => ({ x: window.mouseX || 0, y: window.mouseY || 0 })")
            await self.move_mouse_naturally(page,
                (current_pos['x'], current_pos['y']),
                (base_x + offset_x, base_y + offset_y),
                steps=10)  # Quick movement
            
            # Fixation time
            await asyncio.sleep(random.uniform(0.1, 0.3) * self.metrics.attention_span)
    
    def adapt_behavior(self, detection_score: float) -> None:
        """Adapt behavior based on detection risk."""
        if detection_score > 0.7:
            # High risk - become more cautious
            self.behavior_profile = BehaviorProfile.CAUTIOUS
            self.metrics.mouse_speed *= 0.8
            self.metrics.typing_speed_wpm *= 0.85
        elif detection_score < 0.3:
            # Low risk - can be more aggressive
            self.behavior_profile = BehaviorProfile.AGGRESSIVE
            self.metrics.mouse_speed *= 1.1
            self.metrics.typing_speed_wpm *= 1.05
        else:
            # Normal behavior
            self.behavior_profile = BehaviorProfile.NORMAL