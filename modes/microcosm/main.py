#!/usr/bin/env python3
"""
Microcosm: a tiny landscape that lives on its own.

Everything follows from simple, real rules. Nothing is scripted and nothing is
rescued: whatever disappears can come back, but only when the conditions allow it.

- Temperature drives the year: warm summers, cold winters, warmer days than nights,
  and warm and cold spells that drift over days. Days are long in summer and short
  in winter. The sun rises on the left and sets on the right.
- The land has hills and hollows, different in every world. Rain and melting snow
  fill the lowest ground with water, warmth and sun evaporate it. Ponds slowly silt
  up and the water moves on to the next hollow. Rain washes soil downhill, fallen
  trees leave pits, digging rabbits lower the ground: new hollows keep forming.
- Below freezing, rain falls as snow and stays until it melts; long frost freezes
  the water, thick enough to walk on.
- Grass grows when it is warm enough, with light and water, and spreads to bare
  ground. Where it stays lush, trees take root; woods spread, shade the grass, grow
  old, burn or drown. Rabbits nibble the saplings, and under dense woods nothing new
  can sprout. In spring, flowers bloom under the trees before the leaves come out;
  in autumn, fruit falls. The dead feed the soil.
- Rabbits graze, breed when the days are long (it takes two), dig burrows and hide;
  in hard times they gnaw bark from the trees.
  Foxes hunt, mostly at night, and rest when full. Animals wander in from outside
  when there is food for them; seeds blow in where the land is green.
- Lightning starts fires, dry weather makes them spread. On warm days with plenty of
  grass, locusts come for it. Mushrooms come up under trees in mild wet weather.
  Birds migrate in spring and autumn. Rain followed by sun can leave a rainbow
  opposite the sun, and on clear nights a shooting star may cross the sky. Moonlight
  glints on the water, mist rises from it after a cold clear night, and frost makes
  the grass sparkle at dawn. Wind ripples through the grass and on sunny days cloud
  shadows drift across the land.
- Nights are dark, lighter under a full moon; the moon waxes and wanes over a month,
  and foxes hunt best by its light. Still water mirrors the sky: a sunset glow, stars,
  the moon. A low sun brings out the hills, and hollows stay moist and darker green.
- What the wind carries can be seen: snowflakes drift down, seed fluff blows off the
  lush grass and starts new grass where it lands on bare ground, autumn leaves blow
  from the trees and feed the soil. On warm summer nights fireflies wander over the
  grass. Animals tread down the grass where they walk, so paths appear, and leave
  footprints in the snow until fresh snow fills them. A fallen tree lies rotting for
  half a year, and on damp nights its wood glows faintly with foxfire.
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
settings = config.get("modes", {}).get("microcosm", {})

pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)

W = H = 8
FPS = 12
FRAMES_PER_TICK = 3  # the world itself moves 4 times per second
TICKS_PER_SECOND = FPS // FRAMES_PER_TICK
# A day of 20 minutes, seasons of 8 hours: a year of 32 hours doesn't fit a day on the clock,
# so the seasons come at a different time every day
DAY_MINUTES = settings.get("day_minutes", 20)
SEASON_MINUTES = settings.get("season_minutes", 480)
TICKS_PER_DAY = int(DAY_MINUTES * 60 * TICKS_PER_SECOND)
TICKS_PER_YEAR = int(SEASON_MINUTES * 4 * 60 * TICKS_PER_SECOND)
SAPLING = TICKS_PER_YEAR // 8  # a young tree, small enough to be nibbled away

SEASONS = ["spring", "summer", "autumn", "winter"]
SEASON_GRASS = {"spring": (40, 190, 30), "summer": (60, 165, 15), "autumn": (135, 85, 20), "winter": (70, 95, 40)}
SEASON_TREE = {"spring": (20, 120, 30), "summer": (10, 90, 20), "autumn": (190, 70, 5), "winter": (60, 40, 25)}
WEATHER_CHANCES = {
    # how likely each weather is to come next, per season
    "spring": {"clear": 4, "rain": 4, "storm": 1, "drought": 0, "fog": 2},
    "summer": {"clear": 5, "rain": 2, "storm": 2, "drought": 3, "fog": 0},
    "autumn": {"clear": 3, "rain": 4, "storm": 2, "drought": 0, "fog": 3},
    "winter": {"clear": 4, "rain": 3, "storm": 0, "drought": 0, "fog": 3},
}
WEATHER_DAYS = {"clear": 0.6, "rain": 0.3, "storm": 0.15, "drought": 0.5, "fog": 0.2}
WEATHER_WATER = {"clear": 1.0, "rain": 2.5, "storm": 2.0, "drought": -0.4, "fog": 0.8}  # effect on grass
PRECIPITATION = {"rain": 6, "storm": 10}  # cells of water per day
EVAPORATION = {"drought": 3.0, "clear": 1.0, "fog": 0.3, "rain": 0.0, "storm": 0.0}

SOIL = (35, 22, 8)
MUD = (55, 35, 12)
ASH = (22, 18, 16)
WATER = (10, 60, 170)
ICE = (140, 185, 230)
BURROW = (70, 35, 10)
RABBIT = (150, 130, 100)  # grey-brown like a wild rabbit; pure white outshines everything on real LEDs
FOX = (145, 45, 10)  # rust brown, steady; fire is bright and flickers
RAIN = (90, 140, 255)
SNOW = (160, 172, 200)  # a snow blanket, soft blue-white; full white would outshine everything
FLAKE = (240, 245, 255)  # falling snow catches the light
FLOWERS = [(255, 70, 190), (190, 110, 255), (255, 200, 60)]
FIREFLY = (200, 255, 60)
WOOD_FLOWERS = [(240, 240, 255), (150, 120, 255), (255, 230, 90)]  # anemones, bluebells, celandine
FRUIT = (200, 30, 40)
FROST = (200, 215, 235)
MIST = (150, 160, 175)
MOONLIGHT = (120, 140, 190)
MUSHROOM = (230, 40, 30)
LOCUST = (190, 210, 40)
BIRD = (215, 215, 225)
DEADWOOD = (80, 52, 28)
FOXFIRE = (40, 210, 120)  # the faint green glow of fungi in rotting wood
STARLIGHT = (170, 180, 230)
SKY_GLOW = (255, 120, 60)  # a sunset sky mirrored in the water
SEED = (235, 230, 200)  # grass seed and fluff on the wind
TRACK = (70, 90, 140)  # the blue shadow of a footprint in the snow
MOON_DAYS = 29.5  # from full moon to full moon
RAINBOW = [(255, 0, 0), (255, 120, 0), (255, 230, 0), (0, 200, 0), (0, 90, 255), (140, 0, 220)]
SUN_SWEEP = 0.012  # part of a day between sunrise on the left and on the right column
# Flowers, mushrooms and fruit: off for now to keep the landscape calm (turn on with "plants": true)
PLANTS = settings.get("plants", False)

CELLS = [(x, y) for y in range(H) for x in range(W)]  # row by row, like the LEDs


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def scale(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def add(c1, c2, f):
    """Light of its own adds to what is already there."""
    return tuple(min(255, int(a + b * f)) for a, b in zip(c1, c2))


def blend(canvas, fx, fy, color, alpha, glow=False):
    """Draw something that sits between cells: its light spreads over the cells around it,
    so it glides instead of jumping from cell to cell."""
    x0, y0 = math.floor(fx), math.floor(fy)
    tx, ty = fx - x0, fy - y0
    for x, y, w in ((x0, y0, (1 - tx) * (1 - ty)), (x0 + 1, y0, tx * (1 - ty)),
                    (x0, y0 + 1, (1 - tx) * ty), (x0 + 1, y0 + 1, tx * ty)):
        if w > 0.01 and 0 <= x < W and 0 <= y < H:
            i = y * W + x
            canvas[i] = add(canvas[i], color, alpha * w) if glow else mix(canvas[i], color, alpha * w)


def per_day(amount):
    """Something that happens at a rate of `amount` per day, as a step per tick."""
    return amount / TICKS_PER_DAY


def per_year(amount):
    return amount / TICKS_PER_YEAR


def neighbors(x, y):
    return [(x + dx, y + dy) for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1))
            if 0 <= x + dx < W and 0 <= y + dy < H]


def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class Animal:
    def __init__(self, kind, pos, energy):
        self.kind = kind
        self.pos = pos
        self.energy = energy
        self.age = 0
        # In the wild a rabbit lives about a year, a fox two to four
        years = random.uniform(0.5, 1.0) if kind == "rabbit" else random.uniform(2, 4)
        self.lifespan = int(TICKS_PER_YEAR * years)
        self.flash = 6  # newborns glow for a moment
        self.asleep = False
        self.next_litter = 0  # age at which it can have young again
        self.rest_until = 0  # a resting animal stays down for a while, it doesn't doze on and off
        self.alert_until = 0  # after a scare, a rabbit stays awake and watchful for a while
        self.leaving = False  # on its way out of this piece of land
        self.prev = pos  # where it came from, to glide over instead of jumping
        self.moved = -1  # tick it last moved
        self.breath = random.uniform(0, 2 * math.pi)  # a sleeping animal breathes at its own pace
        # A body can only store so much, young need time to grow up before they breed: a rabbit
        # a few months, a fox most of a year. Rabbits can have a litter every month or so,
        # foxes have one a year
        self.max_energy = 2.0 if kind == "rabbit" else 3.0
        self.adult_age = int(TICKS_PER_YEAR * (0.3 if kind == "rabbit" else 0.8))
        self.pregnancy = int(TICKS_PER_YEAR * (0.08 if kind == "rabbit" else 0.5))

    def can_breed(self):
        return self.age > self.adult_age and self.age > self.next_litter

    def is_adult(self):
        return self.age > self.adult_age


class Mote:
    """Something small drifting over the land: a snowflake, a seed, a leaf, a firefly."""

    def __init__(self, kind, x, y, vx, vy, color, frames):
        self.kind = kind
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.frame = 0
        self.frames = frames
        self.phase = random.uniform(0, 2 * math.pi)

    def fade(self):
        return min(1.0, self.frame / 6, (self.frames - self.frame) / 8)


class Effect:
    """Something passing over the landscape for a while, drawn on top of it."""

    def __init__(self, frames):
        self.frame = 0
        self.frames = frames

    @property
    def done(self):
        return self.frame >= self.frames

    def fade(self):
        """0 -> 1 -> 0 over the effect's lifetime."""
        return min(1.0, self.frame / 12, (self.frames - self.frame) / 12)

    def draw(self, canvas, world):
        self.frame += 1


