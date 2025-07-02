#!/bin/bash

set -e

INSTALL_DIR=$(cd "$(dirname "$0")" && pwd)
SERVICE_NAME=ledmatrix

echo "Installing system packages..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-dev git

echo "Creating Python virtual environment..."
python3 -m venv "$INSTALL_DIR/ledmatrix"

echo "Installing Python packages in virtualenv..."
"$INSTALL_DIR/ledmatrix/bin/pip" install --upgrade pip
"$INSTALL_DIR/ledmatrix/bin/pip" install rpi_ws281x adafruit-circuitpython-neopixel RPi.GPIO flask websocket-client

echo "Ensuring config.json exists with required keys (excluding placeholders)..."
CONFIG_EXAMPLE="$INSTALL_DIR/config.example.json"
CONFIG_TARGET="$INSTALL_DIR/config.json"

if [ ! -f "$CONFIG_TARGET" ]; then
  cp "$CONFIG_EXAMPLE" "$CONFIG_TARGET"
  echo "config.json created from config.example.json"
else
  "$INSTALL_DIR/ledmatrix/bin/python3" - <<EOF
import json
import re
from pathlib import Path

example_path = Path("$CONFIG_EXAMPLE")
target_path = Path("$CONFIG_TARGET")

with example_path.open() as f:
    example = json.load(f)

with target_path.open() as f:
    target = json.load(f)

for key, value in example.items():
    if key not in target:
        if isinstance(value, str) and re.fullmatch(r"<.*?>", value):
            continue
        target[key] = value

with target_path.open("w") as f:
    json.dump(target, f, indent=4)
EOF
  echo "config.json updated with missing non-placeholder keys from config.example.json"
fi

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
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd and enabling service..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "✅ Done! The LED matrix is now running and will auto-start on reboot."
