import pytest
import asyncio
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from playwright.async_api import async_playwright
import psutil
import tracemalloc

# Import StealthMaster modules
from src.stealth.core import StealthCore
from src.stealth.fingerprint import FingerprintGenerator
from src.stealth.behaviors import HumanBehavior
from src.stealth.cdp_bypass_engine import CDPBypassEngine
from src.browser.launcher import BrowserLauncher
from src.browser.pool import BrowserPool
from src.detection.monitor import DetectionMonitor

class TestStealthIntegrity:
    """Tests for anti-bot detection evasion capabilities."""
    
    @pytest.mark.asyncio
    async def test_fingerprint_uniqueness_and_entropy(self):
        """STEALTH-01: Verify fingerprint generation produces unique, high-entropy values."""
        generator = FingerprintGenerator()
        fingerprints = []
        
        # Generate 100 fingerprints
        for _ in range(100):
            fp = await generator.generate()
            fingerprints.append(fp)
        
        # Check uniqueness
        unique_fps = len(set(json.dumps(fp, sort_keys=True) for fp in fingerprints))
        uniqueness_ratio = unique_fps / len(fingerprints)
        
        # Check entropy of canvas fingerprints
        canvas_hashes = [fp.get('canvas_hash', '') for fp in fingerprints]
        unique_canvas = len(set(canvas_hashes))
        
        assert uniqueness_ratio > 0.95, f"Fingerprint uniqueness too low: {uniqueness_ratio}"
        assert unique_canvas > 90, f"Canvas fingerprint entropy too low: {unique_canvas}/100"
    
    @pytest.mark.asyncio
    async def test_webdriver_detection_bypass(self):
        """STEALTH-02: Verify WebDriver properties are properly masked."""
        launcher = BrowserLauncher()
        
        async with async_playwright() as p:
            browser = await launcher.launch(p)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Navigate to detection test page
            await page.goto("data:text/html,<html><body>Test</body></html>")
            
            # Check for WebDriver indicators
            webdriver_present = await page.evaluate("""
                () => {
                    const indicators = [
                        navigator.webdriver,
                        window.chrome && window.chrome.runtime,
                        document.__proto__.selenium_wrapped,
                        window.cdc_adoQpoasnfa76pfcZLmcfl_Promise,
                        window.cdc_adoQpoasnfa76pfcZLmcfl_Array
                    ];
                    return indicators.some(ind => ind !== undefined && ind !== false);
                }
            """)
            
            # Check automation flags
            automation_flags = await page.evaluate("""
                () => {
                    return {
                        webdriver: navigator.webdriver,
                        permissions: Notification.permission,
                        plugins: navigator.plugins.length,
                        languages: navigator.languages.length
                    };
                }
            """)
            
            await browser.close()
            
            assert not webdriver_present, "WebDriver indicators detected"
            assert automation_flags['webdriver'] is False, "navigator.webdriver not masked"
            assert automation_flags['plugins'] > 0, "No plugins detected (suspicious)"
            assert automation_flags['languages'] > 0, "No languages detected (suspicious)"
    
    @pytest.mark.asyncio
    async def test_mouse_movement_entropy(self):
        """STEALTH-03: Verify mouse movements have human-like entropy."""
        behavior = HumanBehavior()
        movements = []
        
        # Generate 50 mouse movements
        for _ in range(50):
            path = await behavior.generate_mouse_path(
                start=(100, 100),
                end=(500, 500)
            )
            movements.extend(path)
        
        # Calculate movement entropy
        deltas = []
        for i in range(1, len(movements)):
            dx = movements[i][0] - movements[i-1][0]
            dy = movements[i][1] - movements[i-1][1]
            deltas.append((dx, dy))
        
        # Check for variation in movement patterns
        unique_deltas = len(set(deltas))
        entropy_score = unique_deltas / len(deltas)
        
        # Check for bezier curve characteristics
        acceleration_changes = 0
        for i in range(2, len(deltas)):
            prev_accel = (deltas[i-1][0] - deltas[i-2][0], deltas[i-1][1] - deltas[i-2][1])
            curr_accel = (deltas[i][0] - deltas[i-1][0], deltas[i][1] - deltas[i-1][1])
            if prev_accel != curr_accel:
                acceleration_changes += 1
        
        assert entropy_score > 0.7, f"Mouse movement entropy too low: {entropy_score}"
        assert acceleration_changes > len(deltas) * 0.3, "Mouse movements too linear"
    
    @pytest.mark.asyncio
    async def test_cdp_detection_evasion(self):
        """STEALTH-04: Verify Chrome DevTools Protocol detection is bypassed."""
        cdp_bypass = CDPBypassEngine()
        
        # Mock CDP session
        mock_session = AsyncMock()
        mock_session.send = AsyncMock()
        
        # Apply bypasses
        await cdp_bypass.apply_all_bypasses(mock_session)
        
        # Verify critical CDP commands were intercepted
        call_args = [call[0][0] for call in mock_session.send.call_args_list]
        
        required_bypasses = [
            'Page.addScriptToEvaluateOnNewDocument',
            'Runtime.enable',
            'Network.setUserAgentOverride'
        ]
        
        for bypass in required_bypasses:
            assert any(bypass in arg for arg in call_args), f"CDP bypass missing: {bypass}"
    
    @pytest.mark.asyncio
    async def test_tls_fingerprint_rotation(self):
        """STEALTH-05: Verify TLS fingerprints rotate properly."""
        from src.network.tls_fingerprint import TLSFingerprintManager
        
        manager = TLSFingerprintManager()
        fingerprints = []
        
        # Get 10 fingerprints
        for _ in range(10):
            fp = await manager.get_fingerprint()
            fingerprints.append(fp)
            await manager.rotate()
        
        # Check diversity
        unique_ciphers = len(set(tuple(fp['ciphers']) for fp in fingerprints))
        unique_extensions = len(set(tuple(fp['extensions']) for fp in fingerprints))
        
        assert unique_ciphers >= 3, f"TLS cipher diversity too low: {unique_ciphers}"
        assert unique_extensions >= 3, f"TLS extension diversity too low: {unique_extensions}"