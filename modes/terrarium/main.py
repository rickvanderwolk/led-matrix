#!/usr/bin/env python3
"""
Terrarium: a small piece of the world seen from the side, like a slice through a snow globe.

Sky above, a strip of land in the middle, the ground below. Everything follows from simple,
real rules: nothing is scripted and nothing is rescued.

- The sky: its colors follow the sun, from a pale blue day through a golden evening and a red
  sunset to the blue hour and a dark night full of stars that slowly turn. The sun climbs high
  in summer and stays low in winter. The moon waxes and wanes over a month and rises later
  every day, like the real one. Clouds drift with the wind and catch the colors of the sky.
- The land has hills and a hollow. Rain and meltwater fill the hollow, sun and warmth dry it
  up, and still water mirrors the sky. Below freezing it snows and the snow piles up; long frost
  freezes the pond.
- Grass grows with warmth, light and water. Where it stays lush a tree can take root; trees
  grow tall, turn with the seasons, grow old and fall, and the fallen trunk rots away and glows
  faintly on damp nights. Lightning strikes the tallest thing and dry weather lets fire spread.
- Rabbits graze at dawn and dusk and rest underground in their burrows; you can see them
  sleeping there. Mice nest deeper down, come out in the dark and hoard seeds in autumn to get
  through the winter. Both only have young when there is food enough around, and drown when
  the pond floods their home. This land is only a small part of where they live: when the
  grass here is eaten they go to feed out of sight, and come back.
- Foxes, owls (at night) and buzzards (by day) come more often when there is more to catch.
  Prey bolts for its hole; trees and deep snow give cover. Birds come by and settle in the
  trees, and the seeds they drop are where new trees come up.
- Fireflies on warm summer nights, migrating birds in spring and autumn, a rainbow opposite
  the sun when it comes out after rain.
"""

import os
import json
import math
import random
import time
import board
import neopixel

CONFIG_PATH = os.environ.get("LEDMATRIX_CONFIG", "config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

LED_COUNT = 64
PIN = board.D18
BRIGHTNESS = config.get("brightness", 0.2)
settings = config.get("modes", {}).get("terrarium", {})

pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)

W = H = 8
FPS = 12
FRAMES_PER_TICK = 3  # the world itself moves 4 times per second
TICKS_PER_SECOND = FPS // FRAMES_PER_TICK
DAY_MINUTES = settings.get("day_minutes", 20)
SEASON_MINUTES = settings.get("season_minutes", 480)
TICKS_PER_DAY = int(DAY_MINUTES * 60 * TICKS_PER_SECOND)
TICKS_PER_YEAR = int(SEASON_MINUTES * 4 * 60 * TICKS_PER_SECOND)
SAPLING = TICKS_PER_YEAR // 8
MOON_DAYS = 29.5
BURROW_ROOM = 4  # rabbits a burrow has room for
NEST_ROOM = 5  # mice a nest has room for
LIFESPAN = {"rabbit": (0.5, 1.0), "fox": (2, 4), "mouse": (0.3, 0.8)}  # years
MAX_ENERGY = {"rabbit": 2.0, "fox": 3.0, "mouse": 1.0}
ADULT = {"rabbit": 0.3, "fox": 0.8, "mouse": 0.12}  # years
LITTER_INTERVAL = {"rabbit": 0.08, "fox": 0.5, "mouse": 0.06}  # years

SEASONS = ["spring", "summer", "autumn", "winter"]
WEATHER_CHANCES = {
    "spring": {"clear": 4, "rain": 4, "storm": 1, "drought": 0, "fog": 2},
    "summer": {"clear": 5, "rain": 2, "storm": 2, "drought": 3, "fog": 0},
    "autumn": {"clear": 3, "rain": 4, "storm": 2, "drought": 0, "fog": 3},
    "winter": {"clear": 4, "rain": 3, "storm": 0, "drought": 0, "fog": 3},
}
WEATHER_DAYS = {"clear": 0.6, "rain": 0.3, "storm": 0.15, "drought": 0.5, "fog": 0.2}
WEATHER_WATER = {"clear": 1.0, "rain": 2.5, "storm": 2.0, "drought": -0.4, "fog": 0.8}  # effect on grass
RAINFALL = {"rain": 1.2, "storm": 2.0}  # cells of water running into the hollow per day
EVAPORATION = {"drought": 3.0, "clear": 1.0, "fog": 0.3, "rain": 0.0, "storm": 0.0}
CLOUDS = {"clear": 3, "drought": 1, "fog": 0, "rain": 4, "storm": 5}  # how many clouds drift over

# The sky at different heights of the sun: (sun height, color overhead, color at the horizon)
SKY = [
    (-1.0, (1, 2, 7), (2, 4, 14)),
    (-0.4, (1, 2, 9), (4, 8, 26)),
    (-0.18, (6, 10, 48), (30, 34, 110)),  # the blue hour
    (-0.05, (28, 22, 95), (190, 60, 55)),  # dusk: a red glow where the sun went down
    (0.04, (45, 60, 150), (255, 110, 35)),  # sunrise and sunset
    (0.2, (35, 90, 205), (235, 160, 90)),  # golden hour
    (0.45, (25, 95, 225), (130, 185, 250)),
    (1.0, (20, 90, 235), (115, 175, 255)),
]
SUN = (255, 235, 170)
SUN_LOW = (255, 120, 30)
SUN_GLOW = (255, 150, 60)
MOON = (210, 215, 200)
STAR = (200, 205, 235)
SEASON_GRASS = {"spring": (40, 190, 30), "summer": (60, 165, 15), "autumn": (135, 85, 20), "winter": (70, 95, 40)}
SEASON_CROWN = {"spring": (60, 200, 70), "summer": (15, 110, 25), "autumn": (210, 80, 5), "winter": (55, 38, 25)}
TRUNK = (70, 42, 20)
LOG = (85, 55, 28)
SOIL = (38, 23, 9)
DEEP_SOIL = (16, 10, 5)
BURROW = (4, 2, 1)
WATER = (15, 70, 170)
ICE = (150, 190, 230)
SNOW = (175, 185, 210)
FLAKE = (240, 245, 255)
RAIN = (215, 225, 255)  # catching the light, brighter than the grey sky behind it
RABBIT = (150, 130, 100)
MOUSE = (115, 100, 85)
OWL = (200, 185, 150)  # a barn owl, pale enough to catch the moonlight
BUZZARD = (95, 62, 35)
FOX = (160, 55, 12)
FIREFLY = (200, 255, 60)
FOXFIRE = (40, 210, 120)
BIRD = (30, 30, 35)
GNAT = (230, 225, 190)
SMOKE = (90, 85, 80)
RAINBOW = [(255, 0, 0), (255, 120, 0), (255, 230, 0), (0, 200, 0), (0, 90, 255), (140, 0, 220)]
GOLDEN_LIGHT = (1.9, 0.95, 0.35)
BLUE_LIGHT = (0.55, 0.7, 1.4)
NIGHT_LIGHT = (0.5, 0.62, 1.1)
HAZE_GOLD = (255, 140, 40)
HAZE_BLUE = (25, 50, 160)
HAZE_NIGHT = (10, 25, 90)


def clamp(v):
    return 0 if v < 0 else (255 if v > 255 else int(v))


def mix(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t), int(c1[1] + (c2[1] - c1[1]) * t), int(c1[2] + (c2[2] - c1[2]) * t))


def scale(c, f):
    return clamp(c[0] * f), clamp(c[1] * f), clamp(c[2] * f)


def add(c1, c2, f):
    return clamp(c1[0] + c2[0] * f), clamp(c1[1] + c2[1] * f), clamp(c1[2] + c2[2] * f)


def blend(canvas, fx, fy, color, alpha, glow=False):
    """Draw something that sits between cells: it glides instead of jumping."""
    x0, y0 = math.floor(fx), math.floor(fy)
    tx, ty = fx - x0, fy - y0
    for x, y, w in ((x0, y0, (1 - tx) * (1 - ty)), (x0 + 1, y0, tx * (1 - ty)),
                    (x0, y0 + 1, (1 - tx) * ty), (x0 + 1, y0 + 1, tx * ty)):
        if w > 0.01 and 0 <= x < W and 0 <= y < H:
            i = y * W + x
            canvas[i] = add(canvas[i], color, alpha * w) if glow else mix(canvas[i], color, alpha * w)


def per_day(amount):
    return amount / TICKS_PER_DAY


def per_year(amount):
    return amount / TICKS_PER_YEAR


class Animal:
    def __init__(self, kind, x, energy):
        self.kind = kind
        self.x = x
        self.prev = x
        self.moved = -1
        self.energy = energy
        self.age = 0
        # A mouse lives about half a year and has a litter every few weeks, a rabbit lives about a
        # year and has a litter every month or so, a fox lives a few years
        self.lifespan = int(TICKS_PER_YEAR * random.uniform(*LIFESPAN[kind]))
        self.max_energy = MAX_ENERGY[kind]
        self.adult_age = int(TICKS_PER_YEAR * ADULT[kind])
        self.pregnancy = int(TICKS_PER_YEAR * LITTER_INTERVAL[kind])
        self.next_litter = 0
        self.asleep = False
        self.underground = False  # resting in a burrow
        self.alert_until = 0
        self.leaving = False
        self.breath = random.uniform(0, 2 * math.pi)

    def is_adult(self):
        return self.age > self.adult_age


class Raptor:
    """A bird of prey visiting: an owl at night, a buzzard by day."""

    def __init__(self, kind, x, y):
        self.kind = kind
        self.x, self.y = x, y
        self.px, self.py = x, y
        self.state = "hunt"
        self.target = None
        self.home_x = random.uniform(1, W - 2)  # where it circles or quarters
        self.t = random.randrange(1000)
        self.fed = 0
        self.rest = 0

    def toward(self, x, y, speed):
        dx, dy = x - self.x, y - self.y
        d = math.hypot(dx, dy)
        if d <= speed:
            self.x, self.y = x, y
            return True
        self.x += dx / d * speed
        self.y += dy / d * speed
        return False


