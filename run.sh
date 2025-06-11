#!/bin/bash
# Convenience script to run StealthMaster

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment and run
source "$DIR/venv/bin/activate"
python "$DIR/stealthmaster.py" "$@"