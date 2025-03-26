#!/bin/bash

# Simple launcher script that runs the frontend using the existing virtual environment

# Get the script directory path for more versatile usage
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to the project directory
cd "$PROJECT_ROOT"

# Activate the virtual environment
source "$SCRIPT_DIR/smartscreen_venv/bin/activate"

# Run the frontend
python -m frontend.main 