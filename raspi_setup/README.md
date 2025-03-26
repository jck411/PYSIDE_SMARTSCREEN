# Raspberry Pi Frontend Setup

This directory contains scripts for setting up the SmartScreen frontend on a Raspberry Pi.

## Prerequisites

- Raspberry Pi with Raspberry Pi OS or similar Debian-based Linux
- Python 3.7 or higher
- Internet connection for downloading packages

## Setup Instructions

1. Connect to your Raspberry Pi via SSH or use the local terminal

2. Clone this repository:
   ```
   git clone https://github.com/yourusername/PYSIDE_SMARTSCREEN.git
   cd PYSIDE_SMARTSCREEN
   ```

3. Install system dependencies:
   ```
   ./raspi_setup/install_system_deps.sh
   ```
   
   This will install necessary system packages for PySide6, audio processing, and Qt.

4. Set up the Python environment:
   ```
   ./raspi_setup/setup_frontend.sh
   ```
   
   This will:
   - Create a Python virtual environment
   - Install all required Python dependencies for the frontend
   - Make the main frontend script executable

5. Start the frontend application:
   ```
   source smartscreen_venv/bin/activate
   python -m frontend.main
   ```

## Troubleshooting

### PyAudio Installation Issues

If you encounter issues installing PyAudio, you may need to install portaudio development libraries first:

```
sudo apt-get update
sudo apt-get install portaudio19-dev
```

### PySide6 Installation Issues

If you experience problems with PySide6 installation, ensure you have the required system dependencies:

```
sudo apt-get update
sudo apt-get install -y build-essential libgl1-mesa-dev libglib2.0-dev
```

### Display Issues

For Raspberry Pi with display issues:

```
sudo apt-get install -y xorg
```

## Running at System Startup

To automatically start the SmartScreen frontend when the Raspberry Pi boots:

1. Create a systemd service file:
   ```
   sudo nano /etc/systemd/system/smartscreen.service
   ```

2. Add the following content:
   ```
   [Unit]
   Description=PySide SmartScreen Frontend
   After=network.target

   [Service]
   User=pi
   WorkingDirectory=/home/pi/PYSIDE_SMARTSCREEN
   ExecStart=/home/pi/PYSIDE_SMARTSCREEN/smartscreen_venv/bin/python -m frontend.main
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```
   sudo systemctl enable smartscreen.service
   sudo systemctl start smartscreen.service
   ``` 