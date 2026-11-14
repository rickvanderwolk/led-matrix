#!/usr/bin/env python3

import random
from core import Matrix

matrix = Matrix()
matrix.fill((0, 255, 0))

for _ in matrix.frames(fps=64):
    idx = random.randint(0, matrix.count - 1)
    channel = random.randint(0, 2)
    direction = random.choice([-1, 1])

    color = list(matrix[idx])
    color[channel] = max(0, min(255, color[channel] + direction))
    matrix[idx] = tuple(color)
