#!/usr/bin/env python3

import os
import json
import board
import neopixel
import time
from datetime import datetime, timedelta

CONFIG_PATH = os.environ.get("LEDMATRIX_CONFIG", "config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

LED_COUNT = 64
PIN = board.D18
BRIGHTNESS = config.get("brightness", 0.2)

pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)

# Pomodoro timer configuration
# Timer starts at fixed times: :00 and :30 of each hour
# :00-:25 = work (25 min)
# :25-:30 = break (5 min)
# :30-:55 = work (25 min)
# :55-:00 = break (5 min)
POMODORO_WORK_MINUTES = 25
POMODORO_BREAK_MINUTES = 5

# Matrix is 8x8, divided into 4 quadrants of 4x4 each
# Top-left: hours (0-3, 0-3)
# Top-right: minutes (4-7, 0-3)
# Bottom-left: seconds (0-3, 4-7)
# Bottom-right: pomodoro timer (4-7, 4-7)

def get_outer_ring_positions(quadrant):
    """
    Get the 12 column-based positions for a quadrant as LED indices.
    Quadrant: 0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right
    Pattern: 4-4-2-2 LEDs per column, leaving center 4x4 empty
    Returns list of LED indices filling columns in the specified pattern
    """
    positions = []

    if quadrant == 0:
        # UREN (top-left): columns from left to right, top to bottom
        # Column 0: 4 LEDs down
        positions.extend([0, 8, 16, 24])
        # Column 1: 4 LEDs down
        positions.extend([1, 9, 17, 25])
        # Column 2: 2 LEDs down
        positions.extend([2, 10])
        # Column 3: 2 LEDs down
        positions.extend([3, 11])

    elif quadrant == 1:
        # MINUTEN (top-right): columns from right to left (mirrored), top to bottom
        # Column 3: 4 LEDs down
        positions.extend([7, 15, 23, 31])
        # Column 2: 4 LEDs down
        positions.extend([6, 14, 22, 30])
        # Column 1: 2 LEDs down
        positions.extend([5, 13])
        # Column 0: 2 LEDs down
        positions.extend([4, 12])

    elif quadrant == 2:
        # SECONDEN (bottom-left): columns from left to right, bottom to top
        # Column 0: 4 LEDs up
        positions.extend([56, 48, 40, 32])
        # Column 1: 4 LEDs up
        positions.extend([57, 49, 41, 33])
        # Column 2: 2 LEDs up
        positions.extend([58, 50])
        # Column 3: 2 LEDs up
        positions.extend([59, 51])

    elif quadrant == 3:
        # POMODORO (bottom-right): columns from right to left (mirrored), bottom to top
        # Column 3: 4 LEDs up
        positions.extend([63, 55, 47, 39])
        # Column 2: 4 LEDs up
        positions.extend([62, 54, 46, 38])
        # Column 1: 2 LEDs up
        positions.extend([61, 53])
        # Column 0: 2 LEDs up
        positions.extend([60, 52])

    return positions

def xy_to_led_index(x, y):
    """
    Convert x,y coordinates to LED index.
    Linear layout: left to right, top to bottom (like reading a book)
    Row 0: 0-7 (left to right)
    Row 1: 8-15 (left to right)
    Row 2: 16-23 (left to right)
    etc.
    """
    return y * 8 + x

def map_to_12(value, max_value):
    """
    Map a value (0 to max_value) to 12 positions (0.0-12.0).
    Returns floating point for smooth animations.
    """
    return (value / max_value) * 12

def get_pomodoro_progress():
    """
    Get Pomodoro timer progress (0.0-12.0 positions on ring).
    Timer starts at fixed times: :00 and :30 of each hour
    Returns (position, is_work) where is_work indicates work session (True) or break (False).
    """
    now = datetime.now()
    minute = now.minute
    second = now.second

    # Determine which 30-minute block we're in
    # 0-29 minutes: first block (work :00-:25, break :25-:30)
    # 30-59 minutes: second block (work :30-:55, break :55-:00)

    if minute < 30:
        # First half of the hour
        minutes_in_block = minute  # 0-29
    else:
        # Second half of the hour
        minutes_in_block = minute - 30  # 0-29

    # Determine if work or break session
    if minutes_in_block < POMODORO_WORK_MINUTES:
        # Work session (0-24 minutes)
        is_work = True
        elapsed_seconds = minutes_in_block * 60 + second
        session_duration = POMODORO_WORK_MINUTES * 60
    else:
        # Break session (25-29 minutes)
        is_work = False
        elapsed_seconds = (minutes_in_block - POMODORO_WORK_MINUTES) * 60 + second
        session_duration = POMODORO_BREAK_MINUTES * 60

    # Map progress to 12 positions (floating point for smooth animation)
    progress = elapsed_seconds / session_duration
    position = progress * 12
    if position > 12:
        position = 12

    return position, is_work

