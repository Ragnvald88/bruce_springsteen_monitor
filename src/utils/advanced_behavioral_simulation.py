# src/utils/advanced_behavioral_simulation.py
# Advanced ML-Based Behavioral Biometrics for 2025 (Perfected & Reviewed Version)

import numpy as np
import asyncio
import random
import time
import math
from typing import Dict, List, Tuple, Optional, Any 
from dataclasses import dataclass, field
from playwright.async_api import Page # Using Page directly
import logging

# Module-level logger for functions outside classes or for general module info
module_logger = logging.getLogger(__name__)

@dataclass
class BiometricProfile:
    """Realistic human behavioral profile based on actual biometric data"""
    typing_speed_wpm: float = field(default_factory=lambda: random.uniform(40, 75))
    mouse_acceleration: float = field(default_factory=lambda: random.uniform(0.9, 2.2)) # Factor for mouse speed/steps
    scroll_velocity_preference: float = field(default_factory=lambda: random.uniform(350, 750)) # Approx pixels per scroll "action"
    click_dwell_time_ms: float = field(default_factory=lambda: random.uniform(60, 150)) # Time between mousedown and mouseup
    movement_jitter_factor: float = field(default_factory=lambda: random.uniform(0.03, 0.10)) # Affects mouse path precision
    pause_between_actions: float = field(default_factory=lambda: random.uniform(0.35, 1.6)) # Base pause in seconds
    reading_speed_wpm: float = field(default_factory=lambda: random.uniform(190, 330))
    attention_span_seconds: float = field(default_factory=lambda: random.uniform(12, 35)) # Average time before potential focus shift
    multitasking_tendency: float = field(default_factory=lambda: random.uniform(0.1, 0.5)) # Probability of engaging in a "distraction"
    fatigue_factor: float = 0.0  # Accumulates from 0 to 1 during a session
    stress_level: float = field(default_factory=lambda: random.uniform(0.05, 0.2)) # Affects timing, jitter, typo rate, from 0 to 1

    # Behavioral action count parameters, configurable per profile
    min_actions_low_intensity: int = field(default_factory=lambda: random.randint(1, 2))
    max_actions_low_intensity: int = field(default_factory=lambda: random.randint(2, 3))
    min_actions_medium_intensity: int = field(default_factory=lambda: random.randint(3, 4))
    max_actions_medium_intensity: int = field(default_factory=lambda: random.randint(4, 7))
    min_actions_high_intensity: int = field(default_factory=lambda: random.randint(5, 7))
    max_actions_high_intensity: int = field(default_factory=lambda: random.randint(8, 12))

