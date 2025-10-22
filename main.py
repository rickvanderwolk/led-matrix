#!/usr/bin/env python3

__version__ = "1.3.1"

import json
import os
import time
import subprocess
import socket

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
MODES_DIR = os.path.join(BASE_DIR, "modes")

# Mode name redirects for backward compatibility
MODE_REDIRECTS = {
    "quadrant-clock-with-pomodoro-timer": "clock",
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

def is_wifi_setup_mode():
    """Check if WiFi Connect is running in Access Point mode"""
    try:
        # Check if wlan0 is in AP/Master mode
        result = subprocess.run(
            ["iwconfig", "wlan0"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # If Mode:Master is in output, we're in AP mode
        if "Mode:Master" in result.stdout:
            return True

        # Alternative: Check if we have internet connectivity
        # If no internet, WiFi Connect might be in setup mode
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return False  # We have internet, not in setup mode

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        # If we can't determine, assume we need setup
        return True
    except Exception:
        return False

def main():
    while True:
        # Check if we're in WiFi setup mode (AP mode active)
        if is_wifi_setup_mode():
            mode = "wifi-setup"
            print("WiFi setup mode detected - Access Point active")
            print("Connect to 'led-matrix' WiFi to configure")
        else:
            config = load_config()
            mode = config.get("selected_mode")

            if not mode:
                print("No mode selected. Waiting...")
                time.sleep(5)
                continue

            # Handle mode name redirects for backward compatibility
            if mode in MODE_REDIRECTS:
                old_mode = mode
                mode = MODE_REDIRECTS[mode]
                print(f"Mode '{old_mode}' has been renamed to '{mode}', redirecting...")

        script_path = os.path.join(MODES_DIR, mode, "main.py")

        if not os.path.exists(script_path):
            print(f"No script found for mode: {mode}")
            time.sleep(5)
            continue

        print(f"Running mode: {mode} (LED Matrix v{__version__})")

        env = os.environ.copy()
        env["LEDMATRIX_CONFIG"] = CONFIG_PATH

        subprocess.run(
            [os.path.join(BASE_DIR, "ledmatrix", "bin", "python3"), script_path],
            env=env
        )

        print("Script exited. Restarting in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    main()
