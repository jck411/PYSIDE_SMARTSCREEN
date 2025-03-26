#!/bin/bash
set -e

echo "Installing system dependencies for PySide SmartScreen frontend..."

# Update package lists
sudo apt-get update

# Install dependencies for PySide6
sudo apt-get install -y build-essential libgl1-mesa-dev libglib2.0-dev

# Install dependencies for audio processing
sudo apt-get install -y portaudio19-dev python3-pyaudio

# Install Qt dependencies
sudo apt-get install -y libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
                       libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 \
                       libxcb-xkb1 libxkbcommon-x11-0

echo "System dependencies installed successfully." 