class MouseDynamicsSimulator:
    def __init__(self, profile: Optional[BiometricProfile]):
        self.profile = profile if profile else BiometricProfile()
        self.logger = logging.getLogger(__name__ + ".MouseDynamicsSimulator")

    async def simulate_realistic_scroll(self, page: Page, amount_y: int, amount_x: int = 0) -> None:
        self.logger.debug(f"Simulating scroll by Y:{amount_y}px, X:{amount_x}px")
        if page.is_closed(): self.logger.warning("Scroll attempt on closed page."); return

        total_distance = math.sqrt(amount_y**2 + amount_x**2)
        if abs(total_distance) < 5: # Ignore tiny scrolls unless it's the only scroll
            if total_distance != 0: await page.mouse.wheel(float(amount_x), float(amount_y))
            return

        # Dynamic chunking based on scroll amount and profile's scroll velocity preference
        avg_scroll_chunk_size = max(50, self.profile.scroll_velocity_preference / random.uniform(3, 7)) # Min chunk size
        scroll_chunks = max(1, int(round(abs(total_distance) / avg_scroll_chunk_size)))
        scroll_chunks = min(scroll_chunks, 15) # Cap max chunks to prevent overly slow scrolls

        y_chunk_val = amount_y / scroll_chunks if scroll_chunks else float(amount_y)
        x_chunk_val = amount_x / scroll_chunks if scroll_chunks else float(amount_x)
        
        for i in range(scroll_chunks):
            if page.is_closed(): return
            # Add variation to each chunk's magnitude and slight directional jitter
            current_y_chunk = y_chunk_val * random.uniform(0.75, 1.25)
            current_x_chunk = x_chunk_val * random.uniform(0.75, 1.25)
            
            if abs(current_y_chunk) < 1 and abs(current_x_chunk) < 1 and i < scroll_chunks -1 : continue # Skip negligible internal chunks

            await page.mouse.wheel(current_x_chunk, current_y_chunk)
            
            if i < scroll_chunks - 1: # Pause between scroll "flicks"
                pause = random.uniform(0.015, 0.07) * (1 + self.profile.stress_level * 0.4 + self.profile.fatigue_factor * 0.2)
                await asyncio.sleep(pause)
        self.logger.debug(f"Scroll by (X:{amount_x}, Y:{amount_y}) completed in {scroll_chunks} chunks.")

    async def simulate_reading_eye_movement(self, page: Page, pattern: str = "read", target_area: Optional[Dict[str,float]] = None) -> None:
        self.logger.debug(f"Simulating reading eye movement (mouse following gaze), pattern: {pattern}")
        if page.is_closed(): return
        try:
            viewport = page.viewport_size or {'width': 1280, 'height': 720}
        except Exception: viewport = {'width': 1280, 'height': 720}

        area = target_area if target_area and all(k in target_area for k in ['left','top','width','height']) else {
            'left': viewport['width'] * 0.05, 'top': viewport['height'] * 0.05,
            'width': viewport['width'] * 0.9, 'height': viewport['height'] * 0.5 # Focus on upper half for general reading
        }
        if area['width'] <= 10 or area['height'] <= 10: self.logger.warning("Reading area too small for simulation."); return

        num_saccades = random.randint(2, 4) if pattern == "scan" else random.randint(4, 7)
        for _ in range(num_saccades):
            if page.is_closed(): return
            target_x = random.uniform(area['left'], area['left'] + area['width'])
            target_y = random.uniform(area['top'], area['top'] + area['height'])
            speed_mod = random.uniform(1.0, 1.5) if pattern == "scan" else random.uniform(0.7, 1.2)
            await self._move_with_human_characteristics(page, target_x, target_y, speed_factor=speed_mod)
            await asyncio.sleep(random.uniform(0.12, 0.4) * (1 + self.profile.stress_level * 0.3))

    async def _move_with_human_characteristics(self, page: Page, target_x: float, target_y: float, speed_factor: float = 1.0) -> None:
        try:
            if page.is_closed(): return
            viewport = page.viewport_size or {'width': 1280, 'height': 720}
            # Clamp target coordinates to be within viewport boundaries
            clamped_x = max(0.0, min(float(target_x), float(viewport['width'] - 1)))
            clamped_y = max(0.0, min(float(target_y), float(viewport['height'] - 1)))

            # Simplified steps calculation, Playwright handles the path. More steps = slower/smoother.
            # This is an approximation as current mouse position isn't easily available.
            start_x_approx, start_y_approx = viewport['width'] / 2, viewport['height'] / 2
            distance = math.sqrt((clamped_x - start_x_approx)**2 + (clamped_y - start_y_approx)**2)
            
            # Adjust step count based on distance, profile acceleration, and speed factor
            base_steps_calc = distance / (25 * self.profile.mouse_acceleration * max(0.2, speed_factor))
            steps = int(max(3, min(base_steps_calc * (1 + self.profile.movement_jitter_factor), 75))) # Clamp steps

            self.logger.debug(f"Moving mouse to ({clamped_x:.0f},{clamped_y:.0f}) in {steps} steps (speed_factor:{speed_factor:.1f}).")
            await page.mouse.move(clamped_x, clamped_y, steps=steps)
            # Tiny pause after movement to simulate human settling
            await asyncio.sleep(random.uniform(0.01, 0.035) * (1 + self.profile.stress_level * 0.2))
        except Exception as e:
            self.logger.warning(f"Error during mouse move to ({target_x},{target_y}): {e}")

