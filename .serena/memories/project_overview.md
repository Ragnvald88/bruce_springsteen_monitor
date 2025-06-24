# StealthMaster Project Overview

## Purpose
StealthMaster is a ticket purchasing bot for FanSale.it (Italian ticket resale platform) designed to automatically detect and purchase available tickets with anti-detection measures.

## Key Features
- **No Login Required**: Discovery that tickets can be reserved without authentication
- **Anti-detection**: Uses undetected-chromedriver and stealth techniques
- **Multi-browser support**: Can run 1-5 concurrent browsers for faster checking
- **Smart filtering**: Can filter tickets by keywords (Prato, Tribuna, etc.)
- **Session management**: Automatic refresh to avoid 404 blocks
- **Performance tracking**: Real-time statistics and check rates
- **Screenshot capture**: Saves screenshots on successful checkout

## Main Components
- `fansale.py` - Original full-featured version with login support
- `fansale_stealth.py` - Streamlined 350-line version
- `fansale_no_login.py` - No-login required version (deleted but recoverable)
- `/utilities` - Enhanced features (stealth, optimization, session management)

## Target Site
FanSale.it - Italian ticket resale platform for concerts and events