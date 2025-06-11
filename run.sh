#!/bin/bash
# StealthMaster - Run Script

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set Chrome path for macOS
export CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Activate virtual environment and run
source "$DIR/venv/bin/activate"
python "$DIR/stealthmaster.py" "$@"