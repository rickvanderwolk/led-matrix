#!/usr/bin/env python3

import os
import json
import board
import neopixel
import time
import threading
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

# Memory management
MAX_CACHE_DIGITS_IN_RAM = 50000  # Keep max 50k digits in RAM
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

# Global buffer for pi bits
bit_buffer = deque()
buffer_lock = threading.Lock()
calculation_offset = 0  # Track how many digits we've calculated
display_position = 0    # Track which digit is being displayed
cache_digits = ""       # Recent calculated digits (limited to 50k in RAM)
cache_start_offset = 0  # Which digit does cache_digits start at

def load_cache():
    """Load cached pi digits and display position from disk"""
    global cache_digits, calculation_offset, display_position, cache_start_offset

    # Load display position first
    if os.path.exists(POSITION_FILE):
        try:
            with open(POSITION_FILE, 'r') as f:
                display_position = int(f.read().strip())
            print(f"Resuming from digit position {display_position}")
        except Exception as e:
            print(f"Could not load position: {e}")
            display_position = 0

    # Load cached digits
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache_digits = f.read().strip()
            calculation_offset = len(cache_digits)
            cache_start_offset = 0

            # Memory optimization: only keep relevant portion in RAM
            if len(cache_digits) > MAX_CACHE_DIGITS_IN_RAM:
                # Keep from display_position onwards, up to MAX_CACHE_DIGITS_IN_RAM
                start_pos = max(0, display_position - 1000)  # Keep 1000 before display pos
                cache_digits = cache_digits[start_pos:]
                cache_start_offset = start_pos

            print(f"Loaded {calculation_offset} digits from cache (keeping {len(cache_digits)} in RAM)")
        except Exception as e:
            print(f"Could not load cache: {e}")
            cache_digits = ""
            calculation_offset = 0
            cache_start_offset = 0

def save_cache_append(new_digits):
    """Append new digits to cache file"""
    try:
        with open(CACHE_FILE, 'a') as f:
            f.write(new_digits)
    except Exception as e:
        print(f"Could not save cache: {e}")

def rotate_cache_file():
    """Remove old digits from cache file to prevent infinite growth"""
    global cache_start_offset

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

            # Update offset
            cache_start_offset = keep_from

            print(f"Cache rotated: removed first {keep_from} digits, keeping last 50k")
    except Exception as e:
        print(f"Could not rotate cache: {e}")

def save_position():
    """Save current display position to disk"""
    try:
        with open(POSITION_FILE, 'w') as f:
            f.write(str(display_position))
    except Exception as e:
        print(f"Could not save position: {e}")

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

def digit_to_binary_bits(digit):
    """Convert a single digit (0-9) to 4 binary bits"""
    binary = format(int(digit), '04b')
    return [int(b) for b in binary]

def background_calculator():
    """Background thread that continuously calculates more pi digits"""
    global calculation_offset, cache_digits

    while True:
        # Calculate next batch of 500 digits (2000 bits)
        # Always keep calculating, building up cache
        print(f"Calculating pi digits {calculation_offset} to {calculation_offset + 500}...")
        new_digits = calculate_pi_digits(calculation_offset, 500)

        if new_digits:
            # Add to cache in RAM
            cache_digits += new_digits

            # Memory management: trim cache_digits if too large
            if len(cache_digits) > MAX_CACHE_DIGITS_IN_RAM + 5000:
                # Keep last 50k + some buffer for display
                trim_amount = len(cache_digits) - MAX_CACHE_DIGITS_IN_RAM
                cache_digits = cache_digits[trim_amount:]
                cache_start_offset += trim_amount
                print(f"Trimmed {trim_amount} digits from RAM cache")

            calculation_offset += len(new_digits)

            # Convert to bits and add to buffer
            new_bits = []
            for digit in new_digits:
                new_bits.extend(digit_to_binary_bits(digit))

            with buffer_lock:
                bit_buffer.extend(new_bits)

            # Save to disk
            save_cache_append(new_digits)

            print(f"Calculated up to digit {calculation_offset} (buffer: {len(bit_buffer)} bits, display at: {display_position})")

            # Check if we need to rotate cache file
            if calculation_offset > CACHE_ROTATION_THRESHOLD and calculation_offset % 10000 == 0:
                rotate_cache_file()

        # Small sleep to prevent CPU hogging
        time.sleep(0.5)

