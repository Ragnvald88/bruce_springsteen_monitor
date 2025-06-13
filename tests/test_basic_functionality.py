"""
Basic functionality tests for StealthMaster.
Tests core components that exist in the current codebase.
"""

import asyncio
import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_settings, Platform, AppMode
from src.profiles.manager import ProfileManager
from src.browser.launcher import launcher
from src.stealth.ultimate_bypass import UltimateAkamaiBypass, BrowserSession
from src.core.exceptions import StealthMasterError
from src.core.resilience import retry, with_timeout


class TestConfiguration:
    """Test configuration loading and validation."""
    
    def test_load_settings(self):
        """Test loading settings from config."""
        with patch('src.config.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.read_text.return_value = """
app_settings:
  mode: stealth
  version: "2.0.0"
  dry_run: false
  mode_configs:
    stealth:
      max_concurrent_monitors: 3
      max_concurrent_strikes: 1
"""
            
            with patch('src.config.yaml.safe_load') as mock_yaml:
                mock_yaml.return_value = {
                    'app_settings': {
                        'mode': 'stealth',
                        'version': '2.0.0',
                        'dry_run': False,
                        'mode_configs': {
                            'stealth': {
                                'max_concurrent_monitors': 3,
                                'max_concurrent_strikes': 1,
                                'max_connections': 50,
                                'cache_size': 1000
                            }
                        }
                    }
                }
                
                settings = load_settings()
                assert settings is not None
                assert settings.app_settings.mode == AppMode.STEALTH
    
    def test_platform_enum(self):
        """Test platform enumeration."""
        assert Platform.FANSALE.value == "fansale"
        assert Platform.TICKETMASTER.value == "ticketmaster"
        assert Platform.VIVATICKET.value == "vivaticket"


class TestBrowserLauncher:
    """Test browser launcher functionality."""
    
    @pytest.mark.asyncio
    async def test_browser_launch(self):
        """Test browser launch functionality."""
        # Mock nodriver core
        with patch('src.browser.launcher.nodriver_core') as mock_nodriver:
            mock_browser_data = {"browser": Mock(), "fingerprint": {}}
            mock_nodriver.create_stealth_browser = AsyncMock(return_value=mock_browser_data)
            
            browser_id = await launcher.launch_browser()
            
            assert browser_id is not None
            assert browser_id in launcher.browsers
            mock_nodriver.create_stealth_browser.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_browser_context_creation(self):
        """Test browser context creation."""
        # Setup mock browser
        browser_id = "test-browser-id"
        launcher.browsers[browser_id] = {"browser": Mock()}
        
        with patch('src.browser.launcher.nodriver_core') as mock_nodriver:
            mock_context_data = {"context": Mock()}
            mock_nodriver.create_stealth_context = AsyncMock(return_value=mock_context_data)
            
            context_id = await launcher.create_context(browser_id)
            
            assert context_id is not None
            assert context_id in launcher.contexts


class TestProfileManager:
    """Test profile management."""
    
    def test_profile_manager_init(self):
        """Test profile manager initialization."""
        mock_settings = Mock()
        manager = ProfileManager(mock_settings)
        
        assert manager.settings == mock_settings
        assert hasattr(manager, 'profiles')


class TestUltimateBypass:
    """Test ultimate bypass functionality."""
    
    def test_browser_session_creation(self):
        """Test BrowserSession data structure."""
        session = BrowserSession(
            browser=Mock(),
            context=Mock(),
            page=Mock(),
            process=Mock(),
            profile_name="test",
            playwright=Mock()
        )
        
        assert session.profile_name == "test"
        assert session.age_seconds >= 0
        assert session.idle_seconds >= 0
    
    @pytest.mark.asyncio
    async def test_session_health_check(self):
        """Test session health checking."""
        bypass = UltimateAkamaiBypass()
        
        # Create mock healthy session
        mock_page = AsyncMock()
        mock_page.evaluate.return_value = 2  # Healthy
        
        session = BrowserSession(
            browser=Mock(),
            context=Mock(),
            page=mock_page,
            process=Mock(poll=Mock(return_value=None)),
            profile_name="test",
            playwright=Mock()
        )
        
        is_healthy = await bypass._is_session_healthy(session)
        assert is_healthy


class TestErrorHandling:
    """Test error handling functionality."""
    
    def test_stealth_master_error(self):
        """Test custom exception creation."""
        error = StealthMasterError("Test error")
        assert str(error) == "StealthMasterError(medium): Test error"
        assert error.recoverable is True
    
    @pytest.mark.asyncio
    async def test_retry_decorator(self):
        """Test retry functionality."""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = await flaky_function()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_timeout_decorator(self):
        """Test timeout functionality."""
        @with_timeout(0.1)
        async def quick_function():
            await asyncio.sleep(0.05)
            return "completed"
        
        result = await quick_function()
        assert result == "completed"
        
        @with_timeout(0.05)
        async def slow_function():
            await asyncio.sleep(0.2)
            return "completed"
        
        from src.core.exceptions import TimeoutError
        with pytest.raises(TimeoutError):
            await slow_function()


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_browser_with_ultimate_bypass(self):
        """Test browser launch with ultimate bypass."""
        bypass = UltimateAkamaiBypass()
        
        # Mock all external dependencies
        with patch('src.stealth.ultimate_bypass.ChromeDiscovery.find_chrome', return_value='/mock/chrome'):
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.poll.return_value = None
                mock_popen.return_value = mock_process
                
                with patch('playwright.async_api.async_playwright') as mock_pw:
                    mock_playwright = AsyncMock()
                    mock_browser = AsyncMock()
                    mock_context = AsyncMock()
                    mock_page = AsyncMock()
                    
                    mock_context.pages = [mock_page]
                    mock_browser.contexts = [mock_context]
                    mock_page.evaluate.return_value = 2
                    
                    mock_pw.return_value.start.return_value = mock_playwright
                    mock_playwright.chromium.connect_over_cdp.return_value = mock_browser
                    
                    # Test session creation
                    session = await bypass.get_or_create_session("test-profile")
                    
                    assert session is not None
                    assert session.profile_name == "test-profile"
                    assert bypass._sessions["test-profile"] == session
                    
                    # Test session reuse
                    session2 = await bypass.get_or_create_session("test-profile")
                    assert session2 == session


if __name__ == "__main__":
    pytest.main([__file__, "-v"])