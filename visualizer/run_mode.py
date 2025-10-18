#!/usr/bin/env python3
"""
LED Matrix Mode Runner with Visualization
Runs LED matrix modes with a virtual display instead of real hardware
"""

import sys
import os
import importlib.util
import threading
import time

# Add parent directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VISUALIZER_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, VISUALIZER_DIR)

# Mode name redirects for backward compatibility
MODE_REDIRECTS = {
    "quadrant-clock-with-pomodoro-timer": "clock",
}

# Import mock hardware BEFORE any mode scripts can import real hardware
import mock_hardware

# Inject mock modules into sys.modules so they're used by all imports
sys.modules['board'] = mock_hardware
sys.modules['neopixel'] = mock_hardware

# Now import the GUI
from gui import ThreadedVisualizer


def run_mode(mode_path, config_path=None):
    """
    Run a LED mode script with visualization

    Args:
        mode_path: Path to the mode's main.py file
        config_path: Optional path to config.json
    """

    if not os.path.exists(mode_path):
        print(f"Error: Mode script not found: {mode_path}")
        return

    # Set up config path
    if config_path:
        os.environ["LEDMATRIX_CONFIG"] = config_path
    elif "LEDMATRIX_CONFIG" not in os.environ:
        default_config = os.path.join(BASE_DIR, "config.json")
        if os.path.exists(default_config):
            os.environ["LEDMATRIX_CONFIG"] = default_config

    # Create visualizer (but don't start it yet)
    mode_name = os.path.basename(os.path.dirname(mode_path))

    print(f"Starting visualizer for mode: {mode_name}")
    print("Controls:")
    print("  Q - Quit")
    print("  SPACE - Pause/Resume")
    print("  +/- - Adjust brightness")
    print()

    # Clear any existing mock instances
    mock_hardware.MockNeoPixel.clear_instances()

    # Load and run the mode script in a separate thread
    script_thread = None
    neopixel_instance_ref = [None]  # Use list to allow modification in closure

    def run_script():
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location("led_mode", mode_path)
            module = importlib.util.module_from_spec(spec)

            # Give visualizer a moment to initialize
            time.sleep(0.2)

            # Execute the module (this runs the mode's main code)
            spec.loader.exec_module(module)

            # After script runs, store the neopixel instance
            neopixel_instance_ref[0] = mock_hardware.MockNeoPixel.get_latest_instance()

        except KeyboardInterrupt:
            print("\nMode interrupted by user")
        except Exception as e:
            print(f"Error running mode: {e}")
            import traceback
            traceback.print_exc()

    script_thread = threading.Thread(target=run_script, daemon=True)
    script_thread.start()

    # Wait a moment for the script to create its NeoPixel instance
    time.sleep(0.3)

    # Get the NeoPixel instance
    neopixel_instance = mock_hardware.MockNeoPixel.get_latest_instance()

    if neopixel_instance:
        print(f"Connected to NeoPixel instance ({neopixel_instance.n} LEDs)")
    else:
        print("Warning: No NeoPixel instance found")

    # Now create visualizer on main thread
    from gui import LEDMatrixVisualizer
    viz = LEDMatrixVisualizer(
        width=8,
        height=8,
        led_size=60,
        spacing=5,
        title=f"LED Matrix: {mode_name}"
    )

    # Set up callback to update visualizer when pixels change
    if neopixel_instance:
        def update_viz(pixels):
            if viz.running and not viz.paused:
                viz.set_pixels(pixels)

        neopixel_instance.set_update_callback(update_viz)

        # Set initial state
        viz.set_pixels(neopixel_instance.get_pixels())

    # Run visualizer on main thread (blocking until closed)
    try:
        viz.run()
    except KeyboardInterrupt:
        print("\nShutting down...")

    print("Visualizer closed")


def list_modes():
    """List available modes"""
    modes_dir = os.path.join(BASE_DIR, "modes")

    if not os.path.exists(modes_dir):
        print("No modes directory found")
        return []

    modes = []
    for item in os.listdir(modes_dir):
        mode_path = os.path.join(modes_dir, item)
        main_path = os.path.join(mode_path, "main.py")

        if os.path.isdir(mode_path) and os.path.exists(main_path):
            modes.append(item)

    return sorted(modes)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="LED Matrix Visualizer")
    parser.add_argument("mode", nargs="?", help="Mode name or path to main.py")
    parser.add_argument("--list", action="store_true", help="List available modes")
    parser.add_argument("--config", help="Path to config.json")

    args = parser.parse_args()

    if args.list:
        print("Available modes:")
        for mode in list_modes():
            print(f"  - {mode}")
        return

    if not args.mode:
        print("Available modes:")
        modes = list_modes()
        for i, mode in enumerate(modes, 1):
            print(f"  {i}. {mode}")

        print()
        choice = input("Select a mode (number or name): ").strip()

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(modes):
                mode = modes[idx]
            else:
                print("Invalid selection")
                return
        else:
            mode = choice
    else:
        mode = args.mode

    # Handle mode name redirects for backward compatibility
    if mode in MODE_REDIRECTS:
        old_mode = mode
        mode = MODE_REDIRECTS[mode]
        print(f"Note: Mode '{old_mode}' has been renamed to '{mode}'")

    # Determine mode path
    if os.path.exists(mode):
        # Direct path provided
        mode_path = mode
    else:
        # Mode name provided
        mode_path = os.path.join(BASE_DIR, "modes", mode, "main.py")

    # Run the mode
    run_mode(mode_path, args.config)


if __name__ == "__main__":
    main()
