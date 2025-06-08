# src/main.py
#!/usr/bin/env python3
"""
StealthMaster AI v3.0 - Main Entry Point
Example of how your main.py should look after v3.0 update
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
import argparse
import yaml
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
from dotenv import load_dotenv
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Import v3 orchestrator - UPDATED IMPORT
from src.core.enhanced_orchestrator_v3 import EnhancedOrchestrator as Orchestrator
# OR if your code expects UltimateOrchestrator:
# from src.core.orchestrator_v3 import UltimateOrchestrator

# Configuration
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "config.yaml"


def setup_logging(config: dict) -> None:
    """Configure logging for v3"""
    
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    
    # Create logs directory
    log_dir = PROJECT_ROOT / log_config.get('log_directory', 'logs')
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with color support
    try:
        from colorama import init, Fore, Style
        init(autoreset=True)
        
        class ColoredFormatter(logging.Formatter):
            COLORS = {
                'DEBUG': Fore.CYAN,
                'INFO': Fore.GREEN,
                'WARNING': Fore.YELLOW,
                'ERROR': Fore.RED,
                'CRITICAL': Fore.RED + Style.BRIGHT
            }
            
            def format(self, record):
                levelname = record.levelname
                if levelname in self.COLORS:
                    record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
                return super().format(record)
        
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
    except ImportError:
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    from logging.handlers import RotatingFileHandler
    
    main_log = log_dir / 'stealthmaster.log'
    file_handler = RotatingFileHandler(
        main_log, maxBytes=10*1024*1024, backupCount=3
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    ))
    root_logger.addHandler(file_handler)
    
    # Suppress noisy libraries
    for lib in ['httpx', 'httpcore', 'playwright._impl', 'websockets', 'urllib3']:
        logging.getLogger(lib).setLevel(logging.WARNING)
    
    logging.info("🛡️ StealthMaster AI v3.0 logging configured")


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file"""
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Process environment variables
    def replace_env_vars(obj):
        if isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        elif isinstance(obj, dict):
            return {k: replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_env_vars(item) for item in obj]
        return obj
    
    return replace_env_vars(config)


def print_banner():
    """Print StealthMaster AI banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║        🎸 STEALTHMASTER AI v3.0 - ULTIMATE EDITION 🎸               ║
    ║                                                                      ║
    ║     Undetectable • Ultra-Efficient • Unstoppable                    ║
    ║                                                                      ║
    ║     CDP Bypass: ✅  Data Optimization: ✅  Stealth: ✅              ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def validate_config(config: dict) -> bool:
    """Validate configuration has required fields"""
    
    required = ['targets', 'proxy_settings', 'app_settings']
    
    for field in required:
        if field not in config:
            logging.error(f"Missing required config field: {field}")
            return False
    
    # Check proxy configuration
    proxy_config = config.get('proxy_settings', {})
    if proxy_config.get('enabled', False):
        if not proxy_config.get('primary_pool'):
            logging.error("Proxy enabled but no proxies configured")
            return False
    
    # Check targets
    targets = config.get('targets', [])
    enabled_targets = [t for t in targets if t.get('enabled', True)]
    
    if not enabled_targets:
        logging.error("No enabled targets found")
        return False
    
    logging.info(f"✅ Configuration validated: {len(enabled_targets)} active targets")
    return True


async def main():
    """Main entry point for StealthMaster AI v3.0"""
    
    parser = argparse.ArgumentParser(
        description='StealthMaster AI v3.0 - Ultimate Ticket Hunter'
    )
    parser.add_argument(
        '-c', '--config', 
        type=Path, 
        default=DEFAULT_CONFIG,
        help='Configuration file path'
    )
    parser.add_argument(
        '--gui',
        action='store_true',
        help='Launch with GUI interface'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode'
    )
    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Run performance benchmark'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        sys.exit(1)
    
    # Setup logging
    setup_logging(config)
    
    # Print banner
    print_banner()
    
    # Run benchmark if requested
    if args.benchmark:
        from src.testing.stealth_test_framework import StealthTestFramework
        logging.info("🧪 Running v3.0 benchmark tests...")
        
        framework = StealthTestFramework()
        report = await framework.run_all_tests()
        
        print(f"\n✅ Benchmark complete! Grade: {report['summary']['grade']}")
        return
    
    # Launch GUI if requested
    if args.gui:
        logging.info("🎮 Launching StealthMaster AI GUI...")
        
        from src.ui.stealth_gui_v3 import StealthMasterGUI
        app = StealthMasterGUI()
        app.run()
        return
    
    # Validate configuration
    if not validate_config(config):
        sys.exit(1)
    
    # Log startup info
    logging.info(f"🚀 Starting StealthMaster AI v3.0")
    logging.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"🔧 Mode: {config['app_settings']['mode']}")
    logging.info(f"🌐 Proxy: {'Enabled' if config['proxy_settings']['enabled'] else 'Disabled'}")
    
    # List targets
    targets = config.get('targets', [])
    enabled_targets = [t for t in targets if t.get('enabled', True)]
    
    logging.info(f"\n📍 ACTIVE TARGETS:")
    for target in enabled_targets:
        logging.info(f"   ✅ {target['event_name']} - {target['platform'].upper()}")
    
    # Create orchestrator with v3.0
    orchestrator = Orchestrator(config)
    
    try:
        # Initialize all v3.0 subsystems
        await orchestrator.initialize()
        
        # Test mode
        if args.test:
            logging.info("🧪 Running in test mode - single check only")
            
            # Run single check for each monitor
            for monitor_id, monitor in orchestrator.monitors.items():
                try:
                    opportunities = await monitor.handler.check_tickets()
                    logging.info(
                        f"Test result for {monitor.platform}: "
                        f"{len(opportunities)} tickets found"
                    )
                except Exception as e:
                    logging.error(f"Test failed for {monitor.platform}: {e}")
            
            # Show v3.0 stats
            stats = orchestrator.get_status()
            logging.info("\n📊 V3.0 System Status:")
            logging.info(f"   CDP Protection: {stats['system']['cdp_status']}")
            logging.info(f"   Behavior Pattern: {stats['system']['behavior_pattern']}")
            logging.info(f"   Data Saved: {stats['system']['data_saved_mb']} MB")
            
        else:
            # Normal operation with v3.0 enhancements
            logging.info("\n🎯 Starting ticket hunt with v3.0 enhancements...")
            logging.info("   • CDP Bypass: ACTIVE")
            logging.info("   • Data Optimization: ACTIVE")
            logging.info("   • Adaptive Behavior: ACTIVE")
            logging.info("   • Detection Monitor: ACTIVE")
            
            await orchestrator.start()
            
    except KeyboardInterrupt:
        logging.info("\n👋 Shutdown requested by user")
    except Exception as e:
        logging.error(f"❌ Fatal error: {e}", exc_info=True)
    finally:
        # Cleanup v3.0 resources
        await orchestrator.shutdown()
        logging.info("🏁 StealthMaster AI v3.0 stopped")


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    # Run the async main
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)