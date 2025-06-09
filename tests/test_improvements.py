#!/usr/bin/env python3
"""Test improvements and optimizations for StealthMaster."""

import asyncio
import time
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from stealth.core import StealthCore
from stealth.fingerprint import FingerprintGenerator
from stealth.injections import StealthInjections
from playwright.async_api import async_playwright


class TestImprovements:
    """Test and implement improvements."""
    
    async def test_improved_stealth(self):
        """Test improved stealth implementation."""
        print("\n🔧 Testing Improved Stealth Implementation...")
        
        # Create improved stealth core
        stealth_core = ImprovedStealthCore()
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--disable-extensions",
                "--disable-gpu",
                "--disable-default-apps",
                "--disable-popup-blocking",
                "--window-size=1920,1080",
                "--start-maximized",
                "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            ]
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York"
        )
        
        page = await context.new_page()
        
        # Apply improved stealth
        await stealth_core.apply_improved_stealth(page)
        
        # Test on bot detection site
        await page.goto("https://bot.sannysoft.com/", wait_until="networkidle", timeout=30000)
        
        # Check detection
        results = await page.evaluate("""
            () => {
                const tests = {};
                
                // Check each test row
                const rows = document.querySelectorAll('table tr');
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 2) {
                        const testName = cells[0].textContent.trim();
                        const result = cells[1].textContent.trim();
                        const passed = cells[1].classList.contains('passed');
                        tests[testName] = { result, passed };
                    }
                });
                
                return tests;
            }
        """)
        
        # Print results
        print("\n📊 Bot Detection Test Results:")
        passed_count = 0
        total_count = 0
        
        for test_name, result in results.items():
            if test_name:
                total_count += 1
                status = "✅" if result["passed"] else "❌"
                print(f"  {status} {test_name}: {result['result']}")
                if result["passed"]:
                    passed_count += 1
        
        success_rate = (passed_count / total_count * 100) if total_count > 0 else 0
        print(f"\n  Success Rate: {passed_count}/{total_count} ({success_rate:.1f}%)")
        
        # Take screenshot for evidence
        await page.screenshot(path="tests/improved_bot_detection.png")
        
        await browser.close()
        await playwright.stop()
        
        return success_rate > 80  # Target 80% pass rate


class ImprovedStealthCore(StealthCore):
    """Improved stealth core with better evasion."""
    
    async def apply_improved_stealth(self, page):
        """Apply improved stealth measures."""
        # Generate fingerprint
        fingerprint = self.fingerprint_gen.generate()
        
        # Pre-page scripts
        await page.add_init_script("""
            // Remove webdriver before page loads
            delete Object.getPrototypeOf(navigator).webdriver;
            
            // Fix chrome.runtime
            if (!window.chrome) {
                window.chrome = {};
            }
            window.chrome.runtime = {
                connect: () => {},
                sendMessage: () => {},
                onMessage: { addListener: () => {} }
            };
            
            // Fix permissions
            const originalQuery = navigator.permissions.query;
            navigator.permissions.query = async (parameters) => {
                if (parameters.name === 'notifications') {
                    return { state: 'prompt', onchange: null };
                }
                return originalQuery(parameters);
            };
            
            // Mock plugins before they're accessed
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const arr = [
                        {
                            name: 'Chrome PDF Plugin',
                            description: 'Portable Document Format',
                            filename: 'internal-pdf-viewer',
                            length: 1,
                            0: { type: 'application/x-google-chrome-pdf', suffixes: 'pdf' }
                        },
                        {
                            name: 'Chrome PDF Viewer',
                            description: 'Portable Document Format',
                            filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                            length: 1,
                            0: { type: 'application/pdf', suffixes: 'pdf' }
                        },
                        {
                            name: 'Native Client',
                            description: 'Native Client Executable',
                            filename: 'internal-nacl-plugin',
                            length: 2,
                            0: { type: 'application/x-nacl', suffixes: '' },
                            1: { type: 'application/x-pnacl', suffixes: '' }
                        }
                    ];
                    arr.item = (i) => arr[i];
                    arr.namedItem = (name) => arr.find(p => p.name === name);
                    arr.refresh = () => {};
                    return arr;
                }
            });
            
            // Fix language detection
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // WebGL vendor spoofing
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 0x1F00) return 'Intel Inc.'; // VENDOR
                if (parameter === 0x1F01) return 'Intel Iris OpenGL Engine'; // RENDERER
                return getParameter.call(this, parameter);
            };
            
            // Battery API
            navigator.getBattery = async () => ({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 0.99,
                onchargingchange: null,
                onchargingtimechange: null,
                ondischargingtimechange: null,
                onlevelchange: null
            });
        """)
        
        # Apply CDP stealth
        await self.cdp_stealth.apply_page_stealth(page)
        
        # Apply standard stealth
        await self._inject_stealth_scripts(page, fingerprint)
        
        # Initialize behaviors
        await self.human_behavior.initialize(page)
        
        # Mark as protected
        page._stealth_applied = True
        page._stealth_fingerprint = fingerprint


async def main():
    """Run improvement tests."""
    tester = TestImprovements()
    
    # Run improved stealth test
    success = await tester.test_improved_stealth()
    
    if success:
        print("\n✅ Improvements successful! Bot detection evasion improved.")
    else:
        print("\n❌ Improvements need more work.")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)