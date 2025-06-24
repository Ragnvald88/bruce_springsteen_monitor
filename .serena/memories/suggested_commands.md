# Suggested Commands

## Running the Bot
```bash
# Main bot execution
python fansale.py                # Full-featured version with login
python fansale_stealth.py        # Streamlined version
python fansale_no_login.py       # No-login version (if restored)

# With specific Python version
python3 fansale.py
```

## Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env
```

## Cleanup and Maintenance
```bash
# Clean up browser profiles
rm -rf browser_profiles/*

# Clear logs
rm fansale_bot.log debug.log

# Clear screenshots
rm screenshots/*.png

# Run cleanup script
python cleanup_resources.py
```

## Git Commands
```bash
# Check status
git status

# View commit history
git log --oneline

# Recover deleted files
git checkout <commit-hash> -- <filename>

# Example: Recover fansale_no_login.py
git checkout ab9acc878899a88044972c3d296d052c77046ae1 -- fansale_no_login.py
```

## System Commands (macOS)
```bash
# List files
ls -la

# Find Python files
find . -name "*.py" -type f

# Search in files
grep -r "pattern" .

# Monitor log file
tail -f fansale_bot.log

# Check running Python processes
ps aux | grep python

# Kill process
kill -9 <PID>
```

## Testing and Debugging
```bash
# Test login functionality
python test_login.py

# Run with debug logging
export DEBUG=1 && python fansale.py

# Check Chrome version
google-chrome --version
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version  # macOS
```

## Performance Monitoring
```bash
# Monitor CPU/Memory usage
top -p <PID>

# Check network activity
netstat -an | grep 443

# View statistics file
cat stats.json | python -m json.tool
```