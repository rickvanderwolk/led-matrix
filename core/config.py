"""
Config loading and resolving values that change over time.

No hardware imports here, so main.py can use this without touching the LEDs.
"""

import json
import os
import random
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODES_DIR = os.path.join(BASE_DIR, "modes")
DEFAULT_BRIGHTNESS = 0.2
DEFAULT_PLAYLIST_MINUTES = 60

# Keys that were renamed, still accepted: old name -> new name
RENAMED_KEYS = {
    "selected_mode": "mode",
    "modes": "mode_settings",
}

# Settings a mode can't do without. "all" skips these modes until the setting is there.
REQUIRED_SETTINGS = {
    "ntfy-sh": "topic",
}

_warned = set()


def warn_once(message):
    # The config is re-read every few seconds; don't repeat the same warning in the log
    if message not in _warned:
        _warned.add(message)
        print(message)


def path():
    return os.environ.get("LEDMATRIX_CONFIG") or os.path.join(BASE_DIR, "config.json")


def load(config_path=None):
    config_path = config_path or path()
    if not os.path.exists(config_path):
        return {}
    with open(config_path) as f:
        return json.load(f)


def upgrade(config):
    """Rename old keys to their current names."""
    # Rename in place to keep the key order; a key that already uses the new name wins
    renamed = {}
    for key, value in config.items():
        new = RENAMED_KEYS.get(key, key)
        if new != key and new in config:
            continue
        renamed[new] = value
    return renamed


TIMED_KEYS = ("mode", "skip_modes", "brightness", "switch_every", "shuffle")


def _minutes(time):
    try:
        hours, minutes = time.split(":")
        hours, minutes = int(hours), int(minutes)
    except ValueError:
        return None
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        return None
    return hours * 60 + minutes


def _at_time(key, times, now):
    """
    The value for right now from {"HH:MM": value, ...}: the value of the latest time that
    has passed, wrapping around midnight. None if there are no valid times.
    """
    entries = []
    for time, value in times.items():
        minutes = _minutes(time)
        if minutes is None:
            warn_once(f'Ignoring invalid time {time!r} in {key} (use HH:MM, like "07:00")')
            continue
        entries.append((minutes, value))
    if not entries:
        return None
    current = now.hour * 60 + now.minute
    passed = [entry for entry in entries if entry[0] <= current]
    return max(passed or entries, key=lambda entry: entry[0])[1]


def active(config, now=None):
    """
    Return the config as it applies right now.

    The keys in TIMED_KEYS can be a value, or a value per time like {"07:00": 0.2, "23:00": 0}.
    A list in "mode" (or "all") switches between those modes and is resolved to the mode for
    the current time slot.
    """
    now = now or datetime.now()
    active = upgrade(config)

    for key in TIMED_KEYS:
        if isinstance(active.get(key), dict):
            value = _at_time(key, active[key], now)
            if value is None:
                del active[key]
            else:
                active[key] = value

    # Keys that must be objects; drop anything else so modes can rely on .get()
    for key in ("display", "mode_settings"):
        if key in active and not isinstance(active[key], dict):
            warn_once(f"Ignoring invalid {key} {active[key]!r} (use an object, like {{...}})")
            del active[key]
    if "mode_settings" in active:
        settings = {}
        for name, value in active["mode_settings"].items():
            if isinstance(value, dict):
                settings[name] = value
            else:
                warn_once(f"Ignoring invalid mode_settings for {name}: {value!r} (use an object, like {{...}})")
        active["mode_settings"] = settings

    mode = active.get("mode")
    if mode == "all":
        mode = _all_modes(active)
    if isinstance(mode, list):
        active["mode"] = _switched_mode(mode, active.get("switch_every"), active.get("shuffle"), now)
    elif mode is not None and not isinstance(mode, str):
        warn_once(f"Ignoring invalid mode {mode!r} (use a mode name, a list of mode names or times)")
        active["mode"] = None
    return active


def available_modes():
    """Names of all modes: directories in modes/ with a main.py. "all" is reserved."""
    if not os.path.isdir(MODES_DIR):
        return []
    return sorted(
        name for name in os.listdir(MODES_DIR)
        if name != "all" and os.path.exists(os.path.join(MODES_DIR, name, "main.py"))
    )


def _all_modes(active):
    """The modes "all" plays: every mode, minus skip_modes and modes missing a required setting."""
    skip = active.get("skip_modes", [])
    if not (isinstance(skip, list) and all(isinstance(name, str) for name in skip)):
        warn_once(f"Ignoring invalid skip_modes {skip!r} (use a list of mode names)")
        skip = []
    modes = []
    for name in available_modes():
        if name in skip:
            continue
        required = REQUIRED_SETTINGS.get(name)
        if required and not active.get("mode_settings", {}).get(name, {}).get(required):
            warn_once(f'Skipping {name} in "all": it needs mode_settings.{name}.{required}')
            continue
        modes.append(name)
    return modes


def brightness(config):
    """The configured brightness as a number from 0 to 1."""
    value = config.get("brightness", DEFAULT_BRIGHTNESS)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        warn_once(f"Ignoring invalid brightness {value!r} (use a number from 0 to 1)")
        return DEFAULT_BRIGHTNESS
    return max(0.0, min(1.0, float(value)))


def _switch_seconds(every):
    """A switch_every interval like "30s", "30m" or "2h" in seconds."""
    if every is None:
        return DEFAULT_PLAYLIST_MINUTES * 60
    match = re.fullmatch(r"(\d+)([smh])", every) if isinstance(every, str) else None
    seconds = int(match[1]) * {"s": 1, "m": 60, "h": 3600}[match[2]] if match else 0
    if seconds <= 0:
        warn_once(f'Ignoring invalid switch_every {every!r} (use a value like "30s", "30m" or "2h"), '
                  f"using {DEFAULT_PLAYLIST_MINUTES} minutes")
        return DEFAULT_PLAYLIST_MINUTES * 60
    return seconds


def _switched_mode(modes, every, shuffle, now):
    """
    The mode from a list of modes that plays right now. Slots line up with the clock
    ("1h" switches on the hour), and the result only depends on the time, so a restart keeps
    playing the same mode.
    """
    if not (modes and all(isinstance(m, str) for m in modes)):
        warn_once(f"Ignoring invalid mode list {modes!r} (needs a list of mode names)")
        return None

    seconds = now.toordinal() * 86400 + now.hour * 3600 + now.minute * 60 + now.second
    slot = seconds // _switch_seconds(every)
    if not shuffle or len(modes) <= 2:  # shuffling two modes would only cause repeats
        return modes[slot % len(modes)]

    # Shuffle each round through the list with a fixed seed, so every mode plays once per round
    def round_order(number):
        order = list(modes)
        random.Random(number).shuffle(order)
        return order

    number, position = divmod(slot, len(modes))
    order = round_order(number)
    if order[0] == round_order(number - 1)[-1]:
        order[0], order[1] = order[1], order[0]  # don't play the same mode twice in a row
    return order[position]
