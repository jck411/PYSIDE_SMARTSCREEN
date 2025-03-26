#!/bin/bash
set -e

VENV_DIR="smartscreen_venv"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Setting up PySide SmartScreen frontend environment..."
echo "Project root: $PROJECT_ROOT"

# Create a virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment: $VENV_DIR"
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists: $VENV_DIR"
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Update pip
pip install --upgrade pip

# Install frontend dependencies
echo "Installing frontend dependencies..."

# Core dependencies for PySide6 and QML
pip install PySide6

# Audio and speech processing
pip install websockets==12.0
pip install aiohttp==3.9.1
pip install sounddevice==0.4.6
pip install numpy==1.24.3
pip install PyAudio==0.2.13
pip install --upgrade deepgram-sdk
pip install azure-cognitiveservices-speech
pip install pydub

# Environment and utilities
pip install python-dotenv==1.0.0

echo "Frontend dependencies installed successfully."
echo ""
echo "To activate the virtual environment and run the frontend, use:"
echo "source $VENV_DIR/bin/activate"
echo "cd $PROJECT_ROOT"
echo "python -m frontend.main"
echo ""
echo "Setup complete!"

# Make the frontend executable
chmod +x "$PROJECT_ROOT/frontend/main.py" 