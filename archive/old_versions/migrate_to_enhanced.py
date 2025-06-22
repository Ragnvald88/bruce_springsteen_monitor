#!/usr/bin/env python3
"""
Migration script to update stealthmaster.py with enhanced anti-detection features
This script will backup the original and apply the improvements incrementally
"""

import shutil
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def create_backup():
    """Create a backup of the original stealthmaster.py"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"stealthmaster_backup_{timestamp}.py"
    
    try:
        shutil.copy2("stealthmaster.py", backup_name)
        logger.info(f"✅ Created backup: {backup_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create backup: {e}")
        return False


def apply_enhancements():
    """Apply the enhanced version"""
    try:
        # Copy enhanced version to main file
        shutil.copy2("stealthmaster_enhanced.py", "stealthmaster.py")
        logger.info("✅ Applied enhanced version to stealthmaster.py")
        
        # Update imports in other files if needed
        update_imports()
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to apply enhancements: {e}")
        return False


def update_imports():
    """Update imports in related files"""
    files_to_check = ["test_stealthmaster.py", "run_benchmarks.py"]
    
    for file in files_to_check:
        if os.path.exists(file):
            try:
                with open(file, 'r') as f:
                    content = f.read()
                
                # Update class name if needed
                if "StealthMaster" in content and "StealthMasterEnhanced" not in content:
                    content = content.replace("StealthMaster(", "StealthMasterEnhanced(")
                    content = content.replace("from stealthmaster import StealthMaster", 
                                            "from stealthmaster import StealthMasterEnhanced")
                    
                    with open(file, 'w') as f:
                        f.write(content)
                    
                    logger.info(f"✅ Updated imports in {file}")
            except Exception as e:
                logger.warning(f"⚠️ Could not update {file}: {e}")


def verify_dependencies():
    """Check if all required dependencies are available"""
    required_modules = ["numpy", "scipy"]
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        logger.warning(f"⚠️ Missing dependencies: {', '.join(missing)}")
        logger.info("Install with: pip install " + " ".join(missing))
        return False
    
    return True


def update_config():
    """Update config.yaml with new anti-detection settings if needed"""
    try:
        import yaml
        
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)
        
        # Add anti-detection settings if missing
        if 'anti_detection' not in config:
            config['anti_detection'] = {
                'randomize_canvas': True,
                'spoof_webgl': True,
                'human_typing': True,
                'mouse_movements': True,
                'random_scrolling': True,
                'random_delays': True,
                'detect_honeypots': True,
                'monitor_detection_level': 'high'
            }
            
            with open("config.yaml", 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            logger.info("✅ Updated config.yaml with anti-detection settings")
    except Exception as e:
        logger.warning(f"⚠️ Could not update config.yaml: {e}")


def main():
    """Main migration process"""
    logger.info("🚀 Starting StealthMaster enhancement migration...")
    
    # Step 1: Verify dependencies
    if not verify_dependencies():
        logger.error("❌ Please install missing dependencies first")
        return False
    
    # Step 2: Create backup
    if not create_backup():
        logger.error("❌ Migration aborted - could not create backup")
        return False
    
    # Step 3: Apply enhancements
    if not apply_enhancements():
        logger.error("❌ Migration failed - your original file is intact")
        return False
    
    # Step 4: Update config
    update_config()
    
    logger.info("✅ Migration completed successfully!")
    logger.info("📝 Summary of enhancements applied:")
    logger.info("  - Enhanced Chrome options for maximum stealth")
    logger.info("  - Comprehensive JavaScript injection to prevent detection")
    logger.info("  - Human-like typing and mouse movements")
    logger.info("  - Smart resource blocking (not too aggressive)")
    logger.info("  - Browser profile persistence")
    logger.info("  - Advanced proxy handling")
    logger.info("  - Detection testing on startup")
    logger.info("  - Improved CAPTCHA detection")
    logger.info("  - Better error recovery")
    
    logger.info("\n🎯 Next steps:")
    logger.info("1. Review the changes in stealthmaster.py")
    logger.info("2. Run detection tests: python stealthmaster.py --test-detection")
    logger.info("3. Start the bot normally: python stealthmaster.py")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)