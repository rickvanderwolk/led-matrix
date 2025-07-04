#!/usr/bin/env python3

import os
import sys
import json
import board
import neopixel
import random
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from utils.matrix_config import load_config, apply_transform

config = load_config()

LED_COUNT = 64
PIN = board.D18
BRIGHTNESS = config.get("brightness", 0.2)

pixel_map = [apply_transform(i, config) for i in range(LED_COUNT)]

pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)
squares = [[0, 255, 0] for _ in range(LED_COUNT)]

def update_one(squares):
    idx = random.randint(0, LED_COUNT - 1)
    channel = random.randint(0, 2)
    direction = random.choice([-1, 1])

    value = squares[idx][channel]
    squares[idx][channel] = max(0, min(255, value + direction))

def render(squares):
    for i in range(LED_COUNT):
        pixels[pixel_map[i]] = tuple(squares[i])
    pixels.show()

try:
    while True:
        update_one(squares)
        render(squares)
        time.sleep(1 / 64)
except KeyboardInterrupt:
    pixels.fill((0, 0, 0))
    pixels.show()
