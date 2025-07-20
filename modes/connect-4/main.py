#!/usr/bin/env python3
import board, neopixel, flask, json, os, threading, time

WIDTH, HEIGHT = 8, 8
SERPENTINE = False
FLIP_X = False
FLIP_Y = False

COLOR_P1 = (255, 0, 0)
COLOR_P2 = (0, 0, 255)
FLASH    = (255, 255, 255)

LED_COUNT = WIDTH * HEIGHT
PIN = board.D18
try:
    with open(os.environ.get("LEDMATRIX_CONFIG","config.json")) as f:
        BRIGHT = json.load(f).get("brightness", 0.2)
except: BRIGHT = 0.2

pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHT, auto_write=False)
app    = flask.Flask(__name__, static_folder='.')

board_state     = [[0]*WIDTH for _ in range(HEIGHT)]
current_player  = 1
winner          = None
lock            = threading.Lock()

def map_xy(x,y):
    if FLIP_X: x = WIDTH-1-x
    if FLIP_Y: y = HEIGHT-1-y
    if SERPENTINE and y%2: x = WIDTH-1-x
    return y*WIDTH + x

def draw(highlight=None):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            v = board_state[y][x]
            col = COLOR_P1 if v==1 else COLOR_P2 if v==2 else (0,0,0)
            if highlight and (y,x) in highlight: col = FLASH
            pixels[map_xy(x,y)] = col
    indicator = COLOR_P1 if current_player==1 else COLOR_P2
    pixels[map_xy(WIDTH-1,0)] = indicator
    pixels.show()

def four(r,c):
    p = board_state[r][c]
    for dx,dy in ((1,0),(0,1),(1,1),(1,-1)):
        pts=[(r,c)]
        for s in (1,-1):
            for i in range(1,4):
                x,y=c+dx*i*s, r+dy*i*s
                if 0<=x<WIDTH and 0<=y<HEIGHT and board_state[y][x]==p:
                    pts.append((y,x))
                else: break
        if len(pts)>=4: return pts[:4]
    return None

def blink(coords):
    for _ in range(10):
        draw(coords); time.sleep(0.25)
        draw();       time.sleep(0.25)

def reset():
    global board_state,current_player,winner
    board_state=[[0]*WIDTH for _ in range(HEIGHT)]
    current_player=1; winner=None; draw()

def drop(col):
    global current_player,winner
    if winner: return
    for y in range(HEIGHT-1,-1,-1):
        if board_state[y][col]==0:
            board_state[y][col]=current_player
            coords=four(y,col)
            if coords:
                winner=current_player
                draw(coords); blink(coords); reset()
            else:
                current_player = 3-current_player
                draw()
            return

@app.route('/')
def root(): return flask.send_from_directory('.', 'index.html')

@app.route('/move', methods=['POST'])
def move():
    col = flask.request.get_json().get('column')
    if isinstance(col,int) and 0<=col<WIDTH:
        with lock: drop(col)
    return ('',204)

if __name__=='__main__':
    draw()
    app.run(host='0.0.0.0', port=5000)
