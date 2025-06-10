# stealthmaster/stealth/behaviors.py
"""Human behavior simulation for anti-detection."""

import asyncio
import random
import math
from typing import Tuple, List, Optional
from playwright.async_api import Page, ElementHandle
import logging

logger = logging.getLogger(__name__)


from .ml_resistant_behaviors import MLResistantBehaviors, BehaviorProfile


class HumanBehavior:
    """Simulates human-like behavior patterns with ML resistance."""
    
    def __init__(self):
        """Initialize behavior simulator."""
        self.last_action_time = 0
        self.action_count = 0
        # Use ML-resistant behaviors
        self.ml_behaviors = MLResistantBehaviors(BehaviorProfile.NORMAL)
    
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
        steps: int = 20
    ) -> None:
        """Move mouse with natural curve."""
        x1, y1 = start
        x2, y2 = end
        
        # Generate control points for bezier curve
        ctrl_x = (x1 + x2) / 2 + random.randint(-50, 50)
        ctrl_y = (y1 + y2) / 2 + random.randint(-50, 50)
        
        for i in range(steps):
            t = i / steps
            # Quadratic bezier curve
            x = (1-t)**2 * x1 + 2*(1-t)*t * ctrl_x + t**2 * x2
            y = (1-t)**2 * y1 + 2*(1-t)*t * ctrl_y + t**2 * y2
            
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.005, 0.015))
    
    async def human_type(
        self,
        page: Page,
        text: str,
        element: Optional[ElementHandle] = None
    ) -> None:
        """Type text with human-like delays and occasional corrections."""
        if element:
            await element.click()
        
        for char in text:
            await page.keyboard.type(char)
            
            # Variable typing speed
            base_delay = random.uniform(0.05, 0.15)
            
            # Occasionally pause longer (thinking)
            if random.random() < 0.1:
                base_delay += random.uniform(0.3, 0.8)
            
            # Simulate typos and corrections occasionally
            if random.random() < 0.02 and len(text) > 5:
                # Make a typo
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                await page.keyboard.type(wrong_char)
                await asyncio.sleep(random.uniform(0.1, 0.3))
                # Delete it
                await page.keyboard.press('Backspace')
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            await asyncio.sleep(base_delay)
    
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
        """Simulate reading behavior with eye movement patterns."""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < duration:
            # Simulate F-pattern reading
            await self.human_scroll(page, "down", random.randint(50, 150))
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Occasional mouse movement
            if random.random() < 0.3:
                await self.random_mouse_movement(page)
    
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
        # For now, return True as behaviors are applied on demand
        return True