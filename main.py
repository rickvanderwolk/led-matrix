#!/usr/bin/env python3

__version__ = "1.4.0"

import json
import os
import subprocess
import sys
import time

from core import config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = config.path()
MODES_DIR = os.path.join(BASE_DIR, "modes")
PYTHON = os.path.join(BASE_DIR, "ledmatrix", "bin", "python3")

CHECK_INTERVAL = 2  # seconds between config checks
RESTART_DELAY = 5  # seconds to wait before restarting a mode that exited

# Mode name redirects for backward compatibility
MODE_REDIRECTS = {
    "quadrant-clock-with-pomodoro-timer": "clock",
}


def desired_state():
    """
    The mode that should run now, plus a fingerprint of everything that requires a restart
    when it changes. Brightness is left out: running modes pick that up themselves.
    """
    active = config.active(config.load(CONFIG_PATH))
    mode = active.get("selected_mode")
    fingerprint = json.dumps(
        [mode, active.get("display"), active.get("modes", {}).get(mode)], sort_keys=True
    )
    return mode, fingerprint


def start(mode):
    if mode in MODE_REDIRECTS:
        print(f"Mode '{mode}' has been renamed to '{MODE_REDIRECTS[mode]}', redirecting...")
        mode = MODE_REDIRECTS[mode]

    script_path = os.path.join(MODES_DIR, mode, "main.py")
    if not os.path.exists(script_path):
        print(f"No script found for mode: {mode}")
        return None

    print(f"Running mode: {mode} (LED Matrix v{__version__})")
    env = os.environ.copy()
    env["LEDMATRIX_CONFIG"] = CONFIG_PATH
    env["LEDMATRIX_MODE"] = mode
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [BASE_DIR, env.get("PYTHONPATH")]))
    python = PYTHON if os.path.exists(PYTHON) else sys.executable
    return subprocess.Popen([python, script_path], env=env)


def stop(process):
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def main():
    process = None
    running = None  # fingerprint of the running mode
    retry_at = 0

    while True:
        try:
            mode, fingerprint = desired_state()
        except (OSError, ValueError) as e:
            # Probably mid-edit; keep whatever is running
            print(f"Could not read config: {e}")
            time.sleep(CHECK_INTERVAL)
            continue

        if process and process.poll() is not None:
            print(f"Mode exited. Restarting in {RESTART_DELAY} seconds...")
            process = None
            retry_at = time.monotonic() + RESTART_DELAY

        if process and fingerprint != running:
            print("Config changed, switching...")
            stop(process)
            process = None
            retry_at = 0

        if process is None and time.monotonic() >= retry_at:
            if not mode:
                print("No mode selected. Waiting...")
            else:
                process = start(mode)
            running = fingerprint
            if process is None:
                retry_at = time.monotonic() + RESTART_DELAY

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
