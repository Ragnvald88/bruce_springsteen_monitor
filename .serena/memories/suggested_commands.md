# Suggested Commands

## Environment Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install undetected-chromedriver selenium python-dotenv

# Force reinstall setuptools for Python 3.13 compatibility
pip install --force-reinstall setuptools
```

## Running the Bot
```bash
# Main execution
python3 fansale.py

# Run with specific Python version if needed
python3.11 fansale.py
```

## Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env  # or vim .env
```

## File Management
```bash
# View logs
tail -f fansale_bot.log

# View statistics
cat fansale_stats.json | python3 -m json.tool

# Clear browser profiles (if needed)
rm -rf browser_profiles/

# Clear screenshots
rm -f screenshots/*.png
```

## Git Commands (Darwin/macOS specific)
```bash
# Status
git status

# Add changes
git add .

# Commit
git commit -m "description"

# View history
git log --oneline

# Diff
git diff
```

## System Commands (Darwin/macOS)
```bash
# List files
ls -la

# Find files
find . -name "*.py"

# Search in files
grep -r "search_term" .

# Process monitoring
ps aux | grep python

# Kill process
kill -9 <PID>

# Monitor system resources
top
```