"""
Browser Warmup Engine for Akamai Bot Detection Bypass

Implements proper browser warmup sequences to establish trust scores
before making actual requests. Critical for bypassing Akamai's initial
detection mechanisms.
"""

import asyncio
import random
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WarmupSequence:
    """Defines a warmup sequence for a specific platform"""
    platform: str
    steps: List[Dict[str, Any]]
    min_duration: float  # Minimum time in seconds
    sensor_collection_urls: List[str]
    

class BrowserWarmupEngine:
    """
    Handles browser warmup to establish trust with Akamai Bot Manager
    
    Key insights from 2025 research:
    - Akamai detects bots heavily on first request
    - Sensor data collection happens early
    - Trust score builds over multiple interactions
    - _abck cookie is critical for session validation
    """
    
    def __init__(self):
        """Initialize warmup engine"""
        self.warmup_sequences = self._init_warmup_sequences()
        self.sensor_data_collected: Dict[str, bool] = {}
        self.trust_scores: Dict[str, float] = {}
        
    def _init_warmup_sequences(self) -> Dict[str, WarmupSequence]:
        """Initialize platform-specific warmup sequences"""
        return {
            'fansale': WarmupSequence(
                platform='fansale',
                steps=[
                    {
                        'action': 'navigate',
                        'url': 'https://www.fansale.de/',
                        'wait': 3.0,
                        'description': 'Load homepage for initial sensor collection'
                    },
                    {
                        'action': 'mouse_movement',
                        'duration': 2.0,
                        'description': 'Natural mouse movements to generate telemetry'
                    },
                    {
                        'action': 'scroll',
                        'direction': 'down',
                        'amount': 300,
                        'description': 'Scroll to trigger viewport events'
                    },
                    {
                        'action': 'wait_for_sensor',
                        'timeout': 5.0,
                        'description': 'Wait for _abck cookie generation'
                    },
                    {
                        'action': 'navigate',
                        'url': 'https://www.fansale.de/fansale/tickets',
                        'wait': 2.0,
                        'description': 'Navigate to tickets section'
                    },
                    {
                        'action': 'interact',
                        'duration': 3.0,
                        'description': 'Interact with page elements'
                    }
                ],
                min_duration=15.0,
                sensor_collection_urls=[
                    'https://www.fansale.de/',
                    'https://www.fansale.de/fansale/'
                ]
            ),
            'ticketmaster': WarmupSequence(
                platform='ticketmaster',
                steps=[
                    {
                        'action': 'navigate',
                        'url': 'https://www.ticketmaster.com/',
                        'wait': 4.0,
                        'description': 'Load homepage with extended wait'
                    },
                    {
                        'action': 'mouse_movement',
                        'duration': 3.0,
                        'description': 'Extended mouse telemetry collection'
                    },
                    {
                        'action': 'click_random',
                        'selector': 'a[href*="browse"]',
                        'description': 'Click browse link'
                    },
                    {
                        'action': 'wait_for_sensor',
                        'timeout': 8.0,
                        'description': 'Extended sensor wait for strict platform'
                    },
                    {
                        'action': 'scroll',
                        'direction': 'down',
                        'amount': 500,
                        'description': 'Deep scroll for behavior analysis'
                    },
                    {
                        'action': 'interact',
                        'duration': 5.0,
                        'description': 'Extended interaction phase'
                    }
                ],
                min_duration=25.0,  # Ticketmaster needs longer warmup
                sensor_collection_urls=[
                    'https://www.ticketmaster.com/',
                    'https://www.ticketmaster.com/browse'
                ]
            ),
            'vivaticket': WarmupSequence(
                platform='vivaticket',
                steps=[
                    {
                        'action': 'navigate',
                        'url': 'https://www.vivaticket.com/',
                        'wait': 2.5,
                        'description': 'Initial page load'
                    },
                    {
                        'action': 'mouse_movement',
                        'duration': 2.0,
                        'description': 'Basic telemetry generation'
                    },
                    {
                        'action': 'wait_for_sensor',
                        'timeout': 4.0,
                        'description': 'Wait for sensor data'
                    },
                    {
                        'action': 'interact',
                        'duration': 2.0,
                        'description': 'Light interaction'
                    }
                ],
                min_duration=12.0,
                sensor_collection_urls=[
                    'https://www.vivaticket.com/'
                ]
            )
        }
        
    async def warmup_browser(
        self,
        page,
        platform: str,
        behavior_engine=None
    ) -> Dict[str, Any]:
        """
        Execute warmup sequence for a platform
        
        Args:
            page: Browser page instance
            platform: Platform name
            behavior_engine: Optional human behavior simulator
            
        Returns:
            Warmup result with collected data
        """
        logger.info(f"Starting browser warmup for {platform}")
        
        sequence = self.warmup_sequences.get(platform)
        if not sequence:
            logger.warning(f"No warmup sequence for {platform}, using generic")
            sequence = self._get_generic_sequence(platform)
            
        start_time = time.time()
        collected_cookies = {}
        sensor_data_valid = False
        
        try:
            for i, step in enumerate(sequence.steps):
                logger.debug(f"Warmup step {i+1}/{len(sequence.steps)}: {step['description']}")
                
                if step['action'] == 'navigate':
                    await self._warmup_navigate(page, step['url'], step['wait'])
                    
                elif step['action'] == 'mouse_movement':
                    await self._warmup_mouse_movement(
                        page, step['duration'], behavior_engine
                    )
                    
                elif step['action'] == 'scroll':
                    await self._warmup_scroll(
                        page, step['direction'], step['amount'], behavior_engine
                    )
                    
                elif step['action'] == 'wait_for_sensor':
                    sensor_data_valid = await self._wait_for_sensor_data(
                        page, step['timeout']
                    )
                    
                elif step['action'] == 'click_random':
                    await self._warmup_click_random(
                        page, step.get('selector'), behavior_engine
                    )
                    
                elif step['action'] == 'interact':
                    await self._warmup_interact(
                        page, step['duration'], behavior_engine
                    )
                    
                # Collect cookies after each step
                cookies = await page.context.cookies()
                for cookie in cookies:
                    if cookie['name'] in ['_abck', 'ak_bmsc', 'bm_sv', 'bm_mi']:
                        collected_cookies[cookie['name']] = cookie['value']
                        
                # Random micro-delays between steps
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
            # Ensure minimum duration
            elapsed = time.time() - start_time
            if elapsed < sequence.min_duration:
                wait_time = sequence.min_duration - elapsed
                logger.debug(f"Additional warmup wait: {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                
            # Final validation
            has_abck = '_abck' in collected_cookies
            trust_score = self._calculate_trust_score(
                sensor_data_valid, has_abck, len(collected_cookies)
            )
            
            self.trust_scores[platform] = trust_score
            
            result = {
                'success': trust_score > 0.7,
                'trust_score': trust_score,
                'duration': time.time() - start_time,
                'cookies_collected': list(collected_cookies.keys()),
                'has_abck': has_abck,
                'sensor_data_valid': sensor_data_valid
            }
            
            logger.info(
                f"Warmup completed for {platform}: "
                f"trust_score={trust_score:.2f}, has_abck={has_abck}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Warmup failed for {platform}: {e}")
            return {
                'success': False,
                'trust_score': 0.0,
                'duration': time.time() - start_time,
                'error': str(e)
            }
            
    async def _warmup_navigate(self, page, url: str, wait_time: float) -> None:
        """Navigate to URL with proper waiting"""
        await page.goto(url, wait_until='domcontentloaded')
        
        # Wait for potential lazy-loaded sensor scripts
        await page.wait_for_load_state('networkidle')
        
        # Additional wait for sensor initialization
        await asyncio.sleep(wait_time)
        
    async def _warmup_mouse_movement(
        self,
        page,
        duration: float,
        behavior_engine=None
    ) -> None:
        """Generate natural mouse movements"""
        if behavior_engine:
            # Use advanced behavior engine
            start_time = time.time()
            while time.time() - start_time < duration:
                await behavior_engine.random_mouse_movement(page)
                await asyncio.sleep(random.uniform(0.5, 1.0))
        else:
            # Simple mouse movements
            viewport = page.viewport_size
            if viewport:
                movements = int(duration * 2)  # ~2 movements per second
                for _ in range(movements):
                    x = random.randint(100, viewport['width'] - 100)
                    y = random.randint(100, viewport['height'] - 100)
                    await page.mouse.move(x, y)
                    await asyncio.sleep(duration / movements)
                    
    async def _warmup_scroll(
        self,
        page,
        direction: str,
        amount: int,
        behavior_engine=None
    ) -> None:
        """Perform natural scrolling"""
        if behavior_engine:
            await behavior_engine.human_scroll(page, direction, amount)
        else:
            # Simple scroll
            if direction == 'down':
                await page.mouse.wheel(0, amount)
            else:
                await page.mouse.wheel(0, -amount)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
    async def _wait_for_sensor_data(self, page, timeout: float) -> bool:
        """Wait for Akamai sensor data collection"""
        try:
            # Check for _abck cookie generation
            start_time = time.time()
            while time.time() - start_time < timeout:
                cookies = await page.context.cookies()
                abck_cookie = next(
                    (c for c in cookies if c['name'] == '_abck'), None
                )
                
                if abck_cookie and len(abck_cookie['value']) > 100:
                    # Valid _abck cookies are typically long
                    logger.debug("Valid _abck cookie detected")
                    return True
                    
                await asyncio.sleep(0.5)
                
            logger.warning("Timeout waiting for sensor data")
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for sensor data: {e}")
            return False
            
    async def _warmup_click_random(
        self,
        page,
        selector: Optional[str],
        behavior_engine=None
    ) -> None:
        """Click random element matching selector"""
        try:
            if selector:
                elements = await page.query_selector_all(selector)
                if elements:
                    element = random.choice(elements)
                    if behavior_engine:
                        await behavior_engine.click_with_hesitation(
                            page, element, random.uniform(0.3, 0.8)
                        )
                    else:
                        await element.click()
                    await asyncio.sleep(random.uniform(1.0, 2.0))
        except Exception as e:
            logger.debug(f"Click failed (non-critical): {e}")
            
    async def _warmup_interact(
        self,
        page,
        duration: float,
        behavior_engine=None
    ) -> None:
        """General page interaction"""
        if behavior_engine:
            await behavior_engine.reading_pattern(page, duration)
        else:
            # Simple interactions
            start_time = time.time()
            while time.time() - start_time < duration:
                action = random.choice(['move', 'scroll', 'wait'])
                
                if action == 'move':
                    viewport = page.viewport_size
                    if viewport:
                        x = random.randint(100, viewport['width'] - 100)
                        y = random.randint(100, viewport['height'] - 100)
                        await page.mouse.move(x, y)
                        
                elif action == 'scroll':
                    await page.mouse.wheel(0, random.randint(50, 200))
                    
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
    def _calculate_trust_score(
        self,
        sensor_valid: bool,
        has_abck: bool,
        cookie_count: int
    ) -> float:
        """Calculate trust score based on warmup results"""
        score = 0.0
        
        # Sensor data is critical
        if sensor_valid:
            score += 0.5
            
        # _abck cookie is essential
        if has_abck:
            score += 0.3
            
        # Other cookies help
        if cookie_count >= 3:
            score += 0.2
        elif cookie_count >= 2:
            score += 0.1
            
        return min(1.0, score)
        
    def _get_generic_sequence(self, platform: str) -> WarmupSequence:
        """Get generic warmup sequence for unknown platforms"""
        return WarmupSequence(
            platform=platform,
            steps=[
                {
                    'action': 'navigate',
                    'url': f'https://www.{platform}.com/',
                    'wait': 2.0,
                    'description': 'Initial load'
                },
                {
                    'action': 'mouse_movement',
                    'duration': 2.0,
                    'description': 'Generate telemetry'
                },
                {
                    'action': 'wait_for_sensor',
                    'timeout': 5.0,
                    'description': 'Wait for sensors'
                }
            ],
            min_duration=10.0,
            sensor_collection_urls=[f'https://www.{platform}.com/']
        )
        
    def should_rewarm(self, platform: str, last_warmup: float) -> bool:
        """Check if browser needs re-warming"""
        # Re-warm if:
        # 1. Never warmed up
        if platform not in self.trust_scores:
            return True
            
        # 2. Low trust score
        if self.trust_scores[platform] < 0.5:
            return True
            
        # 3. Too much time passed (trust decay)
        time_since_warmup = time.time() - last_warmup
        if time_since_warmup > 1800:  # 30 minutes
            return True
            
        return False


# Global instance
browser_warmup_engine = BrowserWarmupEngine()