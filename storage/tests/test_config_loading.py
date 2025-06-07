# tests/test_config_loading.py
import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from src.main import load_and_merge_configs


class TestConfigLoading:
    """Test suite for configuration loading functionality."""
    
    def test_load_basic_config(self, temp_config_dir, sample_config):
        """Test loading a basic configuration file."""
        config_file = temp_config_dir / "config.yaml"
        
        # Write sample config to file
        with open(config_file, 'w') as f:
            yaml.safe_dump(sample_config, f)
        
        loaded_config = load_and_merge_configs(config_file)
        
        assert loaded_config['app_settings']['mode'] == 'adaptive'
        assert loaded_config['app_settings']['version'] == '2.0.1'
        assert len(loaded_config['targets']) == 1
        assert '_metadata' in loaded_config
    
    def test_load_config_file_not_found(self, temp_config_dir):
        """Test loading a non-existent configuration file."""
        non_existent_file = temp_config_dir / "non_existent.yaml"
        
        with pytest.raises(FileNotFoundError):
            load_and_merge_configs(non_existent_file)
    
    def test_load_config_with_beast_mode(self, temp_config_dir, sample_config):
        """Test loading config with beast mode merge."""
        # Create main config
        main_config = sample_config.copy()
        main_config['app_settings']['mode'] = 'beast'
        
        # Create beast config
        beast_config = {
            'strike_settings': {
                'max_parallel': 10,
                'aggressive_mode': True
            },
            'profile_manager': {
                'selection_quality_min_tier': 1
            }
        }
        
        main_config_file = temp_config_dir / "config.yaml"
        beast_config_file = temp_config_dir / "beast_config.yaml"
        
        with open(main_config_file, 'w') as f:
            yaml.safe_dump(main_config, f)
        
        with open(beast_config_file, 'w') as f:
            yaml.safe_dump(beast_config, f)
        
        loaded_config = load_and_merge_configs(main_config_file, beast_config_file)
        
        # Should have merged beast config
        assert loaded_config['strike_settings']['max_parallel'] == 10
        assert loaded_config['strike_settings']['aggressive_mode'] is True
        assert loaded_config['profile_manager']['selection_quality_min_tier'] == 1
    
    def test_config_validation_missing_sections(self, temp_config_dir):
        """Test config validation when required sections are missing."""
        incomplete_config = {
            'app_settings': {
                'mode': 'adaptive'
            }
            # Missing 'targets' and 'monitoring_settings'
        }
        
        config_file = temp_config_dir / "incomplete.yaml"
        with open(config_file, 'w') as f:
            yaml.safe_dump(incomplete_config, f)
        
        loaded_config = load_and_merge_configs(config_file)
        
        # Should add missing sections
        assert 'targets' in loaded_config
        assert 'monitoring_settings' in loaded_config
        assert loaded_config['targets'] == {}
        assert loaded_config['monitoring_settings'] == {}
    
    def test_config_metadata_generation(self, temp_config_dir, sample_config):
        """Test that metadata is properly generated."""
        config_file = temp_config_dir / "config.yaml"
        
        with open(config_file, 'w') as f:
            yaml.safe_dump(sample_config, f)
        
        loaded_config = load_and_merge_configs(config_file)
        
        metadata = loaded_config['_metadata']
        assert 'config_file_path' in metadata
        assert 'loaded_at' in metadata
        assert 'config_hash' in metadata
        assert len(metadata['config_hash']) == 8  # Hash should be 8 characters
    
    def test_deep_merge_functionality(self, temp_config_dir):
        """Test deep merge functionality between configs."""
        main_config = {
            'app_settings': {
                'mode': 'adaptive',
                'version': '1.0'
            },
            'network': {
                'timeout': 30,
                'retries': 3
            }
        }
        
        beast_config = {
            'app_settings': {
                'mode': 'beast',  # Should override
                'debug': True     # Should add
            },
            'network': {
                'timeout': 10,    # Should override
                'max_connections': 100  # Should add
            },
            'new_section': {      # Should add entirely
                'enabled': True
            }
        }
        
        main_file = temp_config_dir / "main.yaml"
        beast_file = temp_config_dir / "beast.yaml"
        
        with open(main_file, 'w') as f:
            yaml.safe_dump(main_config, f)
        with open(beast_file, 'w') as f:
            yaml.safe_dump(beast_config, f)
        
        # Modify main config to trigger beast mode
        main_config['app_settings']['mode'] = 'beast'
        with open(main_file, 'w') as f:
            yaml.safe_dump(main_config, f)
        
        loaded_config = load_and_merge_configs(main_file, beast_file)
        
        # Check overrides
        assert loaded_config['app_settings']['mode'] == 'beast'
        assert loaded_config['network']['timeout'] == 10
        
        # Check additions
        assert loaded_config['app_settings']['debug'] is True
        assert loaded_config['network']['max_connections'] == 100
        assert loaded_config['new_section']['enabled'] is True
        
        # Check preserved values
        assert loaded_config['app_settings']['version'] == '1.0'
        assert loaded_config['network']['retries'] == 3
    
    def test_invalid_yaml_handling(self, temp_config_dir):
        """Test handling of invalid YAML files."""
        config_file = temp_config_dir / "invalid.yaml"
        
        # Write invalid YAML
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: ::::")
        
        with pytest.raises(yaml.YAMLError):
            load_and_merge_configs(config_file)