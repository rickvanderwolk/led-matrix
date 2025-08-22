#!/usr/bin/env python3

import os
import json
import board
import neopixel
import time
from datetime import datetime

CONFIG_PATH = os.environ.get("LEDMATRIX_CONFIG", "config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

LED_COUNT = 64
PIN = board.D18
BRIGHTNESS = config.get("brightness", 0.2)
SPEED = config.get("speed", 0.03)
PALETTE = [
    (255, 64, 64),
    (64, 160, 255),
    (64, 255, 128),
    (255, 200, 64),
    (220, 64, 255)
]

pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)

GLYPH_W = 5
GLYPH_H = 8

font = {
    "0":[0x0E,0x11,0x13,0x15,0x19,0x11,0x11,0x0E],
    "1":[0x04,0x0C,0x04,0x04,0x04,0x04,0x04,0x0E],
    "2":[0x0E,0x11,0x10,0x08,0x04,0x02,0x11,0x1F],
    "3":[0x1E,0x01,0x01,0x0E,0x01,0x01,0x01,0x1E],
    "4":[0x10,0x18,0x14,0x12,0x1F,0x10,0x10,0x10],
    "5":[0x1F,0x01,0x0F,0x10,0x10,0x10,0x11,0x0E],
    "6":[0x0E,0x10,0x10,0x1E,0x11,0x11,0x11,0x0E],
    "7":[0x1F,0x11,0x08,0x08,0x04,0x04,0x02,0x02],
    "8":[0x0E,0x11,0x11,0x0E,0x11,0x11,0x11,0x0E],
    "9":[0x0E,0x11,0x11,0x0F,0x01,0x01,0x01,0x0E],
    ":":[0x00,0x04,0x00,0x00,0x00,0x04,0x00,0x00]
}

def idx(x,y):
    if y % 2 == 0:
        return y*8 + x
    else:
        return y*8 + (7-x)

def clear():
    pixels.fill((0,0,0))

def draw_column(x, col_bits, color):
    for y in range(8):
        bit = (col_bits >> (7-y)) & 1
        pixels[idx(x,y)] = color if bit else (0,0,0)

def build_text_columns(text, spacing=1):
    cols = []
    for i,ch in enumerate(text):
        glyph = font.get(ch, [0]*GLYPH_H)
        for cx in range(GLYPH_W):
            col = 0
            for r in range(GLYPH_H):
                if (glyph[r] >> (GLYPH_W-1-cx)) & 1:
                    col |= (1 << (7-r))
            cols.append((col,i))
        for _ in range(spacing):
            cols.append((0,i))
    return cols

def time_string():
    now = datetime.now()
    return now.strftime("%H:%M"), now.second % 2 == 0

def color_for_index(i):
    return PALETTE[i % len(PALETTE)]

try:
    offset = 0
    cached = ""
    columns = []
    last_rebuild = 0
    while True:
        t, tick = time_string()
        if t != cached or time.time() - last_rebuild > 1.0:
            cached = t
            last_rebuild = time.time()
            msg = t if tick else t.replace(":", " ")
            columns = build_text_columns(msg, spacing=1)
            offset = 0 if offset >= len(columns) else offset
        clear()
        for sx in range(8):
            src = (offset + sx) % len(columns)
            col_bits, char_idx = columns[src]
            draw_column(sx, col_bits, color_for_index(char_idx))
        pixels.show()
        time.sleep(SPEED)
        offset = (offset + 1) % len(columns)
except KeyboardInterrupt:
    pixels.fill((0,0,0))
    pixels.show()