def render_clock():
    """
    Render the current time on the LED matrix.
    """
    now = datetime.now()

    # Get current time values
    hour = now.hour % 12  # Convert to 12-hour format (0-11)
    if hour == 0:
        hour = 12
    minute = now.minute
    second = now.second

    # Map to 12 positions
    hour_pos = map_to_12(hour - 1, 11)  # hour is 1-12, we need 0-11
    minute_pos = map_to_12(minute, 59)
    second_pos = map_to_12(second, 59)

    # Get Pomodoro progress
    pomodoro_pos, is_work_session = get_pomodoro_progress()

    # Clear all pixels
    pixels.fill((0, 0, 0))

    # Get outer ring positions for each quadrant
    hour_ring = get_outer_ring_positions(0)     # Top-left
    minute_ring = get_outer_ring_positions(1)   # Top-right
    second_ring = get_outer_ring_positions(2)   # Bottom-left
    pomodoro_ring = get_outer_ring_positions(3) # Bottom-right

    # Helper function to fill ring with smooth progress and trailing effect
    def fill_ring_smooth(ring, progress, color, trail_length=5):
        """Fill a ring with smooth progress (0.0-12.0) and trailing effect"""
        # The current position in the ring
        current_pos = min(progress, 12.0)

        # Iterate through all positions that should be lit
        for i in range(12):
            if i >= current_pos:
                # Haven't reached this LED yet
                continue

            led_idx = ring[i]

            # Distance from current position (can be fractional)
            distance = current_pos - i

            if distance <= trail_length:
                # Within trail range - calculate brightness
                if distance < 1.0:
                    # Current LED (fractional position) - always brightest
                    brightness = 1.0
                else:
                    # Trail LED - exponential falloff
                    brightness = 1.0 - ((distance - 1.0) / trail_length) ** 2

                trailed_color = tuple(int(c * max(brightness, 0.1)) for c in color)
                pixels[led_idx] = trailed_color
            else:
                # Outside trail range - very dim
                pixels[led_idx] = tuple(int(c * 0.1) for c in color)

    # Helper function to fill ring with discrete LEDs and trailing effect
    def fill_ring_discrete(ring, progress, color, trail_length=5):
        """Fill a ring with discrete LEDs (0.0-12.0) and trailing effect"""
        # The current LED position (round up for discrete)
        current_led = min(int(progress) + 1, 12)

        # Fill all LEDs with trailing effect
        for i in range(12):
            if i >= current_led:
                # Haven't reached this LED yet
                continue

            led_idx = ring[i]

            # Distance from current LED
            distance = current_led - 1 - i

            if i == current_led - 1:
                # Current LED - fully bright
                pixels[led_idx] = color
            elif distance < trail_length:
                # Within trail range - exponential falloff
                brightness = 1.0 - (distance / trail_length) ** 2
                trailed_color = tuple(int(c * max(brightness, 0.1)) for c in color)
                pixels[led_idx] = trailed_color
            else:
                # Outside trail range - very dim
                pixels[led_idx] = tuple(int(c * 0.1) for c in color)

    # Use one color for all quadrants: white for work, purple for break
    base_color = (255, 255, 255) if is_work_session else (128, 0, 255)

    # Fill all quadrants with smooth animation and trailing effect
    fill_ring_smooth(hour_ring, hour_pos, base_color)
    fill_ring_smooth(minute_ring, minute_pos, base_color)
    fill_ring_smooth(second_ring, second_pos, base_color)
    fill_ring_smooth(pomodoro_ring, pomodoro_pos, base_color)

    pixels.show()

try:
    while True:
        render_clock()
        time.sleep(0.1)  # Update 10 times per second
except KeyboardInterrupt:
    pixels.fill((0, 0, 0))
    pixels.show()
