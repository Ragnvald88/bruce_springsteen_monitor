#!/usr/bin/env python3
"""
Speed Optimization Module for StealthMaster
Implements performance improvements while maintaining stealth
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, Future
import asyncio
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
            '--disable-features=CertificateTransparencyComponentUpdater',
            
            # Memory optimization
            '--memory-pressure-off',
            '--max_old_space_size=4096',
            '--disable-features=RendererCodeIntegrity',
            '--disable-features=OptimizationGuideModelDownloading',
            
            # Network optimization
            '--aggressive-cache-discard',
            '--disable-background-networking',
            '--disable-features=SafeBrowsingEnhancedProtection',
            
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
        
        // Lazy load images optimization
        const images = document.querySelectorAll('img[loading="lazy"]');
        images.forEach(img => {
            if (img.getBoundingClientRect().top > window.innerHeight * 2) {
                img.loading = 'eager';
            }
        });
        
        // Remove unnecessary event listeners
        const heavyEvents = ['scroll', 'mousemove', 'touchmove'];
        heavyEvents.forEach(event => {
            const listeners = getEventListeners(window)[event];
            if (listeners && listeners.length > 5) {
                // Keep only essential listeners
                listeners.slice(5).forEach(l => {
                    window.removeEventListener(event, l.listener);
                });
            }
        });
        """
    
    @staticmethod
    def smart_wait(driver, locator: Tuple[str, str], timeout: int = 10, 
                   poll_frequency: float = 0.1) -> Optional[any]:
        """Optimized wait that's faster than standard WebDriverWait"""
        end_time = time.time() + timeout
        last_exception = None
        
        while time.time() < end_time:
            try:
                element = driver.find_element(*locator)
                if element.is_displayed() and element.is_enabled():
                    return element
            except Exception as e:
                last_exception = e
            
            # Dynamic sleep - shorter at the beginning
            elapsed = time.time() - (end_time - timeout)
            if elapsed < 2:
                time.sleep(0.05)  # 50ms for first 2 seconds
            else:
                time.sleep(poll_frequency)
        
        if last_exception:
            raise last_exception
        return None
    
    @staticmethod
    def parallel_element_check(driver, selectors: List[Tuple[str, str]]) -> Dict[str, bool]:
        """Check multiple elements in parallel for faster detection"""
        results = {}
        
        # Create JavaScript to check all elements at once
        js_checks = []
        for i, (by, value) in enumerate(selectors):
            if by == By.CSS_SELECTOR:
                js_checks.append(f"document.querySelector('{value}') !== null")
            elif by == By.XPATH:
                js_checks.append(f"document.evaluate('{value}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue !== null")
            elif by == By.ID:
                js_checks.append(f"document.getElementById('{value}') !== null")
            elif by == By.CLASS_NAME:
                js_checks.append(f"document.getElementsByClassName('{value}').length > 0")
        
        # Execute all checks in one go
        js_code = f"return [{','.join(js_checks)}];"
        
        try:
            results_array = driver.execute_script(js_code)
            for i, (by, value) in enumerate(selectors):
                results[value] = results_array[i]
        except Exception as e:
            logger.error(f"Parallel element check failed: {e}")
            # Fallback to sequential
            for by, value in selectors:
                try:
                    driver.find_element(by, value)
                    results[value] = True
                except:
                    results[value] = False
        
        return results
    
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
                // Verify element is still in DOM
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
        
        // Batch DOM reads for better performance
        window.batchDOMRead = function(selectors) {
            const results = {};
            // Force layout once
            document.body.offsetHeight;
            
            selectors.forEach(selector => {
                results[selector] = window.fastQuery(selector);
            });
            
            return results;
        };
        """)
    
    @staticmethod
    def get_resource_hints() -> str:
        """Preconnect and prefetch hints for faster loading"""
        return """
        // Add resource hints for Fansale
        const hints = [
            {rel: 'preconnect', href: 'https://www.fansale.it'},
            {rel: 'dns-prefetch', href: 'https://www.fansale.it'},
            {rel: 'preconnect', href: 'https://cdn.fansale.it'},
            {rel: 'dns-prefetch', href: 'https://cdn.fansale.it'}
        ];
        
        hints.forEach(hint => {
            const link = document.createElement('link');
            link.rel = hint.rel;
            link.href = hint.href;
            document.head.appendChild(link);
        });
        """
    
    @staticmethod
    async def async_monitor_tickets(driver, selectors: List[str], 
                                  check_interval: float = 2.0) -> Optional[List]:
        """Asynchronous ticket monitoring for better performance"""
        async def check_tickets():
            js_code = f"""
            const selectors = {selectors};
            const results = [];
            
            for (const selector of selectors) {{
                const elements = document.querySelectorAll(selector);
                if (elements.length > 0) {{
                    results.push({{
                        selector: selector,
                        count: elements.length,
                        elements: Array.from(elements).map(el => ({{
                            text: el.textContent,
                            visible: el.offsetParent !== null
                        }}))
                    }});
                }}
            }}
            
            return results;
            """
            
            return driver.execute_script(js_code)
        
        while True:
            try:
                results = await asyncio.get_event_loop().run_in_executor(
                    None, check_tickets
                )
                
                if results:
                    return results
                
                await asyncio.sleep(check_interval)
            
            except Exception as e:
                logger.error(f"Async monitoring error: {e}")
                await asyncio.sleep(check_interval * 2)
    
    @staticmethod
    def optimize_login_flow(driver, email: str, password: str) -> bool:
        """Optimized login flow that's faster but still human-like"""
        try:
            # Pre-compile all selectors
            selectors = {
                'email': "[data-qa='loginEmail']",
                'password': "[data-qa='loginPassword']",
                'submit': "[data-qa='loginSubmit']",
                'cookie_accept': "//button[contains(text(), 'ACCETTA')]"
            }
            
            # Check all elements exist at once
            elements_exist = SpeedOptimizer.parallel_element_check(driver, [
                (By.CSS_SELECTOR, selectors['email']),
                (By.CSS_SELECTOR, selectors['password']),
                (By.CSS_SELECTOR, selectors['submit'])
            ])
            
            if not all(elements_exist.values()):
                logger.error("Login elements not found")
                return False
            
            # Use JavaScript for faster form filling
            js_fill = f"""
            const email = document.querySelector("{selectors['email']}");
            const password = document.querySelector("{selectors['password']}");
            
            // Trigger focus events
            email.focus();
            email.value = "{email}";
            email.dispatchEvent(new Event('input', {{bubbles: true}}));
            
            password.focus();
            password.value = "{password}";
            password.dispatchEvent(new Event('input', {{bubbles: true}}));
            
            // Small delay before submit
            setTimeout(() => {{
                document.querySelector("{selectors['submit']}").click();
            }}, 300);
            """
            
            driver.execute_script(js_fill)
            return True
            
        except Exception as e:
            logger.error(f"Optimized login failed: {e}")
            return False
    
    @staticmethod
    def get_performance_metrics(driver) -> Dict[str, float]:
        """Get detailed performance metrics"""
        metrics = driver.execute_script("""
        const perfData = performance.getEntriesByType('navigation')[0];
        const memory = performance.memory || {};
        
        return {
            // Navigation timing
            domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
            loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
            domInteractive: perfData.domInteractive - perfData.fetchStart,
            
            // Resource timing
            resourceCount: performance.getEntriesByType('resource').length,
            totalResourceTime: performance.getEntriesByType('resource').reduce((sum, r) => sum + (r.responseEnd - r.startTime), 0),
            
            // Memory usage
            usedJSHeapSize: memory.usedJSHeapSize || 0,
            totalJSHeapSize: memory.totalJSHeapSize || 0,
            
            // Paint timing
            firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
            firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
        };
        """)
        
        return metrics
    
    @staticmethod
    def create_performance_profile() -> Dict[str, any]:
        """Create an optimized performance profile"""
        return {
            'cache_strategy': 'aggressive',
            'image_loading': 'lazy',
            'javascript_execution': 'async',
            'network_prediction': True,
            'resource_priorities': {
                'tickets': 'high',
                'analytics': 'low',
                'images': 'low',
                'fonts': 'low'
            },
            'prefetch_patterns': [
                '/fansale/tickets/*',
                '/api/tickets/*',
                '/reservation/*'
            ]
        }