class KeystrokeDynamicsSimulator:
    def __init__(self, profile: Optional[BiometricProfile]):
        self.profile = profile if profile else BiometricProfile()
        self.logger = logging.getLogger(__name__ + ".KeystrokeDynamicsSimulator")

    async def type_with_human_characteristics(self, page: Page, text: str, field_selector: Optional[str] = None) -> None:
        self.logger.debug(f"Typing text: '{text[:30].replace(chr(10),' ')}...' into selector: '{field_selector}'")
        if page.is_closed(): return
        if field_selector:
            try:
                field_loc = page.locator(field_selector).first
                await field_loc.scroll_if_needed(timeout=3000)
                await field_loc.click(timeout=7000, delay=random.uniform(50,120)) # Human-like click delay
                await asyncio.sleep(random.uniform(0.12, 0.40) * (1 + self.profile.stress_level * 0.5))
            except Exception as e:
                self.logger.warning(f"Could not click field '{field_selector}' for typing: {e}. Attempting type anyway.")

        chars_per_sec = (self.profile.typing_speed_wpm * 5) / 60 # Avg 5 chars per word
        base_inter_char_delay_s = 1.0 / chars_per_sec if chars_per_sec > 0 else 0.1

        for char_to_type in text:
            if page.is_closed(): return
            # Calculate delay for this specific character
            delay_mult = random.uniform(0.7, 1.4) * \
                         (1 + self.profile.stress_level * 0.35 + self.profile.fatigue_factor * 0.2)
            current_char_delay_s = base_inter_char_delay_s * delay_mult

            if char_to_type.isspace(): current_char_delay_s *= random.uniform(1.15, 1.8)
            elif char_to_type.isupper(): current_char_delay_s *= random.uniform(1.08, 1.35)
            elif not char_to_type.isalnum(): current_char_delay_s *= random.uniform(1.25, 1.75) # Punctuation
            elif char_to_type.isdigit(): current_char_delay_s *= random.uniform(0.9, 1.2)

            # Simulate typos
            typo_probability = (0.012 + (0.04 * self.profile.stress_level) + (0.03 * self.profile.fatigue_factor))
            if random.random() < typo_probability:
                await self._simulate_typo_correction(page, char_to_type)
            else:
                # Playwright's type() has its own keydown/press/up. The 'delay' is between chars.
                # For more granular key event timing, use page.keyboard.down/up.
                await page.keyboard.type(char_to_type, delay=random.uniform(15, 40)) # Small delay for key press itself
            
            await asyncio.sleep(max(0.018, current_char_delay_s)) # Inter-character pause
        self.logger.debug("Typing simulation complete.")

    async def _simulate_typo_correction(self, page: Page, intended_char: str) -> None:
        self.logger.debug(f"Simulating typo for intended char: '{intended_char}'")
        if page.is_closed(): return
        common_mistakes = {'a':'s', 's':'ad', 'd':'sf', 'f':'fg', 'g':'fh', 'h':'gj', 'j':'hk', 'k':'jl', 'l':'k',
                           'q':'w', 'w':'qe', 'e':'wr', 'r':'et', 't':'ry', 'y':'tu', 'u':'yi', 'i':'uo', 'o':'ip', 'p':'o',
                           'z':'x', 'x':'zc', 'c':'xv', 'v':'cb', 'b':'vn', 'n':'bm', 'm':'n'}
        wrong_char = common_mistakes.get(intended_char.lower(), random.choice("abcdefghijklmnopqrstuvwxyz"))
        if wrong_char == intended_char.lower() and len(wrong_char) == 1: # Ensure it's different
             wrong_char = chr(ord(wrong_char) + 1) if ord(wrong_char) < ord('z') else chr(ord(wrong_char) -1)


        await page.keyboard.type(wrong_char, delay=random.uniform(10,25))
        await asyncio.sleep(random.uniform(0.03, 0.09)) # Typo inter-key
        await asyncio.sleep(random.uniform(0.12, 0.55) * (1 + self.profile.stress_level * 1.2)) # "Oops" pause
        await page.keyboard.press('Backspace')
        await asyncio.sleep(random.uniform(0.04, 0.16)) # Pause after backspace
        await page.keyboard.type(intended_char, delay=random.uniform(10,25)) # Type correct char
        self.logger.debug("Typo corrected.")

class AttentionModel:
    def __init__(self, profile: Optional[BiometricProfile]):
        self.profile = profile if profile else BiometricProfile()
        self.logger = logging.getLogger(__name__ + ".AttentionModel")
        self.last_focus_shift_time = time.time()

    def should_lose_focus(self) -> bool:
        elapsed = time.time() - self.last_focus_shift_time
        attention_span = max(1.0, self.profile.attention_span_seconds * (1 - self.profile.fatigue_factor * 0.5)) # Fatigue reduces attention
        if elapsed < attention_span * 0.3: return False # Less likely to shift focus too soon

        # Probability increases as elapsed time approaches the (fatigued) attention span
        # Heavily influenced by multitasking tendency
        prob_of_shift = (elapsed / attention_span) * (0.05 + self.profile.multitasking_tendency * 0.95)
        return random.random() < min(0.95, prob_of_shift) # Cap probability

    async def simulate_attention_loss(self, page: Optional[Page]) -> None:
        self.logger.debug("Simulating attention loss/shift.")
        distraction_pause = random.uniform(0.7, 2.5)
        if random.random() < self.profile.multitasking_tendency:
            distraction_pause += random.uniform(1.5, 5.0)
            self.logger.debug(f"Attention shift includes 'multitasking' pause extension.")
        await asyncio.sleep(distraction_pause)
        self.last_focus_shift_time = time.time()
        self.logger.debug("Attention shift simulation finished.")

