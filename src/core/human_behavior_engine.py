"""
StealthMaster AI v3.0 - Human Behavior Engine
Simulates realistic human browsing patterns based on behavioral psychology
"""

import asyncio
import random
import math
import time
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from playwright.async_api import Page, BrowserContext
import logging

logger = logging.getLogger(__name__)


class PersonalityType(Enum):
    """Different user personality types for browsing behavior"""
    EAGER = "eager"  # Quick, direct, minimal hesitation
    METHODICAL = "methodical"  # Careful, reads everything, double-checks
    CAUTIOUS = "cautious"  # Slow, lots of hesitation, backs out often
    EXPERIENCED = "experienced"  # Fast but natural, knows the site
    DISTRACTED = "distracted"  # Intermittent attention, long pauses


@dataclass
class BehaviorProfile:
    """Profile defining specific behavior characteristics"""
    personality: PersonalityType
    
    # Timing characteristics (in seconds)
    min_read_time: float = 1.0
    max_read_time: float = 5.0
    
    # Mouse movement
    mouse_speed: float = 1.0  # Multiplier
    mouse_jitter: float = 0.1  # Amount of imprecision
    scroll_speed: float = 1.0
    
    # Decision making
    hesitation_probability: float = 0.3
    hesitation_duration: Tuple[float, float] = (0.5, 2.0)
    
    # Attention patterns
    focus_duration: Tuple[float, float] = (30.0, 180.0)
    distraction_probability: float = 0.1
    distraction_duration: Tuple[float, float] = (5.0, 30.0)
    
    # Interaction patterns
    double_click_probability: float = 0.05
    misclick_probability: float = 0.02
    hover_probability: float = 0.4
    
    @classmethod
    def create_profile(cls, personality: PersonalityType) -> 'BehaviorProfile':
        """Factory method to create personality-specific profiles"""
        
        profiles = {
            PersonalityType.EAGER: cls(
                personality=PersonalityType.EAGER,
                min_read_time=0.5,
                max_read_time=2.0,
                mouse_speed=1.5,
                mouse_jitter=0.05,
                scroll_speed=1.5,
                hesitation_probability=0.1,
                hesitation_duration=(0.2, 0.8),
                focus_duration=(20.0, 60.0),
                distraction_probability=0.05,
                distraction_duration=(2.0, 10.0),
                double_click_probability=0.08,
                misclick_probability=0.01,
                hover_probability=0.2
            ),
            
            PersonalityType.METHODICAL: cls(
                personality=PersonalityType.METHODICAL,
                min_read_time=2.0,
                max_read_time=8.0,
                mouse_speed=0.8,
                mouse_jitter=0.05,
                scroll_speed=0.7,
                hesitation_probability=0.5,
                hesitation_duration=(1.0, 3.0),
                focus_duration=(60.0, 300.0),
                distraction_probability=0.02,
                distraction_duration=(5.0, 15.0),
                double_click_probability=0.02,
                misclick_probability=0.01,
                hover_probability=0.6
            ),
            
            PersonalityType.CAUTIOUS: cls(
                personality=PersonalityType.CAUTIOUS,
                min_read_time=3.0,
                max_read_time=10.0,
                mouse_speed=0.6,
                mouse_jitter=0.15,
                scroll_speed=0.5,
                hesitation_probability=0.7,
                hesitation_duration=(2.0, 5.0),
                focus_duration=(30.0, 120.0),
                distraction_probability=0.15,
                distraction_duration=(10.0, 45.0),
                double_click_probability=0.1,
                misclick_probability=0.05,
                hover_probability=0.7
            ),
            
            PersonalityType.EXPERIENCED: cls(
                personality=PersonalityType.EXPERIENCED,
                min_read_time=0.3,
                max_read_time=1.5,
                mouse_speed=2.0,
                mouse_jitter=0.02,
                scroll_speed=2.0,
                hesitation_probability=0.05,
                hesitation_duration=(0.1, 0.5),
                focus_duration=(60.0, 600.0),
                distraction_probability=0.01,
                distraction_duration=(5.0, 10.0),
                double_click_probability=0.01,
                misclick_probability=0.005,
                hover_probability=0.1
            ),
            
            PersonalityType.DISTRACTED: cls(
                personality=PersonalityType.DISTRACTED,
                min_read_time=1.0,
                max_read_time=15.0,
                mouse_speed=1.0,
                mouse_jitter=0.2,
                scroll_speed=0.8,
                hesitation_probability=0.4,
                hesitation_duration=(1.0, 10.0),
                focus_duration=(10.0, 60.0),
                distraction_probability=0.3,
                distraction_duration=(30.0, 300.0),
                double_click_probability=0.15,
                misclick_probability=0.08,
                hover_probability=0.5
            )
        }
        
        return profiles[personality]


