"""
Speed Optimization Module for StealthMaster
Implements performance improvements while maintaining stealth
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


class SpeedOptimizer:
    """Performance optimization techniques for the bot"""
    
    @staticmethod
    def get_performance_chrome_options() -> List[str]:
        """Chrome options optimized for speed while maintaining stealth"""
        return [
            # Performance options
            '--disable-logging',
            '--disable-gpu-sandbox',
            '--disable-software-rasterizer',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-hang-monitor',
            '--disable-prompt-on-repost',
            '--disable-sync',
            '--disable-domain-reliability',
            '--disable-features=AutofillServerCommunication',
            
            # Memory optimization
            '--memory-pressure-off',
            '--max_old_space_size=4096',
            '--disable-features=RendererCodeIntegrity',
            
            # Network optimization
            '--aggressive-cache-discard',
            '--disable-background-networking',
            
            # Still maintain some stealth
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage'
        ]
    
    @staticmethod
    def get_fast_page_load_script() -> str:
        """JavaScript to speed up page loading"""
        return """
        // Disable animations
        const style = document.createElement('style');
        style.textContent = `
            *, *::before, *::after {
                animation-duration: 0s !important;
                animation-delay: 0s !important;
                transition-duration: 0s !important;
                transition-delay: 0s !important;
            }
        `;
        document.head.appendChild(style);
        
        // Stop videos from autoplaying
        document.querySelectorAll('video').forEach(v => {
            v.pause();
            v.preload = 'none';
        });
        """
    
    @staticmethod
    def optimize_dom_queries(driver):
        """Inject optimized DOM query methods"""
        driver.execute_script("""
        // Cache frequently accessed elements
        window.elementCache = new Map();
        
        // Optimized querySelector with caching
        window.fastQuery = function(selector, useCache = true) {
            if (useCache && window.elementCache.has(selector)) {
                const cached = window.elementCache.get(selector);
                if (document.contains(cached)) {
                    return cached;
                }
            }
            
            const element = document.querySelector(selector);
            if (element && useCache) {
                window.elementCache.set(selector, element);
            }
            return element;
        };
        """)


class FastTicketChecker:
    """Optimized ticket checking logic"""
    
    def __init__(self, driver):
        self.driver = driver
        self.last_check_time = 0
    
    def fast_ticket_check(self) -> Tuple[bool, int]:
        """Ultra-fast ticket availability check"""
        ticket_selector = "[data-qa='ticketToBuy']"
        no_tickets_text = "non sono state trovate"
        
        # Quick JavaScript check - properly escape quotes
        js_check = """
        const tickets = document.querySelectorAll("[data-qa='ticketToBuy']");
        const pageText = document.body.innerText || '';
        
        return {
            hasTickets: tickets.length > 0,
            ticketCount: tickets.length,
            noTicketsMessage: pageText.toLowerCase().includes('non sono state trovate'),
            pageReady: document.readyState === 'complete'
        };
        """
        
        try:
            result = self.driver.execute_script(js_check)
            
            if result['hasTickets']:
                return True, result['ticketCount']
            else:
                return False, 0
                
        except Exception as e:
            logger.error(f"Fast ticket check failed: {e}")
            return False, -1
