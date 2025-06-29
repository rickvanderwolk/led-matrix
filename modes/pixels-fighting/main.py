#!/usr/bin/env python3

import board
import neopixel
import random
import time
import math

LED_COUNT = 64
PIN = board.D18
BRIGHTNESS = 0.2

pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS)

last_color_pair_index = -1

def initialize_battlefield():
    global last_color_pair_index

    contrasting_color_pairs = [
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

    new_index = last_color_pair_index
    while new_index == last_color_pair_index:
        new_index = random.randint(0, len(contrasting_color_pairs) - 1)

    last_color_pair_index = new_index
    color1, color2 = contrasting_color_pairs[new_index]

    for i in range(LED_COUNT):
        if i % 8 < 4:
            pixels[i] = color1
        else:
            pixels[i] = color2

    pixels.show()
    return color1, color2

def colors_are_similar(color1, color2, tolerance=10):
    return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(color1, color2))

def count_color(target_color):
    count = 0
    for i in range(LED_COUNT):
        if colors_are_similar(pixels[i], target_color):
            count += 1
    return count

def is_neighbor_same_color(x, y, color):
    direct_neighbors = [
        (x, y - 1),
        (x - 1, y),
        (x + 1, y),
        (x, y + 1)
    ]

    for nx, ny in direct_neighbors:
        if 0 <= nx < 8 and 0 <= ny < 8:
            neighbor_index = ny * 8 + nx
            if colors_are_similar(pixels[neighbor_index], color, tolerance=10):
                return True
    return False

def fight(color1, color2):
    fight = True
    exponent = random.uniform(0.1, 0.3)

    while fight:
        x, y = random.randint(0, 7), random.randint(0, 7)
        opponent_x = random.randint(0, 7)
        opponent_index = y * 8 + opponent_x

        attacking_color = color1 if x < 4 else color2
        defending_color = color2 if x < 4 else color1

        if is_neighbor_same_color(opponent_x, y, attacking_color) and not colors_are_similar(pixels[opponent_index], attacking_color):
            color1_count = count_color(color1)
            color2_count = count_color(color2)
            total_count = color1_count + color2_count

            if total_count > 0:
                chance_color1 = (color1_count / total_count) ** exponent
                chance_color2 = (color2_count / total_count) ** exponent
            else:
                chance_color1 = chance_color2 = 0.5

            if attacking_color == color1:
                winner_color = color1 if random.random() < chance_color1 else defending_color
            else:
                winner_color = color2 if random.random() < chance_color2 else defending_color

            pixels[opponent_index] = winner_color

        pixels.show()

        if count_color(color1) > LED_COUNT - 1:
            pixels.fill(color1)
            fight = False
            time.sleep(1)
            break
        elif count_color(color2) > LED_COUNT - 1:
            pixels.fill(color2)
            fight = False
            time.sleep(1)
            break

try:
    while True:
        color1, color2 = initialize_battlefield()
        fight(color1, color2)
        time.sleep(1)
except KeyboardInterrupt:
    pixels.fill((0, 0, 0))
    pixels.show()
