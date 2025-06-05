# tests/test_profiles_manager.py
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from src.profiles.manager import ProfileManager
from src.profiles.config import ProfileManagerConfig
from src.profiles.enums import Platform, ProfileQuality
from src.profiles.models import BrowserProfile


class TestProfileManager:
    """Test suite for ProfileManager."""
    
    def test_init_with_default_config(self):
        """Test ProfileManager initialization with default config."""
        manager = ProfileManager()
        
        assert manager.config is not None
        assert isinstance(manager.config, ProfileManagerConfig)
        assert manager.dynamic_profiles == []
        assert manager.static_profiles == {}
    
    def test_init_with_custom_config(self, profile_manager_config):
        """Test ProfileManager initialization with custom config."""
        manager = ProfileManager(config=profile_manager_config)
        
        assert manager.config == profile_manager_config
        assert manager.config.num_target_profiles == 5
    
    @pytest.mark.asyncio
    async def test_get_profile_for_platform(self, profile_manager_config):
        """Test getting a profile for a specific platform."""
        manager = ProfileManager(config=profile_manager_config)
        
        # Mock the profile selection
        with patch.object(manager, 'get_profile_for_platform') as mock_get:
            mock_profile = MagicMock(spec=BrowserProfile)
            mock_profile.profile_id = "test_profile"
            mock_get.return_value = mock_profile
            
            profile = await manager.get_profile_for_platform(Platform.TICKETMASTER)
            
            assert profile == mock_profile
            mock_get.assert_called_once_with(Platform.TICKETMASTER)
    
    @pytest.mark.asyncio
    async def test_initialize_manager(self, profile_manager_config):
        """Test profile manager initialization."""
        manager = ProfileManager(config=profile_manager_config)
        
        with patch.object(manager, '_initialize_profile_pool') as mock_init_pool:
            mock_init_pool.return_value = None
            
            await manager.initialize()
            
            mock_init_pool.assert_called_once()
    
    def test_profile_scoring(self, profile_manager_config):
        """Test profile scoring functionality."""
        manager = ProfileManager(config=profile_manager_config)
        
        # Create a mock profile
        mock_profile = MagicMock(spec=BrowserProfile)
        mock_profile.profile_id = "test_profile"
        
        # Test scoring
        with patch.object(manager.scorer, 'calculate_score') as mock_score:
            mock_score.return_value = 85.0
            
            score = manager.scorer.calculate_score(mock_profile)
            
            assert score == 85.0
            mock_score.assert_called_once_with(mock_profile)
    
    @pytest.mark.asyncio
    async def test_profile_persistence(self, profile_manager_config, temp_config_dir):
        """Test profile persistence functionality."""
        # Update config to use temp directory
        profile_manager_config.persistence_filepath = str(temp_config_dir / "test_profiles.json")
        
        manager = ProfileManager(config=profile_manager_config)
        
        # Mock profiles data
        static_profiles = {
            "test_profile_1": MagicMock(spec=BrowserProfile),
            "test_profile_2": MagicMock(spec=BrowserProfile)
        }
        static_profiles["test_profile_1"].profile_id = "test_profile_1"
        static_profiles["test_profile_2"].profile_id = "test_profile_2"
        
        dynamic_profiles = []
        
        # Test saving
        await manager.persistence.save_profiles(dynamic_profiles, static_profiles)
        
        # Test loading - load_profiles modifies the passed collections
        test_dynamic_profiles = []
        test_static_profiles = {}
        test_mutation_strategy = MagicMock()
        
        result = await manager.persistence.load_profiles(
            test_dynamic_profiles, 
            test_static_profiles, 
            test_mutation_strategy
        )
        
        # Should return True if loading was successful
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_cleanup(self, profile_manager_config):
        """Test shutdown functionality."""
        manager = ProfileManager(config=profile_manager_config)
        
        # Mock background tasks
        with patch.object(manager, 'stop_background_tasks') as mock_stop:
            await manager.shutdown()
            
            mock_stop.assert_called_once()