#!/usr/bin/env python3
import os,json,time,board,neopixel
from datetime import datetime

CONFIG_PATH=os.environ.get("LEDMATRIX_CONFIG","config.json")
with open(CONFIG_PATH) as f:
    config=json.load(f)

PIN=board.D18
WIDTH=int(config.get("width",8))
HEIGHT=int(config.get("height",8))
LED_COUNT=WIDTH*HEIGHT
BRIGHTNESS=float(config.get("brightness",0.25))
SPEED=float(config.get("speed",0.08))
FLIP_X=bool(config.get("flip_x",False))
FLIP_Y=bool(config.get("flip_y",False))
SERPENTINE=bool(config.get("serpentine",False))
FG=tuple(config.get("fg_color",(255,255,255)))
BORDER_EMPTY=tuple(config.get("border_empty",(40,40,40)))
BORDER_FILL=tuple(config.get("border_fill",(0,200,255)))
BG=(0,0,0)

pixels=neopixel.NeoPixel(PIN,LED_COUNT,brightness=BRIGHTNESS,auto_write=False)

def map_xy(x,y):
    if FLIP_X: x=WIDTH-1-x
    if FLIP_Y: y=HEIGHT-1-y
    if SERPENTINE and y%2: x=WIDTH-1-x
    return y*WIDTH+x

font3x6={
    0:[0b111,0b101,0b101,0b101,0b101,0b111],
    1:[0b010,0b110,0b010,0b010,0b010,0b111],
    2:[0b111,0b001,0b111,0b100,0b100,0b111],
    3:[0b111,0b001,0b111,0b001,0b001,0b111],
    4:[0b101,0b101,0b111,0b001,0b001,0b001],
    5:[0b111,0b100,0b111,0b001,0b001,0b111],
    6:[0b111,0b100,0b111,0b101,0b101,0b111],
    7:[0b111,0b001,0b010,0b010,0b010,0b010],
    8:[0b111,0b101,0b111,0b101,0b101,0b111],
    9:[0b111,0b101,0b111,0b001,0b001,0b111]
}

def border_path():
    pts=[]
    for x in range(0,8): pts.append((x,0))
    for y in range(1,7): pts.append((7,y))
    for x in range(7,-1,-1): pts.append((x,7))
    for y in range(6,0,-1): pts.append((0,y))
    return pts

BORDER_POINTS=border_path()
PERIM=len(BORDER_POINTS)

def draw_border(progress):
    filled=int(PERIM*progress+0.5)
    for i,(x,y) in enumerate(BORDER_POINTS):
        pixels[map_xy(x,y)]=BORDER_FILL if i<filled else BORDER_EMPTY

def draw_digit_3x6(d,x0,y0,color):
    rows=font3x6[int(d)]
    for r in range(6):
        row=rows[r]
        for c in range(3):
            if (row>>(2-c))&1:
                pixels[map_xy(x0+c,y0+r)]=color

def hour_digits_and_min_progress():
    n=datetime.now()
    hh=n.strftime("%H")
    m=int(n.strftime("%M"))
    prog=m/60.0
    return int(hh[0]),int(hh[1]),prog

try:
    last_tuple=None
    while True:
        h1,h2,prog=hour_digits_and_min_progress()
        key=(h1,h2,int(prog*60))
        if key!=last_tuple:
            pixels.fill(BG)
            draw_border(prog)
            draw_digit_3x6(h1,1,1,FG)
            draw_digit_3x6(h2,4,1,FG)
            pixels.show()
            last_tuple=key
        time.sleep(SPEED)
except KeyboardInterrupt:
    pixels.fill((0,0,0))
    pixels.show()
