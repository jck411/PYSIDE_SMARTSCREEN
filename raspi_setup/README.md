# Raspberry Pi Frontend Setup

This directory contains scripts for setting up the SmartScreen frontend on a Raspberry Pi.

## Required Files

- `setup_frontend.sh`: Script to create a virtual environment and install required dependencies
- `install_system_deps.sh`: Script to install system dependencies required by the frontend
- `launch.sh`: Simple script to launch the frontend
- `SmartScreen.desktop`: Desktop entry file for launching the application

## Setup Instructions

1. Install system dependencies:
   ```
   ./raspi_setup/install_system_deps.sh
   ```
   
   This will install necessary system packages for PySide6, audio processing, and Qt.

2. Set up the Python environment:
   ```
   ./raspi_setup/setup_frontend.sh
   ```
   
   This will create a virtual environment and install all required Python dependencies.

3. Start the frontend application:
   ```
   ./raspi_setup/launch.sh
   ```

## Desktop Launcher

To create a desktop launcher:

1. Copy the desktop file to your desktop:
   ```
   cp raspi_setup/SmartScreen.desktop ~/Desktop/
   ```

2. Make it executable:
   ```
   chmod +x ~/Desktop/SmartScreen.desktop
   ```

3. Right-click the desktop file and select "Allow Launching"

## Troubleshooting

### PyAudio Installation Issues

If you encounter issues installing PyAudio:
```
sudo apt-get update
sudo apt-get install portaudio19-dev
```

### PySide6 Installation Issues

If you have problems with PySide6 installation:
```
sudo apt-get update
sudo apt-get install -y build-essential libgl1-mesa-dev libglib2.0-dev
```

## Running at System Startup

To run the application at system startup:

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
   WorkingDirectory=/home/jck411/PYSIDE_SMARTSCREEN
   ExecStart=/home/jck411/PYSIDE_SMARTSCREEN/raspi_setup/launch.sh
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```
   sudo systemctl enable smartscreen.service
   sudo systemctl start smartscreen.service
   ``` 