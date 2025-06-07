# tests/conftest.py
import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from typing import Dict, Any

from src.profiles.config import ProfileManagerConfig
from src.profiles.models import BrowserProfile


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "app_settings": {
            "mode": "adaptive",
            "version": "2.0.1",
            "dry_run": True
        },
        "targets": [
            {
                "platform": "ticketmaster",
                "event_name": "Test Event",
                "url": "https://example.com/test",
                "enabled": True,
                "priority": "HIGH",
                "interval_s": 60
            }
        ],
        "monitoring_settings": {
            "default_interval_s": 60,
            "min_monitor_interval_s": 15
        },
        "network": {
            "max_connections_per_host": 10,
            "connect_timeout_seconds": 15
        },
        "profile_manager": {
            "num_target_profiles": 5,
            "profiles_per_platform": 2
        }
    }


@pytest.fixture
def mock_profile():
    """Create a mock browser profile."""
    profile = MagicMock(spec=BrowserProfile)
    profile.profile_id = "test_profile_123"
    profile.user_agent = "Mozilla/5.0 (Test Browser)"
    profile.viewport_width = 1920
    profile.viewport_height = 1080
    profile.proxy_config = None
    return profile


@pytest.fixture
def profile_manager_config():
    """Create a test profile manager configuration."""
    return ProfileManagerConfig(
        num_target_profiles=5,
        profiles_per_platform=2,
        persistence_filepath="test_profiles.json"
    )


@pytest.fixture
def mock_playwright():
    """Create a mock playwright instance."""
    playwright = MagicMock()
    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()
    
    playwright.chromium.launch_persistent_context.return_value = context
    context.new_page.return_value = page
    
    return playwright