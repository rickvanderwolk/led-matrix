#!/usr/bin/env python3

import os
import json
import board
import neopixel
import time
import random

CONFIG_PATH = os.environ.get("LEDMATRIX_CONFIG", "config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

mode_config = config.get("modes", {}).get("ant-party", {})

WIDTH = 8
HEIGHT = 8
LED_COUNT = WIDTH * HEIGHT
PIN = board.D18
BRIGHTNESS = config.get("brightness", 0.2)

pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)

class Ant:
    def __init__(self, x, y, dir, color):
        self.x = x
        self.y = y
        self.dir = dir
        self.color = color

def xy_to_index(x, y):
    return y * WIDTH + x

ants = []
ant_count = mode_config.get("ants", 4)
colors = mode_config.get("colors")

for i in range(ant_count):
    x = random.randint(0, WIDTH - 1)
    y = random.randint(0, HEIGHT - 1)
    dir = random.randint(0, 3)
    if colors and i < len(colors):
        color = tuple(colors[i])
    else:
        default_colors = [
            (255, 255, 0),
            (0, 255, 0),
            (255, 0, 255),
            (0, 255, 255),
            (255, 105, 180),
            (255, 165, 0),
            (0, 128, 255),
            (255, 0, 0),
            (255, 255, 255)
        ]
        color = default_colors[i % len(default_colors)]
    ants.append(Ant(x, y, dir, color))

grid = [{'state': 0, 'owner': None} for _ in range(LED_COUNT)]

def move_ant(ant_index):
    ant = ants[ant_index]
    idx = xy_to_index(ant.x, ant.y)
    cell = grid[idx]

    if cell['state'] == 0:
        ant.dir = (ant.dir + 1) % 4
        grid[idx] = {'state': 1, 'owner': ant_index}
    else:
        ant.dir = (ant.dir + 3) % 4
        grid[idx] = {'state': 0, 'owner': ant_index}

    if ant.dir == 0:
        ant.y -= 1
    elif ant.dir == 1:
        ant.x += 1
    elif ant.dir == 2:
        ant.y += 1
    elif ant.dir == 3:
        ant.x -= 1

    ant.x %= WIDTH
    ant.y %= HEIGHT

def render():
    for y in range(HEIGHT):
        for x in range(WIDTH):
            idx = xy_to_index(x, y)
            cell = grid[idx]
            if cell['state'] == 1 and cell['owner'] is not None:
                pixels[idx] = ants[cell['owner']].color
            else:
                pixels[idx] = (0, 0, 0)

    for ant in ants:
        idx = xy_to_index(ant.x, ant.y)
        pixels[idx] = ant.color

    pixels.show()

try:
    while True:
        for i in range(len(ants)):
            move_ant(i)
        render()
        time.sleep(0.1)
except KeyboardInterrupt:
    pixels.fill((0, 0, 0))
    pixels.show()
