'] / 2
                        await self.move_mouse_natural(page, x, y)
                        await asyncio.sleep(0.5 + random.random())
                        
                        # Sometimes just hover, sometimes click
                        if random.random() < 0.3:
                            await self.human_click(element, page)
                            await asyncio.sleep(1 + random.random() * 2)
                            # Go back if we navigated
                            if page.url != await page.evaluate('() => document.referrer'):
                                await page.go_back()
                
            except Exception as e:
                # Ignore errors during exploration
                pass
            
            await asyncio.sleep(1 + random.random() * 2)
    
    def _get_typing_delay(self) -> float:
        """Get realistic typing delay"""
        # Convert WPM to characters per second
        chars_per_second = (self.typing_speed_wpm * 5) / 60
        base_delay = 1 / chars_per_second
        
        # Add variation
        return base_delay * (0.5 + random.random())
    
    async def simulate_hesitation(self, page: Page):
        """Simulate hesitation/thinking behavior"""
        # Move mouse in small circles
        center_x = random.randint(300, 700)
        center_y = random.randint(200, 500)
        
        for _ in range(random.randint(2, 4)):
            angle = random.random() * 2 * math.pi
            radius = random.randint(20, 50)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            await self.move_mouse_natural(page, x, y)
            await asyncio.sleep(0.3 + random.random() * 0.5)
    
    async def simulate_form_filling(self, page: Page, form_data: dict):
        """Fill form with human-like behavior"""
        for selector, value in form_data.items():
            # Find field
            field = await page.wait_for_selector(selector)
            if not field:
                continue
            
            # Move to field
            await self.human_click(field, page)
            
            # Sometimes click again (double checking)
            if random.random() < 0.2:
                await asyncio.sleep(0.5)
                await field.click()
            
            # Type value
            await self.human_type(field, value)
            
            # Tab to next field sometimes
            if random.random() < 0.7:
                await asyncio.sleep(0.2)
                await page.keyboard.press('Tab')
            
            # Pause between fields
            await asyncio.sleep(0.5 + random.random() * 1.5)


# Enhanced version with more patterns
class AdvancedHumanBehavior(HumanBehavior):
    """Advanced human behavior with learning patterns"""
    
    def __init__(self):
        super().__init__()
        self.behavior_profile = self._generate_profile()
        
    def _generate_profile(self) -> dict:
        """Generate unique behavior profile"""
        return {
            'mouse_speed': random.gauss(1.0, 0.2),
            'typing_speed': random.gauss(45, 10),
            'accuracy': random.gauss(0.97, 0.01),
            'reading_speed': random.gauss(250, 50),
            'impulsiveness': random.random(),  # How quickly they click
            'carefulness': random.random(),     # How much they double-check
            'curiosity': random.random(),       # How much they explore
            'fatigue_rate': random.uniform(0.001, 0.003)  # How quickly they slow down
        }
    
    async def adaptive_behavior(self, page: Page, duration_minutes: float):
        """Adapt behavior over time (fatigue, learning)"""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < duration_minutes * 60:
            # Calculate fatigue
            elapsed = asyncio.get_event_loop().time() - start_time
            fatigue = min(elapsed * self.behavior_profile['fatigue_rate'], 0.5)
            
            # Adjust speeds based on fatigue
            self.mouse_speed = self.behavior_profile['mouse_speed'] * (1 - fatigue)
            self.typing_speed_wpm = self.behavior_profile['typing_speed'] * (1 - fatigue)
            
            await asyncio.sleep(1)