class AdvancedBehavioralBiometrics:
    def __init__(self, profile: Optional[BiometricProfile] = None, stop_event: Optional[asyncio.Event] = None):
        self.logger = logging.getLogger(__name__ + ".AdvancedBehavioralBiometrics")
        self.profile = profile if profile else BiometricProfile()
        self._stop_event = stop_event
        self.session_start_time = time.time()
        self.action_history: List[str] = []
        self.page_dimensions: Optional[Dict[str, Any]] = None
        self.interactive_elements: List[Dict[str, Any]] = []

        self.mouse_dynamics = MouseDynamicsSimulator(self.profile)
        self.keystroke_dynamics = KeystrokeDynamicsSimulator(self.profile)
        self.attention_model = AttentionModel(self.profile)
        # self.eye_tracking_simulation = EyeTrackingSimulator() # Not directly used for actions

        self.logger.info(f"AdvancedBehavioralBiometrics initialized. Profile: {self.profile}")
    def _choose_interaction_type(self) -> str:
        """Choose interaction type based on realistic human behavior patterns"""
        # Ensure self.profile is not None before accessing attributes
        # Access profile attributes safely, providing defaults if self.profile is None
        fatigue = self.profile.fatigue_factor if self.profile else 0.0
        stress = self.profile.stress_level if self.profile else 0.0

        base_probabilities = {
            "scroll": 0.35, 
            "hover": 0.28, 
            "reading": 0.20,
            "pause": 0.12, 
            "click": 0.05  # Clicks are generally less frequent
        }

        # Dynamic adjustments based on profile state
        if fatigue > 0.6:
            base_probabilities["pause"] = base_probabilities.get("pause", 0) + 0.10
            base_probabilities["scroll"] = max(0.05, base_probabilities.get("scroll",0.05) - 0.05)
            base_probabilities["reading"] = max(0.05, base_probabilities.get("reading",0.05) - 0.05)
        if stress > 0.7: 
            base_probabilities["hover"] = base_probabilities.get("hover",0) + 0.05
            base_probabilities["scroll"] = base_probabilities.get("scroll",0) + 0.05
            base_probabilities["reading"] = max(0.05, base_probabilities.get("reading",0.05) - 0.10)

        valid_keys = list(base_probabilities.keys())
        current_probs = [base_probabilities.get(k, 0.0) for k in valid_keys]
        total_prob = sum(current_probs)

        if total_prob <= 0:
            self.logger.warning("_choose_interaction_type: All probabilities summed to zero or less. Defaulting to 'pause'.")
            return random.choice(valid_keys) if valid_keys else "pause"

        normalized_probs = [p / total_prob for p in current_probs]
        # Ensure numpy is imported at the top of advanced_behavioral_simulation.py: import numpy as np
        return np.random.choice(valid_keys, p=normalized_probs)

    def _should_stop(self) -> bool:
        return self._stop_event is not None and self._stop_event.is_set()

    async def _initialize_page_context(self, page: Page) -> None:
        self.logger.debug("Initializing page context...")
        if page.is_closed(): self.logger.warning("Page context init: Page is closed."); return
        try:
            self.page_dimensions = await page.evaluate("""() => ({
                width: window.innerWidth, height: window.innerHeight,
                scrollHeight: document.documentElement.scrollHeight, scrollWidth: document.documentElement.scrollWidth,
                devicePixelRatio: window.devicePixelRatio || 1.0 })""")
            
            self.interactive_elements = await page.evaluate("""() => {
                const elements = []; let idCounter = 0;
                const selectors = [ 'button:not([disabled])', 'a[href]',
                    'input:not([type="hidden"]):not([disabled])', 'select:not([disabled])',
                    'textarea:not([disabled])', '[role="button"]', '[role="link"]', '[role="menuitem"]',
                    '[role="tab"]', '.clickable', '[data-clickable]', '.btn', 'summary', 'label[for]' ];
                selectors.forEach(selector => { try { document.querySelectorAll(selector).forEach(el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    const isActuallyVisible = style.visibility !== 'hidden' && style.display !== 'none' && 
                                          parseFloat(style.opacity || 1) > 0.05 && el.offsetParent !== null &&
                                          rect.width > 2 && rect.height > 2 && // Min dimensions
                                          rect.top < (window.innerHeight + 100) && rect.bottom > -100 && // Generous viewport check
                                          rect.left < (window.innerWidth + 100) && rect.right > -100;
                    if (isActuallyVisible) {
                        if (!el.id) el.id = `pw_bhv_gen_id_${idCounter++}`;
                        elements.push({ id: el.id, x: rect.left + rect.width/2, y: rect.top + rect.height/2,
                            width: rect.width, height: rect.height, tagName: el.tagName.toLowerCase(),
                            text: (el.innerText || el.textContent || el.getAttribute('aria-label') || el.value || el.getAttribute('title') || '').substring(0,60).trim().replace(/\\s+/g, ' '),
                            visible: true }); } });
                } catch (e) { /* console.warn('Selector error during element gathering:', e); */ }});
                // Further filter for elements that are likely primary interaction targets
                return elements.filter(el => el.text || ['input', 'button', 'select', 'textarea', 'a', 'summary'].includes(el.tagName));
            }""")
            self.logger.info(f"Page context init. Viewport: {self.page_dimensions.get('width')}x{self.page_dimensions.get('height')}. Interactive elements: {len(self.interactive_elements)}")
        except Exception as e:
            self.logger.error(f"Failed to initialize page context: {e}", exc_info=True)
            self.page_dimensions = {"width": 1280, "height": 720, "scrollHeight": 1500, "scrollWidth": 1280, "devicePixelRatio": 1.0}
            self.interactive_elements = []

    async def _simulate_page_arrival(self, page: Page) -> None:
        self.logger.debug("Simulating page arrival behavior.")
        if self._should_stop() or page.is_closed(): return
        await asyncio.sleep(random.uniform(0.4, 1.5) * (1 + self.profile.stress_level * 0.2)) # Initial orientation
        if self.page_dimensions:
            scan_area = {'left': 0, 'top': 0, 'width': self.page_dimensions.get('width',1280), 'height': self.page_dimensions.get('height',720) * 0.25}
            await self.mouse_dynamics.simulate_reading_eye_movement(page, pattern="scan", target_area=scan_area)
        if random.random() < 0.7 and self.page_dimensions and self.page_dimensions.get('scrollHeight',0) > self.page_dimensions.get('height',0):
            await self._simulate_overview_scroll(page)

    async def _simulate_reading_behavior(self, page: Page, focus_area_element_info: Optional[Dict[str,Any]] = None) -> None:
        self.logger.debug(f"Simulating reading. Focus: {focus_area_element_info.get('tagName') if focus_area_element_info else 'general'}")
        if self._should_stop() or page.is_closed(): return
        
        words_to_read = random.randint(30, 160) * (1 - self.profile.fatigue_factor * 0.5)
        reading_time_s = (words_to_read / max(10, self.profile.reading_speed_wpm)) * 60
        reading_time_s = max(0.6, min(reading_time_s, 6.0)) * (1 + self.profile.stress_level * 0.25)
        
        read_area = None
        if focus_area_element_info and self.page_dimensions and focus_area_element_info.get('width',0) > 5 :
            read_area = { 'left': max(0, focus_area_element_info['x'] - focus_area_element_info['width']*1.2),
                          'top': max(0, focus_area_element_info['y'] - focus_area_element_info['height']),
                          'width': focus_area_element_info['width'] * 2.4, 'height': focus_area_element_info['height'] * 2 }
            read_area['width'] = min(read_area['width'], self.page_dimensions.get('width',1280) - read_area['left'])
            read_area['height'] = min(read_area['height'], self.page_dimensions.get('height',720) - read_area['top'])
        elif self.page_dimensions: # General area if no specific focus
             read_area = {'left': self.page_dimensions.get('width',0)*0.1, 'top': self.page_dimensions.get('height',0)*0.1, 
                           'width': self.page_dimensions.get('width',0)*0.8, 'height': self.page_dimensions.get('height',0)*0.4}
        
        if read_area and read_area.get('width',0) > 10 and read_area.get('height',0) > 10:
            await self.mouse_dynamics.simulate_reading_eye_movement(page, pattern="read", target_area=read_area)
        
        await asyncio.sleep(reading_time_s)
        self.action_history.append("reading")

    async def _simulate_overview_scroll(self, page: Page) -> None:
        self.logger.debug("Simulating overview scroll.")
        if self._should_stop() or page.is_closed() or not self.page_dimensions or \
           self.page_dimensions.get('scrollHeight',0) <= self.page_dimensions.get('height',0) + 50: return # Add buffer

        for _ in range(random.randint(1, 2)): # Fewer, larger scrolls for overview
            if self._should_stop() or page.is_closed(): break
            vp_h = self.page_dimensions.get('height', 720)
            scroll_dist_px = int(vp_h * random.uniform(0.3, 0.8))
            direction = 1 # Usually scroll down for overview
            await self.mouse_dynamics.simulate_realistic_scroll(page, scroll_dist_px * direction)
            await asyncio.sleep(random.uniform(0.2, 0.9) * (1 + self.profile.fatigue_factor * 0.2))
        
        if random.random() < 0.45 and not (self._should_stop() or page.is_closed()): # Sometimes scroll back a bit
            await self.mouse_dynamics.simulate_realistic_scroll(page, -int(self.page_dimensions.get('height',720) * random.uniform(0.1, 0.4)))
        self.action_history.append("overview_scroll")

    async def _add_realistic_delay(self) -> None:
        if self._should_stop(): return
        delay = self.profile.pause_between_actions * random.uniform(0.75, 1.25) * \
                (1 + self.profile.fatigue_factor * 0.6) * (1 + self.profile.stress_level * 0.35)
        if self.attention_model.should_lose_focus():
            self.logger.debug("Realistic delay extended by attention model shift.")
            await self.attention_model.simulate_attention_loss(None)
        await asyncio.sleep(max(0.12, delay)) # Min delay

    async def _realistic_scroll_interaction(self, page: Page) -> None:
        self.logger.debug("Executing realistic scroll interaction.")
        if self._should_stop() or page.is_closed() or not self.page_dimensions: return
        vp_h = self.page_dimensions.get('height',720)
        scroll_dist = int(vp_h * random.uniform(0.1, 0.55)) * random.choice([-1, 1, 1])
        await self.mouse_dynamics.simulate_realistic_scroll(page, scroll_dist)
        self.action_history.append("scroll")

    async def _realistic_hover_interaction(self, page: Page) -> None:
        self.logger.debug("Executing realistic hover interaction.")
        if self._should_stop() or page.is_closed() or not self.page_dimensions: return
        target_el = None
        visible_elements = [el for el in self.interactive_elements if el.get('visible')] if self.interactive_elements else []
        if visible_elements: target_el = random.choice(visible_elements)

        if target_el:
            x, y = target_el.get('x', self.page_dimensions.get('width',800)/2), target_el.get('y', self.page_dimensions.get('height',600)/2)
            self.logger.debug(f"Hovering near element: {target_el.get('tagName','N/A')} ('{target_el.get('text','N/A')}')")
            await self.mouse_dynamics._move_with_human_characteristics(page, x, y, speed_factor=random.uniform(0.75, 1.25))
            await asyncio.sleep(random.uniform(0.35, 1.1) * (1 + self.profile.stress_level * 0.25))
        else: # Fallback hover
            page_w, page_h = self.page_dimensions.get('width',800), self.page_dimensions.get('height',600)
            await self.mouse_dynamics._move_with_human_characteristics(page, random.uniform(page_w*0.15, page_w*0.85), random.uniform(page_h*0.15, page_h*0.85))
        self.action_history.append("hover")

    async def _realistic_click_interaction(self, page: Page) -> None:
        self.logger.debug("Executing realistic click interaction.")
        if self._should_stop() or page.is_closed() or not self.page_dimensions: return
        target_el = None
        # Prefer elements that are typically clickable and visible
        visible_clickables = [el for el in self.interactive_elements if el.get('visible') and el.get('tagName') in ['button', 'a', 'input', 'summary'] and (el.get('width',0)>5 and el.get('height',0)>5)] if self.interactive_elements else []
        if visible_clickables: target_el = random.choice(visible_clickables)

        if target_el and target_el.get('id'):
            x, y = target_el.get('x',0), target_el.get('y',0)
            self.logger.info(f"Attempting realistic click on element ID: {target_el['id']} (Text: '{target_el.get('text')}')")
            await self.mouse_dynamics._move_with_human_characteristics(page, x, y)
            try:
                click_delay_ms = self.profile.click_dwell_time_ms * random.uniform(0.9, 1.1)
                # Using Playwright's click with a delay to simulate mousedown-wait-mouseup
                await page.locator(f"#{target_el['id']}").click(delay=click_delay_ms, timeout=4000, force=False, no_wait_after=True)
                self.logger.info(f"Clicked element by ID: {target_el['id']}")
                await asyncio.sleep(random.uniform(0.04, 0.12)) # Small post-click reaction
            except Exception as e:
                self.logger.warning(f"Failed to click element by ID '{target_el['id']}', trying coordinate click. Error: {e}")
                await page.mouse.click(x, y, delay=self.profile.click_dwell_time_ms * random.uniform(0.8, 1.2))
        else: # Fallback coordinate click if no suitable element found
            page_w, page_h = self.page_dimensions.get('width',800), self.page_dimensions.get('height',600)
            rand_x, rand_y = random.uniform(page_w*0.25, page_w*0.75), random.uniform(page_h*0.25, page_h*0.75)
            self.logger.info(f"No specific target for click, clicking random coordinates ({rand_x:.0f}, {rand_y:.0f}).")
            await page.mouse.click(rand_x, rand_y, delay=self.profile.click_dwell_time_ms * random.uniform(0.8, 1.2))
        self.action_history.append("click")

    async def _simulate_thinking_pause(self) -> None:
        self.logger.debug("Executing thinking pause.")
        if self._should_stop(): return
        pause_duration = self.profile.pause_between_actions * random.uniform(1.4, 3.0) * \
                         (1 + self.profile.stress_level * 0.5 + self.profile.fatigue_factor * 0.7)
        if self.attention_model.should_lose_focus():
            self.logger.debug("Thinking pause extended by attention model shift (simulating distraction).")
            await self.attention_model.simulate_attention_loss(None)
        await asyncio.sleep(max(0.3, pause_duration))
        self.action_history.append("thinking_pause")

    async def _execute_standard_interaction(self, page: Page, min_actions_override: Optional[int] = None, max_actions_override: Optional[int] = None) -> None:
        min_a = min_actions_override if min_actions_override is not None else self.profile.min_actions_medium_intensity
        max_a = max_actions_override if max_actions_override is not None else self.profile.max_actions_medium_intensity
        if min_a > max_a: min_a = max_a
        interaction_count = random.randint(min_a, max_a) if max_a >= min_a else min_a
        self.logger.debug(f"Standard interaction: Performing {interaction_count} actions.")

        for i in range(interaction_count):
            if self._should_stop() or page.is_closed(): break
            self.profile.fatigue_factor = min(1.0, self.profile.fatigue_factor + random.uniform(0.015, 0.035))
            interaction_type = self._choose_interaction_type()
            self.logger.debug(f"Std. Action #{i+1}/{interaction_count}: {interaction_type} (Fatigue: {self.profile.fatigue_factor:.2f})")

            if interaction_type == "scroll": await self._realistic_scroll_interaction(page)
            elif interaction_type == "hover": await self._realistic_hover_interaction(page)
            elif interaction_type == "click": await self._realistic_click_interaction(page)
            elif interaction_type == "reading":
                focus_el = random.choice([el for el in self.interactive_elements if el.get('visible')]) if self.interactive_elements and any(el.get('visible') for el in self.interactive_elements) else None
                await self._simulate_reading_behavior(page, focus_area_element_info=focus_el)
            elif interaction_type == "pause": await self._simulate_thinking_pause()
            
            if not (interaction_type == "pause" and self.attention_model.should_lose_focus()): # Avoid double delay if attention shift already caused a long pause
                await self._add_realistic_delay()

    async def _execute_minimal_interaction(self, page: Page) -> None:
        self.logger.debug(f"Executing minimal interaction (profile: {self.profile.typing_speed_wpm:.0f} WPM)")
        await self._execute_standard_interaction(page,
                                                 min_actions_override=self.profile.min_actions_low_intensity,
                                                 max_actions_override=self.profile.max_actions_low_intensity)

    async def _execute_comprehensive_interaction(self, page: Page) -> None:
        self.logger.debug(f"Executing comprehensive interaction (profile: {self.profile.typing_speed_wpm:.0f} WPM)")
        await self._execute_standard_interaction(page,
                                                 min_actions_override=self.profile.min_actions_high_intensity,
                                                 max_actions_override=self.profile.max_actions_high_intensity)

    async def _simulate_page_exit_preparation(self, page: Page) -> None:
        self.logger.debug("Simulating page exit preparation.")
        if self._should_stop() or page.is_closed() or not self.page_dimensions : return
        if random.random() < 0.3: # Less frequent exit flourishes
            await self.mouse_dynamics.simulate_realistic_scroll(page, random.randint(-100, 100))
            await self.mouse_dynamics._move_with_human_characteristics(
                page,
                random.uniform(0, self.page_dimensions.get('width',800)),
                random.uniform(0, self.page_dimensions.get('height',600)),
                speed_factor=1.7 )
        await asyncio.sleep(random.uniform(0.1, 0.5))

    async def simulate_realistic_page_interaction(self, page: Page, intensity: str = "medium") -> None:
        """Main orchestrator method for simulating page interaction."""
        try:
            self.logger.info(f"Starting realistic page interaction simulation (Intensity: {intensity}). Page URL: {page.url[:80]}")
            if self._should_stop() or page.is_closed(): return

            await self._initialize_page_context(page)
            if self._should_stop() or page.is_closed(): return

            await self._simulate_page_arrival(page)
            if self._should_stop() or page.is_closed(): return

            if intensity == "low":
                await self._execute_minimal_interaction(page)
            elif intensity == "high":
                await self._execute_comprehensive_interaction(page)
            else: # Default to medium
                await self._execute_standard_interaction(page)

            if self._should_stop() or page.is_closed(): return
            await self._simulate_page_exit_preparation(page)
            self.logger.info(f"Realistic page interaction simulation finished. Performed actions: {self.action_history}")
        except Exception as e:
            self.logger.error(f"Error during simulate_realistic_page_interaction for {page.url[:80]}: {e}", exc_info=True)
            raise # Re-raise to be handled by the global simulate_advanced_human_behavior

