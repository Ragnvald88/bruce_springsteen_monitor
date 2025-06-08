#!/usr/bin/env python3
"""
StealthMaster AI v3.0 - Main Entry Point
Revolutionary ticket monitoring system with maximum stealth
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

# Import v3 orchestrator
from src.core.orchestrator import Orchestrator

# Configuration
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "config.yaml"


def setup_logging(config: dict) -> None:
    """Configure streamlined logging for v3"""
    
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
    
    # Console handler with simple format
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
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
    
    logging.info("🛡️ StealthMaster AI logging initialized")


def load_config(config_path: Path) -> dict:
    """Load and process configuration"""
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Substitute environment variables
    config = substitute_env_vars(config)
    
    return config


def substitute_env_vars(config: dict) -> dict:
    """Recursively substitute environment variables in config"""
    
    if isinstance(config, dict):
        return {k: substitute_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [substitute_env_vars(item) for item in config]
    elif isinstance(config, str):
        # Check for environment variable pattern ${VAR_NAME}
        if config.startswith('${') and config.endswith('}'):
            var_name = config[2:-1]
            value = os.getenv(var_name)
            if value is None:
                logging.warning(f"Environment variable {var_name} not set")
                return config
            # Convert numeric strings to numbers
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                return value
    return config


def print_banner():
    """Print the v3 banner"""
    
    banner = """
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║  ███████╗████████╗███████╗ █████╗ ██╗  ████████╗██╗  ██╗ ██╗   ██╗ ║
    ║  ██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║  ╚══██╔══╝██║  ██║ ██║   ██║ ║
    ║  ███████╗   ██║   █████╗  ███████║██║     ██║   ███████║ ██║   ██║ ║
    ║  ╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██║   ██╔══██║ ╚██╗ ██╔╝ ║
    ║  ███████║   ██║   ███████╗██║  ██║███████╗██║   ██║  ██║  ╚████╔╝  ║
    ║  ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝   ╚═══╝   ║
    ║                                                                      ║
    ║             M A S T E R   A I   v 3 . 0                              ║
    ║                                                                      ║
    ║        🎸 BRUCE SPRINGSTEEN TICKET HUNTER 🎸                         ║
    ║           Maximum Stealth • Minimum Data • Maximum Results          ║
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
            
        # Check for proxy credentials
        proxy = proxy_config['primary_pool'][0]
        if not all(k in proxy for k in ['host', 'port']):
            logging.error("Invalid proxy configuration")
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
    """Main entry point for StealthMaster AI"""
    
    parser = argparse.ArgumentParser(description='StealthMaster AI v3.0 - Ticket Hunter')
    parser.add_argument('-c', '--config', type=Path, default=DEFAULT_CONFIG,
                        help='Configuration file path')
    parser.add_argument('--test', action='store_true',
                        help='Run in test mode (single check then exit)')
    parser.add_argument('--no-gui', action='store_true',
                        help='Run without detection monitor GUI')
    
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
    
    # Create orchestrator
    orchestrator = Orchestrator(config)
    
    try:
        # Initialize subsystems
        await orchestrator.initialize()
        
        # Start monitoring
        if args.test:
            logging.info("🧪 Running in test mode - single check only")
            # Run single check for each monitor
            for monitor_id, monitor in orchestrator.monitors.items():
                try:
                    opportunities = await monitor.handler.check_tickets()
                    logging.info(f"Test result for {monitor.handler.platform}: {len(opportunities)} tickets found")
                except Exception as e:
                    logging.error(f"Test failed for {monitor.handler.platform}: {e}")
        else:
            # Normal operation
            await orchestrator.start()
            
    except KeyboardInterrupt:
        logging.info("\n👋 Shutdown requested by user")
    except Exception as e:
        logging.error(f"❌ Fatal error: {e}", exc_info=True)
    finally:
        # Cleanup
        await orchestrator.shutdown()
        logging.info("🏁 StealthMaster AI stopped")


if __name__ == "__main__":
    # Run the async main
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)