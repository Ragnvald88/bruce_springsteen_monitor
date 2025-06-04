"""Test all critical imports to diagnose issues"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test each import individually"""
    
    print("Testing imports...")
    print(f"Python path: {sys.path[:3]}...")  # Show first 3 paths
    print(f"Current directory: {os.getcwd()}")
    print("-" * 50)
    
    imports_to_test = [
        # Core imports
        ("Core Enums", "from src.core.enums import OperationMode, PlatformType"),
        ("Core Models", "from src.core.models import EnhancedTicketOpportunity"),
        ("Core Managers", "from src.core.managers import ConnectionPoolManager"),
        
        # Profile imports
        ("Profile Manager", "from src.profiles.manager import ProfileManager"),
        ("Profile Enums", "from src.profiles.enums import DataOptimizationLevel"),
        ("Profile Utils", "from src.profiles.utils import create_profile_manager_from_config"),
        
        # Advanced profile system
        ("Advanced Profile", "from src.core.advanced_profile_system import DetectionEvent"),
        
        # Playwright
        ("Playwright", "from playwright.async_api import Playwright"),
        
        # The problematic orchestrator
        ("Orchestrator", "from src.core.orchestrator import UnifiedOrchestrator"),
    ]
    
    for name, import_statement in imports_to_test:
        try:
            exec(import_statement)
            print(f"✅ {name}: SUCCESS")
        except ImportError as e:
            print(f"❌ {name}: IMPORT ERROR - {e}")
        except Exception as e:
            print(f"❌ {name}: ERROR - {type(e).__name__}: {e}")
    
    print("-" * 50)
    
    # Test if profile directory exists
    profile_dir = project_root / "src" / "profiles"
    print(f"Profile directory exists: {profile_dir.exists()}")
    if profile_dir.exists():
        print(f"Profile directory contents: {list(profile_dir.glob('*.py'))[:5]}...")

if __name__ == "__main__":
    test_imports()