class Rainbow(Effect):
    """Always opposite the sun: on the right in the morning, on the left in the evening."""

    def __init__(self, morning):
        super().__init__(FPS * 25)
        self.center = (random.uniform(6, 9) if morning else random.uniform(-2, 1), random.uniform(8, 10))

    def draw(self, canvas, world):
        super().draw(canvas, world)
        cx, cy = self.center
        for y in range(H):
            for x in range(W):
                band = int(math.hypot(x - cx, y - cy) - 4.5)
                if 0 <= band < len(RAINBOW):
                    i = y * W + x
                    canvas[i] = mix(canvas[i], RAINBOW[band], 0.55 * self.fade())


class ShootingStar(Effect):
    def __init__(self):
        super().__init__(10)
        self.x, self.y = random.uniform(0, 4), random.uniform(0, 2)
        self.dx, self.dy = random.uniform(0.6, 0.9), random.uniform(0.2, 0.4)

    def draw(self, canvas, world):
        super().draw(canvas, world)
        for trail in range(3):
            x = int(self.x + self.dx * (self.frame - trail))
            y = int(self.y + self.dy * (self.frame - trail))
            if 0 <= x < W and 0 <= y < H:
                canvas[y * W + x] = mix(canvas[y * W + x], (255, 255, 230), 1 - trail * 0.35)


class Birds(Effect):
    """A V of migrating birds crossing the sky."""

    def __init__(self, leftwards):
        super().__init__(FPS * 6)
        self.leftwards = leftwards
        self.y = random.randint(1, 5)
        self.flock = [(0, 0), (-1, -1), (-1, 1), (-2, -2), (-2, 2)][:random.randint(3, 5)]

    def draw(self, canvas, world):
        super().draw(canvas, world)
        lead = self.frame / (FPS * 0.6) - 1
        for dx, dy in self.flock:
            x = int(lead + dx)
            x = W - 1 - x if self.leftwards else x
            y = self.y + dy
            if 0 <= x < W and 0 <= y < H:
                canvas[y * W + x] = mix(canvas[y * W + x], BIRD, 0.8)


class Locusts(Effect):
    """A swarm drifting across the land, eating the grass where it passes."""

    def __init__(self):
        super().__init__(FPS * 40)
        self.cx, self.cy = -2.0, random.uniform(2, 5)
        self.swarm = [(random.gauss(0, 1.2), random.gauss(0, 1.0)) for _ in range(12)]

    def draw(self, canvas, world):
        super().draw(canvas, world)
        self.cx += (W + 4) / self.frames
        self.cy += random.uniform(-0.05, 0.05)
        for dx, dy in self.swarm:
            x, y = int(self.cx + dx + random.uniform(-0.5, 0.5)), int(self.cy + dy + random.uniform(-0.5, 0.5))
            if 0 <= x < W and 0 <= y < H:
                canvas[y * W + x] = mix(canvas[y * W + x], LOCUST, 0.8)
                world.grass[(x, y)] = max(0.0, world.grass[(x, y)] - 0.01)


