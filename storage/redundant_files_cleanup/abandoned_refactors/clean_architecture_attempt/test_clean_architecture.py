#!/usr/bin/env python3
"""
Test script for the clean architecture implementation.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test imports
def test_domain_imports():
    """Test domain entity imports"""
    try:
        from domain.entities import Platform, PlatformType, BrowserProfile, TicketOpportunity
        print("✅ Domain entities import successfully")
        
        # Test platform
        platform = Platform(PlatformType.FANSALE)
        print(f"✅ Platform created: {platform.name}")
        
        # Test profile
        profile = BrowserProfile()
        print(f"✅ Profile created: {profile.profile_id}")
        
        return True
    except Exception as e:
        print(f"❌ Domain import error: {e}")
        return False


def test_application_imports():
    """Test application layer imports"""
    try:
        from application.config import ApplicationConfig
        print("✅ Application config imports successfully")
        
        # Test config
        config = ApplicationConfig()
        print(f"✅ Config created with mode: {config.mode}")
        
        return True
    except Exception as e:
        print(f"❌ Application import error: {e}")
        return False


def test_adapter_imports():
    """Test adapter imports"""
    try:
        from adapters.platform_adapter import PlatformAdapter
        from adapters.profile_adapter import ProfileAdapter
        print("✅ Adapters import successfully")
        
        # Test platform adapter
        platform = PlatformAdapter.from_string("fansale")
        print(f"✅ Platform adapter works: {platform.name}")
        
        return True
    except Exception as e:
        print(f"❌ Adapter import error: {e}")
        return False


def test_infrastructure_imports():
    """Test infrastructure imports"""
    try:
        from infrastructure.logging import setup_logging
        print("✅ Infrastructure imports successfully")
        
        # Test logging
        logger = setup_logging(level="INFO")
        print("✅ Logging configured")
        
        return True
    except Exception as e:
        print(f"❌ Infrastructure import error: {e}")
        return False


def test_presentation_imports():
    """Test presentation layer imports"""
    try:
        from presentation.cli import CLIPresentation
        print("✅ Presentation imports successfully")
        
        return True
    except Exception as e:
        print(f"❌ Presentation import error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n🧪 Testing Clean Architecture Implementation\n")
    
    tests = [
        test_domain_imports,
        test_application_imports,
        test_adapter_imports,
        test_infrastructure_imports,
        test_presentation_imports
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n✅ All tests passed! Clean architecture is working.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")


if __name__ == "__main__":
    main()