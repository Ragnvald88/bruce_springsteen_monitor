# src/main.py - StealthMaster AI v2.0
"""
Bruce Springsteen Ticket Hunter - Ultra-Stealth Edition
Revolutionary ticket acquisition system with quantum efficiency
"""

import asyncio
import logging
import signal
import sys
import os
import yaml
import time
from pathlib import Path
from datetime import datetime
import argparse

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Environment setup
from dotenv import load_dotenv
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Import enhanced orchestrator
from src.core.enhanced_orchestrator_v3 import UltimateOrchestrator
from src.core.enums import OperationMode

# Configuration
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "config.yaml"

# Global state
_orchestrator_instance = None
_stop_event = asyncio.Event()

logger = logging.getLogger(__name__)


def setup_stealth_logging(config: dict) -> None:
    """Configure ultra-stealth logging system"""
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    
    # Create logs directory
    log_dir = PROJECT_ROOT / log_config.get('log_directory', 'logs')
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler with color coding
    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handlers
    from logging.handlers import RotatingFileHandler
    
    # Main log
    main_log = log_dir / log_config.get('main_log_file', 'stealthmaster.log')
    file_handler = RotatingFileHandler(
        main_log, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    ))
    root_logger.addHandler(file_handler)
    
    # Error log
    error_log = log_dir / log_config.get('error_log_file', 'errors.log')
    error_handler = RotatingFileHandler(
        error_log, maxBytes=5*1024*1024, backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s\n%(exc_info)s'
    ))
    root_logger.addHandler(error_handler)
    
    # Suppress noisy libraries
    for lib in ['httpx', 'httpcore', 'playwright', 'websockets', 'urllib3']:
        logging.getLogger(lib).setLevel(logging.ERROR)
    
    logger.info("🛡️ StealthMaster AI logging initialized")


