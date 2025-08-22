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
BRIGHTNESS=config.get("brightness",0.25)
SPEED=config.get("speed",0.05)
FLIP_X=bool(config.get("flip_x",False))
FLIP_Y=bool(config.get("flip_y",False))
SERPENTINE=bool(config.get("serpentine",True))
BG=(0,0,0)

PALETTE=[(255,64,64),(64,160,255),(64,255,128),(255,200,64),(220,64,255),(255,96,192),(96,255,224),(255,128,64),(64,255,200)]

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

def digit_cells(d,x0,y0):
    s=set()
    rows=glyph[int(d)]
    for r in range(4):
        row=rows[r]
        for cx in range(4):
            if (row>>(3-cx))&1:
                s.add((x0+cx,y0+r))
    return s

tetromino_defs={
    'I':[[(0,0),(0,1),(0,2),(0,3)],[(0,0),(1,0),(2,0),(3,0)]],
    'O':[[(0,0),(1,0),(0,1),(1,1)]],
    'T':[[(0,0),(1,0),(2,0),(1,1)],[(1,0),(0,1),(1,1),(1,2)],[(1,0),(0,1),(1,1),(2,1)],[(0,0),(0,1),(1,1),(0,2)]],
    'L':[[(0,0),(0,1),(0,2),(1,2)],[(0,0),(1,0),(2,0),(0,1)],[(0,0),(1,0),(1,1),(1,2)],[(2,0),(0,1),(1,1),(2,1)]],
    'J':[[(1,0),(1,1),(1,2),(0,2)],[(0,0),(0,1),(1,1),(2,1)],[(0,0),(1,0),(0,1),(0,2)],[(0,0),(1,0),(2,0),(2,1)]],
    'S':[[(1,0),(2,0),(0,1),(1,1)],[(0,0),(0,1),(1,1),(1,2)]],
    'Z':[[(0,0),(1,0),(1,1),(2,1)],[(1,0),(0,1),(1,1),(0,2)]],
}

def translate(shape,dx,dy):
    return [(x+dx,y+dy) for (x,y) in shape]

def in_bounds(shape,x0,y0,x1,y1):
    for x,y in shape:
        if not(x0<=x<x1 and y0<=y<y1): return False
    return True

def neighbors4(x,y):
    return [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]

def thicken_to_multiple_of_4(target,x0,y0,x1,y1):
    t=set(target)
    while len(t)%4!=0:
        border=set()
        for (x,y) in t:
            for nx,ny in neighbors4(x,y):
                if x0<=nx<x1 and y0<=ny<y1 and (nx,ny) not in t:
                    border.add((nx,ny))
        if not border: break
        best=min(border,key=lambda p:sum((abs(p[0]-x)+abs(p[1]-y)) for (x,y) in t))
        t.add(best)
    return t

def exact_cover_tetromino(target,x0,y0,x1,y1):
    cells=set(target)
    placements=[]
    for name,rots in tetromino_defs.items():
        for r in rots:
            w=max(x for x,_ in r)+1
            h=max(y for _,y in r)+1
            for dx in range(x0,x1-w+1):
                for dy in range(y0,y1-h+1):
                    shape=tuple(translate(r,dx,dy))
                    if all(p in cells for p in shape):
                        placements.append((shape,name))
    cell_to_placements={}
    for i,(shape,_) in enumerate(placements):
        for p in shape:
            if p in cells:
                cell_to_placements.setdefault(p,[]).append(i)
    used=[False]*len(placements)
    solution=[]
    def backtrack(rem):
        if not rem: return True
        p=min(rem,key=lambda c:len([i for i in cell_to_placements.get(c,[]) if not used[i]]) or 9999)
        options=[i for i in cell_to_placements.get(p,[]) if not used[i]]
        random.shuffle(options)
        for i in options:
            shape,_=placements[i]
            if any(q not in rem for q in shape): continue
            used[i]=True
            solution.append(i)
            newrem=rem-set(shape)
            if backtrack(newrem): return True
            solution.pop()
            used[i]=False
        return False
    ok=backtrack(set(cells))
    if not ok: return None
    return [(placements[i][0],placements[i][1]) for i in solution]

def color_pair():
    a=random.choice(PALETTE)
    b=random.choice([c for c in PALETTE if c!=a])
    return a,b

