# FanSale Ticket Bot - FINAL Version

A simple, effective ticket bot for FanSale.it with CORRECT timing logic.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure `.env`:**
   ```
   FANSALE_EMAIL="your_email@example.com"
   FANSALE_PASSWORD="your_password"
   
   # IPRoyal Proxy (optional but recommended)
   IPROYAL_USERNAME="your_username"
   IPROYAL_PASSWORD="your_password"
   IPROYAL_HOSTNAME="geo.iproyal.com"
   IPROYAL_PORT="12321"
   ```

3. **Set target URL in `config.yaml`**

4. **Run:**
   ```bash
   python3 fansale_final.py
   ```

## Why This Works

- **Correct Timing**: Refreshes FIRST, then waits (never blind to new tickets)
- **Smart Patterns**: Human-like timing to avoid detection
- **Bandwidth Efficient**: Aggressively blocks images/ads to save proxy data
- **Battle-tested**: Based on proven scraping patterns

## The Critical Difference

❌ WRONG: Check → Wait → Refresh (gives competitors time!)
✅ RIGHT: Check → Refresh → Wait (see new tickets instantly!)

## Features

- ✅ Automatic login with session persistence
- ✅ Human-like patterns (applied AFTER refresh)
- ✅ Aggressive bandwidth optimization
- ✅ Micro-optimized purchase flow
- ✅ Simple, maintainable code

Good luck getting those tickets! 🎫
