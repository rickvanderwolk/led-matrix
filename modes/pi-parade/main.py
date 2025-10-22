#!/usr/bin/env python3

import os
import json
import board
import neopixel
import time
import multiprocessing
from collections import deque
from mpmath import mp

CONFIG_PATH = os.environ.get("LEDMATRIX_CONFIG", "config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

LED_COUNT = 64
PIN = board.D18
BRIGHTNESS = config.get("brightness", 0.2)

pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)

# Colors for binary display
COLOR_ONE = (0, 255, 0)      # Green for 1
COLOR_ZERO = (0, 0, 0)       # Off for 0

# Cache files (in mode directory)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(SCRIPT_DIR, "cache.txt")
POSITION_FILE = os.path.join(SCRIPT_DIR, "cache_position.txt")
CALC_STATE_FILE = os.path.join(SCRIPT_DIR, "calc_state.txt")

# Memory management
CACHE_ROTATION_THRESHOLD = 100000  # Rotate cache file when > 100k digits

# Snake path: bottom-right to top-left zigzag pattern
def create_snake_path():
    path = []
    # Row 7 (bottom): left to right
    for i in range(56, 64):
        path.append(i)
    # Row 6: right to left
    for i in range(55, 47, -1):
        path.append(i)
    # Row 5: left to right
    for i in range(40, 48):
        path.append(i)
    # Row 4: right to left
    for i in range(39, 31, -1):
        path.append(i)
    # Row 3: left to right
    for i in range(24, 32):
        path.append(i)
    # Row 2: right to left
    for i in range(23, 15, -1):
        path.append(i)
    # Row 1: left to right
    for i in range(8, 16):
        path.append(i)
    # Row 0 (top): right to left
    for i in range(7, -1, -1):
        path.append(i)
    return path

SNAKE_PATH = create_snake_path()

def digit_to_binary_bits(digit):
    """Convert a single digit (0-9) to 4 binary bits"""
    binary = format(int(digit), '04b')
    return [int(b) for b in binary]

def calculate_pi_digits(start_digit, num_digits):
    """Calculate pi digits starting from start_digit position"""
    # Set precision high enough to calculate the digits we need
    # We need extra precision to ensure accuracy at the end
    mp.dps = start_digit + num_digits + 100

    # Calculate pi and convert to string
    pi_str = str(mp.pi)

    # Remove "3." from the beginning
    pi_decimals = pi_str.replace('.', '')

    # Extract the digits we need
    if start_digit < len(pi_decimals):
        return pi_decimals[start_digit:start_digit + num_digits]
    return ""

def save_cache_append(new_digits):
    """Append new digits to cache file"""
    try:
        with open(CACHE_FILE, 'a') as f:
            f.write(new_digits)
    except Exception as e:
        print(f"Could not save cache: {e}")

def rotate_cache_file():
    """Remove old digits from cache file to prevent infinite growth"""
    try:
        # Read current cache
        with open(CACHE_FILE, 'r') as f:
            all_digits = f.read().strip()

        # Keep only last 50k digits
        if len(all_digits) > CACHE_ROTATION_THRESHOLD:
            keep_from = len(all_digits) - 50000
            new_cache = all_digits[keep_from:]

            # Write back
            with open(CACHE_FILE, 'w') as f:
                f.write(new_cache)

            print(f"[Calculator] Cache rotated: removed first {keep_from} digits, keeping last 50k")
    except Exception as e:
        print(f"Could not rotate cache: {e}")