class HumanBehaviorEngine:
    """
    Advanced human behavior simulation engine
    Uses behavioral psychology principles to create realistic interactions
    """
    
    def __init__(self, personality: Optional[PersonalityType] = None):
        # Select random personality if not specified
        self.personality = personality or random.choice(list(PersonalityType))
        self.profile = BehaviorProfile.create_profile(self.personality)
        
        # Session state
        self.session_start = datetime.now()
        self.last_action_time = datetime.now()
        self.fatigue_level = 0.0
        self.focus_level = 1.0
        self.action_count = 0
        
        # Movement history for natural patterns
        self.mouse_history: List[Tuple[float, float]] = []
        self.scroll_position = 0
        
        logger.info(f"Initialized human behavior engine with {self.personality.value} personality")
        
    def _calculate_fatigue(self) -> float:
        """Calculate current fatigue level based on session duration"""
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        # Fatigue increases over time (sigmoid curve)
        fatigue = 1 / (1 + math.exp(-0.001 * (session_duration - 1800)))  # 30 min midpoint
        
        # Add random fluctuations
        fatigue += random.gauss(0, 0.05)
        
        return max(0, min(1, fatigue))
        
    def _apply_fatigue_modifier(self, base_value: float) -> float:
        """Apply fatigue effects to timing/precision"""
        fatigue = self._calculate_fatigue()
        
        # Fatigue makes everything slower and less precise
        modifier = 1 + (fatigue * 0.5)  # Up to 50% slower when tired
        
        return base_value * modifier
        
    async def wait_human_duration(self, min_duration: float, max_duration: float) -> None:
        """Wait for a human-like duration with natural distribution"""
        # Use log-normal distribution for more realistic timing
        mean = (min_duration + max_duration) / 2
        std_dev = (max_duration - min_duration) / 4
        
        duration = np.random.lognormal(
            mean=np.log(mean),
            sigma=std_dev / mean
        )
        
        # Apply fatigue
        duration = self._apply_fatigue_modifier(duration)
        
        # Ensure within bounds
        duration = max(min_duration, min(max_duration, duration))
        
        await asyncio.sleep(duration)
        
    async def read_page_section(self, page: Page, selector: str) -> None:
        """Simulate reading a section of the page"""
        try:
            element = await page.query_selector(selector)
            if not element:
                return
                
            # Get element text for reading time calculation
            text_content = await element.text_content() or ""
            word_count = len(text_content.split())
            
            # Calculate reading time (average 250 words per minute)
            base_read_time = (word_count / 250) * 60
            
            # Apply personality modifiers
            read_time = base_read_time * random.uniform(
                self.profile.min_read_time / 2,
                self.profile.max_read_time / 2
            )
            
            # Ensure minimum read time
            read_time = max(self.profile.min_read_time, read_time)
            
            # Simulate eye movement while reading
            bbox = await element.bounding_box()
            if bbox:
                await self._simulate_reading_pattern(page, bbox, read_time)
            else:
                await self.wait_human_duration(read_time * 0.8, read_time * 1.2)
                
        except Exception as e:
            logger.debug(f"Error reading page section: {e}")
            
    async def _simulate_reading_pattern(self, page: Page, bbox: Dict, duration: float) -> None:
        """Simulate natural eye movement patterns while reading"""
        start_time = time.time()
        
        # Starting position (top-left of text)
        current_x = bbox['x'] + 20
        current_y = bbox['y'] + 10
        
        # Simulate scanning lines of text
        line_height = 20  # Approximate line height
        scan_speed = 200  # Pixels per second
        
        while time.time() - start_time < duration:
            # Move across the line
            end_x = bbox['x'] + bbox['width'] - 20
            
            # Add natural saccades (quick eye movements)
            steps = int((end_x - current_x) / 50)
            for _ in range(max(1, steps)):
                next_x = min(current_x + random.uniform(40, 60), end_x)
                next_y = current_y + random.gauss(0, 2)  # Slight vertical variation
                
                await self.move_mouse_naturally(page, (current_x, current_y), (next_x, next_y))
                current_x = next_x
                
                # Fixation pause
                await self.wait_human_duration(0.1, 0.3)
                
            # Move to next line
            current_x = bbox['x'] + 20
            current_y = min(current_y + line_height, bbox['y'] + bbox['height'] - 10)
            
            # Check if we've read the whole area
            if current_y >= bbox['y'] + bbox['height'] - 20:
                break
                
    async def move_mouse_naturally(
        self, 
        page: Page, 
        start: Tuple[float, float], 
        end: Tuple[float, float]
    ) -> None:
        """Move mouse with natural human-like curve"""
        
        # Calculate distance
        distance = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        
        if distance < 5:  # Very short movement
            await page.mouse.move(end[0], end[1])
            return
            
        # Use Bézier curve for natural movement
        control_points = self._generate_bezier_curve(start, end)
        
        # Calculate duration based on distance and speed
        base_duration = distance / (300 * self.profile.mouse_speed)  # 300 pixels/second base
        duration = self._apply_fatigue_modifier(base_duration)
        
        # Number of steps
        steps = max(3, int(distance / 10))
        
        # Move along the curve
        for i in range(steps + 1):
            t = i / steps
            point = self._calculate_bezier_point(control_points, t)
            
            # Add jitter
            jittered_point = (
                point[0] + random.gauss(0, self.profile.mouse_jitter * 5),
                point[1] + random.gauss(0, self.profile.mouse_jitter * 5)
            )
            
            await page.mouse.move(jittered_point[0], jittered_point[1])
            
            # Varying speed (slower at start and end)
            speed_modifier = 1 - (2 * abs(t - 0.5))  # Parabolic speed curve
            step_duration = (duration / steps) * (0.5 + speed_modifier)
            await asyncio.sleep(step_duration)
            
        # Ensure we end at the exact position
        await page.mouse.move(end[0], end[1])
        
        # Update history
        self.mouse_history.append(end)
        if len(self.mouse_history) > 100:
            self.mouse_history.pop(0)
            
    def _generate_bezier_curve(
        self, 
        start: Tuple[float, float], 
        end: Tuple[float, float]
    ) -> List[Tuple[float, float]]:
        """Generate control points for a natural Bézier curve"""
        
        # Calculate curve deviation based on distance
        distance = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        max_deviation = min(distance * 0.3, 100)  # Max 30% deviation or 100px
        
        # Generate two control points
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        
        # Add controlled randomness
        control1 = (
            mid_x + random.gauss(0, max_deviation / 2),
            mid_y + random.gauss(0, max_deviation / 2)
        )
        
        control2 = (
            mid_x + random.gauss(0, max_deviation / 2),
            mid_y + random.gauss(0, max_deviation / 2)
        )
        
        return [start, control1, control2, end]
        
    def _calculate_bezier_point(
        self, 
        points: List[Tuple[float, float]], 
        t: float
    ) -> Tuple[float, float]:
        """Calculate point on Bézier curve at parameter t"""
        
        n = len(points) - 1
        x = 0
        y = 0
        
        for i, (px, py) in enumerate(points):
            # Bernstein polynomial
            b = math.comb(n, i) * (t ** i) * ((1 - t) ** (n - i))
            x += px * b
            y += py * b
            
        return (x, y)
        
    async def hover_element(self, page: Page, selector: str) -> None:
        """Hover over element with natural movement"""
        
        if random.random() > self.profile.hover_probability:
            return
            
        try:
            element = await page.query_selector(selector)
            if not element:
                return
                
            bbox = await element.bounding_box()
            if not bbox:
                return
                
            # Target a natural point within the element
            target_x = bbox['x'] + bbox['width'] * random.uniform(0.3, 0.7)
            target_y = bbox['y'] + bbox['height'] * random.uniform(0.3, 0.7)
            
            # Get current position
            current_pos = self.mouse_history[-1] if self.mouse_history else (100, 100)
            
            # Move to element
            await self.move_mouse_naturally(page, current_pos, (target_x, target_y))
            
            # Hover duration
            await self.wait_human_duration(0.5, 2.0)
            
        except Exception as e:
            logger.debug(f"Error hovering element: {e}")
            
    async def click_element(self, page: Page, selector: str) -> None:
        """Click element with human-like behavior"""
        
        try:
            element = await page.wait_for_selector(selector, timeout=5000)
            if not element:
                return
                
            # Check for hesitation
            if random.random() < self.profile.hesitation_probability:
                await self.wait_human_duration(*self.profile.hesitation_duration)
                
            # Hover first (natural behavior)
            await self.hover_element(page, selector)
            
            # Misclick simulation
            if random.random() < self.profile.misclick_probability:
                # Click near the element
                bbox = await element.bounding_box()
                if bbox:
                    miss_x = bbox['x'] + random.choice([-20, bbox['width'] + 20])
                    miss_y = bbox['y'] + bbox['height'] / 2
                    await page.mouse.click(miss_x, miss_y)
                    await self.wait_human_duration(0.5, 1.0)
                    
            # Actual click
            await element.click()
            
            # Double click simulation
            if random.random() < self.profile.double_click_probability:
                await self.wait_human_duration(0.1, 0.3)
                await element.click()
                
            self.action_count += 1
            self.last_action_time = datetime.now()
            
        except Exception as e:
            logger.debug(f"Error clicking element: {e}")
            
    async def type_text(self, page: Page, selector: str, text: str) -> None:
        """Type text with human-like patterns"""
        
        try:
            element = await page.wait_for_selector(selector, timeout=5000)
            if not element:
                return
                
            # Click to focus
            await self.click_element(page, selector)
            await self.wait_human_duration(0.2, 0.5)
            
            # Clear existing text naturally
            await page.keyboard.press('Control+a')
            await self.wait_human_duration(0.1, 0.2)
            await page.keyboard.press('Delete')
            await self.wait_human_duration(0.2, 0.4)
            
            # Type character by character
            for char in text:
                # Typing speed with variation
                base_delay = 0.1 / self.profile.mouse_speed  # Faster typers have faster mouse too
                delay = random.gauss(base_delay, base_delay * 0.3)
                delay = max(0.05, self._apply_fatigue_modifier(delay))
                
                await page.keyboard.type(char)
                await asyncio.sleep(delay)
                
                # Occasional typos for realism
                if random.random() < 0.02:  # 2% typo rate
                    # Type wrong character
                    wrong_char = random.choice('asdfghjkl')
                    await page.keyboard.type(wrong_char)
                    await self.wait_human_duration(0.2, 0.5)
                    # Backspace
                    await page.keyboard.press('Backspace')
                    await self.wait_human_duration(0.1, 0.3)
                    
        except Exception as e:
            logger.debug(f"Error typing text: {e}")
            
    async def scroll_page(self, page: Page, direction: str = "down", amount: Optional[int] = None) -> None:
        """Scroll page with natural patterns"""
        
        if amount is None:
            amount = random.randint(100, 500)
            
        # Apply personality scroll speed
        amount = int(amount * self.profile.scroll_speed)
        
        # Smooth scrolling with momentum
        steps = random.randint(3, 8)
        for i in range(steps):
            # Easing function (deceleration)
            progress = (i + 1) / steps
            ease = 1 - (1 - progress) ** 2  # Quadratic ease-out
            
            step_amount = int((amount / steps) * ease)
            
            if direction == "down":
                await page.mouse.wheel(0, step_amount)
            else:
                await page.mouse.wheel(0, -step_amount)
                
            await self.wait_human_duration(0.05, 0.15)
            
        self.scroll_position += amount if direction == "down" else -amount
        
    async def simulate_distraction(self) -> None:
        """Simulate user getting distracted"""
        
        if random.random() < self.profile.distraction_probability:
            duration = random.uniform(*self.profile.distraction_duration)
            logger.debug(f"Simulating distraction for {duration:.1f} seconds")
            await asyncio.sleep(duration)
            
    async def check_element_before_action(self, page: Page, selector: str) -> bool:
        """Human-like element checking before interaction"""
        
        try:
            # Natural pause to "look for" element
            await self.wait_human_duration(0.2, 0.8)
            
            # Check if element exists
            element = await page.query_selector(selector)
            if not element:
                # Confusion behavior - scroll around looking for it
                await self.scroll_page(page, "down", 200)
                await self.wait_human_duration(0.5, 1.0)
                await self.scroll_page(page, "up", 200)
                return False
                
            # Check if visible
            is_visible = await element.is_visible()
            if not is_visible:
                # Try scrolling to element
                await element.scroll_into_view_if_needed()
                await self.wait_human_duration(0.3, 0.6)
                
            return True
            
        except Exception:
            return False
            
    def get_session_duration(self) -> float:
        """Get current session duration in seconds"""
        return (datetime.now() - self.session_start).total_seconds()
        
    def should_take_break(self) -> bool:
        """Determine if user should take a break"""
        session_duration = self.get_session_duration()
        
        # Personality-based break patterns
        break_intervals = {
            PersonalityType.EAGER: 3600,  # 1 hour
            PersonalityType.METHODICAL: 2400,  # 40 minutes
            PersonalityType.CAUTIOUS: 1800,  # 30 minutes
            PersonalityType.EXPERIENCED: 5400,  # 1.5 hours
            PersonalityType.DISTRACTED: 900,  # 15 minutes
        }
        
        interval = break_intervals[self.personality]
        
        # Add some randomness
        if session_duration > interval * random.uniform(0.8, 1.2):
            return True
            
        return False
        
    async def take_break(self) -> None:
        """Simulate user taking a break"""
        
        # Break duration based on personality
        break_durations = {
            PersonalityType.EAGER: (60, 180),  # 1-3 minutes
            PersonalityType.METHODICAL: (180, 600),  # 3-10 minutes
            PersonalityType.CAUTIOUS: (300, 900),  # 5-15 minutes
            PersonalityType.EXPERIENCED: (120, 300),  # 2-5 minutes
            PersonalityType.DISTRACTED: (600, 1800),  # 10-30 minutes
        }
        
        duration = random.uniform(*break_durations[self.personality])
        logger.info(f"Taking a break for {duration/60:.1f} minutes")
        
        await asyncio.sleep(duration)
        
        # Reset fatigue after break
        self.fatigue_level = max(0, self.fatigue_level - 0.5)
        
    def get_behavior_stats(self) -> Dict[str, Any]:
        """Get current behavior statistics"""
        
        return {
            'personality': self.personality.value,
            'session_duration': self.get_session_duration(),
            'fatigue_level': self._calculate_fatigue(),
            'action_count': self.action_count,
            'avg_actions_per_minute': self.action_count / max(1, self.get_session_duration() / 60),
            'time_since_last_action': (datetime.now() - self.last_action_time).total_seconds()
        }