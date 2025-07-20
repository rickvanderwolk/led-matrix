#!/usr/bin/env python3

import os
import json
import board
import neopixel
import time
import threading
from flask import Flask, request, send_from_directory

CONFIG_PATH = os.environ.get("LEDMATRIX_CONFIG", "config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

LED_COUNT = 64
PIN = board.D18
BRIGHTNESS = config.get("brightness", 0.2)

pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)
app = Flask(__name__, static_folder='.')

WIDTH, HEIGHT = 8, 8
board_state = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
current_player = 1
winner = None
lock = threading.Lock()

def xy_to_index(x, y):
    if y % 2 == 0:
        return y * WIDTH + x
    else:
        return y * WIDTH + (WIDTH - 1 - x)

def draw_board():
    for y in range(HEIGHT):
        for x in range(WIDTH):
            v = board_state[y][x]
            if v == 0:
                color = (0, 0, 0)
            elif v == 1:
                color = (255, 0, 0)
            elif v == 2:
                color = (0, 0, 255)
            else:
                color = (255, 255, 0)
            pixels[xy_to_index(x, y)] = color
    pixels.show()

def drop_piece(col):
    global current_player, winner
    with lock:
        if winner:
            return
        for y in range(HEIGHT - 1, -1, -1):
            if board_state[y][col] == 0:
                board_state[y][col] = current_player
                if check_win(y, col):
                    winner = current_player
                    highlight_winner()
                else:
                    current_player = 2 if current_player == 1 else 1
                return
        # Kolom vol: doe niks
        return

def check_win(r, c):
    p = board_state[r][c]
    directions = [(1,0), (0,1), (1,1), (1,-1)]
    for dx, dy in directions:
        count = 1
        for s in [1, -1]:
            for i in range(1, 4):
                x = c + dx * i * s
                y = r + dy * i * s
                if 0 <= x < WIDTH and 0 <= y < HEIGHT and board_state[y][x] == p:
                    count += 1
                else:
                    break
        if count >= 4:
            return True
    return False

def highlight_winner():
    for _ in range(10):
        for i in range(LED_COUNT):
            pixels[i] = (255, 255, 0)
        pixels.show()
        time.sleep(0.1)
        for i in range(LED_COUNT):
            pixels[i] = (0, 0, 0)
        pixels.show()
        time.sleep(0.1)

@app.route('/')
def root():
    return send_from_directory('.', 'index.html')

@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    col = data.get('column')
    if isinstance(col, int) and 0 <= col < WIDTH:
        drop_piece(col)
    return ('', 204)

def loop():
    while True:
        draw_board()
        time.sleep(0.1)

if __name__ == '__main__':
    threading.Thread(target=loop, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