# --- Main Entry Function & Fallback ---
async def _fallback_basic_behavior(page: Page, intensity: str, stop_event: Optional[asyncio.Event] = None) -> None:
    """Fallback to a simpler behavior simulation if advanced fails."""
    module_logger.info(f"Executing fallback basic behavior. Intensity: {intensity}, Page: {page.url[:80]}")
    actions_map = {"low": random.randint(1, 2), "medium": random.randint(2, 3), "high": random.randint(3, 4)}
    num_actions = actions_map.get(intensity.lower(), 2)

    for i in range(num_actions):
        if (stop_event and stop_event.is_set()) or page.is_closed():
            module_logger.info("Fallback behavior interrupted by stop event or closed page.")
            break
        action_type = random.choice(["scroll", "hover", "pause"])
        module_logger.debug(f"Fallback action #{i+1}/{num_actions}: {action_type}")
        try:
            if action_type == "scroll": await page.mouse.wheel(0, float(random.randint(-200, 200)))
            elif action_type == "hover":
                vp = page.viewport_size or {'width': 1024, 'height': 768}
                x, y = random.randint(int(vp['width']*0.15), int(vp['width']*0.85)), random.randint(int(vp['height']*0.15), int(vp['height']*0.85))
                await page.mouse.move(float(x), float(y), steps=random.randint(2, 5))
            await asyncio.sleep(random.uniform(0.3, 1.2))
        except Exception as e_fb:
            module_logger.warning(f"Error during fallback action '{action_type}': {e_fb}")
            if page.is_closed(): break
            await asyncio.sleep(0.2)
    module_logger.info(f"Fallback basic behavior simulation finished for {page.url[:80]}.")

