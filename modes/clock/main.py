#!/usr/bin/env python3
import os,json,time,board,neopixel,random
from datetime import datetime

CONFIG_PATH=os.environ.get("LEDMATRIX_CONFIG","config.json")
with open(CONFIG_PATH) as f:
    config=json.load(f)

PIN=board.D18
WIDTH=int(config.get("width",8))
HEIGHT=int(config.get("height",8))
LED_COUNT=WIDTH*HEIGHT
BRIGHTNESS=config.get("brightness",0.2)
SPEED=config.get("speed",0.04)
FLIP_X=bool(config.get("flip_x",False))
FLIP_Y=bool(config.get("flip_y",False))
SERPENTINE=bool(config.get("serpentine",False))
BG=(0,0,0)

PALETTE=[(255,64,64),(64,160,255),(64,255,128),(255,200,64),(220,64,255),(255,96,192),(96,255,224)]

pixels=neopixel.NeoPixel(PIN,LED_COUNT,brightness=BRIGHTNESS,auto_write=False)

def map_xy(x,y):
    if FLIP_X: x=WIDTH-1-x
    if FLIP_Y: y=HEIGHT-1-y
    if SERPENTINE and y%2: x=WIDTH-1-x
    return y*WIDTH+x

glyph={
    0:[0xF,0x9,0x9,0xF],
    1:[0x6,0x2,0x2,0x7],
    2:[0xF,0x1,0xF,0x8],
    3:[0xF,0x1,0xF,0x1],
    4:[0x9,0x9,0xF,0x1],
    5:[0xF,0x8,0xF,0x1],
    6:[0xF,0x8,0xF,0x9],
    7:[0xF,0x1,0x2,0x2],
    8:[0xF,0x9,0xF,0x9],
    9:[0xF,0x9,0xF,0x1]
}

def targets_for_digit(d,x0,y0,color):
    t=set(); c={}
    rows=glyph[int(d)]
    for r in range(4):
        row=rows[r]
        for cx in range(4):
            if (row>>(3-cx))&1:
                p=(x0+cx,y0+r)
                t.add(p); c[p]=color
    return t,c

class QuadTetris:
    def __init__(self,x0,y0,x1,y1,color):
        self.x0=x0; self.y0=y0; self.x1=x1; self.y1=y1; self.color=color
        self.targets=set(); self.colors={}
        self.settled=set(); self.active=[]; self.claimed=set()
        self.flash=0; self.next_t=None; self.next_c=None; self.spawn_tick=0
    def inside(self,x,y):
        return self.x0<=x<self.x1 and self.y0<=y<self.y1
    def set_color(self,color):
        self.color=color
    def set_digit(self,d):
        t,c=targets_for_digit(d,self.x0,self.y0,self.color)
        if self.settled or self.active:
            self.next_t=t; self.next_c=c; self.flash=6
        else:
            self.targets=t; self.colors=c; self.settled=set(); self.active=[]; self.claimed=set()
    def choose_fillable(self):
        cand=list(self.targets-self.claimed)
        random.shuffle(cand)
        for (x,y) in sorted(cand,key=lambda p:(-p[1],p[0])):
            below=(x,y+1)
            if y==self.y1-1 or (below not in self.targets) or (below in self.settled):
                return (x,y)
        return None
    def spawn(self):
        if not self.targets: return
        if self.spawn_tick%2!=0: return
        t=self.choose_fillable()
        if not t: return
        tx,ty=t
        sx=random.randint(self.x0,self.x1-1)
        sy=self.y0-1-random.randint(0,3)
        self.active.append([sx,sy,tx,ty,self.colors[(tx,ty)]])
        self.claimed.add((tx,ty))
    def step(self):
        if self.flash>0:
            self.flash-=1
            if self.flash==1:
                self.targets=self.next_t or set()
                self.colors=self.next_c or {}
                self.settled=set(); self.active=[]; self.claimed=set()
                self.next_t=None; self.next_c=None
            return
        self.spawn()
        nxt=[]
        for sx,sy,tx,ty,col in self.active:
            if sx<tx and random.random()<0.5: sx+=1
            elif sx>tx and random.random()<0.5: sx-=1
            if sy<ty: sy+=1
            if sy>=ty and sx==tx:
                self.settled.add((tx,ty))
            else:
                if sy>ty: sy=ty
                nxt.append([sx,sy,tx,ty,col])
        self.active=nxt
        self.spawn_tick+=1
    def render(self,frame):
        if self.flash and self.flash%2==0:
            for y in range(self.y0,self.y1):
                for x in range(self.x0,self.x1):
                    frame[y][x]=(255,255,255)
            return
        for (x,y) in self.settled:
            frame[y][x]=self.colors[(x,y)]
        for sx,sy,tx,ty,col in self.active:
            if self.inside(sx,sy):
                frame[sy][sx]=col

def draw(frame):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            pixels[map_xy(x,y)]=frame[y][x]
    pixels.show()

def blank():
    pixels.fill(BG); pixels.show()

def now_digits():
    n=datetime.now()
    hh=n.strftime("%H")
    mm=n.strftime("%M")
    return int(hh[0]),int(hh[1]),int(mm[0]),int(mm[1])

def pick_pair(exclude=None):
    choices=PALETTE[:]
    if exclude and exclude in choices: choices.remove(exclude)
    a=random.choice(choices)
    choices=[c for c in PALETTE if c!=a]
    b=random.choice(choices)
    return a,b

try:
    H1=QuadTetris(0,0,4,4,PALETTE[1])
    H2=QuadTetris(0,4,4,8,PALETTE[1])
    M1=QuadTetris(4,0,8,4,PALETTE[2])
    M2=QuadTetris(4,4,8,8,PALETTE[2])
    ph1=ph2=pm1=pm2=None
    left_color,right_color=H1.color,M1.color
    while True:
        h1,h2,m1,m2=now_digits()
        hour_changed=(h1,h2)!=(ph1,ph2)
        minute_changed=(m1,m2)!=(pm1,pm2)
        if hour_changed:
            left_color,_=pick_pair(exclude=right_color)
            H1.set_color(left_color); H2.set_color(left_color)
            H1.set_digit(h1); H2.set_digit(h2)
            ph1,ph2=h1,h2
        if minute_changed:
            _,right_color=pick_pair(exclude=left_color)
            M1.set_color(right_color); M2.set_color(right_color)
            M1.set_digit(m1); M2.set_digit(m2)
            pm1,pm2=m1,m2
        H1.step(); H2.step(); M1.step(); M2.step()
        frame=[[BG]*WIDTH for _ in range(HEIGHT)]
        H1.render(frame); H2.render(frame); M1.render(frame); M2.render(frame)
        draw(frame)
        time.sleep(SPEED)
except KeyboardInterrupt:
    blank()
