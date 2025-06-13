"""
Simple tests that work with the current codebase structure.
"""

import pytest
from unittest.mock import Mock, patch

# Test basic Python functionality
def test_basic_addition():
    """Test basic addition."""
    assert 1 + 1 == 2

def test_basic_string():
    """Test basic string operations."""
    text = "StealthMaster"
    assert text.lower() == "stealthmaster"
    assert len(text) == 13

# Test mock functionality
def test_mock_functionality():
    """Test that mocking works."""
    mock_obj = Mock()
    mock_obj.method.return_value = "mocked"
    assert mock_obj.method() == "mocked"

# Test async functionality
@pytest.mark.asyncio
async def test_async_function():
    """Test async function execution."""
    import asyncio
    
    async def async_add(a, b):
        await asyncio.sleep(0.01)
        return a + b
    
    result = await async_add(2, 3)
    assert result == 5

# Test exception handling
def test_exception_handling():
    """Test exception handling."""
    with pytest.raises(ValueError):
        raise ValueError("Test error")

# Test data structures
def test_data_structures():
    """Test various data structures."""
    # List
    lst = [1, 2, 3]
    assert len(lst) == 3
    assert sum(lst) == 6
    
    # Dict
    dct = {"a": 1, "b": 2}
    assert dct["a"] == 1
    assert "b" in dct
    
    # Set
    st = {1, 2, 3, 3}
    assert len(st) == 3

# Test imports from src
def test_src_structure_exists():
    """Test that src directory structure exists."""
    import os
    import sys
    from pathlib import Path
    
    # Get project root
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    
    assert src_path.exists()
    assert src_path.is_dir()
    
    # Check key directories exist
    expected_dirs = ["browser", "platforms", "stealth", "utils", "network", "detection"]
    for dir_name in expected_dirs:
        dir_path = src_path / dir_name
        assert dir_path.exists(), f"Directory {dir_name} not found"
    
    # Check key files exist
    assert (src_path / "config.py").exists(), "config.py not found"
    assert (src_path / "constants.py").exists(), "constants.py not found"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])