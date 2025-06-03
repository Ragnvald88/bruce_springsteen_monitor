# src/main.py - v3.1 - Refactored Core Logic
from __future__ import annotations

import asyncio
import logging
import logging.handlers
import signal
import sys
import os
import yaml # For config loading
from pathlib import Path
from typing import Dict, List, Optional, Any # Keep necessary typings for this file
import threading # For GUI bridge
import queue as thread_queue # For GUI bridge

# Ensure the project root is in the Python path
# This allows for absolute imports like 'from src.core import ...'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env") # Load .env from project root

# Playwright
from playwright.async_api import async_playwright, Playwright

# --- Core Application Imports ---
# The main orchestrator is now imported
from src.core.orchestrator import UnifiedOrchestrator
# Import enums if used for CLI args or directly in main.py logic
from src.core.enums import OperationMode

# --- Profile System Imports (Minimal, as Orchestrator handles most) ---
# create_profile_manager_from_config is used by Orchestrator,
# but load_and_merge_configs here needs to provide the path.

# Configuration paths (relative to PROJECT_ROOT or where main.py is run from)
# It's often better to make these configurable via CLI or env vars.
# For now, assuming they are in a 'config' subdirectory of PROJECT_ROOT.
DEFAULT_CONFIG_FILE = PROJECT_ROOT / "config" / "config.yaml"
DEFAULT_BEAST_MODE_CONFIG_FILE = PROJECT_ROOT / "config" / "beast_mode_config.yaml"

# Global state for signal handling and GUI interaction
_orchestrator_instance: Optional[UnifiedOrchestrator] = None
_stop_event_asyncio: Optional[asyncio.Event] = None # For the main CLI bot
_gui_stop_event_threading: Optional[threading.Event] = None # For signaling GUI-initiated bot to stop
_gui_bot_asyncio_loop: Optional[asyncio.AbstractEventLoop] = None # Loop for the GUI-initiated bot

logger = logging.getLogger(__name__) # Main.py's own logger

# --- Signal Handling ---
def signal_handler(sig, frame):
    """Handles termination signals for graceful shutdown."""
    signal_name = signal.Signals(sig).name
    logger.warning(f"Received {signal_name}, initiating graceful shutdown...")

    # Signal the asyncio stop event for the primary bot instance
    if _stop_event_asyncio and not _stop_event_asyncio.is_set():
        _stop_event_asyncio.set()
        logger.info("Primary asyncio stop event set.")

    # Signal the threading stop event for any GUI-initiated bot instance
    if _gui_stop_event_threading and not _gui_stop_event_threading.is_set():
        _gui_stop_event_threading.set() # This will be waited on by main_loop_for_gui
        logger.info("GUI threading stop event set.")
    else:
        # If already trying to stop, or no stop event, force exit after a delay
        logger.critical("Shutdown already in progress or stop event missing. Forcing exit if not stopped soon.")
        # A more robust solution might involve a second signal for immediate exit.
        # For now, this relies on the orchestrator's shutdown.
        # os._exit(1) # Avoid immediate os._exit unless absolutely necessary

# --- Logging Setup ---
def setup_logging(config: Dict[str, Any]) -> None:
    """Sets up global logging based on the loaded configuration."""
    log_config = config.get('logging', {})
    log_level_str = log_config.get('level', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    log_dir_str = log_config.get('log_directory', 'logs')
    log_dir = PROJECT_ROOT / log_dir_str # Ensure logs are in project root's log dir
    log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger() # Get the root logger
    root_logger.setLevel(log_level)

    # Clear any existing handlers to avoid duplicate logs if re-initializing
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-35s | %(funcName)-25s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s',
        datefmt='%H:%M:%S'
    )

    # Console Handler (colored if colorlog is available)
    console_handler = logging.StreamHandler(sys.stdout)
    try:
        import colorlog
        color_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s%(reset)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan', 'INFO': 'green',
                'WARNING': 'yellow', 'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(color_formatter)
    except ImportError:
        console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(log_level) # Respect configured level for console too
    root_logger.addHandler(console_handler)

    # File Handler (Rotating)
    main_log_file = log_dir / log_config.get('main_log_file', 'ticket_system.log')
    file_handler = logging.handlers.RotatingFileHandler(
        main_log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)

    # Error File Handler (Rotating)
    error_log_file = log_dir / log_config.get('error_log_file', 'errors.log')
    error_file_handler = logging.handlers.RotatingFileHandler(
        error_log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR) # Only log ERROR and CRITICAL
    error_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_file_handler)

    # Suppress overly verbose third-party loggers
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.WARNING) # Default, can be overridden by specific needs
    logging.getLogger('websockets').setLevel(logging.WARNING)

    logger.info(f"Logging initialized. Level: {log_level_str}. Main log: {main_log_file}")

