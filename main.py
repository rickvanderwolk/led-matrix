#!/usr/bin/env python3

import json
import os
import time
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
MODES_DIR = os.path.join(BASE_DIR, "modes")

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

def main():
    while True:
        config = load_config()
        mode = config.get("selected_mode")

        if not mode:
            print("No mode selected. Waiting...")
            time.sleep(5)
            continue

        script_path = os.path.join(MODES_DIR, mode, "main.py")

        if not os.path.exists(script_path):
            print(f"No script found for mode: {mode}")
            time.sleep(5)
            continue

        print(f"Running mode: {mode}")

        env = os.environ.copy()
        env["LEDMATRIX_CONFIG"] = CONFIG_PATH  # kan ook hardcoded blijven, of BASE_DIR gebruiken

        subprocess.run(
            [os.path.join(BASE_DIR, "ledmatrix", "bin", "python3"), script_path],
            env=env
        )

        print("Script exited. Restarting in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    main()
