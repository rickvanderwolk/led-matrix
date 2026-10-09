"""
The LED matrix as modes see it: an 8x8 canvas you draw on, then show().

Everything that isn't mode logic lives here: config, brightness (including the
schedule and fading), rotation/flipping, gamma, frame timing and switching the LEDs
off on exit.
"""

import atexit
import os
import signal
import sys
import threading
import time

import board
import neopixel

from . import config as config_module
from .color import BLACK

WIDTH = 8
HEIGHT = 8
COUNT = WIDTH * HEIGHT
CONFIG_CHECK_INTERVAL = 5  # seconds between checks for a scheduled brightness change
FADE_SECONDS = 1.0  # fade in on start and on brightness changes
FADE_OUT_SECONDS = 0.5  # fade out on exit, e.g. when switching modes
FADE_STEPS_PER_SECOND = 30


def _mode_name():
    name = os.environ.get("LEDMATRIX_MODE")
    if name:
        return name
    main_file = getattr(sys.modules.get("__main__"), "__file__", None)
    return os.path.basename(os.path.dirname(os.path.abspath(main_file))) if main_file else None


def _build_map(display):
    """Lookup table: physical LED index -> canvas index. None when nothing is transformed."""
    rotate = display.get("rotate", 0)
    flip_x = display.get("flip_x", False)
    flip_y = display.get("flip_y", False)
    if rotate not in (0, 90, 180, 270):
        print(f"Ignoring invalid display.rotate {rotate!r} (use 0, 90, 180 or 270)")
        rotate = 0
    if not (rotate or flip_x or flip_y):
        return None

    source = [0] * COUNT
    for y in range(HEIGHT):
        for x in range(WIDTH):
            px, py = x, y
            if flip_x:
                px = WIDTH - 1 - px
            if flip_y:
                py = HEIGHT - 1 - py
            for _ in range(rotate // 90):  # clockwise
                px, py = WIDTH - 1 - py, px
            source[py * WIDTH + px] = y * WIDTH + x
    return source


def _build_gamma(gamma):
    """Lookup table for gamma correction. None for gamma 1 (off)."""
    if gamma == 1:
        return None
    return [round(255 * (v / 255) ** gamma) for v in range(256)]


class Matrix:
    width = WIDTH
    height = HEIGHT
    count = COUNT

    def __init__(self):
        self.mode = _mode_name()
        self._config_path = config_module.path()
        config = config_module.active(config_module.load(self._config_path))

        # This mode's own settings: config["mode_settings"][<mode name>]
        self.settings = config.get("mode_settings", {}).get(self.mode, {})

        display = config.get("display", {})
        self._map = _build_map(display)
        self._gamma = _build_gamma(display.get("gamma", 1))

        self._canvas = [BLACK] * COUNT
        self._shown = None
        self._lock = threading.Lock()
        self._next_config_check = time.monotonic() + CONFIG_CHECK_INTERVAL
        self._fade_id = 0  # bumped to cancel a running fade

        # Start dark and fade in on the first frame
        self.brightness = config_module.brightness(config)
        self.pixels = neopixel.NeoPixel(board.D18, COUNT, brightness=0, auto_write=False)
        self._started = False

        # Signal handlers can only be installed from the main thread (the visualizer runs
        # modes in a background thread and handles shutdown itself).
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
            signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
            atexit.register(self.off)

    # Drawing. matrix[x, y] or matrix[index] (row by row, 0 = top left).
    # Writes outside the matrix are ignored, reads outside return None.

    def __setitem__(self, key, color):
        if isinstance(key, tuple):
            x, y = key
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                self._canvas[y * WIDTH + x] = color
        elif 0 <= key < COUNT:
            self._canvas[key] = color

    def __getitem__(self, key):
        if isinstance(key, tuple):
            x, y = key
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                return self._canvas[y * WIDTH + x]
            return None
        if 0 <= key < COUNT:
            return self._canvas[key]
        return None

    def __len__(self):
        return COUNT

    def fill(self, color):
        self._canvas = [color] * COUNT

    def clear(self):
        self.fill(BLACK)

    def neighbors(self, x, y, diagonal=False):
        """Coordinates of the neighbors of (x, y) that are on the matrix."""
        offsets = [(0, -1), (-1, 0), (1, 0), (0, 1)]
        if diagonal:
            offsets += [(-1, -1), (1, -1), (-1, 1), (1, 1)]
        return [(x + dx, y + dy) for dx, dy in offsets
                if 0 <= x + dx < WIDTH and 0 <= y + dy < HEIGHT]

    # Output

    def show(self):
        """Send the canvas to the LEDs. Cheap to call often: unchanged frames are skipped."""
        with self._lock:
            self._check_config()

            frame = self._canvas if self._map is None else [self._canvas[i] for i in self._map]
            if self._gamma is not None:
                g = self._gamma
                frame = [(g[r], g[gr], g[b]) for r, gr, b in frame]
            else:
                frame = list(frame)

            if frame != self._shown:
                self.pixels[:] = frame
                self.pixels.show()
                self._shown = frame

            if not self._started:
                self._started = True
                self._fade_to(self.brightness, FADE_SECONDS)

    def frames(self, fps=30):
        """
        Loop at a steady frame rate: draw inside the loop, showing happens for you.

            for frame in matrix.frames(fps=30):
                matrix[frame % 8, 0] = (255, 0, 0)
        """
        interval = 1.0 / fps
        next_time = time.monotonic()
        frame = 0
        while True:
            yield frame
            self.show()
            frame += 1
            next_time += interval
            delay = next_time - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            else:
                next_time = time.monotonic()  # running behind: don't try to catch up

    def off(self):
        """Fade out and switch all LEDs off (also happens automatically on exit)."""
        self._fade_id += 1
        try:
            start = self.pixels.brightness
            steps = int(FADE_OUT_SECONDS * FADE_STEPS_PER_SECOND)
            for step in range(1, steps + 1):
                with self._lock:
                    self.pixels.brightness = start * (1 - step / steps)
                    self.pixels.show()
                time.sleep(FADE_OUT_SECONDS / steps)
            with self._lock:
                self.pixels.fill(BLACK)
                self.pixels.show()
                self._shown = None
        except Exception:
            pass

    def _fade_to(self, target, seconds):
        """Fade the brightness to target in the background, replacing any running fade."""
        self._fade_id += 1
        fade_id = self._fade_id
        start = self.pixels.brightness
        steps = max(1, int(seconds * FADE_STEPS_PER_SECOND))

        def run():
            for step in range(1, steps + 1):
                with self._lock:
                    if fade_id != self._fade_id:
                        return
                    self.pixels.brightness = start + (target - start) * step / steps
                    self.pixels.show()
                time.sleep(seconds / steps)

        threading.Thread(target=run, daemon=True).start()

    def _check_config(self):
        """Apply scheduled brightness changes without restarting the mode."""
        now = time.monotonic()
        if now < self._next_config_check:
            return
        self._next_config_check = now + CONFIG_CHECK_INTERVAL
        try:
            brightness = config_module.brightness(config_module.active(config_module.load(self._config_path)))
        except (OSError, ValueError):
            return  # config is being edited or unreadable; keep the current brightness
        if brightness != self.brightness:
            self.brightness = brightness
            self._fade_to(brightness, FADE_SECONDS)
