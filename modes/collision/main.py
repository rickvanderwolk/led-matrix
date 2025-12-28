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

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def is_out_of_bounds(self):
        return self.x < 0 or self.x > 7 or self.y < 0 or self.y > 7

    def position(self):
        return (self.x, self.y)


def spawn_particle():
    """Spawn a new particle from an edge, moving inward."""
    direction = random.choice(list(DIRECTIONS.keys()))
    # 1/16 chance for white (cleaner)
    if random.random() < 1/16:
        color = WHITE
    else:
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
explosions = {}  # {(x, y): color} - permanent explosion remnants


def update():
    global particles

    # Chance to spawn new particles (can spawn 0, 1, or 2)
    if random.random() < 0.3:
        particles.append(spawn_particle())
    if random.random() < 0.1:
        particles.append(spawn_particle())

    # Move all particles
    for p in particles:
        p.move()

    # Remove out-of-bounds particles
    particles = [p for p in particles if not p.is_out_of_bounds()]

    # Check for collisions between particles
    positions = {}
    collided = set()

    for i, p in enumerate(particles):
        pos = p.position()
        if pos in positions:
            # Collision detected
            other_idx = positions[pos]
            other = particles[other_idx]
            # If either particle is white, remove everything at this position
            if p.color == WHITE or other.color == WHITE:
                if pos in explosions:
                    del explosions[pos]
            else:
                # Both colored: mix colors
                mixed = mix_colors(p.color, other.color)
                explosions[pos] = mixed
            collided.add(i)
            collided.add(other_idx)
        else:
            positions[pos] = i

    # Check collision with explosion remnants
    for i, p in enumerate(particles):
        pos = p.position()
        if pos in explosions and i not in collided:
            if p.color == WHITE:
                # White removes explosion remnant
                del explosions[pos]
            else:
                # Color mixes with remnant
                mixed = mix_colors(p.color, explosions[pos])
                explosions[pos] = mixed
            collided.add(i)

    # Remove collided particles
    particles = [p for i, p in enumerate(particles) if i not in collided]


def render():
    # Clear display
    pixels.fill((0, 0, 0))

    # Draw explosions (permanent remnants)
    for (x, y), color in explosions.items():
        if 0 <= x <= 7 and 0 <= y <= 7:
            pixels[xy_to_index(x, y)] = color

    # Draw particles
    for p in particles:
        if 0 <= p.x <= 7 and 0 <= p.y <= 7:
            idx = xy_to_index(p.x, p.y)
            # If there's already an explosion here, brighten it
            if (p.x, p.y) in explosions:
                pixels[idx] = p.color
            else:
                pixels[idx] = p.color

    pixels.show()


try:
    while True:
        update()
        render()
        time.sleep(0.15)
except KeyboardInterrupt:
    pixels.fill((0, 0, 0))
    pixels.show()
