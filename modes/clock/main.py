#!/usr/bin/env python3
import os,json,time,board,neopixel,colorsys,random
from datetime import datetime

CONFIG_PATH=os.environ.get("LEDMATRIX_CONFIG","config.json")
with open(CONFIG_PATH) as f:
    config=json.load(f)

PIN=board.D18
WIDTH=int(config.get("width",8))
HEIGHT=int(config.get("height",8))
LED_COUNT=WIDTH*HEIGHT
BRIGHTNESS=float(config.get("brightness",0.28))
SPEED=float(config.get("speed",0.05))
FLIP_X=bool(config.get("flip_x",False))
FLIP_Y=bool(config.get("flip_y",False))
SERPENTINE=bool(config.get("serpentine",False))
BG=(0,0,0)

pixels=neopixel.NeoPixel(PIN,LED_COUNT,brightness=BRIGHTNESS,auto_write=False)

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

def map_xy(x,y):
    if FLIP_X: x=WIDTH-1-x
    if FLIP_Y: y=HEIGHT-1-y
    if SERPENTINE and y%2: x=WIDTH-1-x
    return y*WIDTH+x

def digit_mask(hh):
    a=int(hh[0]); b=int(hh[1])
    m=set()
    for r in range(6):
        row=font3x6[a][r]
        for c in range(3):
            if (row>>(2-c))&1: m.add((1+c,1+r))
        row=font3x6[b][r]
        for c in range(3):
            if (row>>(2-c))&1: m.add((4+c,1+r))
    return m

def gradient_colors(n,h1,h2,s=1.0,v=1.0):
    cols=[]
    for i in range(n):
        t=i/max(1,n-1)
        h=(h1+(h2-h1)*t)%360
        r,g,b=colorsys.hsv_to_rgb(h/360.0,s,v)
        cols.append((int(r*255),int(g*255),int(b*255)))
    return cols

def bottom_up_order():
    pts=[]
    for y in range(HEIGHT-1,-1,-1):
        for x in range(WIDTH):
            pts.append((x,y))
    return pts

def fill_frame_bottom(mask,order,progress,cols):
    background=[p for p in order if p not in mask]
    lit_count=int(progress*len(background))
    frame=[[BG for _ in range(WIDTH)] for __ in range(HEIGHT)]
    for i,p in enumerate(background[:lit_count]):
        x,y=p
        frame[y][x]=cols[min(i,len(cols)-1)]
    for (x,y) in mask:
        frame[y][x]=BG
    return frame

def draw(frame):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            pixels[map_xy(x,y)]=frame[y][x]
    pixels.show()

def gravity_fall(frame,steps=30,delay=0.03):
    for _ in range(steps):
        moved=False
        for y in range(HEIGHT-2,-1,-1):
            for x in range(WIDTH):
                c=frame[y][x]
                if c!=BG and frame[y+1][x]==BG:
                    frame[y+1][x]=c
                    frame[y][x]=BG
                    moved=True
        draw(frame)
        time.sleep(delay)
        if not moved: break

try:
    order=bottom_up_order()
    last_hour=None
    h1=random.uniform(0,360)
    h2=(h1+random.uniform(120,220))%360
    cols=gradient_colors(LED_COUNT,h1,h2,1.0,1.0)
    while True:
        now=datetime.now()
        hh=now.strftime("%H")
        mm=int(now.strftime("%M"))
        ss=int(now.strftime("%S"))
        if last_hour is None:
            last_hour=int(hh)
        if int(hh)!=last_hour and mm==0 and ss==0:
            m_prev=digit_mask(f"{last_hour:02d}")
            frame=fill_frame_bottom(m_prev,order,1.0,cols)
            gravity_fall(frame,steps=40,delay=max(0.01,SPEED*0.6))
            frame=[[BG for _ in range(WIDTH)] for __ in range(HEIGHT)]
            draw(frame)
            last_hour=int(hh)
            h1=(h1+random.uniform(90,180))%360
            h2=(h1+random.uniform(120,220))%360
            cols=gradient_colors(LED_COUNT,h1,h2,1.0,1.0)
        mask=digit_mask(hh)
        progress=(mm*60+ss)/3600.0
        frame=fill_frame_bottom(mask,order,progress,cols)
        draw(frame)
        time.sleep(SPEED)
except KeyboardInterrupt:
    pixels.fill((0,0,0))
    pixels.show()
