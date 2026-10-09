#!/usr/bin/env python3

import random
import time
from core import Matrix

matrix = Matrix()

# Fight attempts per second. Before, speed depended on how fast the hardware happened to be.
ATTEMPTS_PER_SECOND = matrix.settings.get("speed", 200)
FPS = 50

CONTRASTING_COLOR_PAIRS = [
    ((255, 0, 0), (0, 0, 255)),
    ((255, 0, 0), (255, 255, 0)),
    ((255, 0, 0), (0, 255, 0)),
    ((0, 0, 255), (255, 255, 0)),
    ((255, 0, 255), (0, 255, 255)),
    ((255, 165, 0), (0, 128, 255)),
    ((128, 0, 128), (0, 255, 128)),
    ((57, 255, 20), (255, 20, 147)),
    ((0, 255, 255), (255, 105, 180)),
    ((255, 192, 203), (0, 0, 255)),
    ((255, 255, 224), (255, 69, 0)),
    ((139, 69, 19), (173, 255, 47)),
    ((70, 130, 180), (255, 215, 0)),
    ((0, 0, 0), (255, 255, 255)),
    ((50, 50, 50), (255, 0, 255)),
]

last_color_pair_index = -1


def pick_colors():
    global last_color_pair_index
    new_index = last_color_pair_index
    while new_index == last_color_pair_index:
        new_index = random.randint(0, len(CONTRASTING_COLOR_PAIRS) - 1)
    last_color_pair_index = new_index
    return CONTRASTING_COLOR_PAIRS[new_index]


def attempt(owner, counts, exponent):
    """One random attack: a pixel from one side tries to take over a pixel bordering its territory."""
    x, y = random.randint(0, 7), random.randint(0, 7)
    target_x = random.randint(0, 7)
    attacker = 0 if x < 4 else 1
    target = y * 8 + target_x

    if owner[target] == attacker:
        return None
    if not any(owner[ny * 8 + nx] == attacker for nx, ny in matrix.neighbors(target_x, y)):
        return None

    # The bigger side wins more often
    chance = (counts[attacker] / matrix.count) ** exponent
    if random.random() < chance:
        owner[target] = attacker
        counts[attacker] += 1
        counts[1 - attacker] -= 1
        return target
    return None


def fight():
    colors = pick_colors()
    owner = [0 if i % 8 < 4 else 1 for i in range(matrix.count)]
    counts = [owner.count(0), owner.count(1)]
    for i, side in enumerate(owner):
        matrix[i] = colors[side]
    matrix.show()

    exponent = random.uniform(0.1, 0.3)
    attempts_per_frame = max(1, round(ATTEMPTS_PER_SECOND / FPS))

    for _ in matrix.frames(fps=FPS):
        for _ in range(attempts_per_frame):
            target = attempt(owner, counts, exponent)
            if target is not None:
                matrix[target] = colors[owner[target]]
            if matrix.count in counts:
                matrix.show()
                return


while True:
    fight()
    time.sleep(2)