class World:
    def __init__(self):
        # Every world starts differently: terrain, season, water, trees, burrows and animals
        self.tick = random.randrange(TICKS_PER_YEAR)
        if settings.get("start_season") in SEASONS:
            quarter = TICKS_PER_YEAR // 4
            self.tick = SEASONS.index(settings["start_season"]) * quarter + random.randrange(quarter // 4)
        # Start mid-morning, with the sun up, so the world is visible straight away
        self.tick -= self.tick % TICKS_PER_DAY
        sunrise = 0.5 - self.day_length() / 2
        self.tick += int(TICKS_PER_DAY * (sunrise + random.uniform(0.08, 0.15)))
        self.day = 0
        self.spell = random.gauss(0, 2)  # warm or cold spell, drifts over days
        self.height = self.make_terrain()
        self.volume = random.uniform(0, 5)  # how many cells' worth of water there is
        self.water = set()
        self.ice = 0.0  # 0 open water, 1 thick ice
        self.snow = 0.0  # 0 none, 1 a thick blanket
        self.mud = {}  # pos -> ticks left; ground that was under water, wet and fertile
        self.fertile = {}  # pos -> ticks left; where something died and feeds the soil
        self.grass = {pos: random.uniform(0.1, 0.9) for pos in CELLS}
        self.trees = {}  # pos -> age in ticks
        self.burrows = {}  # pos -> tick last used
        self.fire = {}  # pos -> ticks left burning
        self.flowers = {}  # pos -> (color, ticks left)
        self.mushrooms = {}  # pos -> ticks left
        self.wood_flowers = {}  # pos -> (color, ticks left), spring flowers under trees
        self.fruit = {}  # pos -> ticks left, fallen autumn fruit under trees
        self.frost = 0.0  # rime on the grass after a freezing clear night
        self.tracks = {}  # pos -> ticks left; footprints in the snow
        self.deadwood = {}  # pos -> ticks left; a fallen tree rotting away
        self.motes = []  # snowflakes, seeds, leaves and fireflies drifting about
        self.moon_start = random.uniform(0, MOON_DAYS)
        self.night_floor = 0.45
        self.mist = 0.0  # mist over the water after a cold clear night
        self.animals = []
        self.weather = "clear"
        self.update_water()
        for pos in random.sample(self.land(), random.randint(0, 4)):
            self.trees[pos] = random.randrange(TICKS_PER_YEAR * 2)
        for pos in random.sample([p for p in self.land() if p not in self.trees], random.randint(1, 3)):
            self.burrows[pos] = self.tick
        self.lush = {pos: 0 for pos in CELLS}  # ticks a cell has been lush, for trees to sprout
        self.dryness = 0.0  # builds up in dry weather, makes fire spread
        self.flashes = {}  # pos -> (color, frames left)
        self.drops = []  # falling rain or snow [x, y]
        self.effects = []  # rainbows, birds, ... passing over
        self.birds_due = False
        self.weather_left = TICKS_PER_DAY // 2
        self.lightning = 0
        self.wind = random.uniform(0, 2 * math.pi)  # direction the wind blows to, drifts slowly
        self.clouds = [[random.uniform(0, W), random.uniform(0, H), random.uniform(1.5, 3)] for _ in range(3)]
        for _ in range(random.randint(2, 6)):
            self.spawn("rabbit", 1.0)
        for _ in range(random.randint(0, 1)):
            self.spawn("fox", 1.5)

    def make_terrain(self):
        """Gentle hills and hollows: a few random bumps and dips, smoothed out."""
        bumps = [(random.uniform(-1, W), random.uniform(-1, H), random.uniform(-1, 1), random.uniform(1.5, 4))
                 for _ in range(random.randint(3, 6))]
        height = {}
        for x, y in CELLS:
            h = sum(a * math.exp(-((x - bx) ** 2 + (y - by) ** 2) / (2 * r * r)) for bx, by, a, r in bumps)
            height[(x, y)] = h + random.uniform(-0.05, 0.05)
        low, high = min(height.values()), max(height.values())
        return {p: (h - low) / (high - low) for p, h in height.items()}

    def land(self):
        return [p for p in CELLS if p not in self.water]

    # Time and climate

    def year_phase(self):
        return (self.tick % TICKS_PER_YEAR) / TICKS_PER_YEAR

    def season(self):
        return SEASONS[int(self.year_phase() * 4)]

    def seasonal(self, table):
        """A value from a per-season table, blending into the next season towards its end."""
        position = self.year_phase() * 4
        index, progress = int(position), position % 1
        current, upcoming = table[SEASONS[index]], table[SEASONS[(index + 1) % 4]]
        blend = max(0.0, (progress - 0.75) / 0.25)
        return mix(current, upcoming, blend)

    def summer_ness(self):
        """Warmth of the year: 1 at midsummer, -1 at midwinter (lagging behind the sun)."""
        return math.cos(2 * math.pi * (self.year_phase() - 0.375))

    def day_length(self):
        """Part of the day the sun is up: equal at the start of spring and autumn,
        longest at the start of summer, shortest at the start of winter."""
        return 0.5 + 0.17 * math.cos(2 * math.pi * (self.year_phase() - 0.25))

    def light(self, x=3.5):
        """Height of the sun, 0 (down) to 1. The sun reaches the left side first."""
        t = ((self.tick % TICKS_PER_DAY) / TICKS_PER_DAY + (3.5 - x) * SUN_SWEEP) % 1.0
        length = self.day_length()
        sunrise = 0.5 - length / 2
        if not sunrise < t < sunrise + length:
            return 0.0
        return math.sin(math.pi * (t - sunrise) / length)

    def moon(self):
        """How full the moon is, 0 (new) to 1 (full)."""
        days = self.tick / TICKS_PER_DAY + self.moon_start
        return 0.5 - 0.5 * math.cos(2 * math.pi * days / MOON_DAYS)

    def moonlight(self):
        """How much moonlight reaches the land: a full moon on a clear night, little behind clouds."""
        if self.light() > 0:
            return 0.0
        return self.moon() * {"clear": 1.0, "drought": 1.0, "fog": 0.3, "rain": 0.15, "storm": 0.1}[self.weather]

    def sun_direction(self):
        """Where the sun stands, seen from the land: on the left in the morning, low in the
        south (the bottom) at noon, on the right in the evening."""
        t = (self.tick % TICKS_PER_DAY) / TICKS_PER_DAY
        length = self.day_length()
        progress = min(1.0, max(0.0, (t - (0.5 - length / 2)) / length))
        return -math.cos(math.pi * progress), math.sin(math.pi * progress)

    def relief(self, x, y, sun):
        """Slopes facing the sun catch more light than slopes facing away, most when it is low."""
        h = self.height
        gx = h[(min(x + 1, W - 1), y)] - h[(max(x - 1, 0), y)]
        gy = h[(x, min(y + 1, H - 1))] - h[(x, max(y - 1, 0))]
        return max(0.6, min(1.4, 1 - 1.6 * (gx * sun[0] + gy * sun[1])))

    def morning(self):
        return (self.tick % TICKS_PER_DAY) / TICKS_PER_DAY < 0.5

    def twilight(self, light):
        """How much of a sunrise or sunset glow there is, 0-1: a golden hour that warms up
        as the sun gets low, strongest just before it sets."""
        if light <= 0:
            return 0.0
        return light / 0.15 if light < 0.15 else max(0.0, 1 - (light - 0.15) / 0.35)

    def lit(self, color, x, y, light, sunny):
        """A color as the sun shows it: darker and cooler at night, warmer at sunrise and sunset.
        The light tints each color rather than painting over it, so things stay apart in the dusk."""
        night = 1 - light
        glow = self.twilight(light) if self.weather != "fog" else 0.0
        color = (color[0] * (1 - 0.6 * night) * (1 + 1.2 * glow),
                 color[1] * (1 - 0.45 * night) * (1 + 0.25 * glow),
                 color[2] * (1 - 0.1 * night) * (1 - 0.5 * glow))
        if sunny and light > 0:
            color = scale(color, 1 - self.cloud_shade(x, y) * light)
        # At night only the moon lights the land: you see a little more under a full moon
        floor = self.night_floor
        return scale(color, floor + (1 - floor) * light)

    def is_night(self):
        return self.light() < 0.15

    def temperature(self):
        """In degrees: the season, day and night, the weather and the current warm or cold spell."""
        t = 10 + 10 * self.summer_ness() + self.spell
        light = self.light()
        if self.weather in ("clear", "drought"):
            t += 6 * light - 3  # sunny days warm up, clear nights cool down
        else:
            t += 2 * light - 1
        if self.weather == "drought":
            t += 4
        return t

    # Helpers

    def occupant(self, pos):
        for animal in self.animals:
            if animal.pos == pos:
                return animal
        return None

    def walkable(self, pos, kind="rabbit"):
        if kind == "fox" and pos in self.burrows:
            return False
        if pos in self.water and self.ice < 0.8:
            return False
        return pos not in self.fire

    def spawn(self, kind, energy, edge=False):
        taken = {a.pos for a in self.animals}
        cells = [p for p in CELLS if self.walkable(p, kind) and p not in taken and p not in self.water]
        if edge:
            cells = [p for p in cells if p[0] in (0, W - 1) or p[1] in (0, H - 1)]
        if cells:
            # Animals that settle here are grown ones, not newborns
            animal = Animal(kind, random.choice(cells), energy)
            animal.age = random.randint(animal.adult_age, (animal.adult_age + animal.lifespan) // 2)
            self.animals.append(animal)
            return True
        return False

    def count(self, kind):
        return sum(1 for a in self.animals if a.kind == kind)

    def move(self, animal, pos):
        """An animal steps to a new cell: it treads down the grass a little (where animals keep
        walking, paths appear) and leaves footprints in the snow."""
        if pos == animal.pos:
            return
        if self.snow > 0.3:
            self.tracks[animal.pos] = TICKS_PER_DAY // 2
        self.grass[pos] = max(0.0, self.grass[pos] - 0.02)
        animal.prev, animal.pos, animal.moved = animal.pos, pos, self.tick

    def kill(self, animal, color):
        if animal in self.animals:
            self.animals.remove(animal)
            self.flashes[animal.pos] = (color, 6)
            self.fertile[animal.pos] = TICKS_PER_DAY * 2  # the dead feed the soil

    # Simulation

    def step(self):
        self.tick += 1
        if self.tick % TICKS_PER_DAY == 0:
            self.day += 1
            print(f"Day {self.day} ({self.season()}, {self.temperature():.0f}°): {self.count('rabbit')} rabbits, "
                  f"{self.count('fox')} foxes, {len(self.trees)} trees, {len(self.water)} water, "
                  f"{len(self.burrows)} burrows, snow {self.snow:.1f}, {self.weather}")
        if self.tick % (TICKS_PER_YEAR // 4) == 0 and self.season() in ("spring", "autumn"):
            self.birds_due = True

        # Warm and cold spells come and go over a couple of days
        self.spell += -self.spell / (TICKS_PER_DAY * 1.5) + random.gauss(0, 3.4 / math.sqrt(TICKS_PER_DAY))

        self.wind += random.gauss(0, 0.01)
        self.update_weather()
        self.update_water()
        self.update_land()
        self.grow()
        self.spread_fire()
        self.change_trees()
        for animal in random.sample(self.animals, len(self.animals)):
            if animal in self.animals:
                (self.rabbit if animal.kind == "rabbit" else self.fox)(animal)
        self.arrivals()
        self.nature()

    def update_weather(self):
        self.weather_left -= 1
        if self.weather_left <= 0:
            was_raining = self.weather in ("rain", "storm")
            if self.weather == "drought":
                self.weather = random.choice(("rain", "rain", "storm"))  # droughts end with rain or thunder
            else:
                chances = dict(WEATHER_CHANCES[self.season()])
                if self.temperature() < 15:
                    chances["drought"] = 0  # droughts need heat
                options = [w for w in chances if w != self.weather and chances[w]]
                self.weather = random.choices(options, [chances[w] for w in options])[0]
            self.weather_left = int(TICKS_PER_DAY * WEATHER_DAYS[self.weather] * random.uniform(0.6, 1.5))
            print(f"Weather: {self.weather}")
            if was_raining and self.weather == "clear" and self.light() > 0.3 and self.temperature() > 2:
                self.effects.append(Rainbow(self.morning()))  # sun right after rain
                print("Event: rainbow")

        temperature = self.temperature()
        if self.weather in ("drought", "clear") and temperature > 18:
            self.dryness = min(1.0, self.dryness + per_day(0.7))
        elif self.weather in ("rain", "storm"):
            self.dryness = max(0.0, self.dryness - per_day(4.3))
            for pos in list(self.fire):
                if random.random() < 0.3:
                    del self.fire[pos]

        if self.weather == "storm" and random.random() < per_day(22):
            self.lightning = 3
            # Most lightning stays in the clouds or comes down somewhere else; now and then it
            # hits this piece of land, and then it goes for the tallest things: trees if there are any
            if random.random() < 0.1:
                self.strike()

    def strike(self):
        strike = random.choice(list(self.trees)) if self.trees and random.random() < 0.7 else random.choice(CELLS)
        victim = self.occupant(strike)
        if victim and random.random() < 0.2:
            self.kill(victim, (255, 255, 255))
        fuel = 1.0 if strike in self.trees else self.grass[strike]
        if strike not in self.water and self.snow < 0.3 and random.random() < fuel * (0.3 + self.dryness):
            self.fire[strike] = 12 if strike in self.trees else 8
            print("Event: lightning starts a fire")

    def update_water(self):
        """Water fills the lowest ground. Rain and snowmelt add to it, warmth and sun take it away."""
        temperature = self.temperature()
        falling = per_day(PRECIPITATION.get(self.weather, 0))
        if temperature < 1:
            self.snow = min(1.0, self.snow + falling * 0.5)  # it snows
        else:
            self.volume += falling
        if temperature > 1 and self.snow > 0:
            melt = min(self.snow, per_day(0.43) * (temperature - 1) * (0.5 + self.light()))
            self.snow -= melt
            self.volume += melt * 8  # meltwater runs into the hollows
        if temperature > 0 and self.ice < 0.5:
            heat = EVAPORATION[self.weather] * max(0.0, temperature) / 12 * (0.3 + self.light())
            self.volume -= per_day(0.26) * heat * (2 + len(self.water))
        # Water that reaches the edge of the land slowly runs off, like a stream out of the pond
        edge = sum(1 for x, y in self.water if x in (0, W - 1) or y in (0, H - 1))
        self.volume -= per_day(0.43) * edge
        self.volume = max(0.0, min(float(len(CELLS) // 4), self.volume))
        freeze = per_day(0.72) if temperature < 0 else per_day(2.9)
        self.ice = max(0.0, min(1.0, self.ice - freeze * temperature))

        # The shoreline only moves for a real change: a whole cell more or less water, or dry
        # ground that has become clearly lower than the water's edge (no flickering back and forth)
        before = len(self.water)
        dry = [p for p in CELLS if p not in self.water]
        if self.volume >= len(self.water) + 1 and dry:
            self.flood(min(dry, key=lambda p: self.height[p]))
        elif self.volume < len(self.water) - 0.3:
            self.drain(max(self.water, key=lambda p: self.height[p]))
        elif self.water and dry:
            low = min(dry, key=lambda p: self.height[p])
            high = max(self.water, key=lambda p: self.height[p])
            if self.height[low] < self.height[high] - 0.03:
                self.drain(high)
                self.flood(low)
        if before == 0 and self.water:
            print("Event: a pond forms")
        elif before and not self.water:
            print("Event: the last pond dries up")

        for pos in list(self.mud):
            self.mud[pos] -= 1
            if self.mud[pos] <= 0:
                del self.mud[pos]

    def update_land(self):
        """The ground itself changes: ponds silt up, rain washes soil downhill."""
        snowing = self.weather in ("rain", "storm") and self.temperature() < 1
        for pos in list(self.tracks):
            self.tracks[pos] -= 8 if snowing else 1  # fresh snow fills footprints fast
            if self.tracks[pos] <= 0 or self.snow < 0.3:
                del self.tracks[pos]
        for pos in list(self.deadwood):
            self.deadwood[pos] -= 1
            if self.deadwood[pos] <= 0:
                del self.deadwood[pos]
        for pos in self.water:
            self.height[pos] += per_year(0.23)  # silt and plants slowly fill the pond
        if self.weather in ("rain", "storm"):
            strength = per_day(0.58) if self.weather == "storm" else per_day(0.29)
            for pos in CELLS:
                if pos in self.water or (pos in self.trees and random.random() < 0.8):
                    continue  # roots hold the soil
                low = min(neighbors(*pos), key=lambda n: self.height[n])
                drop = self.height[pos] - self.height[low]
                if drop > 0:
                    moved = drop * strength
                    self.height[pos] -= moved
                    self.height[low] += moved

    def drain(self, pos):
        """Water leaves a cell: wet, bare and fertile ground remains."""
        self.water.discard(pos)
        self.mud[pos] = TICKS_PER_DAY * 4
        self.grass[pos] = 0.0

    def flood(self, pos):
        """What happens to a cell that goes under water."""
        self.water.add(pos)
        if pos in self.trees:
            del self.trees[pos]
            print("Event: a tree drowns")
        self.burrows.pop(pos, None)
        self.flowers.pop(pos, None)
        self.mushrooms.pop(pos, None)
        self.wood_flowers.pop(pos, None)
        self.fruit.pop(pos, None)
        self.fire.pop(pos, None)
        self.deadwood.pop(pos, None)
        animal = self.occupant(pos)
        if animal:
            dry = [n for n in neighbors(*pos) if n not in self.water and not self.occupant(n)]
            if dry:
                self.move(animal, random.choice(dry))
            else:
                self.kill(animal, RAIN)

    def grow(self):
        temperature = self.temperature()
        warmth = max(0.0, min(1.3, (temperature - 4) / 12))  # grass grows from about 5 degrees
        water = WEATHER_WATER[self.weather]
        light = self.light()
        for pos in CELLS:
            if pos in self.water or pos in self.fire or pos in self.trees:
                continue
            amount = self.grass[pos]
            near = neighbors(*pos)
            wet = 1.8 if pos in self.mud or any(n in self.water for n in near) else 1.0
            fed = 1.6 if pos in self.fertile else 1.0
            if water > 0:
                # Bare land is reseeded from lush neighbors, shade under trees slows it down
                seeding = max((self.grass[n] for n in near if n not in self.water), default=0)
                shade = 0.7 if any(n in self.trees for n in near) else 1.0
                growth = warmth * water * fed
                rate = per_day(5.8) * growth * (0.2 + light) * wet * shade
                amount += rate * (1.05 - amount) + per_day(0.58) * growth * seeding
            else:
                amount += per_day(0.75) * water / wet  # drought: the grass dries out slowly, it doesn't vanish
            self.grass[pos] = max(0.0, min(1.0, amount))
            self.lush[pos] = self.lush[pos] + 1 if self.grass[pos] > 0.75 else 0

            # Lush grass flowers on warm sunny days
            if (PLANTS and temperature > 12 and self.weather == "clear" and light > 0.5 and self.grass[pos] > 0.85
                    and pos not in self.flowers and random.random() < per_day(0.58)):
                self.flowers[pos] = (random.choice(FLOWERS), int(TICKS_PER_DAY * random.uniform(0.3, 0.8)))

        for pos in list(self.flowers):
            color, left = self.flowers[pos]
            if left <= 1 or self.grass[pos] < 0.2 or temperature < 0:
                del self.flowers[pos]  # wilted, eaten or frozen
            else:
                self.flowers[pos] = (color, left - 1)
        for pos in list(self.fertile):
            self.fertile[pos] -= 1
            if self.fertile[pos] <= 0:
                del self.fertile[pos]

    def spread_fire(self):
        for pos in list(self.fire):
            self.grass[pos] = 0.0
            self.deadwood.pop(pos, None)
            if pos in self.trees:
                del self.trees[pos]
                print("Event: a tree burns down")
            victim = self.occupant(pos)
            if victim:
                self.kill(victim, (255, 200, 0))
            for n in neighbors(*pos):
                fuel = (1.0 if n in self.trees or n in self.deadwood else self.grass[n]) * (1 - self.snow)
                if n not in self.fire and n not in self.water and random.random() < 0.08 * (1 + 2 * self.dryness) * fuel:
                    self.fire[n] = 12 if n in self.trees else 8
            self.fire[pos] -= 1
            if self.fire[pos] <= 0:
                del self.fire[pos]
                self.fertile[pos] = TICKS_PER_DAY  # ash feeds the soil

    def change_trees(self):
        """Trees take root where grass has been lush for a while, spread into woods and grow old."""
        if self.temperature() > 8:
            for pos, ticks in self.lush.items():
                near_trees = sum(n in self.trees for n in neighbors(*pos))
                if near_trees >= 3:
                    continue  # too dark under dense woods for a seedling
                chance = per_year(2.3) if near_trees else per_year(0.35)  # woods spread, lone seeds blow in
                if ticks > TICKS_PER_DAY // 4 and pos not in self.burrows and random.random() < chance:
                    self.trees[pos] = 0
                    self.lush[pos] = 0
                    print("Event: a tree takes root")
                    break
        for pos in list(self.trees):
            self.trees[pos] += 1
            # Crowded woods and old age: trees eventually fall and leave a pit where the roots were
            crowded = sum(n in self.trees for n in neighbors(*pos))
            if self.trees[pos] > TICKS_PER_YEAR * (3 - 0.4 * crowded) and random.random() < per_year(3.5):
                del self.trees[pos]
                self.grass[pos] = 0.3
                self.fertile[pos] = TICKS_PER_DAY * 4
                self.deadwood[pos] = TICKS_PER_YEAR // 2  # the trunk stays and slowly rots away
                self.height[pos] -= 0.12
                mound = random.choice(neighbors(*pos))
                self.height[mound] += 0.08
                print("Event: an old tree falls")

        for pos, used in list(self.burrows.items()):
            if self.tick - used > TICKS_PER_DAY * 3:
                del self.burrows[pos]
                print("Event: an empty burrow collapses")

    def rabbit(self, rabbit):
        rabbit.age += 1
        rabbit.flash = max(0, rabbit.flash - 1)
        foxes = [a for a in self.animals if a.kind == "fox"]
        danger = min((distance(rabbit.pos, f.pos) for f in foxes), default=99)
        if rabbit.pos in self.burrows:
            self.burrows[rabbit.pos] = self.tick

        cold = self.temperature() < 0
        # Asleep at night; a hungry rabbit wakes up and eats its fill before it sleeps again,
        # and a rabbit startled by a fox stays alert for a while
        if danger <= 2:
            rabbit.alert_until = self.tick + TICKS_PER_SECOND * 12
        startled = self.tick < rabbit.alert_until
        if rabbit.asleep:
            rabbit.asleep = self.is_night() and rabbit.energy > 0.4 and not startled
        else:
            rabbit.asleep = self.is_night() and rabbit.energy > 1.2 and not startled
        # Rabbits mostly sit and graze, hop on when the grass runs out, and only sprint when a fox is near
        if danger <= 3:
            pace = 1.0
        elif self.grass[rabbit.pos] < 0.15 or (cold and rabbit.pos not in self.burrows):
            pace = 0.3
        else:
            pace = 0.06
        if self.weather in ("rain", "storm") and danger > 3:
            pace *= 0.5
        if not rabbit.asleep and random.random() < pace:
            options = [rabbit.pos] + [n for n in neighbors(*rabbit.pos) if self.walkable(n) and not self.occupant(n)]

            def score(pos):
                treats = pos in self.mushrooms or pos in self.wood_flowers or pos in self.fruit
                s = self.grass[pos] + random.uniform(0, 0.3) + (0.5 if treats else 0)
                if self.burrows and (danger <= 3 or cold):
                    s -= 0.8 * min(distance(pos, b) for b in self.burrows)  # head home
                if danger <= 3:
                    s += 0.6 * min(distance(pos, f.pos) for f in foxes)  # away from foxes
                return s

            self.move(rabbit, max(options, key=score))

        # Snow hides the grass; in a burrow or asleep a rabbit uses little energy
        if rabbit.pos not in self.water and not rabbit.asleep and rabbit.energy < self.capacity(rabbit) - 0.1:
            bite = min(self.grass[rabbit.pos], per_day(14)) * (1 - 0.8 * self.snow)  # only eats when hungry
            self.grass[rabbit.pos] -= bite
            rabbit.energy += bite
        sheltered = rabbit.pos in self.burrows
        # A full rabbit can go about a day without food, longer resting in a burrow
        if rabbit.asleep:
            rabbit.energy -= per_day(0.35) if sheltered else per_day(0.55)
        else:
            rabbit.energy -= per_day(1.5) + (per_day(0.4) if cold else 0)  # staying warm costs energy
        # When grass is scarce or under snow, rabbits gnaw bark from trees next to them
        if not rabbit.asleep and rabbit.energy < 1.0 and (self.snow > 0.3 or self.grass[rabbit.pos] < 0.1):
            trees = [n for n in neighbors(*rabbit.pos) if n in self.trees]
            if trees:
                rabbit.energy += per_day(1.5)
                if random.random() < per_year(5.8):
                    gnawed = random.choice(trees)
                    if self.trees[gnawed] < TICKS_PER_YEAR:  # a young tree ringed bare dies
                        del self.trees[gnawed]
                        print("Event: rabbits gnaw a young tree to death")
        for treats, value in ((self.mushrooms, 0.3), (self.wood_flowers, 0.2), (self.fruit, 0.4)):
            if treats.pop(rabbit.pos, None):
                rabbit.energy += value
        if rabbit.pos in self.trees and self.trees[rabbit.pos] < SAPLING and random.random() < per_year(576):
            del self.trees[rabbit.pos]  # a sapling nibbled away
            self.grass[rabbit.pos] = 0.3

        rabbit.energy = min(rabbit.energy, self.capacity(rabbit))

        # Rabbits breed while the days are long
        if (rabbit.energy > 1.5 and self.day_length() > 0.5 and rabbit.can_breed() and random.random() < per_day(43)
                and self.has_mate(rabbit)):
            self.give_birth(rabbit, random.randint(1, 3), 0.6, 0.3)

        # Dig a new burrow, away from the others (and lower the ground a little)
        far = not self.burrows or min(distance(rabbit.pos, b) for b in self.burrows) > 2
        if (far and not cold and rabbit.energy > 1.2 and rabbit.pos not in self.trees
                and rabbit.pos not in self.water and random.random() < per_day(2.9)):
            self.burrows[rabbit.pos] = self.tick
            self.height[rabbit.pos] -= 0.03
            print("Event: rabbits dig a new burrow")

        if rabbit.energy <= 0 or rabbit.age > rabbit.lifespan:
            self.kill(rabbit, (60, 40, 30))

    def fox(self, fox):
        fox.age += 1
        fox.flash = max(0, fox.flash - 1)
        night = self.is_night()
        full = fox.energy > 1.6
        # A full fox lies down for a good while, and in the middle of the day it rests too
        if self.tick >= fox.rest_until:
            if full:
                fox.rest_until = self.tick + int(TICKS_PER_DAY * random.uniform(0.1, 0.25))
            elif not night and fox.energy > 1.0 and self.light() > 0.6:
                fox.rest_until = self.tick + int(TICKS_PER_DAY * random.uniform(0.05, 0.1))
        fox.asleep = self.tick < fox.rest_until
        rabbits = [a for a in self.animals if a.kind == "rabbit"]
        # A fox's territory is far bigger than this piece of land: after a while it moves on
        # (young ones go along with the family), sooner when there is nothing to catch here
        if not fox.asleep and not fox.leaving and random.random() < per_day(1 if rabbits else 3):
            fox.leaving = True
        # A fox needs about one rabbit every two to three days
        if fox.asleep or (not night and self.tick % 2):
            fox.energy -= per_day(0.29)
        else:
            prey = min(rabbits, key=lambda r: distance(fox.pos, r.pos), default=None)
            options = [n for n in neighbors(*fox.pos) if self.walkable(n, "fox")]
            if fox.leaving:
                edge = min(fox.pos[0], W - 1 - fox.pos[0], fox.pos[1], H - 1 - fox.pos[1])
                if edge == 0:
                    self.animals.remove(fox)
                    print("Event: a fox moves on")
                    return
                target = min(options, key=lambda n: min(n[0], W - 1 - n[0], n[1], H - 1 - n[1]) + random.uniform(0, 0.5),
                             default=fox.pos)
            elif prey and not full and distance(fox.pos, prey.pos) <= 3:
                # Hungry and on the hunt: a sprint straight at the prey (a full fox leaves rabbits be)
                target = min(options, key=lambda n: distance(n, prey.pos) + random.uniform(0, 0.5), default=fox.pos)
            elif options and random.random() < 0.2:
                target = random.choice(options)  # roaming at a slow trot
            else:
                target = fox.pos

            other = self.occupant(target)
            if other and other.kind == "rabbit" and not full and not fox.leaving:
                hidden = target in self.trees and not night  # cover under the trees
                # A fox sees best by the light of the full moon
                if not hidden and random.random() < ((0.35 + 0.2 * self.moon()) if night else 0.2):
                    self.kill(other, (255, 0, 0))
                    fox.energy += 1.0
                    self.move(fox, target)
            elif not other and target not in self.water:
                self.move(fox, target)
            fox.energy -= per_day(1.15) if self.temperature() < 0 else per_day(0.86)

        fox.energy = min(fox.energy, self.capacity(fox))

        # Foxes breed in early spring, when the days are getting longer
        if (fox.energy > 2.0 and self.season() == "spring" and fox.can_breed() and random.random() < per_day(72)
                and self.has_mate(fox)):
            self.give_birth(fox, random.randint(1, 3), 0.9, 0.4)

        if fox.energy <= 0 or fox.age > fox.lifespan:
            self.kill(fox, (60, 30, 10))

    def capacity(self, animal):
        """How much energy an animal can store: in autumn and winter they put on fat."""
        return animal.max_energy * (1.75 if self.season() in ("autumn", "winter") else 1.0)

    def has_mate(self, animal):
        """Young need two parents: another adult of the same kind. This piece of land is small
        compared with how far animals roam, so any adult here can find the other."""
        return any(other is not animal and other.kind == animal.kind and other.is_adult() for other in self.animals)

    def give_birth(self, parent, litter, child_energy, cost):
        """A litter of young next to the parent, as many as there is room for."""
        free = [n for n in neighbors(*parent.pos)
                if self.walkable(n, parent.kind) and n not in self.water and not self.occupant(n)]
        born = random.sample(free, min(litter, len(free)))
        for pos in born:
            self.animals.append(Animal(parent.kind, pos, child_energy))
        if born:
            parent.energy -= cost * (1 + len(born))
            parent.next_litter = parent.age + parent.pregnancy

    def arrivals(self):
        """The world isn't closed: animals wander in from outside when there's food for them."""
        if self.snow > 0.5:
            return
        food = sum(self.grass.values()) / len(CELLS) * (1 - self.snow)
        if food > 0.3 and random.random() < per_day(0.25):
            if self.spawn("rabbit", 1.0, edge=True):
                print("Event: a rabbit wanders in")
        # Foxes roaming their territory come by now and then; they keep out of each other's way,
        # so there are never more than a couple of them here at once
        if self.count("fox") < 2 and random.random() < per_day(0.2):
            if self.spawn("fox", random.uniform(0.8, 1.6), edge=True):
                print("Event: a fox comes by")

    def nature(self):
        """Things that happen when the conditions are right."""
        temperature = self.temperature()
        light = self.light()

        if self.is_night() and self.weather == "clear" and random.random() < 1 / (TICKS_PER_DAY * 0.15):
            self.effects.append(ShootingStar())

        if self.birds_due and light > 0.5 and self.weather in ("clear", "fog"):
            self.effects.append(Birds(leftwards=self.season() == "autumn"))
            self.birds_due = False
            print("Event: migrating birds")

        # Abundant grass on a hot day draws locusts
        grass = sum(self.grass.values()) / len(CELLS)
        if (temperature > 20 and light > 0.5 and grass > 0.75 and self.weather in ("clear", "drought")
                and not any(isinstance(e, Locusts) for e in self.effects) and random.random() < per_day(2.9)):
            self.effects.append(Locusts())
            print("Event: a locust swarm comes for the grass")

        # Mushrooms come up under trees in mild, wet weather
        if PLANTS and self.weather == "rain" and 5 < temperature < 16:
            for pos in CELLS:
                if (pos not in self.water and pos not in self.trees and pos not in self.mushrooms
                        and (pos in self.deadwood or any(n in self.trees for n in neighbors(*pos)))
                        and random.random() < per_day(0.72)):
                    self.mushrooms[pos] = int(TICKS_PER_DAY * random.uniform(0.5, 1.0))
        for pos in list(self.mushrooms):
            self.mushrooms[pos] -= 1
            if self.mushrooms[pos] <= 0 or temperature < -2:
                del self.mushrooms[pos]

        # In spring, before the leaves are out, flowers bloom on the woodland floor
        season = self.season()
        if PLANTS and season == "spring" and temperature > 6 and light > 0.3:
            for pos in CELLS:
                if (pos not in self.water and pos not in self.trees and pos not in self.wood_flowers
                        and any(n in self.trees for n in neighbors(*pos)) and random.random() < per_day(0.43)):
                    self.wood_flowers[pos] = (random.choice(WOOD_FLOWERS), int(TICKS_PER_DAY * random.uniform(0.5, 1.5)))
        # In late summer and autumn, ripe fruit drops from old trees
        if PLANTS and season in ("summer", "autumn") and self.summer_ness() < 0.3:
            for pos, age in self.trees.items():
                if age > TICKS_PER_YEAR and random.random() < per_day(0.43):
                    spot = random.choice(neighbors(*pos))
                    if spot not in self.water and spot not in self.trees:
                        self.fruit[spot] = int(TICKS_PER_DAY * random.uniform(0.5, 1.5))
        for store in (self.wood_flowers, self.fruit):
            for pos in list(store):
                left = store[pos][1] if isinstance(store[pos], tuple) else store[pos]
                if left <= 1 or temperature < -2:
                    del store[pos]
                elif isinstance(store[pos], tuple):
                    store[pos] = (store[pos][0], left - 1)
                else:
                    store[pos] = left - 1

        # Frost on clear freezing nights, mist over the water when a cold night meets the sun
        if temperature < 0 and self.weather == "clear" and self.is_night():
            self.frost = min(1.0, self.frost + per_day(2.9))
            if self.water:
                self.mist = min(1.0, self.mist + per_day(1.4))
        elif temperature > 2:
            self.frost = max(0.0, self.frost - per_day(5.8) * (0.3 + light))
            if light > 0.4:
                self.mist = max(0.0, self.mist - per_day(4.3))

    # Drawing

    def wind_speed(self):
        return {"storm": 3.0, "rain": 1.5, "clear": 1.0, "drought": 0.7, "fog": 0.2}[self.weather]

    def cloud_shade(self, x, y):
        """Shadow of drifting clouds on a sunny day, 0 (none) to about 0.35."""
        shade = 0.0
        for cx, cy, r in self.clouds:
            d = math.hypot(x - cx, y - cy)
            shade = max(shade, 0.35 * max(0.0, 1 - d / r))
        return shade

    def render(self, frame):
        column_light = [self.light(x) for x in range(W)]
        light = self.light()
        moon = self.moonlight()
        self.night_floor = 0.22 + 0.23 * moon  # a dark night, a bit lighter under a full moon
        speed = self.wind_speed()
        dx, dy = math.cos(self.wind), math.sin(self.wind)
        for cloud in self.clouds:
            cloud[0] += dx * speed * 0.01
            cloud[1] += dy * speed * 0.01
            # A cloud that has drifted off the land is replaced by a new one coming in upwind
            if not (-4 < cloud[0] < W + 4 and -4 < cloud[1] < H + 4):
                cloud[0] = W / 2 - dx * (W / 2 + 3) + random.uniform(-2, 2)
                cloud[1] = H / 2 - dy * (H / 2 + 3) + random.uniform(-2, 2)
                cloud[2] = random.uniform(1.5, 3)
        sunny = self.weather in ("clear", "drought")
        clear_night = light == 0 and sunny
        temperature = self.temperature()
        raining = self.weather in ("rain", "storm") and temperature >= 1
        grass_color = self.seasonal(SEASON_GRASS)
        tree_color = self.seasonal(SEASON_TREE)
        sun = self.sun_direction()
        # Low sun on a clear day brings out the hills: strongest in the morning and evening
        relief = min(1.0, 4 * light) * (1.1 - light) if sunny and light > 0 else 0.0
        damp = self.weather in ("rain", "fog", "clear") and temperature > 4 and self.snow < 0.3
        canvas = []
        for pos in CELLS:
            x, y = pos
            col_light = column_light[x]
            if pos in self.fire:
                color = mix((255, 30, 0), (255, 220, 60), random.random() ** 0.7)
            elif pos in self.water:
                shimmer = 0.85 + 0.15 * math.sin(frame * 0.15 + x * 1.3 + y)
                if raining and random.random() < 0.15:
                    shimmer = 1.4  # raindrops on the water
                color = mix(scale(WATER, shimmer), ICE, min(1.0, self.ice * 1.5))
            elif pos in self.trees:
                young = min(1.0, self.trees[pos] / SAPLING)
                color = mix(mix(grass_color, tree_color, 0.4 + 0.6 * young), SNOW, 0.5 * self.snow)
            elif pos in self.burrows:
                color = mix(BURROW, SNOW, 0.6 * self.snow)
            elif pos in self.flowers or pos in self.wood_flowers or pos in self.mushrooms or pos in self.fruit:
                # A soft, steady tint in the grass: a flowering meadow, not blinking lights
                if pos in self.flowers:
                    tint, amount = self.flowers[pos][0], 0.45
                elif pos in self.wood_flowers:
                    tint, amount = self.wood_flowers[pos][0], 0.45
                elif pos in self.mushrooms:
                    tint, amount = MUSHROOM, 0.5
                else:
                    tint, amount = FRUIT, 0.55
                color = mix(mix(SOIL, grass_color, self.grass[pos]), tint, amount)
            else:
                bare = MUD if pos in self.mud else (ASH if self.grass[pos] < 0.02 else SOIL)
                # Hollows stay moist and their grass grows dense and dark; on the hilltops it is thinner
                ground = scale(grass_color, 0.75 + 0.4 * self.height[pos])
                color = mix(bare, ground, self.grass[pos])
                if pos in self.deadwood:
                    color = mix(color, DEADWOOD, 0.5 * min(1.0, self.deadwood[pos] / (TICKS_PER_YEAR / 8)))
                color = mix(color, SNOW, self.snow)
                if pos in self.tracks:
                    color = mix(color, TRACK, 0.6 * min(1.0, self.tracks[pos] / (TICKS_PER_DAY / 8)))
                color = mix(color, FROST, 0.6 * self.frost)
                # Wind ripples through tall grass
                if self.grass[pos] > 0.3 and self.snow < 0.5:
                    wave = math.sin((x * dx + y * dy) * 1.3 - frame * 0.08 * speed)
                    color = scale(color, 1 + 0.12 * min(1.0, speed) * self.grass[pos] * wave)
                sparkle = (self.snow > 0.3 or self.frost > 0.3) and (col_light > 0 or moon > 0.4)
                if sparkle and random.random() < 0.01:
                    color = (255, 255, 255)  # glittering snow or rime, in the sun or the moonlight
            if relief and pos not in self.water and pos not in self.fire:
                color = scale(color, 1 + (self.relief(x, y, sun) - 1) * relief)

            if self.weather == "drought" and pos not in self.water:
                color = mix(color, (120, 90, 20), 0.35)
            if self.weather == "fog":
                color = mix(color, (70, 70, 75), 0.45)

            # Fire gives light of its own, everything else is lit by the sun or the moon
            if pos not in self.fire:
                color = self.lit(color, x, y, col_light, sunny)
                if clear_night and moon > 0.2:
                    color = scale(color, 1 - 0.6 * self.cloud_shade(x, y))  # clouds drift past the moon
                if pos in self.water and self.ice < 0.5:
                    color = self.reflect(color, x, y, col_light, frame, moon, sunny)
                if pos in self.deadwood and col_light == 0 and damp:
                    # Foxfire: fungi in the wet rotting wood glow faintly in the dark
                    pulse = 0.7 + 0.3 * math.sin(frame * 0.02 + x * 1.7 + y)
                    color = add(color, FOXFIRE, 0.22 * pulse * min(1.0, self.deadwood[pos] / (TICKS_PER_YEAR / 8)))
                if self.mist > 0.05 and (pos in self.water or any(n in self.water for n in neighbors(*pos))):
                    drift = 0.6 + 0.4 * math.sin(frame * 0.05 + x * 0.8 + y * 0.5)
                    mist = self.lit(MIST, x, y, col_light, False)
                    color = mix(color, mist, self.mist * drift * (0.8 if pos in self.water else 0.4))
            canvas.append(color)

        # Animals glide from one cell to the next; asleep they breathe slowly.
        # They give no light of their own: the same light falls on them
        glide = (frame % FRAMES_PER_TICK + 1) / FRAMES_PER_TICK
        for animal in self.animals:
            x, y = animal.pos
            if animal.asleep:
                f = 0.55 + 0.1 * math.sin(frame * 0.12 + animal.breath)
            else:
                f = 1.15 if animal.flash else 1.0  # a newborn is a little brighter for a moment
            color = self.lit(scale(RABBIT if animal.kind == "rabbit" else FOX, f), x, y, column_light[x], sunny)
            if animal.moved == self.tick and glide < 1:
                px, py = animal.prev
                blend(canvas, px + (x - px) * glide, py + (y - py) * glide, color, 1.0)
            else:
                canvas[y * W + x] = color

        for pos in list(self.flashes):
            color, left = self.flashes[pos]
            i = pos[1] * W + pos[0]
            shown = self.lit(color, pos[0], pos[1], column_light[pos[0]], sunny)
            canvas[i] = mix(canvas[i], shown, 0.6 * left / 6)
            if left <= 1:
                del self.flashes[pos]
            else:
                self.flashes[pos] = (color, left - 1)

        self.update_motes(canvas, frame, column_light, temperature, tree_color, sunny)
        self.render_precipitation(canvas, temperature, column_light, sunny)

        for effect in self.effects:
            effect.draw(canvas, self)
        self.effects = [e for e in self.effects if not e.done]

        if self.lightning:
            self.lightning -= 1
            canvas = [mix(c, (255, 255, 255), 0.8) for c in canvas]
        return canvas

    def reflect(self, color, x, y, light, frame, moon, sunny):
        """Still water mirrors the sky: the glow of a sunset, the stars and the moon at night."""
        if not sunny:
            return color
        glow = self.twilight(light)
        if glow:
            color = mix(color, scale(SKY_GLOW, 0.5 + 0.5 * light), 0.45 * glow)
        if light == 0:
            # The moon washes out the fainter stars
            if random.random() < 0.025 * (1 - 0.6 * moon):
                color = mix(color, STARLIGHT, 0.5)
            glint = max(0.0, math.sin(frame * 0.07 + x * 0.9 - y * 0.6)) ** 6
            color = mix(color, MOONLIGHT, 0.7 * glint * moon)
        return color

    def update_motes(self, canvas, frame, column_light, temperature, tree_color, sunny):
        """Snowflakes, seeds, leaves and fireflies: each drifts on the wind and lands for real."""
        speed = self.wind_speed()
        dx, dy = math.cos(self.wind), math.sin(self.wind)
        light = self.light()
        season = self.season()
        snowing = self.weather in ("rain", "storm") and temperature < 1

        # Snow comes down slowly, swaying, carried a little by the wind
        if snowing and random.random() < (0.7 if self.weather == "storm" else 0.4):
            self.motes.append(Mote("flake", random.uniform(-1, W), -0.5, dx * speed * 0.02,
                                   random.uniform(0.05, 0.09), FLAKE, random.randint(60, 110)))
        # Late spring and summer: lush grass sets seed and the wind takes the fluff
        lush = sum(1 for g in self.grass.values() if g > 0.8)
        if (season in ("spring", "summer") and self.year_phase() > 0.15 and sunny and light > 0.3
                and temperature > 12 and random.random() < 0.0006 * lush * speed):
            x, y = random.choice([p for p, g in self.grass.items() if g > 0.8])
            self.motes.append(Mote("seed", x, y, dx * speed * 0.05, dy * speed * 0.05, SEED, random.randint(30, 90)))
        # Autumn wind takes the leaves from the trees
        if season == "autumn" and self.trees and random.random() < min(0.2, 0.01 * len(self.trees) * speed):
            x, y = random.choice(list(self.trees))
            self.motes.append(Mote("leaf", x, y, dx * speed * 0.04, dy * speed * 0.04,
                                   mix(tree_color, (230, 150, 20), random.random()), random.randint(20, 60)))
        # Fireflies on warm summer nights, over the grass and along the woods and water
        fireflies = sum(1 for m in self.motes if m.kind == "firefly")
        wanted = 0
        if light == 0 and sunny and season == "summer":
            wanted = int(min(6, max(0, temperature - 14)) * min(1.0, lush / 20))
        if fireflies < wanted and random.random() < 0.02:
            x, y = random.choice([p for p, g in self.grass.items() if g > 0.8])
            self.motes.append(Mote("firefly", x, y, 0.0, 0.0, FIREFLY, FPS * random.randint(60, 240)))

        for mote in self.motes:
            mote.frame += 1
            if mote.kind == "flake":
                mote.x += mote.vx + 0.02 * math.sin(mote.frame * 0.15 + mote.phase)
                mote.y += mote.vy
            elif mote.kind == "firefly":
                # A slow wandering flight; it flashes for a moment every few seconds
                mote.vx = max(-0.03, min(0.03, mote.vx + random.gauss(0, 0.004)))
                mote.vy = max(-0.03, min(0.03, mote.vy + random.gauss(0, 0.004)))
                mote.x = min(W - 1.0, max(0.0, mote.x + mote.vx))
                mote.y = min(H - 1.0, max(0.0, mote.y + mote.vy))
                if light > 0 or fireflies > wanted:
                    mote.frames = min(mote.frames, mote.frame + 8)  # the night is over
            else:
                mote.x += mote.vx + random.uniform(-0.03, 0.03)
                mote.y += mote.vy + random.uniform(-0.03, 0.03)

            fade = mote.fade()
            if mote.kind == "firefly":
                flash = (math.sin(mote.frame * 0.13 + mote.phase) - 0.7) / 0.3
                if flash > 0:
                    blend(canvas, mote.x, mote.y, mote.color, 0.9 * flash * fade, glow=True)
            else:
                x = min(W - 1, max(0, int(mote.x)))
                color = self.lit(mote.color, x, 0, column_light[x], sunny)
                blend(canvas, mote.x, mote.y, color, 0.75 * fade)

        for mote in self.motes:
            if mote.frame >= mote.frames:
                self.settle(mote)
        self.motes = [m for m in self.motes
                      if m.frame < m.frames and -2 < m.x < W + 1 and -2 < m.y < H + 1]

    def settle(self, mote):
        """Where a seed comes down on bare ground, grass starts; fallen leaves feed the soil."""
        pos = (int(round(mote.x)), int(round(mote.y)))
        if pos not in self.grass or pos in self.water:
            return
        if mote.kind == "seed" and self.grass[pos] < 0.5:
            self.grass[pos] += 0.15
        elif mote.kind == "leaf" and pos not in self.trees:
            self.fertile[pos] = max(self.fertile.get(pos, 0), TICKS_PER_DAY // 2)

    def render_precipitation(self, canvas, temperature, column_light, sunny):
        if self.weather in ("rain", "storm") and temperature >= 1:
            for _ in range(2 if self.weather == "storm" else 1):
                if random.random() < 0.4:
                    self.drops.append([random.randrange(W), 0])
        for drop in self.drops:
            x, y = drop
            canvas[y * W + x] = mix(canvas[y * W + x], self.lit(RAIN, x, y, column_light[x], sunny), 0.35)
            drop[1] += 1
        self.drops = [d for d in self.drops if d[1] < H]


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
