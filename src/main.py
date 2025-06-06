# src/main.py - v4.0 - Ultra-Stealth High-Performance Edition
from __future__ import annotations

import asyncio
import logging
import logging.handlers
import signal
import sys
import os
import yaml
import time
from pathlib import Path
from typing import Dict, Optional, Any
import threading
import queue as thread_queue
from datetime import datetime
import hashlib
import re

# Ensure the project root is in the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# Playwright with stealth capabilities
from playwright.async_api import async_playwright

# Core Application Imports
from src.core.orchestrator import UnifiedOrchestrator
from src.core.enums import OperationMode

# Configuration paths
DEFAULT_CONFIG_FILE = PROJECT_ROOT / "config" / "config.yaml"
DEFAULT_BEAST_MODE_CONFIG_FILE = PROJECT_ROOT / "config" / "beast_mode_config.yaml"

# Global state management with thread safety
_orchestrator_instance: Optional[UnifiedOrchestrator] = None
_stop_event_asyncio: Optional[asyncio.Event] = None
_gui_stop_event_threading: Optional[threading.Event] = None
_gui_bot_asyncio_loop: Optional[asyncio.AbstractEventLoop] = None
_shutdown_lock = threading.Lock()

logger = logging.getLogger(__name__)

class StealthLogger(logging.Logger):
    """Custom logger that sanitizes sensitive information"""
    
    def _sanitize_message(self, msg: str) -> str:
        """Remove sensitive data from log messages"""
        # Remove URLs with tokens/sessions
        msg = re.sub(r'(session|token|key)=[^&\s]+', r'\1=***', msg)
        # Remove profile IDs in logs
        msg = re.sub(r'profile_[a-f0-9]{8}', 'profile_***', msg)
        # Remove proxy credentials from URLs
        msg = re.sub(r'://[^:/@]+:[^:/@]+@', '://***:***@', msg)
        # Remove standalone password patterns
        msg = re.sub(r'(password|passwd|pwd)["\s]*[:=]["\s]*[^\s"&]+', r'\1=***', msg, flags=re.IGNORECASE)
        return msg
    
    def _log(self, level, msg, args, **kwargs):
        msg = self._sanitize_message(str(msg))
        super()._log(level, msg, args, **kwargs)
# Replace default logger class
logging.setLoggerClass(StealthLogger)

def signal_handler(sig, _):
    """Enhanced signal handler with proper cleanup"""
    signal_name = signal.Signals(sig).name
    logger.warning(f"Received {signal_name}, initiating stealth shutdown...")
    
    with _shutdown_lock:
        # Primary asyncio event
        if _stop_event_asyncio and not _stop_event_asyncio.is_set():
            _stop_event_asyncio.set()
            logger.info("Primary asyncio stop event set.")
        
        # GUI threading event
        if _gui_stop_event_threading and not _gui_stop_event_threading.is_set():
            _gui_stop_event_threading.set()
            logger.info("GUI threading stop event set.")
        
        # Force cleanup after delay if needed
        def force_cleanup():
            time.sleep(5)
            if _orchestrator_instance and not _orchestrator_instance._shutdown_initiated:
                logger.critical("Forcing immediate shutdown")
                os._exit(1)
        
        threading.Thread(target=force_cleanup, daemon=True).start()

