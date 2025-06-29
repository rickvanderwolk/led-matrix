#!/bin/bash

set -e

INSTALL_DIR=$(pwd)
SERVICE_NAME=ledmatrix

echo "Installing system packages..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-dev git

echo "Creating Python virtual environment..."
python3 -m venv "$INSTALL_DIR/ledmatrix"

echo "Installing Python packages in virtualenv..."
"$INSTALL_DIR/ledmatrix/bin/pip" install --upgrade pip
"$INSTALL_DIR/ledmatrix/bin/pip" install rpi_ws281x adafruit-circuitpython-neopixel RPi.GPIO flask

echo "Creating default config.json..."
cat > "$INSTALL_DIR/config.json" <<EOF
{
  "selected_mode": null
}
EOF

echo "Creating systemd service file..."
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=LED Matrix Mode Runner
After=network.target

[Service]
ExecStart=$INSTALL_DIR/ledmatrix/bin/python3 $INSTALL_DIR/main.py
WorkingDirectory=$INSTALL_DIR
Restart=always
User=$(whoami)
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd and enabling service..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "✅ Install complete. Service is running."
