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
calculating = False

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
    """Background thread that calculates more pi digits when buffer is low"""
    global calculation_offset, calculating

    while True:
        with buffer_lock:
            buffer_size = len(bit_buffer)

        # If buffer is getting low (less than 1000 bits), calculate more
        if buffer_size < 1000:
            calculating = True

            # Calculate next batch of 500 digits (2000 bits)
            new_digits = calculate_pi_digits(calculation_offset, 500)

            # Convert to bits
            new_bits = []
            for digit in new_digits:
                new_bits.extend(digit_to_binary_bits(digit))

            # Add to buffer
            with buffer_lock:
                bit_buffer.extend(new_bits)
                calculation_offset += len(new_digits)

            calculating = False
            print(f"Calculated pi up to digit {calculation_offset} (buffer: {len(bit_buffer)} bits)")

        time.sleep(0.1)

def initialize_buffer():
    """Initialize buffer with first 1000 digits of pi"""
    global calculation_offset

    print("Initializing pi buffer...")
    digits = calculate_pi_digits(0, 1000)

    bits = []
    for digit in digits:
        bits.extend(digit_to_binary_bits(digit))

    with buffer_lock:
        bit_buffer.extend(bits)
        calculation_offset = 1000

    print(f"Buffer initialized with {len(bit_buffer)} bits (first 1000 digits)")

def get_next_bit():
    """Get the next bit from the buffer"""
    with buffer_lock:
        if bit_buffer:
            return bit_buffer.popleft()
    return 0

# Initialize matrix state (all zeros)
matrix = [0] * LED_COUNT

def render_matrix():
    """Render the current matrix state to the LEDs"""
    for i in range(LED_COUNT):
        bit = matrix[i]
        pixels[i] = COLOR_ONE if bit == 1 else COLOR_ZERO
    pixels.show()

def main():
    # Initialize buffer
    initialize_buffer()

    # Start background calculator thread
    calculator_thread = threading.Thread(target=background_calculator, daemon=True)
    calculator_thread.start()

    print("Starting Pi Parade...")
    print("Each digit of pi is shown in 4-bit binary, scrolling through the matrix")

    try:
        while True:
            # Get next bit
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

            # Control scroll speed (adjust as needed)
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\nStopping Pi Parade...")
        pixels.fill((0, 0, 0))
        pixels.show()

if __name__ == "__main__":
    main()