async def simulate_advanced_human_behavior(
        page: Page,
        intensity: str = "medium",
        profile: Optional[BiometricProfile] = None,
        stop_event: Optional[asyncio.Event] = None
    ) -> bool:
    module_logger.debug(f"Called simulate_advanced_human_behavior. Intensity: {intensity}, Page: {page.url[:80]}")
    try:
        if page.is_closed():
            module_logger.warning("Page is already closed before starting advanced behavior simulation.")
            return False
        
        behavioral_system = AdvancedBehavioralBiometrics(profile, stop_event=stop_event)
        await behavioral_system.simulate_realistic_page_interaction(page, intensity)
        module_logger.info(f"Advanced behavioral simulation completed successfully for {page.url[:80]}.")
        return True
    except asyncio.CancelledError:
        module_logger.info(f"Advanced behavioral simulation CANCELLED for {page.url[:80]}.")
        return False
    except Exception as e:
        module_logger.error(f"Advanced behavioral simulation FAILED for {page.url[:80]}: {e}", exc_info=True)
        module_logger.info(f"Falling back to basic behavior simulation for {page.url[:80]}.")
        try:
            await _fallback_basic_behavior(page, intensity, stop_event)
        except Exception as e_fallback_outer:
            module_logger.error(f"Error during _fallback_basic_behavior for {page.url[:80]}: {e_fallback_outer}", exc_info=True)
        return False

