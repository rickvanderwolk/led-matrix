#!/usr/bin/env python3
"""Simple test mode to verify visualizer works"""

import board
import neopixel
import time
import json
import os

CONFIG_PATH = os.environ.get("LEDMATRIX_CONFIG", "config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

LED_COUNT = 64
PIN = board.D18
BRIGHTNESS = config.get("brightness", 0.2)

print("Creating NeoPixel instance...", flush=True)
pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=True)

print("Testing visualizer with simple animations...", flush=True)

# Test 1: Fill red
print("Test 1: RED", flush=True)
pixels.fill((255, 0, 0))
time.sleep(1)

# Test 2: Fill green
print("Test 2: GREEN", flush=True)
pixels.fill((0, 255, 0))
time.sleep(1)

# Test 3: Fill blue
print("Test 3: BLUE", flush=True)
pixels.fill((0, 0, 255))
time.sleep(1)

# Test 4: Animation
print("Test 4: ANIMATION", flush=True)
for i in range(64):
    pixels[i] = (255, 255, 255)
    time.sleep(0.05)

print("Test 5: Clear", flush=True)
pixels.fill((0, 0, 0))

print("All tests complete! Visualizer is working.", flush=True)
print("Press Ctrl+C to exit...", flush=True)

# Keep running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
    pixels.fill((0, 0, 0))
