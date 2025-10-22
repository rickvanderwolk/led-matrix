#!/usr/bin/env python3

import os
import json
import board
import neopixel
import time
import math

CONFIG_PATH = os.environ.get("LEDMATRIX_CONFIG", "config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

LED_COUNT = 64
PIN = board.D18
BRIGHTNESS = config.get("brightness", 0.2)
ROTATION = config.get("rotation", 0)
MIRROR_X = config.get("mirror_x", False)
MIRROR_Y = config.get("mirror_y", False)

pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)

def xy_to_index(x, y):
    """Convert x,y coordinates to LED index with rotation and mirroring"""
    # Apply mirroring
    if MIRROR_X:
        x = 7 - x
    if MIRROR_Y:
        y = 7 - y

    # Apply rotation (0, 90, 180, 270)
    for _ in range(ROTATION // 90):
        x, y = y, 7 - x

    # Convert to index (zigzag pattern)
    if y % 2 == 0:
        return y * 8 + x
    else:
        return y * 8 + (7 - x)

def draw_wifi_icon(brightness_factor=1.0):
    """Draw a WiFi icon with pulsing animation"""
    # Clear screen
    pixels.fill((0, 0, 0))

    # Define WiFi symbol pattern (8x8 grid)
    # Using a simplified WiFi icon that's recognizable
    wifi_pattern = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 1, 1, 0, 0],
        [0, 1, 0, 0, 0, 0, 1, 0],
        [1, 0, 0, 1, 1, 0, 0, 1],
        [0, 0, 1, 0, 0, 1, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]

    # Calculate color based on brightness factor
    # Blue/cyan for WiFi, pulsing
    r = int(50 * brightness_factor)
    g = int(150 * brightness_factor)
    b = int(255 * brightness_factor)

    # Draw the pattern
    for y in range(8):
        for x in range(8):
            if wifi_pattern[y][x]:
                idx = xy_to_index(x, y)
                pixels[idx] = (r, g, b)

    pixels.show()

def main():
    """Main animation loop for WiFi setup mode"""
    print("WiFi Setup Mode - Connect to 'led-matrix' to configure")

    try:
        phase = 0
        while True:
            # Create pulsing effect using sine wave
            brightness = (math.sin(phase) + 1) / 2  # Range 0-1
            brightness = 0.3 + (brightness * 0.7)  # Range 0.3-1.0

            draw_wifi_icon(brightness)

            phase += 0.1
            time.sleep(0.05)

    except KeyboardInterrupt:
        pixels.fill((0, 0, 0))
        pixels.show()

if __name__ == "__main__":
    main()