# --- Configuration Loading ---
def load_and_merge_configs(main_config_path: Path, beast_config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Loads the main configuration and optionally merges a beast mode override."""
    if not main_config_path.exists():
        logger.critical(f"Main configuration file not found: {main_config_path}")
        raise FileNotFoundError(f"Main configuration file not found: {main_config_path}")

    with open(main_config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    if beast_config_path and beast_config_path.exists() and config.get('app_settings', {}).get('mode') == 'beast':
        logger.info(f"Beast mode detected. Merging with beast config: {beast_config_path}")
        with open(beast_config_path, 'r', encoding='utf-8') as f:
            beast_override_config = yaml.safe_load(f)
        
        # Simple deep merge (can be made more sophisticated if needed)
        def deep_merge(source, destination):
            for key, value in source.items():
                if isinstance(value, dict):
                    node = destination.setdefault(key, {})
                    deep_merge(value, node)
                else:
                    destination[key] = value
            return destination
        config = deep_merge(beast_override_config, config) # Beast overrides main

    config["config_file_path_loaded_from"] = str(main_config_path.resolve()) # Store the path for Orchestrator
    return config

# --- Main Async Logic ---
async def async_main_logic(config: Dict[str, Any], stop_event: asyncio.Event,
                     gui_queue: Optional[thread_queue.Queue] = None) -> None: # gui_queue is thread_queue.Queue
    """Core asynchronous logic, instantiates and runs the orchestrator."""
    global _orchestrator_instance
    # The UnifiedOrchestrator now takes config_file_path
    config_file_path = Path(config["config_file_path_loaded_from"])

    try:
        async with async_playwright() as playwright:
            # Pass gui_queue to orchestrator if it's designed to use it.
            # The current UnifiedOrchestrator __init__ needs to be adapted if it directly uses the queue.
            # For now, assuming it's passed and potentially used by components it creates or for logging.
            _orchestrator_instance = UnifiedOrchestrator(config, playwright, config_file_path)
            # If orchestrator needs gui_queue: _orchestrator_instance.set_gui_queue(gui_queue) or pass in init

            await _orchestrator_instance.run(stop_event) # run() now takes the asyncio.Event

    except Exception as e:
        logger.critical(f"Fatal error in async_main_logic: {e}", exc_info=True)
        if gui_queue:
             gui_queue.put(("log", (f"FATAL BOT ERROR: {e}", "CRITICAL")))
    finally:
        if _orchestrator_instance:
            logger.info("Shutting down orchestrator from async_main_logic.")
            await _orchestrator_instance.graceful_shutdown()
        logger.info("async_main_logic finished.")

# --- GUI Bridge Functions ---
# These functions are called by gui.py

_gui_bot_thread: Optional[threading.Thread] = None
_gui_asyncio_stop_event: Optional[asyncio.Event] = None # Asyncio event for the GUI bot loop

def main_loop_for_gui(config_for_gui: Dict[str, Any],
                      stop_event_from_gui: threading.Event, # This is a threading.Event from GUI
                      gui_q_ref: thread_queue.Queue):
    """
    Starts the bot's asyncio logic in a separate thread, managed by the GUI.
    """
    global _gui_bot_thread, _gui_asyncio_stop_event, _gui_bot_asyncio_loop, _gui_stop_event_threading
    
    logger.info("GUI initiated bot start. Creating new asyncio event loop for bot thread.")
    _gui_stop_event_threading = stop_event_from_gui # Store the threading event
    _gui_asyncio_stop_event = asyncio.Event() # Create a new asyncio.Event for this bot run

    def run_bot_in_thread():
        global _gui_bot_asyncio_loop
        _gui_bot_asyncio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_gui_bot_asyncio_loop)
        try:
            # Pass the asyncio stop event to the core logic
            _gui_bot_asyncio_loop.run_until_complete(
                async_main_logic(config_for_gui, _gui_asyncio_stop_event, gui_q_ref)
            )
        except Exception as e_thread:
            logger.error(f"Exception in GUI bot thread's asyncio loop: {e_thread}", exc_info=True)
            if gui_q_ref:
                gui_q_ref.put(("log", (f"Bot Thread Error: {e_thread}", "ERROR")))
        finally:
            logger.info("GUI bot thread's asyncio loop finished.")
            if gui_q_ref:
                 gui_q_ref.put(("bot_stopped", "Status: Gestopt (async loop beëindigd)"))
            # Ensure the threading event is also set if loop finishes unexpectedly
            if _gui_stop_event_threading and not _gui_stop_event_threading.is_set():
                _gui_stop_event_threading.set()


    _gui_bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True, name="GUIBotThread")
    _gui_bot_thread.start()

    # This outer function will now wait for the GUI to signal stop via the threading.Event
    _gui_stop_event_threading.wait()
    logger.info("GUI 'stop_event_from_gui' (threading.Event) received in main_loop_for_gui.")

    # Signal the asyncio event to stop the bot's async tasks
    if _gui_bot_asyncio_loop and _gui_asyncio_stop_event and not _gui_asyncio_stop_event.is_set():
        logger.info("Signaling asyncio stop event for GUI bot loop...")
        _gui_bot_asyncio_loop.call_soon_threadsafe(_gui_asyncio_stop_event.set)

    if _gui_bot_thread and _gui_bot_thread.is_alive():
        logger.info("Waiting for GUI bot thread to join...")
        _gui_bot_thread.join(timeout=10.0) # Increased timeout
        if _gui_bot_thread.is_alive():
            logger.warning("GUI bot thread did not terminate cleanly after 10s.")
        else:
            logger.info("GUI bot thread terminated.")
    _gui_bot_thread = None
    _gui_bot_asyncio_loop = None


def load_app_config_for_gui(config_path_str: Optional[str] = None) -> Dict[str, Any]:
    """Loads application configuration, intended to be called by the GUI."""
    # Determine actual path to load
    path_to_load = Path(config_path_str) if config_path_str else DEFAULT_CONFIG_FILE
    # Determine beast_config path relative to the main config path
    beast_path_to_load = path_to_load.parent / DEFAULT_BEAST_MODE_CONFIG_FILE.name

    logger.info(f"GUI requesting config load from: {path_to_load}")
    try:
        loaded_config = load_and_merge_configs(path_to_load, beast_path_to_load)
        # Store the actual path used, so Orchestrator can find profile config relative to it
        loaded_config["config_file_path_loaded_from"] = str(path_to_load.resolve())
        return loaded_config
    except FileNotFoundError:
        logger.error(f"Config file not found by GUI loader: {path_to_load}")
        # Return a minimal default config to prevent GUI from crashing
        return {
            "app_settings": {"mode": "adaptive", "logging": {"level": "INFO"}},
            "targets": [],
            "config_file_path_loaded_from": str(path_to_load.resolve()) # Still provide path
        }
    except Exception as e:
        logger.error(f"Error loading config for GUI: {e}", exc_info=True)
        return {
            "app_settings": {"mode": "adaptive", "logging": {"level": "INFO"}},
            "targets": [],
            "config_file_path_loaded_from": str(path_to_load.resolve())
        }


# --- CLI Entry Point ---
def main_cli():
    """Main Command Line Interface entry point."""
    global _stop_event_asyncio # Use the global asyncio stop event for CLI mode

    parser = argparse.ArgumentParser(
        description="Unified Ticket Automation System v3.1",
        formatter_class=argparse.RawTextHelpFormatter, # Changed for better multiline help
        epilog="""
Examples:
  python src/main.py                          # Run in default mode from config
  python src/main.py --mode beast             # Force beast mode
  python src/main.py --config path/to/custom_config.yaml
  python src/main.py --gui                    # Launch the GUI
"""
    )
    parser.add_argument(
        '--mode', type=str, choices=[mode.value for mode in OperationMode],
        help='Override operation mode defined in config.'
    )
    parser.add_argument(
        '--config', type=Path, default=DEFAULT_CONFIG_FILE,
        help=f'Path to the main configuration file (default: {DEFAULT_CONFIG_FILE})'
    )
    parser.add_argument(
        '--beast-config', type=Path, default=DEFAULT_BEAST_MODE_CONFIG_FILE,
        help=f'Path to beast mode override config (default: {DEFAULT_BEAST_MODE_CONFIG_FILE})'
    )
    parser.add_argument(
        '--gui', action='store_true', help='Launch the Graphical User Interface.'
    )
    # Add other CLI arguments as needed (e.g., --data-limit, --dry-run)

    args = parser.parse_args()

    if args.gui:
        print("Launching GUI mode...") # Log to console before GUI takes over logging
        # Ensure basic logging is available if GUI fails to start or setup its own
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)-7s] %(name)-20s :: %(message)s")
        try:
            from src.gui import start_gui # Import GUI starter function
            start_gui() # This will take over
        except ImportError as e:
            print(f"Could not import GUI module. Ensure customtkinter and other dependencies are installed: {e}", file=sys.stderr)
            logger.error(f"GUI Import Error: {e}", exc_info=True)
            sys.exit(1)
        except Exception as e_gui:
            print(f"An error occurred while trying to start the GUI: {e_gui}", file=sys.stderr)
            logger.error(f"GUI Startup Error: {e_gui}", exc_info=True)
            sys.exit(1)
        return # Exit after GUI closes

    # --- CLI Mode Execution ---
    try:
        config = load_and_merge_configs(args.config, args.beast_config)
    except FileNotFoundError:
        # Logger might not be set up yet if config fails to load
        print(f"CRITICAL: Main configuration file not found at {args.config}. Exiting.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"CRITICAL: Error loading configuration: {e}. Exiting.", file=sys.stderr)
        sys.exit(1)

    # Override mode from CLI if provided
    if args.mode:
        config.setdefault('app_settings', {})['mode'] = args.mode

    setup_logging(config) # Setup logging based on the final config

    logger.info("="*60)
    logger.info("Unified Ticket Automation System v3.1 - CLI Mode Starting")
    logger.info(f"Using configuration: {args.config}")
    logger.info(f"Operation Mode: {config.get('app_settings', {}).get('mode', 'N/A').upper()}")
    logger.info(f"Python Version: {sys.version.split()[0]}")
    logger.info("="*60)

    if not config.get('targets') or not any(t.get('enabled') for t in config.get('targets', [])):
        logger.critical("No enabled targets found in the configuration. Exiting.")
        sys.exit(1)

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    _stop_event_asyncio = asyncio.Event() # Initialize the asyncio stop event

    try:
        if sys.platform == "win32": # Required for Windows to prevent ProactorEventLoop errors with Playwright
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(async_main_logic(config, _stop_event_asyncio))
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received in main_cli. Signaling stop.")
        if _stop_event_asyncio and not _stop_event_asyncio.is_set():
            _stop_event_asyncio.set()
        # The asyncio.run will wait for async_main_logic to finish, which includes orchestrator shutdown
    except Exception as e:
        logger.critical(f"Unhandled exception in main_cli: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("CLI Mode: System shutdown process complete.")

if __name__ == "__main__":
    import argparse # Ensure argparse is imported for CLI
    main_cli()
