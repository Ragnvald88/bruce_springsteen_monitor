# 🚀 StealthMaster Quick Start

## Setup (One Time)

1. **Install Dependencies**:
   ```bash
   pip install undetected-chromedriver selenium python-dotenv
   ```

2. **Check .env File**:
   ```
   FANSALE_EMAIL="your@email.com"
   FANSALE_PASSWORD="yourpassword"
   FANSALE_TARGET_URL="https://www.fansale.it/..."
   ```

## Running the Bot

### Option 1: Simple & Stealthy (Recommended)
```bash
python fansale_stealth.py
```
- Cleaner code (350 lines)
- Better stealth
- Manual login only
- Faster startup

### Option 2: Full Features
```bash
python fansale.py
```
- All features (1151 lines)
- Proxy support
- Auto-login option
- Ticket filtering

## Configuration

When you run, you'll be asked:
1. **Browsers**: 1-2 recommended (more = higher detection risk)
2. **Proxy**: Only if needed (slows down)
3. **Max tickets**: How many to buy (1-4)

## Tips for Success

1. **Login Manually** - More reliable than auto-login
2. **Use 1-2 Browsers** - Balance speed vs detection
3. **Run During Peak Times** - When real users are active
4. **Take Breaks** - Don't run 24/7

## Troubleshooting

- **"Already logged in" but not**: Fixed - was a code bug
- **Session expires**: Normal after ~15 minutes
- **Browser crashes**: Restart the bot
- **No tickets found**: Check if event is sold out

## Project Structure

```
stealthmaster/
├── fansale_stealth.py    # Recommended - simple & fast
├── fansale.py           # Original with all features
├── .env                 # Your credentials
├── requirements.txt     # Dependencies
├── browser_profiles/    # Saved sessions
└── utilities/          # Optional enhancements
```

Choose `fansale_stealth.py` for best results!