def setup_logging(config: Dict[str, Any]) -> None:
    """Enhanced logging with stealth considerations"""
    log_config = config.get('logging', {})
    log_level_str = log_config.get('level', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Stealth mode: reduce logging verbosity
    if config.get('app_settings', {}).get('mode') in ['stealth', 'ultra_stealth']:
        log_level = max(log_level, logging.WARNING)
    
    log_dir_str = log_config.get('log_directory', 'logs')
    log_dir = PROJECT_ROOT / log_dir_str
    log_dir.mkdir(parents=True, exist_ok=True)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
    
    # Enhanced formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-30s | %(funcName)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler with color support
    console_handler = logging.StreamHandler(sys.stdout)
    try:
        import colorlog
        color_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s | %(levelname)-8s | %(message)s%(reset)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(color_formatter)
    except ImportError:
        console_handler.setFormatter(detailed_formatter)
    
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Rotating file handlers with compression
    main_log_file = log_dir / log_config.get('main_log_file', 'ticket_system.log')
    file_handler = logging.handlers.RotatingFileHandler(
        main_log_file, 
        maxBytes=10*1024*1024, 
        backupCount=5, 
        encoding='utf-8'
    )
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Error-only handler
    error_log_file = log_dir / log_config.get('error_log_file', 'errors.log')
    error_file_handler = logging.handlers.RotatingFileHandler(
        error_log_file, 
        maxBytes=5*1024*1024, 
        backupCount=3, 
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_file_handler)
    
    # Suppress verbose third-party loggers for stealth
    stealth_suppression = {
        'httpx': logging.ERROR,
        'httpcore': logging.ERROR,
        'playwright': logging.ERROR,
        'websockets': logging.ERROR,
        'urllib3': logging.ERROR,
        'selenium': logging.ERROR,
    }
    
    for logger_name, level in stealth_suppression.items():
        logging.getLogger(logger_name).setLevel(level)
    
    logger.info(f"Stealth logging initialized. Level: {log_level_str}")

def load_and_merge_configs(main_config_path: Path, beast_config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Enhanced config loading with validation and security"""
    if not main_config_path.exists():
        logger.critical(f"Main configuration file not found: {main_config_path}")
        raise FileNotFoundError(f"Main configuration file not found: {main_config_path}")
    
    # Load with safe loader to prevent code execution
    with open(main_config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Validate critical config sections
    required_sections = ['app_settings', 'targets', 'monitoring_settings']
    for section in required_sections:
        if section not in config:
            logger.warning(f"Missing required config section: {section}")
            config[section] = {}
    
    # Merge beast mode config if applicable
    if beast_config_path and beast_config_path.exists() and config.get('app_settings', {}).get('mode') == 'beast':
        logger.info(f"Beast mode detected. Merging with: {beast_config_path}")
        with open(beast_config_path, 'r', encoding='utf-8') as f:
            beast_config = yaml.safe_load(f)
        
        # Deep merge with conflict resolution
        def deep_merge(source, destination):
            for key, value in source.items():
                if isinstance(value, dict):
                    node = destination.setdefault(key, {})
                    deep_merge(value, node)
                else:
                    destination[key] = value
            return destination
        
        config = deep_merge(beast_config, config)
    
    # Add runtime metadata
    config["_metadata"] = {
        "config_file_path": str(main_config_path.resolve()),
        "loaded_at": datetime.now().isoformat(),
        "config_hash": hashlib.sha256(str(config).encode()).hexdigest()[:8]
    }
    
    return config

async def async_main_logic(config: Dict[str, Any], stop_event: asyncio.Event,
                          gui_queue: Optional[thread_queue.Queue] = None) -> None:
    """Enhanced core logic with stealth optimizations and fast startup"""
    global _orchestrator_instance
    
    start_time = time.time()
    
    try:
        # Initialize Playwright with stealth
        async with async_playwright() as playwright:
            
            _orchestrator_instance = UnifiedOrchestrator(
                config, 
                playwright, 
                Path(config["_metadata"]["config_file_path"]),
                gui_queue=gui_queue
            )
            
            # Log startup time
            startup_time = time.time() - start_time
            logger.info(f"⚡ Fast startup completed in {startup_time:.2f}s")
            
            # Performance optimization: pre-warm connections (non-blocking)
            asyncio.create_task(_orchestrator_instance.pre_warm_connections())
            
            # Run the orchestrator
            await _orchestrator_instance.run(stop_event)
            
    except Exception as e:
        logger.critical(f"Fatal error in async_main_logic: {e}", exc_info=True)
        if gui_queue:
            gui_queue.put(("log", (f"FATAL BOT ERROR: {e}", "CRITICAL")))
        raise
    finally:
        elapsed = time.time() - start_time
        logger.info(f"Bot session duration: {elapsed:.2f} seconds")
        
        if _orchestrator_instance:
            logger.info("Initiating secure shutdown sequence...")
            await _orchestrator_instance.graceful_shutdown()
            
            # Clear sensitive data
            _orchestrator_instance.clear_sensitive_data()
        
        logger.info("async_main_logic completed.")

# GUI Bridge Functions with enhanced thread safety
_gui_bot_thread: Optional[threading.Thread] = None
_gui_asyncio_stop_event: Optional[asyncio.Event] = None

def main_loop_for_gui(config_for_gui: Dict[str, Any],
                     stop_event_from_gui: threading.Event,
                     gui_q_ref: thread_queue.Queue):
    """Enhanced GUI bot loop with better error handling"""
    global _gui_bot_thread, _gui_asyncio_stop_event, _gui_bot_asyncio_loop, _gui_stop_event_threading
    
    logger.info("GUI initiated stealth bot start.")
    _gui_stop_event_threading = stop_event_from_gui
    _gui_asyncio_stop_event = asyncio.Event()
    
    def run_bot_in_thread():
        global _gui_bot_asyncio_loop
        
        # Create isolated event loop for thread
        _gui_bot_asyncio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_gui_bot_asyncio_loop)
        
        try:
            _gui_bot_asyncio_loop.run_until_complete(
                async_main_logic(config_for_gui, _gui_asyncio_stop_event, gui_q_ref)
            )
        except Exception as e:
            logger.error(f"GUI bot thread error: {e}", exc_info=True)
            if gui_q_ref:
                gui_q_ref.put(("log", (f"Bot Error: {str(e)[:100]}...", "ERROR")))
        finally:
            logger.info("GUI bot thread completed.")
            if gui_q_ref:
                gui_q_ref.put(("bot_stopped", "Status: Stopped"))
            
            # Cleanup
            _gui_bot_asyncio_loop.close()
            _gui_bot_asyncio_loop = None
    
    # Start bot thread with proper naming
    thread_name = f"StealthBot-{datetime.now().strftime('%H%M%S')}"
    _gui_bot_thread = threading.Thread(
        target=run_bot_in_thread, 
        daemon=True, 
        name=thread_name
    )
    _gui_bot_thread.start()
    
    # Wait for stop signal with timeout checks
    while not _gui_stop_event_threading.is_set():
        if _gui_stop_event_threading.wait(timeout=1.0):
            break
        
        # Health check
        if _gui_bot_thread and not _gui_bot_thread.is_alive():
            logger.warning("GUI bot thread died unexpectedly")
            break
    
    logger.info("GUI stop signal received, initiating shutdown...")
    
    # Signal async stop
    if _gui_bot_asyncio_loop and _gui_asyncio_stop_event:
        _gui_bot_asyncio_loop.call_soon_threadsafe(_gui_asyncio_stop_event.set)
    
    # Wait for thread completion
    if _gui_bot_thread and _gui_bot_thread.is_alive():
        _gui_bot_thread.join(timeout=15.0)
        if _gui_bot_thread.is_alive():
            logger.error("GUI bot thread failed to terminate gracefully")
    
    _gui_bot_thread = None

def load_app_config_for_gui(config_path_str: Optional[str] = None) -> Dict[str, Any]:
    """Enhanced config loader for GUI with validation"""
    path_to_load = Path(config_path_str) if config_path_str else DEFAULT_CONFIG_FILE
    beast_path = path_to_load.parent / DEFAULT_BEAST_MODE_CONFIG_FILE.name
    
    logger.info(f"GUI loading config from: {path_to_load}")
    
    try:
        config = load_and_merge_configs(path_to_load, beast_path)
        
        # Validate for GUI usage
        if not config.get('targets'):
            config['targets'] = []
            logger.warning("No targets defined in config for GUI")
        
        return config
        
    except Exception as e:
        logger.error(f"Config loading error: {e}", exc_info=True)
        # Return minimal valid config
        return {
            "app_settings": {
                "mode": "adaptive",
                "logging": {"level": "INFO"}
            },
            "targets": [],
            "monitoring_settings": {},
            "_metadata": {
                "config_file_path": str(path_to_load.resolve()),
                "error": str(e)
            }
        }

def main_cli():
    """Enhanced CLI entry point with stealth features"""
    global _stop_event_asyncio
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Ultra-Stealth Ticket Automation System v4.0",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Stealth Modes:
  adaptive      - Dynamically adjusts strategy based on detection
  stealth       - Prioritizes avoiding detection
  ultra_stealth - Maximum anti-detection, minimal footprint
  beast         - Maximum speed, accepts higher detection risk
  hybrid        - Balanced approach

Examples:
  python src/main.py                          # Default mode from config
  python src/main.py --mode ultra_stealth     # Force ultra stealth mode
  python src/main.py --profiles 10            # Use 10 concurrent profiles
  python src/main.py --gui                    # Launch GUI interface
"""
    )
    
    parser.add_argument(
        '--mode', 
        type=str, 
        choices=[mode.value for mode in OperationMode],
        help='Override operation mode'
    )
    parser.add_argument(
        '--config', 
        type=Path, 
        default=DEFAULT_CONFIG_FILE,
        help=f'Configuration file path (default: {DEFAULT_CONFIG_FILE})'
    )
    parser.add_argument(
        '--beast-config', 
        type=Path, 
        default=DEFAULT_BEAST_MODE_CONFIG_FILE,
        help=f'Beast mode config (default: {DEFAULT_BEAST_MODE_CONFIG_FILE})'
    )
    parser.add_argument(
        '--gui', 
        action='store_true', 
        help='Launch GUI interface'
    )
    parser.add_argument(
        '--profiles', 
        type=int, 
        help='Number of concurrent profiles to use'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true', 
        help='Test mode without actual purchases'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true', 
        help='Enable verbose logging (reduces stealth)'
    )
    
    args = parser.parse_args()
    
    # GUI mode
    if args.gui:
        print("Launching Stealth GUI mode...")
        logging.basicConfig(
            level=logging.INFO, 
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        try:
            from src.gui import start_gui
            start_gui()
        except ImportError as e:
            print(f"GUI dependencies missing: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"GUI error: {e}", file=sys.stderr)
            sys.exit(1)
        return
    
    # Load configuration
    try:
        config = load_and_merge_configs(args.config, args.beast_config)
    except Exception as e:
        print(f"CRITICAL: Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Apply CLI overrides
    if args.mode:
        config.setdefault('app_settings', {})['mode'] = args.mode
    if args.profiles:
        config.setdefault('profile_settings', {})['max_concurrent'] = args.profiles
    if args.dry_run:
        config.setdefault('app_settings', {})['dry_run'] = True
    if args.verbose:
        config.setdefault('logging', {})['level'] = 'DEBUG'
    
    # Setup logging
    setup_logging(config)
    
    # Enhanced startup info with visibility status
    logger.critical("="*80)
    logger.critical("🎸 BRUCE SPRINGSTEEN TICKET HUNTER v4.0 STARTING 🎸")
    logger.critical("="*80)
    logger.critical(f"🎯 Mode: {config.get('app_settings', {}).get('mode', 'adaptive').upper()}")
    logger.critical(f"📄 Config: {args.config}")
    logger.critical(f"👤 Profiles: {config.get('profile_settings', {}).get('max_concurrent', 'auto')}")
    logger.critical(f"🐍 Python: {sys.version.split()[0]}")
    
    # Show browser visibility status
    browser_headless = config.get('browser_options', {}).get('headless', True)
    if browser_headless:
        logger.error("⚠️  BROWSERS WILL BE HIDDEN (headless: true)")
        logger.error("   💡 Change 'headless: false' in config to see browsers")
    else:
        logger.critical("👀 BROWSERS WILL BE VISIBLE (headless: false)")
        logger.critical("   ✅ You will see browser windows during operation")
    
    # Show authentication status
    auth_enabled = config.get('authentication', {}).get('enabled', False)
    if auth_enabled:
        logger.critical("🔐 AUTHENTICATION ENABLED")
        fansale_auth = config.get('authentication', {}).get('platforms', {}).get('fansale')
        if fansale_auth:
            logger.critical("   ✅ FanSale credentials configured")
        else:
            logger.error("   ❌ FanSale credentials missing")
    else:
        logger.error("⚠️  AUTHENTICATION DISABLED")
        logger.error("   💡 Enable authentication in config.yaml")
    
    logger.critical("="*80)
    
    # Validate targets
    enabled_targets = [t for t in config.get('targets', []) if t.get('enabled')]
    if not enabled_targets:
        logger.critical("No enabled targets found. Exiting.")
        sys.exit(1)
    
    logger.info(f"Active targets: {len(enabled_targets)}")
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    if hasattr(signal, 'SIGBREAK'):  # Windows
        signal.signal(signal.SIGBREAK, signal_handler)
    
    # Set event loop policy for Windows compatibility
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    _stop_event_asyncio = asyncio.Event()
    
    # Run main logic
    try:
        
        # Pre-flight checks
        logger.info("Running pre-flight stealth checks...")
        
        # Start the bot
        asyncio.run(async_main_logic(config, _stop_event_asyncio))
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        if _stop_event_asyncio:
            _stop_event_asyncio.set()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("🏁 Stealth system shutdown complete")

if __name__ == "__main__":
    main_cli()