class FastTicketChecker:
    """Optimized ticket checking logic"""
    
    def __init__(self, driver):
        self.driver = driver
        self.optimizer = SpeedOptimizer()
        self.last_check_time = 0
        self.cached_selectors = {}
    
    def fast_ticket_check(self) -> Tuple[bool, int]:
        """Ultra-fast ticket availability check"""
        # Use cached selectors if available
        ticket_selector = "[data-qa='ticketToBuy']"
        no_tickets_text = "Sfortunatamente non sono state trovate"
        
        # Quick JavaScript check
        js_check = f"""
        const tickets = document.querySelectorAll('{ticket_selector}');
        const pageText = document.body.innerText;
        
        return {{
            hasTickets: tickets.length > 0,
            ticketCount: tickets.length,
            noTicketsMessage: pageText.includes('{no_tickets_text}'),
            pageReady: document.readyState === 'complete'
        }};
        """
        
        try:
            result = self.driver.execute_script(js_check)
            
            if result['hasTickets']:
                return True, result['ticketCount']
            elif result['noTicketsMessage']:
                return False, 0
            else:
                # Page might still be loading
                return False, -1
                
        except Exception as e:
            logger.error(f"Fast ticket check failed: {e}")
            return False, -1
    
    def get_ticket_details_fast(self) -> List[Dict]:
        """Get ticket details using optimized JavaScript"""
        js_extract = """
        const tickets = document.querySelectorAll('[data-qa="ticketToBuy"]');
        return Array.from(tickets).map(ticket => {
            const priceEl = ticket.querySelector('[class*="price"]');
            const sectionEl = ticket.querySelector('[class*="section"]');
            const quantityEl = ticket.querySelector('[class*="quantity"]');
            
            return {
                price: priceEl ? parseFloat(priceEl.textContent.replace(/[^0-9.,]/g, '').replace(',', '.')) : 0,
                section: sectionEl ? sectionEl.textContent.trim() : '',
                quantity: quantityEl ? parseInt(quantityEl.textContent) : 1,
                element: ticket
            };
        });
        """
        
        try:
            return self.driver.execute_script(js_extract)
        except Exception as e:
            logger.error(f"Failed to extract ticket details: {e}")
            return []


