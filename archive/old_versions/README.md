# Archived StealthMaster Versions

This directory contains older/alternative versions of the StealthMaster application that have been archived for reference purposes.

## Files

### stealthmaster_working.py
- **Type:** Simplified working version
- **Lines:** 424
- **Description:** A minimal, self-contained version without proxy support
- **Features:**
  - Basic Selenium-based monitoring
  - Simple cookie dismissal
  - Basic block detection
  - Hard-coded targets (Bruce Springsteen concerts)
  - No authentication or advanced features

### stealthmaster_final.py
- **Type:** Enhanced standalone version
- **Lines:** 800
- **Description:** A more advanced self-contained version with proxy support
- **Features:**
  - Proxy support with authentication extension
  - Enhanced stealth techniques and JavaScript injection
  - Better ticket detection logic
  - Progressive backoff for blocks
  - Driver recreation on multiple failures
  - Interactive proxy choice at startup

## Note
These versions were created during development/testing and are kept for reference only. The main production version is `stealthmaster.py` in the root directory, which uses the modular architecture in the `src/` directory.

For production use, always use the main `stealthmaster.py` file.