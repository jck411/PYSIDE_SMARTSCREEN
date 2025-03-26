#!/bin/bash

# FILE: install-ssh-vnc-bootstrap.sh
# PURPOSE: One-step setup for SSH, VNC, and headless config on any Raspberry Pi
#
# USAGE:
# 1. SSH into your Raspberry Pi:
#    ssh pi@<raspi-ip>
#
# 2. Create this script:
#    nano install-ssh-vnc-bootstrap.sh
#    (Paste this entire file in, then save and exit)
#
# 3. Run it:
#    chmod +x install-ssh-vnc-bootstrap.sh
#    ./install-ssh-vnc-bootstrap.sh
#
# The Pi will automatically:
# - Enable SSH and VNC via raspi-config
# - Install RealVNC Server
# - Configure headless HDMI resolution
# - Create and enable a systemd service to re-apply settings at boot
# - Reboot immediately

set -e

SERVICE_NAME="enable-ssh-and-vnc"
SCRIPT_PATH="/usr/local/bin/${SERVICE_NAME}.sh"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

# ------------------------------
# 1. Create persistent boot script
# ------------------------------
echo "📄 Writing persistent config script..."
sudo tee $SCRIPT_PATH >/dev/null <<'EOF'
#!/bin/bash

sudo raspi-config nonint do_ssh 0
sudo raspi-config nonint do_vnc 0

sudo apt update
sudo apt install -y realvnc-vnc-server

sudo systemctl enable ssh
sudo systemctl start ssh

sudo systemctl enable vncserver-x11-serviced.service
sudo systemctl start vncserver-x11-serviced.service

CONFIG=/boot/config.txt
sudo sed -i '/^#\?hdmi_force_hotplug/d' \$CONFIG
sudo sed -i '/^#\?hdmi_group/d' \$CONFIG
sudo sed -i '/^#\?hdmi_mode/d' \$CONFIG

echo "hdmi_force_hotplug=1" | sudo tee -a \$CONFIG
echo "hdmi_group=2" | sudo tee -a \$CONFIG
echo "hdmi_mode=85" | sudo tee -a \$CONFIG

EOF

sudo chmod +x $SCRIPT_PATH

# ------------------------------
# 2. Create the systemd service
# ------------------------------
echo "🔧 Creating systemd service..."
sudo tee $SERVICE_PATH >/dev/null <<EOF
[Unit]
Description=Enable SSH, VNC, and headless resolution on every boot
After=network-online.target

[Service]
Type=oneshot
ExecStart=$SCRIPT_PATH
RemainAfterExit=true

[Install]
WantedBy=multi-user.target
EOF

# ------------------------------
# 3. Enable and run
# ------------------------------
echo "✅ Enabling systemd service and rebooting..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME.service
sudo systemctl start $SERVICE_NAME.service

sudo reboot
