"""
Smart Resource Manager
Dynamically controls resource loading based on context
"""

import asyncio
from typing import Dict, Set, Optional, Any
from enum import Enum

from ..utils.logging import get_logger

logger = get_logger(__name__)


class ResourceMode(Enum):
    """Resource loading modes"""
    MINIMAL = "minimal"      # Block all non-essential resources
    DETECTION = "detection"  # Allow resources needed for ticket detection
    PURCHASE = "purchase"    # Allow all resources for purchasing
    

class SmartResourceManager:
    """
    Manages resource loading intelligently based on monitoring phase
    """
    
    def __init__(self):
        self.current_mode = ResourceMode.MINIMAL
        self.blocked_count: Dict[str, int] = {
            'images': 0,
            'scripts': 0,
            'stylesheets': 0,
            'fonts': 0,
            'media': 0
        }
        self.active_pages: Dict[str, Any] = {}  # page_id -> page object
        self.purchase_sessions: Set[str] = set()  # URLs in purchase mode
        
    async def configure_page(self, page: Any, platform: str, initial_mode: ResourceMode = ResourceMode.MINIMAL):
        """Configure resource blocking for a page"""
        page_id = f"{platform}_{id(page)}"
        self.active_pages[page_id] = page
        
        logger.info(f"Configuring resource manager for {platform} in {initial_mode.value} mode")
        
        # Set up request interception
        if hasattr(page, 'route'):  # Playwright
            await self._setup_playwright_blocking(page, page_id, initial_mode)
        else:  # Selenium
            await self._setup_selenium_blocking(page, page_id, initial_mode)
            
    async def _setup_playwright_blocking(self, page: Any, page_id: str, mode: ResourceMode):
        """Set up resource blocking for Playwright"""
        
        async def route_handler(route):
            request = route.request
            resource_type = request.resource_type
            url = request.url
            
            # Always allow main document and XHR/Fetch (needed for functionality)
            if resource_type in ['document', 'xhr', 'fetch', 'websocket']:
                await route.continue_()
                return
            
            # Check if we're in purchase mode for this domain
            if any(purchase_url in url for purchase_url in self.purchase_sessions):
                # In purchase mode, allow everything
                await route.continue_()
                return
            
            # Apply mode-specific rules
            should_block = self._should_block_resource(resource_type, url, mode)
            
            if should_block:
                self.blocked_count[resource_type] = self.blocked_count.get(resource_type, 0) + 1
                await route.abort()
            else:
                await route.continue_()
        
        await page.route('**/*', route_handler)
        
        # Store the resource counts on the page object for telemetry
        page._blocked_images = 0
        page._blocked_scripts = 0
        
    async def _setup_selenium_blocking(self, page: Any, page_id: str, mode: ResourceMode):
        """Set up resource blocking for Selenium using Chrome DevTools Protocol"""
        
        # For Selenium, we'll use a different approach
        # Inject JavaScript to block image loading
        script = """
        // Block image loading based on mode
        const originalImage = window.Image;
        window.Image = function() {
            const img = new originalImage();
            const originalSrc = Object.getOwnPropertyDescriptor(img.__proto__, 'src');
            
            Object.defineProperty(img, 'src', {
                set: function(value) {
                    if (window.__STEALTHMASTER_RESOURCE_MODE === 'minimal') {
                        // Block image loading in minimal mode
                        console.log('Blocked image:', value);
                        window.__STEALTHMASTER_BLOCKED_IMAGES = (window.__STEALTHMASTER_BLOCKED_IMAGES || 0) + 1;
                        return;
                    }
                    originalSrc.set.call(this, value);
                },
                get: function() {
                    return originalSrc.get.call(this);
                }
            });
            
            return img;
        };
        
        // Also block CSS background images
        const originalStyle = CSSStyleDeclaration.prototype.setProperty;
        CSSStyleDeclaration.prototype.setProperty = function(property, value, priority) {
            if (property.includes('background') && value.includes('url(') && 
                window.__STEALTHMASTER_RESOURCE_MODE === 'minimal') {
                console.log('Blocked background image:', value);
                window.__STEALTHMASTER_BLOCKED_IMAGES = (window.__STEALTHMASTER_BLOCKED_IMAGES || 0) + 1;
                return;
            }
            return originalStyle.call(this, property, value, priority);
        };
        
        // Set initial mode
        window.__STEALTHMASTER_RESOURCE_MODE = '""" + mode.value + """';
        window.__STEALTHMASTER_BLOCKED_IMAGES = 0;
        window.__STEALTHMASTER_BLOCKED_SCRIPTS = 0;
        """
        
        page.execute_script(script)
        
    def _should_block_resource(self, resource_type: str, url: str, mode: ResourceMode) -> bool:
        """Determine if a resource should be blocked based on mode"""
        
        # Essential domains that should never be blocked
        essential_domains = [
            'ticketmaster.com',
            'fansale.it', 'fansale.de',
            'vivaticket.com',
            'queue-it.net',  # Queue system
            'recaptcha.net', 'gstatic.com'  # Captcha
        ]
        
        # Check if URL is from essential domain
        is_essential = any(domain in url for domain in essential_domains)
        
        if mode == ResourceMode.MINIMAL:
            # Block most resources except essential ones
            if resource_type == 'image':
                return not is_essential
            elif resource_type == 'stylesheet':
                # Keep essential styles for layout
                return not is_essential and 'critical' not in url
            elif resource_type == 'script':
                # Keep essential scripts for functionality
                return not is_essential and not any(s in url for s in ['ticket', 'seat', 'checkout'])
            elif resource_type in ['font', 'media']:
                return True  # Always block in minimal mode
                
        elif mode == ResourceMode.DETECTION:
            # Allow more resources for better detection
            if resource_type == 'image':
                # Allow images that might show ticket availability
                return not any(indicator in url.lower() for indicator in ['seat', 'ticket', 'available', 'sold'])
            elif resource_type in ['stylesheet', 'script']:
                return False  # Allow for proper page rendering
            elif resource_type in ['font', 'media']:
                return True  # Still block these
                
        elif mode == ResourceMode.PURCHASE:
            # Allow everything during purchase
            return False
            
        return False
    
    async def switch_to_detection_mode(self, page: Any, platform: str):
        """Switch to detection mode when looking for tickets"""
        logger.info(f"Switching {platform} to detection mode - allowing ticket-related resources")
        
        page_id = f"{platform}_{id(page)}"
        self.current_mode = ResourceMode.DETECTION
        
        if hasattr(page, 'evaluate'):  # Playwright
            await page.evaluate("window.__STEALTHMASTER_RESOURCE_MODE = 'detection';")
        else:  # Selenium
            page.execute_script("window.__STEALTHMASTER_RESOURCE_MODE = 'detection';")
            
    async def switch_to_purchase_mode(self, page: Any, platform: str, url: str):
        """Switch to purchase mode - allow all resources"""
        logger.info(f"🎯 Switching {platform} to PURCHASE MODE - enabling all resources")
        
        page_id = f"{platform}_{id(page)}"
        self.current_mode = ResourceMode.PURCHASE
        self.purchase_sessions.add(url)
        
        # Enable all resources
        if hasattr(page, 'evaluate'):  # Playwright
            await page.evaluate("""
                window.__STEALTHMASTER_RESOURCE_MODE = 'purchase';
                
                // Show notification
                const notification = document.createElement('div');
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #4CAF50;
                    color: white;
                    padding: 15px 25px;
                    border-radius: 5px;
                    z-index: 999999;
                    font-family: Arial, sans-serif;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    animation: slideIn 0.3s ease-out;
                `;
                notification.innerHTML = `
                    <strong>🎫 Purchase Mode Active</strong><br>
                    <small>All resources enabled for checkout</small>
                `;
                document.body.appendChild(notification);
                
                // Add animation
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes slideIn {
                        from { transform: translateX(100%); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                `;
                document.head.appendChild(style);
                
                // Auto-remove after 5 seconds
                setTimeout(() => notification.remove(), 5000);
                
                // Reload images that were blocked
                document.querySelectorAll('img').forEach(img => {
                    if (!img.complete && img.dataset.src) {
                        img.src = img.dataset.src;
                    }
                });
            """)
        else:  # Selenium
            page.execute_script("""
                window.__STEALTHMASTER_RESOURCE_MODE = 'purchase';
                console.log('PURCHASE MODE ACTIVATED - All resources enabled');
                
                // Reload any blocked images
                document.querySelectorAll('img').forEach(img => {
                    if (!img.complete && img.dataset.src) {
                        img.src = img.dataset.src;
                    }
                });
            """)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get resource blocking statistics"""
        total_blocked = sum(self.blocked_count.values())
        
        # Estimate data saved (rough estimates)
        data_saved_mb = (
            self.blocked_count.get('images', 0) * 0.1 +  # ~100KB per image
            self.blocked_count.get('scripts', 0) * 0.05 + # ~50KB per script
            self.blocked_count.get('stylesheets', 0) * 0.02 + # ~20KB per stylesheet
            self.blocked_count.get('fonts', 0) * 0.05 + # ~50KB per font
            self.blocked_count.get('media', 0) * 1.0  # ~1MB per media file
        )
        
        return {
            'current_mode': self.current_mode.value,
            'total_blocked': total_blocked,
            'blocked_breakdown': self.blocked_count.copy(),
            'estimated_data_saved_mb': round(data_saved_mb, 2),
            'active_pages': len(self.active_pages),
            'purchase_sessions': len(self.purchase_sessions)
        }
    
    async def cleanup(self):
        """Clean up resources"""
        self.active_pages.clear()
        self.purchase_sessions.clear()
        self.blocked_count.clear()


# Global instance
resource_manager = SmartResourceManager()
