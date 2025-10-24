#!/usr/bin/env python3

import os
import json
import board
import neopixel
import time
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

# Colors for progress indicator
COLOR_WHITE = (255, 255, 255)  # White for progress display
COLOR_BLACK = (0, 0, 0)         # Black/off for background

# Position file to track where we are
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POSITION_FILE = os.path.join(SCRIPT_DIR, "position.txt")

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

def number_to_binary_markers(number):
    """Convert a number to binary representation with white markers"""
    # Convert each digit of the number to binary
    number_str = str(number)
    markers = []

    for digit_char in number_str:
        digit_bits = digit_to_binary_bits(digit_char)
        # Convert bits to white markers ('W') or black (0)
        for bit in digit_bits:
            markers.append('W' if bit == 1 else 0)

    return markers

# 7-segment display patterns for digits 0-9
# Each digit is 3 columns wide x 5 rows tall
# Format: list of 15 values (5 rows × 3 cols), 1=on, 0=off
DIGIT_PATTERNS = {
    '0': [1, 1, 1,
          1, 0, 1,
          1, 0, 1,
          1, 0, 1,
          1, 1, 1],
    '1': [0, 0, 1,
          0, 0, 1,
          0, 0, 1,
          0, 0, 1,
          0, 0, 1],
    '2': [1, 1, 1,
          0, 0, 1,
          1, 1, 1,
          1, 0, 0,
          1, 1, 1],
    '3': [1, 1, 1,
          0, 0, 1,
          1, 1, 1,
          0, 0, 1,
          1, 1, 1],
    '4': [1, 0, 1,
          1, 0, 1,
          1, 1, 1,
          0, 0, 1,
          0, 0, 1],
    '5': [1, 1, 1,
          1, 0, 0,
          1, 1, 1,
          0, 0, 1,
          1, 1, 1],
    '6': [1, 1, 1,
          1, 0, 0,
          1, 1, 1,
          1, 0, 1,
          1, 1, 1],
    '7': [1, 1, 1,
          0, 0, 1,
          0, 0, 1,
          0, 0, 1,
          0, 0, 1],
    '8': [1, 1, 1,
          1, 0, 1,
          1, 1, 1,
          1, 0, 1,
          1, 1, 1],
    '9': [1, 1, 1,
          1, 0, 1,
          1, 1, 1,
          0, 0, 1,
          1, 1, 1],
}


def calculate_pi_digit(position):
    """Calculate a single digit of pi at the given position (0-indexed, after decimal point)"""
    # Set precision high enough to calculate this digit
    # We need extra precision to ensure accuracy
    mp.dps = position + 50

    # Calculate pi and convert to string
    pi_str = str(mp.pi)

    # Remove "3." from the beginning to get just decimal digits
    pi_decimals = pi_str.replace('.', '')

    # Return the digit at this position
    if position < len(pi_decimals):
        return pi_decimals[position]
    return None

def load_position():
    """Load current display position from disk"""
    if os.path.exists(POSITION_FILE):
        try:
            with open(POSITION_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            pass
    return 0

def save_position(position):
    """Save current display position to disk"""
    try:
        with open(POSITION_FILE, 'w') as f:
            f.write(str(position))
    except Exception as e:
        print(f"Could not save position: {e}")

# Initialize matrix state (all zeros)
# Each element can be: 0, 1 (for binary), or 'W' for white progress marker
matrix = [0] * LED_COUNT

def render_matrix():
    """Render the current matrix state to the LEDs"""
    for i in range(LED_COUNT):
        value = matrix[i]
        if value == 'W':
            pixels[i] = COLOR_WHITE
        elif value == 1:
            pixels[i] = COLOR_ONE
        else:
            pixels[i] = COLOR_ZERO
    pixels.show()

def main():
    # Load starting position
    current_digit_position = load_position()

    print("Starting Pi Parade (Real-Time Mode)...", flush=True)
    print(f"Starting from digit position: {current_digit_position}", flush=True)
    print("Each digit is calculated in real-time as we go", flush=True)
    print("Display will naturally slow down as calculations get harder", flush=True)
    print("Running at full speed - no artificial delays!", flush=True)

    # Test: Flash the display to show it's working
    print("Testing display...", flush=True)
    pixels.fill((255, 0, 0))  # Red
    pixels.show()
    time.sleep(0.5)
    pixels.fill((0, 0, 0))  # Off
    pixels.show()
    print("Display test complete!", flush=True)

    bit_buffer = []  # Buffer to hold the 4 bits of current digit
    last_log_position = current_digit_position
    last_progress_display = (current_digit_position // 100) * 100  # Last 100-mark we showed

    try:
        while True:
            # If buffer is empty, calculate the next digit
            if len(bit_buffer) == 0:
                calc_start = time.time()

                digit = calculate_pi_digit(current_digit_position)

                calc_time = time.time() - calc_start

                if digit is None:
                    print(f"Could not calculate digit at position {current_digit_position}")
                    break

                # Convert digit to 4 bits and add to buffer
                bit_buffer = digit_to_binary_bits(digit)

                # Save position every digit
                save_position(current_digit_position)

                # Add progress marker every 100 digits
                # Insert white/black binary representation of position number
                if current_digit_position > 0 and current_digit_position % 100 == 0 and current_digit_position != last_progress_display:
                    print(f"[MILESTONE] Reached digit {current_digit_position}!")
                    # Convert position to binary markers (white for 1, black for 0)
                    progress_markers = number_to_binary_markers(current_digit_position)
                    print(f"[DEBUG] Progress markers for {current_digit_position}: {progress_markers}")
                    # Prepend to buffer so it flows through the snake
                    bit_buffer = progress_markers + bit_buffer
                    print(f"[DEBUG] Buffer after adding markers: {bit_buffer}")
                    last_progress_display = current_digit_position

                # Log every 10 digits
                if current_digit_position - last_log_position >= 10:
                    print(f"[Position {current_digit_position}] Digit: {digit} = {bit_buffer} (calculated in {calc_time:.3f}s)")
                    last_log_position = current_digit_position

                # Move to next digit for next time
                current_digit_position += 1

            # Get next bit from buffer
            next_bit = bit_buffer.pop(0)

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

            # Tiny sleep to keep SSH responsive
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nStopping Pi Parade...")
        save_position(current_digit_position)
        pixels.fill((0, 0, 0))
        pixels.show()

# Run main function directly (no if __name__ check needed for visualizer compatibility)
main()
