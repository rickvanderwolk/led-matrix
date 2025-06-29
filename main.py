#!/usr/bin/env python3

import json
import os
import time
import subprocess

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
MODES_DIR = os.path.join(os.path.dirname(__file__), "modes")

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {"selected_mode": None}

def main():
    while True:
        config = load_config()
        mode = config.get("selected_mode")
        if not mode:
            print("No mode selected. Waiting...")
            time.sleep(5)
            continue

        mode_path = os.path.join(MODES_DIR, mode)
        script_path = os.path.join(mode_path, "main.py")

        if not os.path.exists(script_path):
            print(f"No script found for mode: {mode}")
            time.sleep(5)
            continue

        print(f"Running mode: {mode}")
        subprocess.run(["/usr/bin/sudo", os.path.join(os.path.dirname(__file__), "ledmatrix", "bin", "python3"), script_path])
        print("Script exited. Restarting in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    main()
