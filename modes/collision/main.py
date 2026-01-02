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

LED_COUNT = 64
PIN = board.D18
BRIGHTNESS = config.get("brightness", 0.2)
pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)

# 16 vibrant colors for particles
COLORS = [
    (255, 0, 0),      # Red
    (0, 255, 0),      # Green
    (0, 0, 255),      # Blue
    (255, 255, 0),    # Yellow
    (255, 0, 255),    # Magenta
    (0, 255, 255),    # Cyan
    (255, 128, 0),    # Orange
    (128, 0, 255),    # Purple
    (255, 64, 128),   # Pink
    (0, 255, 128),    # Spring green
    (128, 255, 0),    # Lime
    (0, 128, 255),    # Sky blue
    (255, 128, 128),  # Light red
    (128, 255, 128),  # Light green
    (128, 128, 255),  # Light blue
    (255, 255, 128),  # Light yellow
]

# Special color: white clears explosion remnants
WHITE = (255, 255, 255)

# Directions: (dx, dy)
DIRECTIONS = {
    'right': (1, 0),
    'left': (-1, 0),
    'down': (0, 1),
    'up': (0, -1),
}


def xy_to_index(x, y):
    return y * 8 + x


def mix_colors(color1, color2):
    """Mix two colors by averaging their RGB values."""
    return (
        (color1[0] + color2[0]) // 2,
        (color1[1] + color2[1]) // 2,
        (color1[2] + color2[2]) // 2,
    )


class Particle:
    def __init__(self, x, y, direction, color):
        self.x = x
        self.y = y
        self.direction = direction
        self.color = color
        self.dx, self.dy = DIRECTIONS[direction]
        self.trail = [(x, y)]  # Track all positions visited

    def move(self):
        self.x += self.dx
        self.y += self.dy
        if not self.is_out_of_bounds():
            self.trail.append((self.x, self.y))

    def is_out_of_bounds(self):
        return self.x < 0 or self.x > 7 or self.y < 0 or self.y > 7

    def position(self):
        return (self.x, self.y)


def spawn_particle():
    """Spawn a new particle from an edge, moving inward."""
    direction = random.choice(list(DIRECTIONS.keys()))
    color = random.choice(COLORS)

    if direction == 'right':
        x, y = 0, random.randint(0, 7)
    elif direction == 'left':
        x, y = 7, random.randint(0, 7)
    elif direction == 'down':
        x, y = random.randint(0, 7), 0
    elif direction == 'up':
        x, y = random.randint(0, 7), 7

    return Particle(x, y, direction, color)


# State
particles = []
trails = {}  # {(x, y): color} - color trails that fade over time
flash_positions = set()  # positions that flash bright this frame
FADE_AMOUNT = 3  # How much RGB values decrease per frame
MIN_BRIGHTNESS = 10  # Trails below this total brightness disappear


def update():
    global particles, flash_positions

    flash_positions = set()

    # Build position map for collision detection
    positions_before = {}
    for i, p in enumerate(particles):
        positions_before[i] = p.position()

    # Move all particles
    for p in particles:
        p.move()

    # Every particle leaves a trail at its current position
    for i, p in enumerate(particles):
        if p.is_out_of_bounds():
            continue

        pos = p.position()

        # Mix with existing trail or create new
        if pos in trails:
            trails[pos] = mix_colors(p.color, trails[pos])
            flash_positions.add(pos)  # Flash on overlap
        else:
            trails[pos] = p.color

    # Remove out-of-bounds particles
    particles = [p for p in particles if not p.is_out_of_bounds()]

    # Fade all trails
    to_remove = []
    for pos, color in trails.items():
        faded = (
            max(0, color[0] - FADE_AMOUNT),
            max(0, color[1] - FADE_AMOUNT),
            max(0, color[2] - FADE_AMOUNT),
        )
        if sum(faded) < MIN_BRIGHTNESS:
            to_remove.append(pos)
        else:
            trails[pos] = faded
    for pos in to_remove:
        del trails[pos]

    # Spawn new particles
    spawn_count = random.choices([0, 1, 2, 3], weights=[20, 40, 30, 10])[0]
    for _ in range(spawn_count):
        particles.append(spawn_particle())


def brighten(color, factor=1.5):
    """Make a color brighter for flash effect."""
    return (
        min(255, int(color[0] * factor)),
        min(255, int(color[1] * factor)),
        min(255, int(color[2] * factor)),
    )


def render():
    # Clear display
    pixels.fill((0, 0, 0))

    # Draw trails (permanent color paths)
    for (x, y), color in trails.items():
        if 0 <= x <= 7 and 0 <= y <= 7:
            idx = xy_to_index(x, y)
            # Flash bright where particles crossed
            if (x, y) in flash_positions:
                pixels[idx] = brighten(color, 2.0)
            else:
                pixels[idx] = color

    # Draw active particles (brightest)
    for p in particles:
        if 0 <= p.x <= 7 and 0 <= p.y <= 7:
            idx = xy_to_index(p.x, p.y)
            pixels[idx] = brighten(p.color, 1.5)

    pixels.show()


try:
    while True:
        update()
        render()
        time.sleep(0.15)
except KeyboardInterrupt:
    pixels.fill((0, 0, 0))
    pixels.show()