class ColoredFormatter(logging.Formatter):
    """Colored console output for better visibility"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.warning(f"Received signal {sig} - initiating graceful shutdown...")
    _stop_event.set()


async def main(args):
    """Main entry point for StealthMaster AI"""
    global _orchestrator_instance
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    setup_stealth_logging(config)
    
    # Print epic startup banner
    print_startup_banner(config)
    
    # Validate configuration
    if not validate_config(config):
        logger.critical("Configuration validation failed!")
        return 1
    
    # Initialize orchestrator
    logger.info("🚀 Initializing Ultimate Orchestrator v2.0...")
    
    try:
        orchestrator = UltimateOrchestrator(config, gui_queue=None)
        _orchestrator_instance = orchestrator
        
        # Initialize subsystems
        await orchestrator.initialize()
        
        # Start the hunt!
        logger.critical("="*80)
        logger.critical("🎸 STARTING THE HUNT FOR BRUCE SPRINGSTEEN TICKETS! 🎸")
        logger.critical("="*80)
        
        # Start orchestrator
        orchestrator_task = asyncio.create_task(orchestrator.start())
        
        # Wait for stop signal
        await _stop_event.wait()
        
        # Graceful shutdown
        logger.info("Initiating graceful shutdown...")
        await orchestrator.stop()
        
        # Wait for tasks to complete
        await asyncio.wait_for(orchestrator_task, timeout=10)
        
        # Print final stats
        print_final_stats(orchestrator.get_stats())
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        return 1
    
    logger.info("StealthMaster AI shutdown complete")
    return 0


def load_config(config_path: str) -> dict:
    """Load and validate configuration"""
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.critical(f"Configuration file not found: {config_file}")
        sys.exit(1)
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Apply environment variable substitutions
    config = substitute_env_vars(config)
    
    return config


def substitute_env_vars(config: dict) -> dict:
    """Recursively substitute environment variables in config"""
    if isinstance(config, dict):
        return {k: substitute_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [substitute_env_vars(item) for item in config]
    elif isinstance(config, str) and config.startswith('${') and config.endswith('}'):
        var_name = config[2:-1]
        value = os.environ.get(var_name, config)
        # If the value looks like a number, convert it to int
        if value != config and value.isdigit():
            return int(value)
        return value
    else:
        return config


def validate_config(config: dict) -> bool:
    """Validate configuration completeness"""
    required_sections = ['app_settings', 'targets', 'monitoring_settings']
    
    for section in required_sections:
        if section not in config:
            logger.error(f"Missing required config section: {section}")
            return False
    
    # Validate targets
    targets = config.get('targets', [])
    if not any(t.get('enabled', True) for t in targets):
        logger.error("No enabled targets found!")
        return False
    
    # Validate authentication if enabled
    if config.get('authentication', {}).get('enabled'):
        platforms = config['authentication'].get('platforms', {})
        for target in targets:
            if target.get('enabled'):
                platform = target['platform']
                if platform not in platforms:
                    logger.warning(f"No authentication configured for {platform}")
    
    return True


def print_startup_banner(config: dict):
    """Print epic startup banner"""
    mode = config['app_settings']['mode'].upper()
    
    banner = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     _____ _             _ _   _     ___  ___          _              ___     ║
║    /  ___| |           | | | | |   |  \\/  |         | |            / _ \\    ║
║    \\ `--.| |_ ___  __ _| | |_| |__ | .  . | __ _ ___| |_ ___ _ __ / /_\\ \\   ║
║     `--. \\ __/ _ \\/ _` | | __| '_ \\| |\\/| |/ _` / __| __/ _ \\ '__||  _  |   ║
║    /\\__/ / ||  __/ (_| | | |_| | | | |  | | (_| \\__ \\ ||  __/ |   | | | |   ║
║    \\____/ \\__\\___|\\__,_|_|\\__|_| |_|_|  |_|\\__,_|___/\\__\\___|_|   \\_| |_/   ║
║                                                                              ║
║                        🎸 BRUCE SPRINGSTEEN TICKET HUNTER 🎸                 ║
║                              Ultra-Stealth Edition v2.0                       ║
║                                                                              ║
║                             Mode: {mode:^10}                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    
    print("\033[35m" + banner + "\033[0m")  # Magenta color
    
    # Show enabled targets
    print("\n📍 TARGETS:")
    for target in config.get('targets', []):
        if target.get('enabled'):
            status = "✅" if target.get('enabled') else "❌"
            print(f"   {status} {target['event_name']} - {target['platform'].upper()}")
    print()


def print_final_stats(stats: dict):
    """Print final statistics"""
    print("\n" + "="*80)
    print("📊 FINAL STATISTICS")
    print("="*80)
    
    uptime_hours = stats['uptime'] / 3600
    print(f"⏱️  Uptime: {uptime_hours:.2f} hours")
    print(f"🔍 Total Opportunities Found: {stats['quantum_metrics']['total_opportunities']}")
    print(f"⚡ Total Strikes Executed: {stats['quantum_metrics']['total_strikes']}")
    print(f"✅ Successful Strikes: {stats['quantum_metrics']['successful_strikes']}")
    print(f"📈 Success Rate: {stats['success_rate']*100:.1f}%")
    
    if stats['strikes_executed']:
        strike_stats = stats['strikes_executed']
        print(f"\n🎯 STRIKE FORCE STATS:")
        print(f"   Fastest Strike: {strike_stats.get('fastest_strike', 'N/A')}s")
        print(f"   Average Response: {strike_stats.get('avg_response_time', 0):.2f}s")
        
        if strike_stats.get('top_profiles'):
            print(f"\n🏆 TOP PERFORMING PROFILES:")
            for i, (profile_id, wins) in enumerate(strike_stats['top_profiles'][:3], 1):
                print(f"   {i}. {profile_id}: {wins} wins")
    
    print("="*80)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="StealthMaster AI - Bruce Springsteen Ticket Hunter"
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default=str(DEFAULT_CONFIG),
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--mode',
        choices=['stealth', 'beast', 'ultra_stealth', 'adaptive', 'hybrid'],
        help='Override operation mode'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without actually purchasing tickets'
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    # Parse arguments
    args = parse_arguments()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the async main
    try:
        exit_code = asyncio.run(main(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nShutdown requested... cleaning up.")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)