# Performance benchmark utilities
def benchmark_optimization(func):
    """Decorator to benchmark function performance"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.debug(f"{func.__name__} took {end_time - start_time:.3f}s")
        return result
    
    return wrapper


# Example usage in main bot
class OptimizedStealthMaster:
    """Example of how to integrate speed optimizations"""
    
    def __init__(self, config):
        self.config = config
        self.optimizer = SpeedOptimizer()
        self.fast_checker = None
    
    def setup_optimized_driver(self, driver):
        """Apply all speed optimizations to driver"""
        # Inject performance scripts
        driver.execute_script(self.optimizer.get_fast_page_load_script())
        driver.execute_script(self.optimizer.get_resource_hints())
        self.optimizer.optimize_dom_queries(driver)
        
        # Create fast checker
        self.fast_checker = FastTicketChecker(driver)
        
        logger.info("✅ Speed optimizations applied")
    
    @benchmark_optimization
    def check_tickets_optimized(self):
        """Optimized ticket checking"""
        has_tickets, count = self.fast_checker.fast_ticket_check()
        
        if has_tickets:
            # Get details only when tickets are found
            details = self.fast_checker.get_ticket_details_fast()
            return True, details
        
        return False, []


if __name__ == "__main__":
    # Test speed optimizations
    logger.info("Speed optimization module loaded")
    logger.info(f"Performance Chrome options: {len(SpeedOptimizer.get_performance_chrome_options())} options")
    logger.info("Use these optimizations in stealthmaster.py for better performance!")