# Example for direct testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)-7s] %(name)-55s :: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    module_logger.info("Running advanced_behavioral_simulation.py directly for testing.")

    async def test_simulation_main():
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(viewport={'width': 1366, 'height': 768})
            page = await context.new_page()
            test_stop = asyncio.Event()
            try:
                test_sites = ["https://www.wikipedia.org", "https://example.com"]
                intensities = ["low", "medium", "high"]
                for site_url in test_sites:
                    if test_stop.is_set(): break
                    module_logger.info(f"\nNavigating to {site_url} for testing...")
                    await page.goto(site_url, wait_until="domcontentloaded", timeout=20000)
                    module_logger.info(f"Page loaded: {page.url}")
                    
                    selected_intensity = random.choice(intensities)
                    module_logger.info(f"--- TESTING '{selected_intensity.upper()}' INTENSITY on {site_url} ---")
                    
                    custom_profile = BiometricProfile(
                        typing_speed_wpm=random.uniform(30,80), 
                        reading_speed_wpm=random.uniform(150,350), 
                        attention_span_seconds=random.uniform(8,25),
                        pause_between_actions=random.uniform(0.2, 1.5)
                    )
                    await simulate_advanced_human_behavior(page, intensity=selected_intensity, profile=custom_profile, stop_event=test_stop)
                    await asyncio.sleep(1.5) 
                module_logger.info("\nTest simulations finished. Browser will close in 5 seconds.")
                await asyncio.sleep(5)
            except Exception as e_test_main:
                module_logger.error(f"Error in test_simulation_main: {e_test_main}", exc_info=True)
            finally:
                module_logger.info("Closing browser from test_simulation_main.")
                if not test_stop.is_set(): test_stop.set()
                await browser.close()
    try:
        asyncio.run(test_simulation_main())
    except KeyboardInterrupt:
        module_logger.info("Test run interrupted by user.")
    module_logger.info("Test script finished.")