class HalfPlayfield:
    def __init__(self,x0,y0,x1,y1):
        self.x0=x0; self.y0=y0; self.x1=x1; self.y1=y1
        self.pieces=[]
        self.active=[]
        self.colors=[]
        self.done_flag=True
    def build_from_digits(self,d_top,d_bot,base_colors):
        target=digit_cells(d_top,self.x0,self.y0) | digit_cells(d_bot,self.x0,self.y0+4)
        target=thicken_to_multiple_of_4(target,self.x0,self.y0,self.x1,self.y1)
        tiling=exact_cover_tetromino(target,self.x0,self.y0,self.x1,self.y1)
        if tiling is None:
            fill=list(target)
            tiling=[]
            while fill:
                block=fill[:4]; fill=fill[4:]
                tiling.append((tuple(block),'X'))
        cols=[]
        for i,_ in enumerate(tiling):
            if i%2==0: cols.append(base_colors[0])
            else: cols.append(base_colors[1])
        self.pieces=[(list(shape),name) for (shape,name) in tiling]
        self.colors=cols
        self.active=[]
        for i,(shape,name) in enumerate(self.pieces):
            tops=min(y for _,y in shape)
            spawn=[(x, self.y0-1-random.randint(0,3) - random.randint(0,2)) for (x,_) in shape]
            self.active.append({'idx':i,'pos':spawn,'target':shape,'name':name,'color':self.colors[i]})
        self.done_flag=False
    def step(self):
        if self.done_flag: return
        moving=False
        for a in self.active:
            newpos=[]
            reached=True
            for (x,y),(tx,ty) in zip(a['pos'],a['target']):
                nx=x; ny=y
                if nx<tx and random.random()<0.5: nx+=1
                elif nx>tx and random.random()<0.5: nx-=1
                if ny<ty: ny+=1
                newpos.append((nx,ny))
                if nx!=tx or ny!=ty: reached=False
            a['pos']=newpos
            if not reached: moving=True
        if not moving: self.done_flag=True
    def render(self,frame):
        for a in self.active:
            for (x,y) in a['pos']:
                if self.x0<=x<self.x1 and self.y0<=y<self.y1 and 0<=y<HEIGHT:
                    frame[y][x]=a['color']
    def done(self):
        return self.done_flag

def draw(frame):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            pixels[map_xy(x,y)]=frame[y][x]
    pixels.show()

def now_digits():
    n=datetime.now()
    hh=n.strftime("%H")
    mm=n.strftime("%M")
    return int(hh[0]),int(hh[1]),int(mm[0]),int(mm[1])

try:
    left=HalfPlayfield(0,0,4,8)
    right=HalfPlayfield(4,0,8,8)
    ph1=ph2=pm1=pm2=None
    lc1,lc2=color_pair()
    rc1,rc2=color_pair()
    if rc1==lc1 or rc1==lc2: rc1=random.choice([c for c in PALETTE if c not in (lc1,lc2)])
    if rc2==lc1 or rc2==lc2 or rc2==rc1: rc2=random.choice([c for c in PALETTE if c not in (lc1,lc2,rc1)])
    while True:
        h1,h2,m1,m2=now_digits()
        hour_changed=(h1,h2)!=(ph1,ph2)
        minute_changed=(m1,m2)!=(pm1,pm2)
        if ph1 is None:
            left.build_from_digits(h1,h2,(lc1,lc2))
            right.build_from_digits(m1,m2,(rc1,rc2))
            ph1,ph2,pm1,pm2=h1,h2,m1,m2
        else:
            if hour_changed and left.done():
                lc1,lc2=color_pair()
                if lc1 in (rc1,rc2): lc1=random.choice([c for c in PALETTE if c not in (rc1,rc2)])
                if lc2 in (rc1,rc2,lc1): lc2=random.choice([c for c in PALETTE if c not in (rc1,rc2,lc1)])
                left.build_from_digits(h1,h2,(lc1,lc2))
                ph1,ph2=h1,h2
            if minute_changed and right.done():
                rc1,rc2=color_pair()
                if rc1 in (lc1,lc2): rc1=random.choice([c for c in PALETTE if c not in (lc1,lc2)])
                if rc2 in (lc1,lc2,rc1): rc2=random.choice([c for c in PALETTE if c not in (lc1,lc2,rc1)])
                right.build_from_digits(m1,m2,(rc1,rc2))
                pm1,pm2=m1,m2
        left.step(); right.step()
        frame=[[BG]*WIDTH for _ in range(HEIGHT)]
        left.render(frame); right.render(frame)
        draw(frame)
        time.sleep(SPEED)
except KeyboardInterrupt:
    pixels.fill(BG); pixels.show()