def load_calc_state():
    """Load calculator state from disk"""
    if os.path.exists(CALC_STATE_FILE):
        try:
            with open(CALC_STATE_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            pass
    return 0

def save_calc_state(offset):
    """Save calculator state to disk"""
    try:
        with open(CALC_STATE_FILE, 'w') as f:
            f.write(str(offset))
    except Exception as e:
        print(f"Could not save calc state: {e}")

def calculator_process():
    """Separate process that continuously calculates pi digits"""
    try:
        # Lower process priority to not interfere with display
        os.nice(10)  # Lower priority (higher nice value)
    except:
        pass  # nice() not available on all platforms

    print("[Calculator] Starting calculation process...")

    # Load state
    calculation_offset = load_calc_state()

    # If no cache exists, create initial cache
    if not os.path.exists(CACHE_FILE) or calculation_offset == 0:
        print("[Calculator] Creating initial cache (2000 digits)...")
        digits = calculate_pi_digits(0, 2000)
        save_cache_append(digits)
        calculation_offset = len(digits)
        save_calc_state(calculation_offset)
        print(f"[Calculator] Initial cache created: {calculation_offset} digits")

    # Continuous calculation loop
    while True:
        # Calculate next batch of 500 digits (2000 bits)
        print(f"[Calculator] Calculating pi digits {calculation_offset} to {calculation_offset + 500}...")
        new_digits = calculate_pi_digits(calculation_offset, 500)

        if new_digits:
            # Save to disk
            save_cache_append(new_digits)
            calculation_offset += len(new_digits)
            save_calc_state(calculation_offset)

            print(f"[Calculator] Calculated up to digit {calculation_offset}")

            # Check if we need to rotate cache file
            if calculation_offset > CACHE_ROTATION_THRESHOLD and calculation_offset % 10000 == 0:
                rotate_cache_file()

        # Sleep between calculations to keep CPU usage reasonable
        # This doesn't affect display smoothness since we're in separate process
        time.sleep(1.0)

def load_display_position():
    """Load display position from disk"""
    if os.path.exists(POSITION_FILE):
        try:
            with open(POSITION_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            pass
    return 0

def save_display_position(position):
    """Save display position to disk"""
    try:
        with open(POSITION_FILE, 'w') as f:
            f.write(str(position))
    except Exception as e:
        print(f"Could not save position: {e}")

def load_cache_digits():
    """Load all cached digits from disk"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Could not load cache: {e}")
    return ""

def initialize_display_buffer(display_position):
    """Initialize display buffer from cache"""
    # Wait for cache to exist (calculator process creates it)
    print("[Display] Waiting for cache file...")
    while not os.path.exists(CACHE_FILE):
        time.sleep(0.1)

    # Load cache
    cache_digits = load_cache_digits()
    print(f"[Display] Loaded {len(cache_digits)} digits from cache")

    # Extract digits from display position
    if display_position < len(cache_digits):
        digits_to_load = cache_digits[display_position:]
    else:
        print(f"[Display] Position {display_position} beyond cache, starting from 0")
        digits_to_load = cache_digits
        display_position = 0

    # Convert to bits
    bits = []
    for digit in digits_to_load[:3000]:  # Load up to 3000 digits initially
        bits.extend(digit_to_binary_bits(digit))

    print(f"[Display] Buffer initialized with {len(bits)} bits")
    return bits, display_position

# Initialize matrix state (all zeros)
matrix = [0] * LED_COUNT

def render_matrix():
    """Render the current matrix state to the LEDs"""
    for i in range(LED_COUNT):
        bit = matrix[i]
        pixels[i] = COLOR_ONE if bit == 1 else COLOR_ZERO
    pixels.show()

def main():
    # Start calculator process
    calc_process = multiprocessing.Process(target=calculator_process, daemon=True)
    calc_process.start()
    print("[Display] Calculator process started")

    # Load display position
    display_position = load_display_position()
    print(f"[Display] Resuming from digit position {display_position}")

    # Initialize buffer
    bit_buffer, display_position = initialize_display_buffer(display_position)
    bit_buffer = deque(bit_buffer)

    # Keep track of last cache reload
    last_cache_reload = time.time()
    cache_digits = load_cache_digits()

    print("[Display] Starting Pi Parade...")
    print("[Display] Each digit of pi is shown in 4-bit binary, scrolling through the matrix")

    bit_counter = 0  # Count bits to track digit progression
    frame_counter = 0  # Count frames for periodic position saves

    try:
        while True:
            # Reload cache periodically to get new digits
            if time.time() - last_cache_reload > 10.0:  # Every 10 seconds
                new_cache = load_cache_digits()
                if len(new_cache) > len(cache_digits):
                    # New digits available
                    new_digits = new_cache[len(cache_digits):]
                    cache_digits = new_cache

                    # Add new bits to buffer
                    for digit in new_digits:
                        bit_buffer.extend(digit_to_binary_bits(digit))

                    print(f"[Display] Loaded {len(new_digits)} new digits (buffer: {len(bit_buffer)} bits)")

                last_cache_reload = time.time()

            # Get next bit from buffer
            if len(bit_buffer) > 0:
                next_bit = bit_buffer.popleft()
            else:
                # Buffer empty, wait for more calculation
                print("[Display] Buffer empty, waiting for calculation...")
                time.sleep(2.0)
                # Reload cache immediately
                cache_digits = load_cache_digits()
                last_cache_reload = time.time()
                continue

            # Shift all bits along the snake path
            for i in range(63, 0, -1):
                src_pos = SNAKE_PATH[i-1]
                dst_pos = SNAKE_PATH[i]
                matrix[dst_pos] = matrix[src_pos]

            # Add new bit at the start of snake (bottom-right)
            entry_pos = SNAKE_PATH[0]
            matrix[entry_pos] = next_bit

            # Render to LEDs
            render_matrix()

            # Update display position
            bit_counter += 1
            if bit_counter >= 4:
                display_position += 1
                bit_counter = 0

            # Save position periodically (every 500 frames = ~100 seconds = ~1.5 min)
            frame_counter += 1
            if frame_counter >= 500:
                save_display_position(display_position)
                frame_counter = 0

            # Control scroll speed
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\n[Display] Stopping Pi Parade...")
        save_display_position(display_position)  # Save position on exit
        pixels.fill((0, 0, 0))
        pixels.show()
        calc_process.terminate()

if __name__ == "__main__":
    main()