class Mote:
    """Something small moving through the air: a raindrop, a flake, a leaf, a firefly, smoke."""

    def __init__(self, kind, x, y, vx, vy, color, frames):
        self.kind = kind
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.frame = 0
        self.frames = frames
        self.phase = random.uniform(0, 2 * math.pi)

    def fade(self):
        return min(1.0, self.frame / 4, (self.frames - self.frame) / 6)


class World:
    def __init__(self):
        self.tick = random.randrange(TICKS_PER_YEAR)
        if settings.get("start_season") in SEASONS:
            quarter = TICKS_PER_YEAR // 4
            self.tick = SEASONS.index(settings["start_season"]) * quarter + random.randrange(quarter // 4)
        self.tick -= self.tick % TICKS_PER_DAY
        self.tick += int(TICKS_PER_DAY * (0.5 - self.day_length() / 2 + random.uniform(0.08, 0.15)))
        self.day = 0
        self.spell = random.gauss(0, 2)
        self.weather = "clear"
        self.weather_left = TICKS_PER_DAY // 2
        self.dryness = 0.0
        self.humidity = 0.5  # how damp the air is: high after rain and near water
        self.mist = 0.0  # mist lying in the hollow, 0 none to 1 thick
        self.murmuration = None
        self.murmuration_day = -1
        self.wind = random.choice((-1, 1)) * random.uniform(0.3, 1.0)  # to the right is positive
        self.moon_start = random.uniform(0, MOON_DAYS)

        # Hills and a hollow, in cells of ground; it slowly changes
        self.ground = self.make_terrain()
        self.volume = random.uniform(0, 2)  # cells of water in the hollow
        self.level = 0.0
        self.ice = 0.0
        self.snow = 0.0
        self.grass = [random.uniform(0.3, 0.9) for _ in range(W)]
        self.lush = [0] * W
        self.trees = {}  # column -> age in ticks
        for x in random.sample(range(W), random.randint(1, 3)):
            self.trees[x] = random.randrange(TICKS_PER_YEAR * 3)
        self.logs = {}  # column -> ticks left of a fallen trunk
        self.burrows = {}  # column -> tick last used
        self.nests = {}  # column -> tick last used; mouse nests, deeper down
        self.stores = {}  # column -> seeds hoarded in a mouse nest for the winter
        self.raptors = []
        self.away = []  # [animal, tick it comes back]: off foraging beyond the edges of the view
        self.fire = {}  # column -> ticks left burning
        self.fertile = {}  # column -> ticks left
        self.animals = []
        self.update_water()
        for x in random.sample([x for x in range(W) if not self.wet(x) and x not in self.trees], random.randint(1, 2)):
            self.burrows[x] = self.tick
        for _ in range(random.randint(1, 3)):
            self.spawn("rabbit", 1.2)
        for _ in range(random.randint(0, 3)):
            self.spawn("mouse", 0.8)

        # The sky
        self.stars = [[random.uniform(0, 2 * W), random.uniform(0, 4.5), random.uniform(0.3, 1.0),
                       random.uniform(0, 2 * math.pi)] for _ in range(16)]
        self.clouds = []
        self.motes = []
        self.rainbow = 0  # frames left
        self.rainbow_side = 1
        self.lightning = None  # (column, frames left)
        self.birds = None
        self.birds_due = False
        self.flyers = []  # birds about their day, swallows and bats hunting, gnats dancing
        self.shooting = None

    def make_terrain(self):
        """A strip of land two to four cells high, with gentle hills and at least one hollow."""
        a, b = random.uniform(0.6, 1.2), random.uniform(0, 2 * math.pi)
        c, d = random.uniform(0.2, 0.6), random.uniform(0, 2 * math.pi)
        heights = [3 + a * math.sin(x * 0.7 + b) + c * math.sin(x * 1.6 + d) for x in range(W)]
        low, high = min(heights), max(heights)
        return [2.0 + 2.4 * (h - low) / (high - low) for h in heights]

    # Time and climate

    def year_phase(self):
        return (self.tick % TICKS_PER_YEAR) / TICKS_PER_YEAR

    def season(self):
        return SEASONS[int(self.year_phase() * 4)]

    def seasonal(self, table):
        position = self.year_phase() * 4
        index, progress = int(position), position % 1
        blend_ = max(0.0, (progress - 0.75) / 0.25)
        return mix(table[SEASONS[index]], table[SEASONS[(index + 1) % 4]], blend_)

    def summer_ness(self):
        return math.cos(2 * math.pi * (self.year_phase() - 0.375))

    def day_length(self):
        return 0.5 + 0.17 * math.cos(2 * math.pi * (self.year_phase() - 0.25))

    def day_time(self):
        return (self.tick % TICKS_PER_DAY) / TICKS_PER_DAY

    def sun_height(self):
        """-1 (deepest night) to 1 (the sun at its highest)."""
        t, length = self.day_time(), self.day_length()
        sunrise = 0.5 - length / 2
        if sunrise < t < sunrise + length:
            return math.sin(math.pi * (t - sunrise) / length)
        return -math.sin(math.pi * ((t - sunrise - length) % 1.0) / (1 - length))

    def sun_progress(self):
        """0 at sunrise, 1 at sunset."""
        length = self.day_length()
        return (self.day_time() - (0.5 - length / 2)) / length

    def light(self):
        return max(0.0, self.sun_height())

    def is_night(self):
        return self.light() < 0.15

    def moon_age(self):
        """Days since new moon."""
        return (self.tick / TICKS_PER_DAY + self.moon_start) % MOON_DAYS

    def moon(self):
        """How full the moon is, 0 to 1."""
        return 0.5 - 0.5 * math.cos(2 * math.pi * self.moon_age() / MOON_DAYS)

    def moon_position(self):
        """The moon follows the sun's path, a little later every day: a new moon rises with the
        sun, a full moon when the sun sets. Returns its progress across the sky (0-1) or None."""
        t = (self.day_time() - self.moon_age() / MOON_DAYS) % 1.0
        progress = (t - 0.25) / 0.5
        return progress if 0 <= progress <= 1 else None

    def twilight(self, light):
        if light <= 0:
            return 0.0
        return light / 0.15 if light < 0.15 else max(0.0, 1 - (light - 0.15) / 0.35)

    def temperature(self):
        t = 10 + 10 * self.summer_ness() + self.spell
        light = self.light()
        if self.weather in ("clear", "drought"):
            t += 6 * light - 3
        else:
            t += 2 * light - 1
        if self.weather == "drought":
            t += 4
        return t

    # The land

    def top(self, x):
        """Row of the top ground cell in a column."""
        return H - int(round(self.ground[x]))

    def wet(self, x):
        return self.level > round(self.ground[x]) + 0.05

    def walkable(self, x):
        return 0 <= x < W and (not self.wet(x) or self.ice > 0.8) and x not in self.fire

    def update_water(self):
        """The water lies in the lowest hollow and spreads as it rises, over a ridge into the next one."""
        heights = [round(h) for h in self.ground]
        low = min(range(W), key=lambda x: heights[x])

        def basin(level):
            left = right = low
            while left > 0 and heights[left - 1] < level:
                left -= 1
            while right < W - 1 and heights[right + 1] < level:
                right += 1
            return left, right

        def volume_at(level):
            left, right = basin(level)
            return sum(max(0.0, level - heights[x]) for x in range(left, right + 1))

        lo, hi = float(heights[low]), float(H - 2)
        if self.volume <= 0:
            self.level = lo
        else:
            for _ in range(20):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if volume_at(mid) < self.volume else (lo, mid)
            self.level = lo
        self.basin = basin(self.level) if self.level > heights[low] else None

    def update_land(self):
        temperature = self.temperature()
        falling = per_day(RAINFALL.get(self.weather, 0))
        if temperature < 1:
            self.snow = min(1.6, self.snow + falling * 0.8)
        else:
            self.volume += falling
        if temperature > 1 and self.snow > 0:
            melt = min(self.snow, per_day(0.43) * (temperature - 1) * (0.5 + self.light()))
            self.snow -= melt
            self.volume += melt * 1.5
        area = (self.basin[1] - self.basin[0] + 1) if self.basin else 0
        if temperature > 0 and self.ice < 0.5:
            heat = EVAPORATION[self.weather] * max(0.0, temperature) / 12 * (0.3 + self.light())
            self.volume -= per_day(0.12) * heat * (1 + area)
        if self.basin and (self.basin[0] == 0 or self.basin[1] == W - 1):
            self.volume -= per_day(0.6)  # it overflows at the edge, like a stream running off
        self.volume = max(0.0, min(10.0, self.volume))
        freeze = per_day(0.72) if temperature < 0 else per_day(2.9)
        self.ice = max(0.0, min(1.0, self.ice - freeze * temperature))

        before = [self.wet(x) for x in range(W)]
        self.update_water()
        for x in range(W):
            if self.wet(x) and not before[x]:
                self.flood(x)

        # Ponds silt up, rain washes soil from the hills into the hollows
        for x in range(W):
            if self.wet(x):
                self.ground[x] = min(4.4, self.ground[x] + per_year(0.25))
        if self.weather in ("rain", "storm"):
            strength = per_day(0.04 if self.weather == "storm" else 0.02)
            for x in range(W):
                if x in self.trees and random.random() < 0.8:
                    continue  # roots hold the soil
                lower = [n for n in (x - 1, x + 1) if 0 <= n < W and self.ground[n] < self.ground[x]]
                if lower:
                    n = min(lower, key=lambda n: self.ground[n])
                    moved = (self.ground[x] - self.ground[n]) * strength
                    self.ground[x] -= moved
                    self.ground[n] += moved
        self.ground = [max(1.6, min(4.4, h)) for h in self.ground]

    def flood(self, x):
        """The water rises over a column: trees drown, burrows fill up."""
        if x in self.trees:
            del self.trees[x]
            print("Event: a tree drowns")
        self.logs.pop(x, None)
        self.fire.pop(x, None)
        self.grass[x] = 0.0
        if x in self.burrows:
            del self.burrows[x]
            print("Event: a burrow floods")
        if x in self.nests:
            del self.nests[x]
            self.stores.pop(x, None)
            print("Event: a mouse nest floods")
        for animal in [a for a in self.animals if a.x == x]:
            dry = [n for n in (x - 1, x + 1) if self.walkable(n)]
            if dry:
                animal.underground = False
                self.move(animal, random.choice(dry))
            else:
                self.kill(animal, "drowned")

    def grow(self):
        temperature = self.temperature()
        warmth = max(0.0, min(1.3, (temperature - 4) / 12))
        water = WEATHER_WATER[self.weather]
        light = self.light()
        for x in range(W):
            if self.wet(x) or x in self.fire:
                self.lush[x] = 0
                continue
            amount = self.grass[x]
            near_water = any(self.wet(n) for n in (x - 1, x + 1) if 0 <= n < W)
            wet = 1.8 if near_water else 1.0
            fed = 1.6 if x in self.fertile else 1.0
            shade = 0.6 if x in self.trees and self.trees[x] > SAPLING else 1.0
            if water > 0:
                seeding = max((self.grass[n] for n in (x - 1, x + 1) if 0 <= n < W), default=0)
                growth = warmth * water * fed
                amount += per_day(5.8) * growth * (0.2 + light) * wet * shade * (1.05 - amount)
                amount += per_day(0.58) * growth * seeding
            else:
                amount += per_day(0.75) * water / wet
            self.grass[x] = max(0.0, min(1.0, amount))
            self.lush[x] = self.lush[x] + 1 if self.grass[x] > 0.75 else 0
        for x in list(self.fertile):
            self.fertile[x] -= 1
            if self.fertile[x] <= 0:
                del self.fertile[x]

    def change_trees(self):
        if self.temperature() > 8:
            for x in range(W):
                if x in self.trees or x in self.burrows or self.wet(x) or self.lush[x] < TICKS_PER_DAY // 4:
                    continue
                near = sum(n in self.trees for n in (x - 1, x + 1))
                if random.random() < (per_year(2.3) if near else per_year(0.35)):
                    self.trees[x] = 0
                    print("Event: a tree takes root")
        for x in list(self.trees):
            self.trees[x] += 1
            crowded = sum(n in self.trees for n in (x - 1, x + 1))
            if self.trees[x] > TICKS_PER_YEAR * (3 - 0.4 * crowded) and random.random() < per_year(3.5):
                del self.trees[x]
                self.logs[x] = TICKS_PER_YEAR // 2  # the trunk stays and slowly rots away
                self.fertile[x] = TICKS_PER_DAY * 4
                print("Event: an old tree falls")
        for x in list(self.logs):
            self.logs[x] -= 1
            if self.logs[x] <= 0:
                del self.logs[x]
        for x, used in list(self.burrows.items()):
            if self.tick - used > TICKS_PER_DAY * 3:
                del self.burrows[x]
                print("Event: an empty burrow collapses")
        for x, used in list(self.nests.items()):
            if self.tick - used > TICKS_PER_DAY * 3:
                del self.nests[x]
                self.stores.pop(x, None)

    def spread_fire(self):
        for x in list(self.fire):
            self.grass[x] = 0.0
            self.logs.pop(x, None)
            if x in self.trees and random.random() < 0.1:
                del self.trees[x]
                print("Event: a tree burns down")
            for animal in [a for a in self.animals if a.x == x and not a.underground]:
                self.kill(animal, "fire")
            for n in (x - 1, x + 1):
                if 0 <= n < W and n not in self.fire and not self.wet(n):
                    fuel = (1.0 if n in self.trees or n in self.logs else self.grass[n]) * (1 - min(1.0, self.snow))
                    if random.random() < 0.02 * (1 + 2 * self.dryness) * fuel:
                        self.fire[n] = 40 if n in self.trees else 20
            self.fire[x] -= 1
            if self.fire[x] <= 0 or self.weather in ("rain", "storm") and random.random() < 0.05:
                del self.fire[x]
                self.fertile[x] = TICKS_PER_DAY

    def update_mist(self):
        """On a clear, calm, cold night the damp air in the hollow cools and condenses: by dawn
        a layer of mist lies there. The morning sun and the wind take it away."""
        if self.weather in ("rain", "storm"):
            self.humidity = 1.0
        else:
            self.humidity = max(0.0, self.humidity - per_day(0.7))
        damp = self.humidity + (0.3 if self.basin else 0.0)
        light = self.light()
        if self.weather == "fog":
            self.mist = min(1.0, self.mist + per_day(6))
        elif (light == 0 and self.weather == "clear" and abs(self.wind) < 0.7 and self.temperature() < 10
                and damp > 0.4):
            self.mist = min(1.0, self.mist + per_day(3) * damp)
        elif light > 0.1 or abs(self.wind) > 1.0 or self.weather in ("rain", "storm", "drought"):
            self.mist = max(0.0, self.mist - per_day(5) * (light + 0.3 * abs(self.wind)))

    def update_weather(self):
        self.weather_left -= 1
        if self.weather_left <= 0:
            was_raining = self.weather in ("rain", "storm")
            if self.weather == "drought":
                self.weather = random.choice(("rain", "rain", "storm"))
            else:
                chances = dict(WEATHER_CHANCES[self.season()])
                if self.temperature() < 15:
                    chances["drought"] = 0
                options = [w for w in chances if w != self.weather and chances[w]]
                self.weather = random.choices(options, [chances[w] for w in options])[0]
            self.weather_left = int(TICKS_PER_DAY * WEATHER_DAYS[self.weather] * random.uniform(0.6, 1.5))
            print(f"Weather: {self.weather}")
            if was_raining and self.weather == "clear" and self.light() > 0.2 and self.temperature() > 2:
                self.rainbow = FPS * 30  # the sun comes out after rain
                self.rainbow_side = -1 if self.sun_progress() < 0.5 else 1  # opposite the sun
                print("Event: rainbow")
        self.wind += random.gauss(0, 0.01) - self.wind * 0.0005
        temperature = self.temperature()
        if self.weather in ("drought", "clear") and temperature > 18:
            self.dryness = min(1.0, self.dryness + per_day(0.7))
        elif self.weather in ("rain", "storm"):
            self.dryness = max(0.0, self.dryness - per_day(4.3))
        if self.weather == "storm" and random.random() < per_day(22):
            # Lightning goes for the tallest thing: a tree if there is one
            target = max(self.trees, key=lambda x: self.trees[x]) if self.trees and random.random() < 0.7 else random.randrange(W)
            self.lightning = (target, 4)
            if random.random() < 0.1 and not self.wet(target) and self.snow < 0.3:
                fuel = 1.0 if target in self.trees else self.grass[target]
                if random.random() < fuel * (0.3 + self.dryness):
                    self.fire[target] = 40 if target in self.trees else 20
                    print("Event: lightning starts a fire")

    # Animals

    def spawn(self, kind, energy, edge=False):
        columns = [x for x in range(W) if self.walkable(x) and not self.occupant(x)]
        if edge:
            columns = [x for x in columns if x in (0, W - 1)]
        if columns:
            animal = Animal(kind, random.choice(columns), energy)
            animal.age = random.randint(animal.adult_age, (animal.adult_age + animal.lifespan) // 2)
            self.animals.append(animal)
            return True
        return False

    def occupant(self, x):
        """A rabbit or fox on the land here (a mouse is small enough to slip past)."""
        for animal in self.animals:
            if animal.x == x and not animal.underground and animal.kind != "mouse":
                return animal
        return None

    def in_burrow(self, x, kind="rabbit"):
        return sum(1 for a in self.animals if a.underground and a.x == x and a.kind == kind)

    def nest_row(self, x):
        return self.top(x) + min(2, int(round(self.ground[x])) - 1)

    def threats(self, animal):
        """How close the nearest danger is: a fox on the land, or a bird of prey coming down."""
        near = [abs(animal.x - a.x) for a in self.animals if a.kind == "fox"]
        near += [abs(animal.x - r.x) for r in self.raptors if r.state == "dive"]
        return min(near, default=99)

    def count(self, kind):
        return sum(1 for a in self.animals if a.kind == kind)

    def move(self, animal, x):
        if x != animal.x:
            animal.prev, animal.x, animal.moved = animal.x, x, self.tick
            self.grass[x] = max(0.0, self.grass[x] - 0.02)

    def kill(self, animal, cause):
        if animal in self.animals:
            self.animals.remove(animal)
            self.fertile[animal.x] = TICKS_PER_DAY * 2
            print(f"Event: a {animal.kind} dies ({cause})")

    def capacity(self, animal):
        return animal.max_energy * (1.75 if self.season() in ("autumn", "winter") else 1.0)

    def plenty(self):
        """Is there food enough around to raise young? When grass runs short, rabbits and mice
        stop having litters (rabbits even reabsorb their embryos)."""
        return sum(self.grass) / W > 0.45

    def has_mate(self, animal):
        return any(o is not animal and o.kind == animal.kind and o.is_adult() for o in self.animals)

    def rabbit(self, rabbit):
        rabbit.age += 1
        danger = self.threats(rabbit)
        if danger <= 2:
            rabbit.alert_until = self.tick + TICKS_PER_SECOND * 12
        alert = self.tick < rabbit.alert_until
        cold = self.temperature() < 0
        light = self.light()
        home = min(self.burrows, key=lambda b: abs(b - rabbit.x), default=None)
        if rabbit.underground and rabbit.x not in self.burrows:
            rabbit.underground = False  # the burrow is gone

        # Rabbits graze at dawn, dusk and in the night, and rest underground in the bright middle
        # of the day, in the small hours and when it is freezing. A hungry rabbit comes out anyway
        hungry = rabbit.energy < (0.6 if rabbit.underground else 0.9)
        rest = (light > 0.7 or (light == 0 and rabbit.energy > 1.4) or (cold and rabbit.energy > 0.8)
                or alert and rabbit.underground)
        if rabbit.underground:
            if not rest or hungry:
                if not alert or rabbit.energy < 0.3:
                    rabbit.underground = False
                    rabbit.asleep = False
        elif (rest and not hungry) or (alert and home is not None):
            # Head home, or bolt down the burrow when a fox is near
            if home is not None and home == rabbit.x and self.in_burrow(rabbit.x) < BURROW_ROOM:
                rabbit.underground = True
                rabbit.asleep = not alert
            elif home is not None and random.random() < (1.0 if alert else 0.3):
                step = rabbit.x + (1 if home > rabbit.x else -1)
                if self.walkable(step) and not self.occupant(step):
                    self.move(rabbit, step)
            else:
                rabbit.asleep = home is None and light == 0
        elif alert and danger <= 3:
            # No burrow to dive into: run away from the danger
            rabbit.asleep = False
            threat = min([a.x for a in self.animals if a.kind == "fox"] + [r.x for r in self.raptors],
                         key=lambda t: abs(t - rabbit.x))
            away = rabbit.x + (1 if rabbit.x > threat else -1 if rabbit.x < threat else random.choice((-1, 1)))
            if self.walkable(away) and not self.occupant(away):
                self.move(rabbit, away)
        else:
            rabbit.asleep = False
            if self.forage_elsewhere(rabbit):
                return
            if self.grass[rabbit.x] < 0.15 and random.random() < 0.3 or random.random() < 0.03:
                options = [n for n in (rabbit.x - 1, rabbit.x + 1) if self.walkable(n) and not self.occupant(n)]
                if options:
                    self.move(rabbit, max(options, key=lambda n: self.grass[n] + random.uniform(0, 0.3)))

        if not rabbit.underground and not rabbit.asleep and rabbit.energy < self.capacity(rabbit) - 0.1:
            bite = min(self.grass[rabbit.x], per_day(14)) * (1 - 0.8 * min(1.0, self.snow))
            self.grass[rabbit.x] -= bite
            rabbit.energy += bite
        if rabbit.underground:
            rabbit.energy -= per_day(0.35)
        elif rabbit.asleep:
            rabbit.energy -= per_day(0.55)
        else:
            rabbit.energy -= per_day(1.5) + (per_day(0.4) if cold else 0)
        if not rabbit.underground and rabbit.energy < 1.0 and self.snow > 0.3 and rabbit.x in self.trees:
            rabbit.energy += per_day(1.5)  # gnawing bark in the snow
        if rabbit.x in self.trees and self.trees[rabbit.x] < SAPLING and not rabbit.underground \
                and random.random() < per_year(576 / 8):
            del self.trees[rabbit.x]  # a sapling nibbled away
        if rabbit.x in self.burrows:
            self.burrows[rabbit.x] = self.tick
        rabbit.energy = min(rabbit.energy, self.capacity(rabbit))

        # Young are born in a nest in the burrow while the days are long, as many as there is room for
        room = BURROW_ROOM - self.in_burrow(rabbit.x)
        if (rabbit.underground and room > 0 and rabbit.energy > 1.5 and self.day_length() > 0.5 and self.plenty()
                and rabbit.is_adult()
                and rabbit.age > rabbit.next_litter and random.random() < per_day(43) and self.has_mate(rabbit)):
            litter = min(room, random.randint(1, 3))
            for _ in range(litter):
                young = Animal("rabbit", rabbit.x, 0.6)
                young.underground = young.asleep = True
                self.animals.append(young)
            rabbit.energy -= 0.3 * (1 + litter)
            rabbit.next_litter = rabbit.age + rabbit.pregnancy
            print(f"Event: {litter} young rabbits are born")

        # Dig a new burrow away from the others (or when they are full), in well-drained higher ground
        crowded = home is not None and self.in_burrow(home) >= BURROW_ROOM
        far = not self.burrows or min(abs(rabbit.x - b) for b in self.burrows) > 2 or crowded
        dry = self.ground[rabbit.x] >= sorted(self.ground)[W // 2] and not any(
            self.wet(n) for n in (rabbit.x - 1, rabbit.x + 1) if 0 <= n < W)
        if (far and dry and rabbit.x not in self.burrows and not cold and rabbit.energy > 1.2 and not rabbit.underground and rabbit.x not in self.trees
                and not self.wet(rabbit.x) and round(self.ground[rabbit.x]) >= 2 and random.random() < per_day(2.9)):
            self.burrows[rabbit.x] = self.tick
            print("Event: rabbits dig a new burrow")

        if rabbit.energy <= 0:
            self.kill(rabbit, "starved")
        elif rabbit.age > rabbit.lifespan:
            self.kill(rabbit, "old")

    def fox(self, fox):
        fox.age += 1
        night = self.is_night()
        full = fox.energy > 1.6
        rabbits = [a for a in self.animals if a.kind in ("rabbit", "mouse") and not a.underground
                   and not (a.kind == "mouse" and self.snow > 0.5)]  # mice run under the snow
        if not fox.leaving and random.random() < per_day(1 if rabbits or self.count("rabbit") else 3):
            fox.leaving = True
        fox.asleep = (full or not night and self.light() > 0.6) and not fox.leaving
        if fox.asleep:
            fox.energy -= per_day(0.29)
        elif not night and self.tick % 2:
            fox.energy -= per_day(0.29)
        else:
            if fox.leaving:
                if fox.x in (0, W - 1):
                    self.animals.remove(fox)
                    print("Event: a fox moves on")
                    return
                target = fox.x + (1 if fox.x >= W / 2 else -1)
            else:
                prey = min(rabbits, key=lambda r: abs(r.x - fox.x), default=None)
                if prey and not full and abs(prey.x - fox.x) <= 3:
                    target = fox.x + (1 if prey.x > fox.x else -1 if prey.x < fox.x else 0)
                elif random.random() < 0.15:
                    target = fox.x + random.choice((-1, 1))
                else:
                    target = fox.x
            if self.walkable(target):
                other = self.occupant(target)
                if other is fox:
                    other = None
                mouse = next((a for a in rabbits if a.kind == "mouse" and a.x == target), None)
                if mouse and not other and not full and not fox.leaving and random.random() < 0.3:
                    self.kill(mouse, "eaten by a fox")  # a pounce into the grass
                    fox.energy += 0.3
                if other and other.kind == "rabbit" and not full and not fox.leaving:
                    # A fox sees best by the light of the full moon; under trees there is cover
                    hidden = target in self.trees and not night
                    if not hidden and random.random() < ((0.35 + 0.2 * self.moon()) if night else 0.2):
                        self.kill(other, "eaten by a fox")
                        fox.energy += 1.0
                        self.move(fox, target)
                elif not other:
                    self.move(fox, target)
            fox.energy -= per_day(1.15) if self.temperature() < 0 else per_day(0.86)
        fox.energy = min(fox.energy, self.capacity(fox))
        if fox.energy <= 0:
            self.kill(fox, "starved")
        elif fox.age > fox.lifespan:
            self.kill(fox, "old")

    def mouse(self, mouse):
        """Mice live in nests deep in the ground and come out in the dark to look for seeds.
        Under deep snow they keep foraging in tunnels, out of sight of owls and foxes."""
        mouse.age += 1
        if self.threats(mouse) <= 1:
            mouse.alert_until = self.tick + TICKS_PER_SECOND * 20
        alert = self.tick < mouse.alert_until
        light = self.light()
        cold = self.temperature() < 0
        home = min(self.nests, key=lambda n: abs(n - mouse.x), default=None)
        if mouse.underground and mouse.x not in self.nests:
            mouse.underground = False
        # Living off the hoard: a mouse with a full larder stays in on cold days
        store = self.stores.get(mouse.x, 0.0) if mouse.underground else 0.0
        lean = self.season() == "winter" or self.snow > 0.3 or self.grass[mouse.x] < 0.1
        if store > 0 and lean and mouse.energy < 0.8 * self.capacity(mouse):
            take = min(store, per_day(3))
            self.stores[mouse.x] = store - take
            mouse.energy += take
        hungry = mouse.energy < 0.3
        rest = light > 0.1 or mouse.energy > 0.95 * self.capacity(mouse) or (cold and self.stores.get(home, 0) > 0.1)
        if mouse.underground:
            if (not rest or hungry) and not alert:
                mouse.underground = mouse.asleep = False
        elif rest or alert:
            if home == mouse.x and self.in_burrow(mouse.x, "mouse") < NEST_ROOM:
                mouse.underground = True
                mouse.asleep = not alert
            elif home is not None:
                step = mouse.x + (1 if home > mouse.x else -1)
                if self.walkable(step):
                    self.move(mouse, step)
            else:
                mouse.asleep = True  # curled up in the grass
        elif self.forage_elsewhere(mouse):
            return
        elif random.random() < 0.15:
            options = [n for n in (mouse.x - 1, mouse.x + 1) if self.walkable(n)]
            if options:
                self.move(mouse, max(options, key=lambda n: self.grass[n] + random.uniform(0, 0.5)))

        if not mouse.underground and not mouse.asleep and mouse.energy < self.capacity(mouse) - 0.05:
            bite = min(self.grass[mouse.x], per_day(5)) * (1 - 0.3 * min(1.0, self.snow))
            self.grass[mouse.x] -= bite * 0.5  # seeds and shoots
            mouse.energy += bite
            # In autumn mice carry seeds home and hoard them for the winter
            if self.season() == "autumn" and home is not None and self.stores.get(home, 0) < 3:
                gathered = min(self.grass[mouse.x], per_day(4))
                self.grass[mouse.x] -= gathered * 0.5
                self.stores[home] = self.stores.get(home, 0) + gathered
        if mouse.underground:
            mouse.energy -= per_day(0.3)
        elif mouse.asleep:
            mouse.energy -= per_day(0.5)
        else:
            mouse.energy -= per_day(1.0) + (per_day(0.3) if cold else 0)
        if mouse.x in self.nests:
            self.nests[mouse.x] = self.tick
        mouse.energy = min(mouse.energy, self.capacity(mouse))

        room = NEST_ROOM - self.in_burrow(mouse.x, "mouse")
        if (mouse.underground and mouse.x in self.nests and room > 0 and mouse.energy > 0.7 and self.season() != "winter"
                and self.plenty()
                and mouse.is_adult() and mouse.age > mouse.next_litter and random.random() < per_day(30)
                and self.has_mate(mouse)):
            litter = min(room, random.randint(2, 4))
            for _ in range(litter):
                young = Animal("mouse", mouse.x, 0.4)
                young.underground = young.asleep = True
                self.animals.append(young)
            mouse.energy -= 0.12 * (1 + litter)
            mouse.next_litter = mouse.age + mouse.pregnancy
            print(f"Event: {litter} young mice are born")

        far = home is None or abs(home - mouse.x) > 2  # mice keep their nests apart
        deep = round(self.ground[mouse.x]) >= 3 or mouse.x not in self.burrows
        dry = self.ground[mouse.x] >= sorted(self.ground)[W // 2] and not any(
            self.wet(n) for n in (mouse.x - 1, mouse.x + 1) if 0 <= n < W)
        if (far and deep and dry and not mouse.underground and mouse.x not in self.nests and not self.wet(mouse.x)
                and round(self.ground[mouse.x]) >= 2 and random.random() < per_day(3)):
            self.nests[mouse.x] = self.tick
            print("Event: mice make a nest")

        if mouse.energy <= 0:
            self.kill(mouse, "starved")
        elif mouse.age > mouse.lifespan:
            self.kill(mouse, "old")

    def raptor(self, bird):
        """Owls quarter low over the land at night, buzzards circle high by day. When they spot
        prey out in the open they come down on it; the prey dives for cover if it can."""
        bird.px, bird.py = bird.x, bird.y
        bird.t += 1
        owl = bird.kind == "owl"
        light = self.light()
        if bird.state == "leave" or (owl and light > 0.1) or (not owl and (light < 0.2 or self.weather in ("rain", "storm"))):
            bird.state = "leave"
            edge = -2.0 if bird.x < W / 2 else W + 1.0
            if bird.toward(edge, 0.5, 0.35):
                self.raptors.remove(bird)
                print(f"Event: the {bird.kind} flies off")
            return
        if bird.state == "hunt":
            if owl:
                # Barn owls fly slowly back and forth, low over the land
                bird.x = bird.home_x + 2.8 * math.sin(bird.t * 0.02)
                ground = self.top(min(W - 1, max(0, int(round(bird.x)))))
                bird.y += (ground - 3 - bird.y) * 0.1
            else:
                bird.x = bird.home_x + 2.5 * math.sin(bird.t * 0.04)
                bird.y = 1.0 + 0.5 * math.cos(bird.t * 0.04)
            prey = [a for a in self.animals if a.kind in ("mouse", "rabbit") and not a.underground
                    and abs(a.x - bird.x) <= 3 and not (a.kind == "mouse" and self.snow > 0.5)
                    and not (a.x in self.trees and self.trees[a.x] >= TICKS_PER_YEAR)]  # trees give cover
            if owl:
                prey = [a for a in prey if a.kind == "mouse" or not a.is_adult()]  # owls take mice and young rabbits
            if prey and random.random() < 0.05:
                bird.target = min(prey, key=lambda a: abs(a.x - bird.x))
                bird.state = "dive"
            if random.random() < per_day(4):
                bird.state = "leave"
        elif bird.state == "dive":
            prey = bird.target
            if prey not in self.animals or prey.underground:
                bird.state = "climb"
                return
            if bird.toward(prey.x, self.top(prey.x) - 1, 0.6):
                odds = (0.5 if owl else 0.35) if prey.kind == "mouse" else (0.3 if owl else 0.25)
                if random.random() < odds:
                    self.kill(prey, f"caught by a {bird.kind}")
                    bird.fed += 1
                bird.state = "climb"
        elif bird.state == "climb":
            column = min(W - 1, max(0, int(round(bird.x))))
            if bird.toward(bird.x, 1.0 if not owl else max(0.5, self.top(column) - 3), 0.25):
                bird.home_x = min(W - 2.0, max(1.0, bird.x))
                bird.t = 0
                bird.state = "leave" if bird.fed >= (2 if owl else 1) else "hunt"

    def forage_elsewhere(self, animal):
        """This piece of land is only a small part of where an animal lives. When the grass here
        is eaten, it heads for the edge and goes to feed somewhere out of sight."""
        if sum(self.grass) / W > 0.25 or self.grass[animal.x] > 0.15 or random.random() > 0.3:
            return False
        edge = 0 if animal.x < W / 2 else W - 1
        if animal.x == edge:
            self.animals.remove(animal)
            animal.underground = animal.asleep = False
            self.away.append([animal, self.tick + int(TICKS_PER_DAY * random.uniform(0.3, 1.5))])
            return True
        step = animal.x + (1 if edge > animal.x else -1)
        if self.walkable(step) and (animal.kind == "mouse" or not self.occupant(step)):
            self.move(animal, step)
        return False

    def out_of_sight(self):
        """Animals out of sight live on what the season offers elsewhere, and come back: when it
        is time, and rabbits and mice with a home here in the dusk to sleep in it."""
        gain = {"spring": 1.2, "summer": 1.2, "autumn": 0.8, "winter": -0.15}[self.season()]
        dusk = self.light() < 0.2
        for entry in list(self.away):
            animal, back = entry
            animal.age += 1
            animal.energy = min(self.capacity(animal), animal.energy + per_day(gain) * animal.max_energy / 2)
            if animal.energy <= 0 or animal.age > animal.lifespan or random.random() < per_day(0.03):
                self.away.remove(entry)  # it never comes back
                continue
            home = self.burrows if animal.kind == "rabbit" else self.nests
            if self.tick >= back or (dusk and home and random.random() < per_day(4)):
                edge = random.choice((0, W - 1))
                if self.walkable(edge) and (animal.kind == "mouse" or not self.occupant(edge)):
                    animal.x = animal.prev = edge
                    animal.moved = -1
                    animal.alert_until = 0
                    self.animals.append(animal)
                    self.away.remove(entry)

    def arrivals(self):
        prey = sum(1 for a in self.animals if a.kind in ("mouse", "rabbit"))
        owls = [r for r in self.raptors if r.kind == "owl"]
        # Predators roam a big territory and spend their time where there is something to catch
        if prey and not owls and self.light() == 0 and self.weather != "storm" and random.random() < per_day(0.15 * prey):
            self.raptors.append(Raptor("owl", random.choice((-1.0, W * 1.0)), 1.0))
            print("Event: an owl comes hunting")
        buzzards = [r for r in self.raptors if r.kind == "buzzard"]
        if (prey and not buzzards and self.light() > 0.3 and self.weather in ("clear", "drought")
                and random.random() < per_day(0.1 * prey)):
            self.raptors.append(Raptor("buzzard", random.choice((-1.0, W * 1.0)), 0.5))
            print("Event: a buzzard circles overhead")
        food = sum(self.grass) / W
        if self.count("mouse") < 2 and food > 0.3 and self.snow < 0.5 and random.random() < per_day(0.3):
            if self.spawn("mouse", 0.6, edge=True):
                print("Event: a mouse wanders in")
        if self.snow > 0.5:
            return
        food = sum(self.grass) / W * (1 - min(1.0, self.snow))
        if food > 0.3 and random.random() < per_day(0.25):
            if self.spawn("rabbit", 1.0, edge=True):
                print("Event: a rabbit wanders in")
        prey = sum(1 for a in self.animals if a.kind in ("mouse", "rabbit"))
        if self.count("fox") == 0 and random.random() < per_day(0.05 + 0.05 * prey):
            if self.spawn("fox", random.uniform(0.8, 1.6), edge=True):
                print("Event: a fox comes by")

    def step(self):
        self.tick += 1
        if self.tick % TICKS_PER_DAY == 0:
            self.day += 1
            print(f"Day {self.day} ({self.season()}, {self.temperature():.0f}°): {self.count('rabbit')} rabbits, "
                  f"{self.count('fox')} foxes, {len(self.trees)} trees, water {self.volume:.1f}, "
                  f"snow {self.snow:.1f}, {self.weather}")
        if self.tick % (TICKS_PER_YEAR // 4) == 0 and self.season() in ("spring", "autumn"):
            self.birds_due = True
        self.spell += -self.spell / (TICKS_PER_DAY * 1.5) + random.gauss(0, 3.4 / math.sqrt(TICKS_PER_DAY))
        self.update_weather()
        self.update_mist()
        self.update_land()
        self.grow()
        self.spread_fire()
        self.change_trees()
        for animal in random.sample(self.animals, len(self.animals)):
            if animal in self.animals:
                {"rabbit": self.rabbit, "fox": self.fox, "mouse": self.mouse}[animal.kind](animal)
        for bird in list(self.raptors):
            self.raptor(bird)
        self.out_of_sight()
        self.arrivals()

    # Drawing

    def wind_strength(self):
        return {"storm": 3.0, "rain": 1.5, "clear": 1.0, "drought": 0.7, "fog": 0.2}[self.weather] * (0.4 + abs(self.wind))

    def sky_colors(self, height):
        for (h1, z1, r1), (h2, z2, r2) in zip(SKY, SKY[1:]):
            if height <= h2:
                t = (height - h1) / (h2 - h1)
                return mix(z1, z2, t), mix(r1, r2, t)
        return SKY[-1][1], SKY[-1][2]

    def light_color(self, height, sunny):
        """The light falling on the land: white at midday, golden low, blue after sunset, dark at night."""
        clear = 1.0 if sunny else 0.35
        floor = 0.22 + 0.23 * self.moon() * (clear if height <= 0 else 1)
        if height > 0:
            gold = self.twilight(height) * clear
            tint = tuple(1 + (g - 1) * gold for g in GOLDEN_LIGHT)
            # With the sun right at the horizon we look into the light: the land turns into a dark
            # silhouette against the glowing sky
            backlit = max(0.0, 1 - height / 0.15) * clear
            strength = (floor + (1 - floor) * math.sqrt(height)) * (1 - 0.7 * backlit)
            return tint, strength, HAZE_GOLD, 0.45 * gold * (1 - 0.6 * backlit)
        blue = max(0.0, 1 + height / 0.35) * clear
        tint = tuple(n + (b - n) * blue for n, b in zip(NIGHT_LIGHT, BLUE_LIGHT))
        return tint, (floor + 0.2 * blue) * (1 - 0.45 * blue), mix(HAZE_NIGHT, HAZE_BLUE, blue), (0.4 + 0.15 * blue) * (1 - 0.5 * blue)

    def lit(self, color):
        tint, strength, haze, amount = self.light_now
        own, air = strength * (1 - amount), strength * amount
        return (clamp(color[0] * tint[0] * own + haze[0] * air), clamp(color[1] * tint[1] * own + haze[1] * air),
                clamp(color[2] * tint[2] * own + haze[2] * air))

    def render(self, frame):
        height = self.sun_height()
        light = max(0.0, height)
        sunny = self.weather in ("clear", "drought")
        self.light_now = self.light_color(height, sunny)
        self.underground_light = 0.5 + 0.5 * self.light_now[1]
        temperature = self.temperature()
        season = self.season()
        zenith, horizon = self.sky_colors(height)
        overcast = {"clear": 0.0, "drought": 0.0, "fog": 0.85, "rain": 0.75, "storm": 0.9}[self.weather]
        grey = scale((120, 125, 135), 0.15 + 0.85 * light)
        dark_sky = max(0.0, 1 - max(sum(zenith), sum(horizon) * 0.5) / 120)

        # Where the sun and the moon stand: high in summer, low in winter
        arc = 4.2 + 1.6 * self.summer_ness()
        sun = None
        if height > -0.05:
            p = self.sun_progress()
            sun = (-0.5 + p * W, max(0.3, H - 2.6 - arc * math.sin(math.pi * min(1.0, max(0.0, p)))))
        moon = None
        mp = self.moon_position()
        if mp is not None:
            moon = (-0.5 + mp * W, max(0.3, H - 2.6 - 3.8 * math.sin(math.pi * mp)))

        canvas = [None] * (W * H)
        # The sky, darkest overhead and lightest towards the horizon, glowing around the sun
        for y in range(H):
            t = min(1.0, max(0.0, (H - 3 - y) / (H - 3))) ** 0.8
            base = mix(horizon, zenith, t)
            base = mix(base, grey, overcast)
            for x in range(W):
                color = base
                if sun:
                    d = math.hypot(x - sun[0], y - sun[1])
                    glow = max(0.0, 1 - d / 3.5) ** 2 * (0.25 + 0.6 * self.twilight(max(light, 0.01)))
                    color = add(color, SUN_GLOW, glow * (1 - overcast))
                canvas[y * W + x] = color

        # Stars turn slowly with the sky, the moon washes out the faint ones
        if dark_sky > 0.2:
            for star in self.stars:
                star[0] = (star[0] + 2 * W / (TICKS_PER_DAY * FRAMES_PER_TICK)) % (2 * W)
                x, y = int(star[0]), int(star[1])
                if x < W:
                    twinkle = 0.55 + 0.45 * math.sin(frame * (0.2 + star[2] * 0.3) + star[3]) * random.uniform(0.7, 1.0)
                    bright = star[2] * twinkle * dark_sky * (1 - overcast) * (1 - 0.5 * self.moon() * (star[2] < 0.6))
                    canvas[y * W + x] = add(canvas[y * W + x], STAR, 0.55 * bright)
        if moon and self.moon() > 0.05:
            daylight = 1 - 0.7 * min(1.0, light * 2)
            blend(canvas, moon[0], moon[1], MOON, (0.3 + 0.7 * self.moon()) * daylight * (1 - overcast * 0.8), glow=True)
        if sun:
            sun_color = mix(SUN_LOW, SUN, min(1.0, light * 3))
            blend(canvas, sun[0], sun[1], sun_color, 1.0 - overcast * 0.85)

        # A shooting star on a clear dark night
        if self.shooting is None and dark_sky > 0.6 and sunny and random.random() < 0.0015:
            self.shooting = [random.uniform(0, 4), random.uniform(0, 1.5), 0]
        if self.shooting:
            sx, sy, f = self.shooting
            for k in range(3):
                blend(canvas, sx + 0.7 * (f - k), sy + 0.3 * (f - k), STAR, 0.9 - 0.3 * k, glow=True)
            self.shooting[2] += 1
            if self.shooting[2] > 12:
                self.shooting = None

        # A rainbow opposite the sun
        if self.rainbow:
            self.rainbow -= 1
            fade = min(1.0, self.rainbow / 24, (FPS * 30 - self.rainbow) / 24)
            cx = W / 2 + self.rainbow_side * 3
            for y in range(H):
                for x in range(W):
                    band = int((math.hypot(x - cx, (y - (H - 1)) * 1.1) - 3.6) * 1.4)
                    if 0 <= band < len(RAINBOW):
                        canvas[y * W + x] = mix(canvas[y * W + x], RAINBOW[band], 0.45 * fade)

        self.draw_clouds(canvas, frame, light, horizon, overcast)
        self.draw_birds(canvas, light)
        self.draw_flyers(canvas, frame, height, temperature)
        self.draw_murmuration(canvas, height)

        # The land: trees against the sky, water in the hollow, the ground and what lives in it
        crown = self.seasonal(SEASON_CROWN)
        grass_color = self.seasonal(SEASON_GRASS)
        wind = self.wind_strength()
        sway_speed = 0.05 + 0.04 * wind
        snow = min(1.0, self.snow)
        damp = self.weather in ("rain", "fog", "clear") and temperature > 4 and self.snow < 0.3
        for x, age in self.trees.items():
            top = self.top(x)
            if age < SAPLING:
                parts = [(x, top - 1, mix(grass_color, crown, 0.5), 0.5 + 0.5 * age / SAPLING)]
            elif age < TICKS_PER_YEAR:
                parts = [(x, top - 1, crown, 1.0)]
            elif age < 2 * TICKS_PER_YEAR:
                parts = [(x, top - 1, TRUNK, 1.0), (x, top - 2, crown, 1.0)]
            else:
                parts = [(x, top - 1, TRUNK, 1.0), (x, top - 2, TRUNK, 1.0), (x, top - 3, crown, 1.0),
                         (x - 1, top - 3, crown, 0.6), (x + 1, top - 3, crown, 0.6), (x, top - 4, crown, 0.5)]
            for px, py, color, alpha in parts:
                if 0 <= px < W and 0 <= py < H:
                    leafy = color is crown
                    if leafy and snow > 0.3 and season == "winter":
                        color = mix(color, SNOW, 0.5 * snow)
                    if x in self.fire:
                        color = mix((255, 40, 0), (255, 210, 60), random.random() ** 0.7)
                        canvas[py * W + px] = color
                    elif leafy:
                        # The crown sways in the wind, more at the top
                        reach = 0.22 * min(2.0, wind) * (1 + 0.4 * (top - 1 - py))
                        sway = reach * math.sin(frame * sway_speed + x * 1.7 + py * 0.4)
                        blend(canvas, px + sway, py, self.lit(color), alpha)
                    else:
                        canvas[py * W + px] = mix(canvas[py * W + px], self.lit(color), alpha)

        sky_row = [mix(horizon, grey, overcast)] * W
        for x in range(W):
            top = self.top(x)
            ground = round(self.ground[x])
            # Water: the level shows smoothly as it rises, still water mirrors the sky
            if self.basin and self.basin[0] <= x <= self.basin[1]:
                surface = H - self.level
                for y in range(max(0, math.floor(surface)), top):
                    fill = min(1.0, (y + 1) - surface) if y < surface else 1.0
                    water = self.lit(WATER)
                    if self.ice < 0.5:
                        water = mix(water, sky_row[x], 0.35 if y == math.floor(surface) else 0.15)
                        if dark_sky > 0.5 and random.random() < 0.02:
                            water = add(water, STAR, 0.3)  # a star mirrored in the water
                        water = scale(water, 0.85 + 0.2 * math.sin(frame * (0.08 + 0.05 * wind) + x * 1.3 + y))
                    else:
                        water = mix(water, self.lit(ICE), min(1.0, self.ice) if y == math.floor(surface) else 0.3)
                    canvas[y * W + x] = mix(canvas[y * W + x], water, fill)
            # Ground: grass or snow on top, soil getting darker with depth, a burrow inside
            for y in range(top, H):
                depth = y - top
                if depth == 0:
                    if self.wet(x):
                        color = mix(SOIL, (40, 30, 20), 0.5)
                    else:
                        color = mix(SOIL, grass_color, self.grass[x])
                        # Gusts roll through the grass
                        wave = math.sin(x * 1.1 * (1 if self.wind > 0 else -1) - frame * 0.06 * (0.5 + wind))
                        color = scale(color, 1 + 0.35 * min(1.0, wind) * self.grass[x] * wave * (1 - snow))
                        color = mix(color, SNOW, snow)
                        if x in self.logs:
                            color = mix(color, LOG, 0.4)
                    color = self.lit(color)
                else:
                    # No sunlight reaches under the ground: the cut through it stays the same, only dimmer at night
                    color = mix(SOIL, DEEP_SOIL, min(1.0, depth / 2.5))
                    if depth == 1 and x in self.burrows:
                        color = BURROW
                    if x in self.nests and y == self.nest_row(x):
                        color = mix(color, BURROW, 0.7)
                    color = scale(color, self.underground_light)
                if x in self.fire and depth == 0:
                    color = mix((255, 40, 0), (255, 210, 60), random.random() ** 0.7)
                canvas[y * W + x] = color
            # Tall grass shows above the ground, bending with the gusts
            if self.grass[x] > 0.5 and snow < 0.3 and not self.wet(x) and top > 0:
                wave = math.sin(x * 1.1 * (1 if self.wind > 0 else -1) - frame * 0.06 * (0.5 + wind))
                tall = (self.grass[x] - 0.5) * 2
                i = (top - 1) * W + x
                canvas[i] = mix(canvas[i], self.lit(grass_color), tall * (0.35 + 0.3 * wave * min(1.0, wind)))
            # Deep snow piles up on the land
            if self.snow > 1.0 and not self.wet(x) and top > 0:
                i = (top - 1) * W + x
                canvas[i] = mix(canvas[i], self.lit(SNOW), min(1.0, (self.snow - 1.0) / 0.5))
            # A fallen trunk lies on the ground; on damp nights it glows faintly with foxfire
            if x in self.logs and top > 0:
                i = (top - 1) * W + x
                rot = min(1.0, self.logs[x] / (TICKS_PER_YEAR / 8))
                canvas[i] = mix(canvas[i], self.lit(LOG), 0.8 * rot)
                if light == 0 and damp:
                    canvas[i] = add(canvas[i], FOXFIRE, 0.3 * rot * (0.7 + 0.3 * math.sin(frame * 0.02 + x)))
            if x in self.fire and top > 0 and random.random() < 0.15:
                self.motes.append(Mote("smoke", x, top - 1.5, self.wind * 0.02, -0.04, SMOKE, 40))

        # Animals: on the land they glide from column to column, in the burrow they sleep and breathe
        glide = (frame % FRAMES_PER_TICK + 1) / FRAMES_PER_TICK
        for animal in sorted(self.animals, key=lambda a: a.kind != "mouse"):  # mice first, the rest on top
            color = {"rabbit": RABBIT, "fox": FOX, "mouse": MOUSE}[animal.kind]
            top = self.top(animal.x)
            small = 0.65 if animal.kind == "mouse" else 1.0
            if animal.underground:
                y = self.nest_row(animal.x) if animal.kind == "mouse" else top + 1
                f = 0.55 + 0.15 * math.sin(frame * 0.12 + animal.breath)
                canvas[y * W + animal.x] = scale(color, f * self.underground_light)
                continue
            f = 0.6 + 0.1 * math.sin(frame * 0.12 + animal.breath) if animal.asleep else 1.0
            color = self.lit(scale(color, f))
            fx, fy = animal.x, top - 1
            if animal.moved == self.tick and glide < 1:
                px, ptop = animal.prev, self.top(animal.prev) - 1
                fx, fy = px + (animal.x - px) * glide, ptop + (fy - ptop) * glide
            blend(canvas, fx, fy, color, small)

        # Birds of prey
        for bird in self.raptors:
            x = bird.px + (bird.x - bird.px) * glide
            y = bird.py + (bird.y - bird.py) * glide
            if bird.kind == "owl":
                color = add(self.lit(OWL), OWL, 0.12)  # pale feathers show even in the dark
            else:
                color = self.lit(BUZZARD)
            flap = 1.0 if bird.state == "dive" else 0.75 + 0.25 * math.sin(frame * (0.3 if bird.kind == "owl" else 0.15))
            blend(canvas, x, y, color, 0.95 * flap)

        self.draw_mist(canvas, frame, horizon)
        self.draw_weather(canvas, frame, temperature, light, crown, season)

        if self.lightning:
            x, left = self.lightning
            # The bolt from the cloud down to what it hits, and the whole sky lights up
            for y in range(self.top(x)):
                bx = min(W - 1, max(0, x + (random.choice((-1, 0, 0, 1)) if y < self.top(x) - 1 else 0)))
                canvas[y * W + bx] = (255, 255, 240)
            if left > 2:
                canvas = [add(c, (200, 200, 230), 0.4) for c in canvas]
            self.lightning = (x, left - 1) if left > 1 else None
        return canvas

    def draw_murmuration(self, canvas, height):
        """On autumn and winter evenings starlings gather before they roost: a cloud of birds
        that swirls, stretches and folds across the sky, then drops into the trees."""
        if self.murmuration is None:
            dusk = -0.12 < height < 0.08 and self.sun_progress() > 0.5
            if (dusk and self.murmuration_day != self.day and self.season() in ("autumn", "winter")
                    and self.weather in ("clear", "drought")):
                self.murmuration_day = self.day
                if random.random() < 0.35:
                    side = random.choice((-1, 1))
                    start = -4.0 if side > 0 else W + 3.0
                    self.murmuration = {"t": 0, "side": side, "cx": start, "cy": 2.0,
                                        "birds": [[start + random.gauss(0, 1), 2 + random.gauss(0, 0.7),
                                                   0.1 * side, 0.0] for _ in range(32)]}
                    print("Event: a murmuration of starlings")
            return
        m = self.murmuration
        m["t"] += 1
        t, length = m["t"], FPS * 50
        if t < length:
            # The flock as a whole wanders over the sky in slow loops
            tx = W / 2 + m["side"] * 3.5 * math.sin(t * 0.011) + 1.5 * math.sin(t * 0.027)
            ty = 2.0 + 1.0 * math.sin(t * 0.019)
        else:
            roost = max(self.trees, key=lambda x: self.trees[x]) if self.trees else W / 2
            tx, ty = roost, self.top(int(roost)) - 2  # dropping into the trees to roost
        m["cx"] += (tx - m["cx"]) * 0.04
        m["cy"] += (ty - m["cy"]) * 0.04
        # Each bird keeps close to the flock and flies along with its neighbours; how tightly
        # they hold together keeps changing, so the cloud swells and shrinks
        hold = 0.006 + 0.005 * math.sin(t * 0.05)
        vx = sum(b[2] for b in m["birds"]) / len(m["birds"])
        vy = sum(b[3] for b in m["birds"]) / len(m["birds"])
        fade = min(1.0, (length + FPS * 6 - t) / (FPS * 4)) if t > length else 1.0
        color = (18, 14, 24)
        for b in m["birds"]:
            b[2] += (m["cx"] - b[0]) * hold + (vx - b[2]) * 0.06 + random.gauss(0, 0.01)
            b[3] += (m["cy"] - b[1]) * hold * 1.4 + (vy - b[3]) * 0.06 + random.gauss(0, 0.008)
            speed = math.hypot(b[2], b[3])
            if speed > 0.25:
                b[2], b[3] = b[2] * 0.25 / speed, b[3] * 0.25 / speed
            b[0] += b[2]
            b[1] += b[3]
            blend(canvas, b[0], b[1], color, 0.4 * fade)
        if fade <= 0:
            self.murmuration = None

    def draw_mist(self, canvas, frame, horizon):
        """The mist lies in the lowest part of the land, thickest at the bottom, slowly drifting.
        It takes the color of the light: pale grey in the night, pink and gold at sunrise."""
        if self.mist < 0.03:
            return
        low = H - min(round(h) for h in self.ground)  # top of the lowest ground
        depth = 0.8 + 2.4 * self.mist
        tint, strength, _, _ = self.light_now
        color = mix(scale((215, 220, 232), 0.5 + 0.5 * strength), horizon, 0.25)
        for y in range(max(0, int(low - depth)), H):
            for x in range(W):
                if y > self.top(x):
                    continue
                above = low - y + 0.5  # how far above the floor of the hollow
                density = self.mist * max(0.0, 1 - above / depth)
                if density <= 0:
                    continue
                drift = 0.75 + 0.25 * math.sin(frame * 0.02 + x * 0.7 + y * 1.3)
                i = y * W + x
                canvas[i] = mix(canvas[i], color, min(0.85, density * drift * (0.5 if y == self.top(x) else 0.9)))

    def draw_clouds(self, canvas, frame, light, horizon, overcast):
        """Clouds drift with the wind and take the colors of the sky: white by day, pink and
        orange at sunset, dark at night."""
        wanted = CLOUDS[self.weather]
        if len(self.clouds) < wanted and random.random() < 0.01:
            # A new cloud drifts in from upwind; when the weather turns, clouds are already about
            side = -3.0 if self.wind > 0 else W + 2.0
            if len(self.clouds) < wanted - 1:
                side = random.uniform(-2, W + 1)
            y = random.uniform(0, 2.4)
            size = random.uniform(1.5, 3.2) if self.weather in ("rain", "storm") else random.uniform(0.9, 2.0)
            self.clouds.append([side, y, size, 1.6 - 0.3 * y])  # higher clouds go faster
        storm = self.weather == "storm"
        # Rain and snow come from the whole grey sky, not just from the clouds drifting below it
        if self.weather in ("rain", "storm"):
            snowing = self.temperature() < 1
            for _ in range(2 if storm else 1):
                if random.random() < (0.35 if snowing else 0.7):
                    x = random.uniform(-1, W)
                    if snowing:
                        self.motes.append(Mote("flake", x, -0.5, self.wind * 0.03, random.uniform(0.04, 0.08), FLAKE, 200))
                    else:
                        self.motes.append(Mote("drop", x, -0.5, self.wind * 0.08, random.uniform(0.5, 0.7), RAIN, 20))
        base = (60, 62, 70) if storm else ((150, 155, 165) if self.weather == "rain" else (230, 232, 240))
        color = mix(scale(base, 0.08 + 0.92 * light), horizon, 0.35 * self.twilight(max(light, 0.001)) + 0.1)
        if light == 0:
            color = add(scale(base, 0.06), (60, 65, 80), 0.25 * self.moon())  # moonlit edges
        speed = 0.015 + 0.03 * abs(self.wind) * (2 if storm else 1)
        for cloud in self.clouds:
            cloud[0] += speed * cloud[3] * (1 if self.wind > 0 else -1)
            cx, cy, r = cloud[:3]
            for y in range(max(0, int(cy - 1)), min(H, int(cy + 2))):
                for x in range(max(0, int(cx - r)), min(W, int(cx + r) + 1)):
                    d = math.hypot((x - cx) / r, (y - cy) * 1.4)
                    if d < 1:
                        canvas[y * W + x] = mix(canvas[y * W + x], color, 0.85 * (1 - d * d))

        self.clouds = [c for c in self.clouds if -4 < c[0] < W + 3
                       and (len(self.clouds) <= wanted or random.random() > 0.002)]

    def draw_birds(self, canvas, light):
        if self.birds_due and light > 0.4 and self.weather in ("clear", "fog"):
            self.birds = [0, 1 if self.season() == "autumn" else -1]  # south in autumn, back in spring
            self.birds_due = False
            print("Event: migrating birds")
        if self.birds:
            self.birds[0] += 1
            lead = self.birds[0] / (FPS * 0.7) - 1
            for dx, dy in ((0, 0), (-1, -1), (-1, 1), (-2, -2), (-2, 2)):
                x = lead + dx
                x = W - 1 - x if self.birds[1] < 0 else x
                blend(canvas, x, 2 + dy * 0.6, self.lit((200, 200, 210)) if light < 0.3 else BIRD, 0.8)
            if lead > W + 3:
                self.birds = None

    def draw_flyers(self, canvas, frame, height, temperature):
        """Birds come by during the day and sometimes settle in a tree for a while; swallows hunt
        low over the land in the summer evening, bats at dusk; gnats dance in the low sun."""
        light = max(0.0, height)
        season = self.season()
        calm = self.weather in ("clear", "drought", "fog")
        warm = season in ("spring", "summer") and temperature > 12
        kinds = [f["kind"] for f in self.flyers]
        if calm and light > 0.25 and kinds.count("bird") < 2 and random.random() < 0.003:
            side = random.choice((0, 1))
            perch = random.choice(list(self.trees)) if self.trees and random.random() < 0.6 else None
            self.flyers.append({"kind": "bird", "x": -1.0 if side == 0 else W * 1.0, "y": random.uniform(0.5, 3),
                                "vx": 0.12 if side == 0 else -0.12, "perch": perch, "rest": 0, "t": 0})
        if (calm and warm and season == "summer" and 0 < light < 0.35 and kinds.count("swallow") < 2
                and random.random() < 0.004):
            self.flyers.append({"kind": "swallow", "x": random.choice((-1.0, W * 1.0)), "y": 4.0, "vx": 0.0, "t": 0})
        if calm and warm and -0.3 < height < 0 and kinds.count("bat") < 2 and random.random() < 0.004:
            self.flyers.append({"kind": "bat", "x": random.uniform(1, W - 2), "y": random.uniform(1, 3), "vx": 0.0, "t": 0})
        if warm and calm and light > 0.05 and kinds.count("gnat") < 5 and random.random() < 0.02:
            x = random.randrange(W)
            self.flyers.append({"kind": "gnat", "x": x, "y": self.top(x) - random.uniform(1.5, 3), "vx": 0.0, "t": 0})

        for f in self.flyers:
            f["t"] += 1
            kind = f["kind"]
            if kind == "bird":
                if f["perch"] is not None and f["perch"] in self.trees and f["rest"] >= 0:
                    tx, ty = f["perch"], self.top(f["perch"]) - (3 if self.trees[f["perch"]] >= 2 * TICKS_PER_YEAR else 2)
                    dx, dy = tx - f["x"], ty - f["y"]
                    if abs(dx) + abs(dy) < 0.2:
                        f["rest"] += 1  # sitting in the tree
                        if f["rest"] > FPS * random.uniform(10, 40) or not calm:
                            f["rest"] = -1  # off again
                            f["vx"] = random.choice((-0.12, 0.12))
                    else:
                        f["x"] += max(-0.12, min(0.12, dx * 0.08))
                        f["y"] += max(-0.08, min(0.08, dy * 0.08))
                else:
                    f["x"] += f["vx"]
                    f["y"] += 0.04 * math.sin(f["t"] * 0.3) - (0.02 if f["rest"] < 0 else 0)
                resting = f["rest"] > 0
                # Birds spread seeds: from berries eaten while sitting in a tree, or an acorn buried
                # on the way. Where one lands in good grass, a tree can come up
                if random.random() < (1 / (FPS * 60) if resting else 1 / (FPS * 200)):
                    spot = min(W - 1, max(0, int(round(f["x"])) + (random.choice((-1, 1)) if resting else 0)))
                    if spot not in self.trees and spot not in self.burrows and not self.wet(spot) and self.grass[spot] > 0.5:
                        self.trees[spot] = 0
                        print("Event: a bird sows a tree")
                flap = 1.0 if resting else 0.7 + 0.3 * math.sin(f["t"] * 0.9)
                color = scale(BIRD, 1) if light > 0.3 else self.lit((80, 75, 70))
                blend(canvas, f["x"], f["y"], color, 0.9 * flap)
                f["done"] = not (-2 < f["x"] < W + 1) or f["y"] < -1
            elif kind == "swallow":
                # Fast, low swoops back and forth
                f["x"] += 0.25 * math.cos(f["t"] * 0.05)
                f["y"] = 4 + 1.2 * math.sin(f["t"] * 0.13)
                column = min(W - 1, max(0, int(round(f["x"]))))
                f["y"] = min(f["y"], self.top(column) - 1.2)
                blend(canvas, f["x"], f["y"], self.lit((25, 25, 40)), 0.85)
                f["done"] = f["t"] > FPS * 40 or light == 0
            elif kind == "bat":
                f["x"] += random.uniform(-0.2, 0.2) + 0.05 * math.sin(f["t"] * 0.2)
                f["y"] += random.uniform(-0.12, 0.12)
                f["x"] = min(W - 1.0, max(0.0, f["x"]))
                f["y"] = min(4.0, max(0.5, f["y"]))
                blend(canvas, f["x"], f["y"], (8, 6, 10), 0.8)
                f["done"] = f["t"] > FPS * 30 or height < -0.4
            else:
                # Midges dance in a little cloud; in the low sun they catch the light
                f["x"] += random.uniform(-0.08, 0.08)
                f["y"] += random.uniform(-0.08, 0.08)
                glow = 0.15 + 0.5 * self.twilight(light)
                blend(canvas, f["x"], f["y"], GNAT, glow * (0.5 + 0.5 * random.random()), glow=True)
                f["done"] = f["t"] > FPS * 20 or light == 0
        self.flyers = [f for f in self.flyers if not f.get("done")]

    def draw_weather(self, canvas, frame, temperature, light, crown, season):
        """Rain, snow, falling leaves, fireflies and smoke, each moving through the air."""
        if season == "autumn" and self.trees and random.random() < min(0.15, 0.03 * len(self.trees) * (0.5 + abs(self.wind))):
            x = random.choice(list(self.trees))
            if self.trees[x] >= TICKS_PER_YEAR:
                self.motes.append(Mote("leaf", x, self.top(x) - 3, self.wind * 0.06, 0.05,
                                       mix(crown, (230, 150, 20), random.random()), 60))
        fireflies = sum(1 for m in self.motes if m.kind == "firefly")
        wanted = 0
        if light == 0 and self.weather in ("clear", "drought") and season == "summer":
            wanted = int(min(5, max(0, temperature - 14)) * min(1.0, sum(self.grass) / 5))
        if fireflies < wanted and random.random() < 0.02:
            x = random.randrange(W)
            self.motes.append(Mote("firefly", x, self.top(x) - random.uniform(1, 2.5), 0.0, 0.0, FIREFLY,
                                   FPS * random.randint(60, 200)))
        for mote in self.motes:
            mote.frame += 1
            if mote.kind == "firefly":
                mote.vx = max(-0.03, min(0.03, mote.vx + random.gauss(0, 0.004)))
                mote.vy = max(-0.02, min(0.02, mote.vy + random.gauss(0, 0.003)))
                mote.x = min(W - 1.0, max(0.0, mote.x + mote.vx))
                ground = self.top(int(round(mote.x))) - 1
                mote.y = min(ground, max(ground - 3.0, mote.y + mote.vy))
                if light > 0 or fireflies > wanted:
                    mote.frames = min(mote.frames, mote.frame + 8)
                flash = (math.sin(mote.frame * 0.13 + mote.phase) - 0.7) / 0.3
                if flash > 0:
                    blend(canvas, mote.x, mote.y, FIREFLY, 0.9 * flash * mote.fade(), glow=True)
                continue
            if mote.kind == "flake":
                mote.x += mote.vx + 0.02 * math.sin(mote.frame * 0.15 + mote.phase)
            elif mote.kind == "leaf":
                mote.x += mote.vx + 0.04 * math.sin(mote.frame * 0.25 + mote.phase)
            else:
                mote.x += mote.vx
            mote.y += mote.vy
            column = int(round(mote.x))
            if 0 <= column < W:
                land = H - max(self.level, round(self.ground[column])) if self.wet(column) else self.top(column)
                if mote.kind != "smoke" and mote.y >= land - 0.5:
                    mote.frames = min(mote.frames, mote.frame + (1 if mote.kind == "drop" else 6))
                    mote.vy = 0
            color = mote.color if mote.kind == "smoke" else self.lit(mote.color)
            alpha = {"drop": 0.6, "flake": 0.85, "leaf": 0.8, "smoke": 0.35}[mote.kind]
            blend(canvas, mote.x, mote.y, color, alpha * mote.fade())
            if mote.kind == "drop":
                blend(canvas, mote.x - mote.vx, mote.y - mote.vy, color, 0.3 * mote.fade())  # a streak
        self.motes = [m for m in self.motes if m.frame < m.frames and -2 < m.x < W + 1 and -2 < m.y < H + 1]


def show(canvas):
    for i, color in enumerate(canvas):
        pixels[i] = color
    pixels.show()


world = World()
print(f"Start: {world.season()}, {world.temperature():.0f}°")
frame = 0
try:
    while True:
        if frame % FRAMES_PER_TICK == 0:
            world.step()
        show(world.render(frame))
        frame += 1
        time.sleep(1 / FPS)
except KeyboardInterrupt:
    pixels.fill((0, 0, 0))
    pixels.show()
