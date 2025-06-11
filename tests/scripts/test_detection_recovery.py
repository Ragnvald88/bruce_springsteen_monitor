import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.detection.monitor import DetectionMonitor
from src.detection.recovery import RecoveryEngine
from src.browser.pool import BrowserPool
from src.stealth.core import StealthCore

class TestDetectionRecovery:
    """Tests for bot detection and recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_detection_pattern_matching(self):
        """DETECT-01: Test detection pattern recognition accuracy."""
        monitor = DetectionMonitor()
        
        test_cases = [
            # (console_message, should_detect)
            ("Chrome headless detected", True),
            ("Automation detected", True),
            ("Normal console log", False),
            ("WebDriver property found", True),
            ("Page loaded successfully", False),
            ("Bot behavior detected", True),
        ]
        
        for message, should_detect in test_cases:
            detected = await monitor.analyze_console_message(message)
            assert detected == should_detect, f"Wrong detection for: {message}"
    
    @pytest.mark.asyncio
    async def test_network_pattern_analysis(self):
        """DETECT-02: Test network pattern bot detection."""
        monitor = DetectionMonitor()
        
        # Simulate suspicious network patterns
        requests = [
            {'url': '/api/check', 'timing': 0.001},  # Too fast
            {'url': '/api/check', 'timing': 0.001},  # Repeated fast
            {'url': '/api/check', 'timing': 0.001},  # Pattern
        ]
        
        detection_score = await monitor.analyze_network_patterns(requests)
        
        assert detection_score > 0.7, f"Failed to detect bot pattern: {detection_score}"
    
    @pytest.mark.asyncio
    async def test_recovery_action_execution(self):
        """DETECT-03: Test recovery action effectiveness."""
        recovery = RecoveryEngine()
        pool = AsyncMock(spec=BrowserPool)
        
        # Mock detected context
        context = AsyncMock()
        context.id = 'test_context'
        context.detection_score = 0.9
        
        # Execute recovery
        recovery_success = await recovery.execute_recovery(context, pool)
        
        assert recovery_success, "Recovery failed"
        assert pool.quarantine_context.called, "Context not quarantined"
        assert pool.create_fresh_context.called, "Fresh context not created"
    
    @pytest.mark.asyncio
    async def test_javascript_detection_checks(self):
        """DETECT-04: Test JavaScript-based detection checks."""
        monitor = DetectionMonitor()
        
        # Mock page
        page = AsyncMock()
        
        # Test various detection vectors
        detection_checks = {
            'navigator.webdriver': True,
            'window.chrome.runtime': None,
            'document.hidden': False,
            'navigator.plugins.length': 3,
        }
        
        page.evaluate = AsyncMock(side_effect=lambda js: 
            detection_checks.get(js.split('.')[1], False)
        )
        
        score = await monitor.calculate_detection_score(page)
        
        assert score > 0.5, f"Detection score too low: {score}"
    
    @pytest.mark.asyncio
    async def test_adaptive_stealth_adjustment(self):
        """DETECT-05: Test adaptive stealth level adjustment."""
        stealth = StealthCore()
        
        # Initial detection
        await stealth.record_detection_event({
            'type': 'console',
            'message': 'Bot detected',
            'severity': 'high'
        })
        
        # Check if stealth level increased
        initial_level = stealth.current_level
        
        # More detections
        for _ in range(3):
            await stealth.record_detection_event({
                'type': 'network',
                'severity': 'medium'
            })
        
        final_level = stealth.current_level
        
        assert final_level > initial_level, "Stealth level did not adapt"
    
    @pytest.mark.asyncio
    async def test_false_positive_filtering(self):
        """DETECT-06: Test false positive filtering in detection."""
        monitor = DetectionMonitor()
        
        # Known false positive patterns
        false_positives = [
            "Chrome PDF viewer",
            "Extensions loaded",
            "DevTools agent",
        ]
        
        for pattern in false_positives:
            detected = await monitor.analyze_console_message(pattern)
            assert not detected, f"False positive not filtered: {pattern}"