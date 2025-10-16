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
    Get the 12 outer ring positions for a quadrant as LED indices.
    Quadrant: 0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right
    Returns list of LED indices in clockwise order like a clock
    """
    # Base coordinates for each quadrant (top-left corner)
    base_x = (quadrant % 2) * 4
    base_y = (quadrant // 2) * 4

    # Manually define the 12 positions clockwise for each quadrant
    # We'll convert to LED indices directly
    positions = []

    # Top row (y=0): 4 positions, left to right
    for x in range(4):
        positions.append(xy_to_led_index(base_x + x, base_y))

    # Right column (x=3): 3 positions going down (y=1,2,3)
    for y in range(1, 4):
        positions.append(xy_to_led_index(base_x + 3, base_y + y))

    # Bottom row (y=3): 3 positions going left (x=2,1,0)
    for x in range(2, -1, -1):
        positions.append(xy_to_led_index(base_x + x, base_y + 3))

    # Left column (x=0): 2 positions going up (y=2,1)
    for y in range(2, 0, -1):
        positions.append(xy_to_led_index(base_x, base_y + y))

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

    # Helper function to fill ring with smooth progress (for fast-changing values)
    def fill_ring_smooth(ring, progress, color):
        """Fill a ring with smooth progress (0.0-12.0)"""
        full_leds = int(progress)  # Number of fully lit LEDs
        fraction = progress - full_leds  # Fractional part for partial LED

        # Fill all fully lit LEDs
        for i in range(min(full_leds, 12)):
            led_idx = ring[i]
            pixels[led_idx] = color

        # Fill partial LED with dimmed brightness
        if full_leds < 12 and fraction > 0:
            led_idx = ring[full_leds]
            dimmed_color = tuple(int(c * fraction) for c in color)
            pixels[led_idx] = dimmed_color

    # Helper function to fill ring with discrete LEDs (for slow-changing values)
    def fill_ring_discrete(ring, progress, color):
        """Fill a ring with discrete LEDs (0.0-12.0)"""
        full_leds = int(progress) + 1  # Number of fully lit LEDs (round up)

        # Fill all fully lit LEDs
        for i in range(min(full_leds, 12)):
            led_idx = ring[i]
            pixels[led_idx] = color

    # Fill hours (red) - discrete
    fill_ring_discrete(hour_ring, hour_pos, (255, 0, 0))

    # Fill minutes (green) - discrete
    fill_ring_discrete(minute_ring, minute_pos, (0, 255, 0))

    # Fill seconds (blue) - smooth
    fill_ring_smooth(second_ring, second_pos, (0, 0, 255))

    # Fill Pomodoro timer (yellow for work, purple for break) - smooth
    pomodoro_color = (255, 255, 0) if is_work_session else (128, 0, 255)
    fill_ring_smooth(pomodoro_ring, pomodoro_pos, pomodoro_color)

    pixels.show()

try:
    while True:
        render_clock()
        time.sleep(0.1)  # Update 10 times per second
except KeyboardInterrupt:
    pixels.fill((0, 0, 0))
    pixels.show()