def initialize_buffer():
    """Initialize buffer with cached or newly calculated digits"""
    global calculation_offset, cache_digits, display_position, cache_start_offset

    # Load cache first
    load_cache()

    # If we have cached digits, use them
    if cache_digits and len(cache_digits) > 0:
        print(f"Using cached digits (total calculated: {calculation_offset}, in RAM: {len(cache_digits)})")

        # Calculate which digits to load into buffer
        # display_position is absolute, cache_start_offset tells us where cache_digits starts
        relative_display_pos = display_position - cache_start_offset

        if relative_display_pos >= 0 and relative_display_pos < len(cache_digits):
            # Fill buffer from cache starting at display position
            digits_to_load = cache_digits[relative_display_pos:]

            bits = []
            for digit in digits_to_load[:2000]:  # Load up to 2000 digits
                bits.extend(digit_to_binary_bits(digit))

            with buffer_lock:
                bit_buffer.extend(bits)

            print(f"Buffer initialized with {len(bit_buffer)} bits from cache")
        else:
            print(f"Display position {display_position} not in current cache, recalculating...")
            # This shouldn't happen, but fallback: recalculate from display position
            digits = calculate_pi_digits(display_position, 2000)
            cache_digits = digits
            cache_start_offset = display_position
            calculation_offset = display_position + len(digits)

            bits = []
            for digit in digits:
                bits.extend(digit_to_binary_bits(digit))

            with buffer_lock:
                bit_buffer.extend(bits)

            print(f"Buffer initialized with {len(bit_buffer)} bits (recalculated)")
    else:
        # No cache, calculate initial batch
        print("No cache found, calculating initial 2000 digits...")
        digits = calculate_pi_digits(0, 2000)

        cache_digits = digits
        cache_start_offset = 0
        calculation_offset = len(digits)

        bits = []
        for digit in digits:
            bits.extend(digit_to_binary_bits(digit))

        with buffer_lock:
            bit_buffer.extend(bits)

        # Save initial cache
        save_cache_append(digits)

        print(f"Buffer initialized with {len(bit_buffer)} bits (first 2000 digits)")

def get_next_bit():
    """Get the next bit from the buffer, wait if empty"""
    while True:
        with buffer_lock:
            if bit_buffer:
                return bit_buffer.popleft()

        # Buffer is empty, wait for background calculator
        print("Buffer empty, waiting for calculation...")
        time.sleep(0.5)

# Initialize matrix state (all zeros)
matrix = [0] * LED_COUNT

def render_matrix():
    """Render the current matrix state to the LEDs"""
    for i in range(LED_COUNT):
        bit = matrix[i]
        pixels[i] = COLOR_ONE if bit == 1 else COLOR_ZERO
    pixels.show()

def main():
    global display_position

    # Initialize buffer (load cache or calculate)
    initialize_buffer()

    # Start background calculator thread
    calculator_thread = threading.Thread(target=background_calculator, daemon=True)
    calculator_thread.start()

    print("Starting Pi Parade...")
    print("Each digit of pi is shown in 4-bit binary, scrolling through the matrix")

    bit_counter = 0  # Count bits to track digit progression
    frame_counter = 0  # Count frames for periodic position saves

    try:
        while True:
            # Get next bit (waits if buffer empty)
            next_bit = get_next_bit()

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
                save_position()
                frame_counter = 0

            # Control scroll speed
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\nStopping Pi Parade...")
        save_position()  # Save position on exit
        pixels.fill((0, 0, 0))
        pixels.show()

if __name__ == "__main__":
    main()
