"""
Config loading and schedule resolution.

No hardware imports here, so main.py can use this without touching the LEDs.
"""

import json
import os
import random
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BRIGHTNESS = 0.2
DEFAULT_PLAYLIST_MINUTES = 60

# Keys that were renamed, still accepted: old name -> new name
RENAMED_KEYS = {
    "selected_mode": "mode",
    "modes": "mode_settings",
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


def merge(base, override):
    """Recursively merge override into a copy of base. Dicts merge, everything else replaces."""
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def _minutes(time):
    try:
        hours, minutes = time.split(":")
        hours, minutes = int(hours), int(minutes)
    except ValueError:
        return None
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        return None
    return hours * 60 + minutes


def _overlap(base, override, prefix=""):
    """Keys (dotted for nested dicts) that override replaces in base."""
    keys = []
    for key, value in override.items():
        if key not in base:
            continue
        if isinstance(value, dict) and isinstance(base[key], dict):
            keys += _overlap(base[key], value, f"{prefix}{key}.")
        else:
            keys.append(prefix + key)
    return keys


def active(config, now=None):
    """
    Return the config as it applies right now.

    Each schedule entry overrides any config key from its time onwards. Entries stack: a
    value stays in effect until a later entry changes it, wrapping around midnight. A list
    in "mode" is a playlist, resolved to the mode for the current time slot.
    """
    now = now or datetime.now()
    config = upgrade(config)
    base = {key: value for key, value in config.items() if key != "schedule"}
    schedule = config.get("schedule") or {}
    if not isinstance(schedule, dict):
        warn_once('Ignoring schedule: use times as keys, like {"07:00": {"brightness": 0.2}}')
        schedule = {}
    entries = []
    for time, values in schedule.items():
        minutes = _minutes(time)
        if minutes is None or not isinstance(values, dict):
            warn_once(f"Ignoring invalid schedule entry: {time!r}: {values!r}")
            continue
        entries.append((minutes, values))
        for key in _overlap(base, values):
            warn_once(f"'{key}' is set both in the schedule and outside it: the schedule always wins, "
                      f"so the value outside it is never used")

    if entries:
        base = _apply_schedule(base, entries, now)
    mode = base.get("mode")
    if isinstance(mode, list):
        base["mode"] = _playlist_mode(mode, base.get("every"), base.get("shuffle"), now)
    elif mode is not None and not isinstance(mode, str):
        warn_once(f"Ignoring invalid mode {mode!r} (use a mode name or a list of mode names)")
        base["mode"] = None

    # Keys that must be objects; drop anything else so modes can rely on .get()
    for key in ("display", "mode_settings"):
        if key in base and not isinstance(base[key], dict):
            warn_once(f"Ignoring invalid {key} {base[key]!r} (use an object, like {{...}})")
            del base[key]
    if "mode_settings" in base:
        settings = {}
        for name, value in base["mode_settings"].items():
            if isinstance(value, dict):
                settings[name] = value
            else:
                warn_once(f"Ignoring invalid mode_settings for {name}: {value!r} (use an object, like {{...}})")
        base["mode_settings"] = settings
    return base


def _apply_schedule(base, entries, now):
    current = now.hour * 60 + now.minute
    entries.sort(key=lambda e: e[0])

    # Replay one full day ending now: entries after the current time ran "yesterday",
    # the rest ran today. The most recent entry for each key wins.
    replay = [e for e in entries if e[0] > current] + [e for e in entries if e[0] <= current]
    for _, override in replay:
        base = merge(base, override)
    return base


def brightness(config):
    """The configured brightness as a number from 0 to 1."""
    value = config.get("brightness", DEFAULT_BRIGHTNESS)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        warn_once(f"Ignoring invalid brightness {value!r} (use a number from 0 to 1)")
        return DEFAULT_BRIGHTNESS
    return max(0.0, min(1.0, float(value)))


def _every_seconds(every):
    """A playlist interval like "30s", "30m" or "2h" in seconds."""
    if every is None:
        return DEFAULT_PLAYLIST_MINUTES * 60
    match = re.fullmatch(r"(\d+)([smh])", every) if isinstance(every, str) else None
    seconds = int(match[1]) * {"s": 1, "m": 60, "h": 3600}[match[2]] if match else 0
    if seconds <= 0:
        warn_once(f'Ignoring invalid playlist interval {every!r} (use a value like "30s", "30m" or "2h"), '
                  f"using {DEFAULT_PLAYLIST_MINUTES} minutes")
        return DEFAULT_PLAYLIST_MINUTES * 60
    return seconds


def _playlist_mode(modes, every, shuffle, now):
    """
    The mode a playlist plays right now. Slots line up with the clock (every 60 minutes
    switches on the hour), and the result only depends on the time, so a restart keeps
    playing the same mode.
    """
    if not (modes and all(isinstance(m, str) for m in modes)):
        warn_once(f"Ignoring invalid playlist {modes!r} (needs a list of mode names)")
        return None

    seconds = now.toordinal() * 86400 + now.hour * 3600 + now.minute * 60 + now.second
    slot = seconds // _every_seconds(every)
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
