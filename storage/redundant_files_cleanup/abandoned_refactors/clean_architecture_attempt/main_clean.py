#!/usr/bin/env python3
"""
Bruce Springsteen Ticket Monitor - Clean Architecture Version
Main entry point using the new clean architecture.
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from application.config import ApplicationConfig
from infrastructure.logging import setup_logging
from presentation.cli import CLIPresentation

# Setup logging
logger = setup_logging()


async def main():
    """Main entry point"""
    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    try:
        config = ApplicationConfig.from_yaml(str(config_path))
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        return 1
    
    # Validate configuration
    errors = config.validate()
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        return 1
    
    # Create and run CLI presentation
    cli = CLIPresentation(config)
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(cli.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the application
    try:
        await cli.run()
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)