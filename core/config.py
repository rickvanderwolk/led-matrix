"""
Config loading and schedule resolution.

No hardware imports here, so main.py can use this without touching the LEDs.
"""

import json
import os
import random
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


def _warn_once(message):
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
    """Rename old keys to their current names, at the top level and in schedule entries."""
    def rename(section):
        # Rename in place to keep the key order; a key that already uses the new name wins
        renamed = {}
        for key, value in section.items():
            new = RENAMED_KEYS.get(key, key)
            if new != key and new in section:
                continue
            renamed[new] = value
        return renamed

    config = rename(config)
    if isinstance(config.get("schedule"), list):
        config["schedule"] = [rename(e) if isinstance(e, dict) else e for e in config["schedule"]]
    return config


def merge(base, override):
    """Recursively merge override into a copy of base. Dicts merge, everything else replaces."""
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def _minutes(entry):
    try:
        hours, minutes = entry["from"].split(":")
        hours, minutes = int(hours), int(minutes)
    except (KeyError, AttributeError, ValueError):
        return None
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        return None
    return hours * 60 + minutes


def active(config, now=None):
    """
    Return the config as it applies right now.

    Each schedule entry overrides any config key from its "from" time onwards. Entries
    stack: a value stays in effect until a later entry changes it, wrapping around
    midnight. A playlist in "mode" is resolved to the mode for the current time slot.
    """
    now = now or datetime.now()
    config = upgrade(config)
    base = {key: value for key, value in config.items() if key != "schedule"}
    entries = []
    for entry in config.get("schedule") or []:
        minutes = _minutes(entry) if isinstance(entry, dict) else None
        if minutes is None:
            _warn_once(f"Ignoring invalid schedule entry: {entry!r}")
            continue
        entries.append((minutes, {key: value for key, value in entry.items() if key != "from"}))

    if entries:
        base = _apply_schedule(base, entries, now)
    if isinstance(base.get("mode"), dict):
        base["mode"] = _playlist_mode(base["mode"], now)
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
        _warn_once(f"Ignoring invalid brightness {value!r} (use a number from 0 to 1)")
        return DEFAULT_BRIGHTNESS
    return max(0.0, min(1.0, float(value)))


def _playlist_mode(playlist, now):
    """
    The mode a playlist plays right now. Slots line up with the clock (every 60 minutes
    switches on the hour), and the result only depends on the time, so a restart keeps
    playing the same mode.
    """
    modes = playlist.get("playlist")
    every = playlist.get("every", DEFAULT_PLAYLIST_MINUTES)
    if not (isinstance(modes, list) and modes and all(isinstance(m, str) for m in modes)):
        _warn_once(f"Ignoring invalid playlist {playlist!r} (needs a list of mode names)")
        return None
    if isinstance(every, bool) or not isinstance(every, (int, float)) or every <= 0:
        _warn_once(f"Ignoring invalid playlist interval {every!r}, using {DEFAULT_PLAYLIST_MINUTES} minutes")
        every = DEFAULT_PLAYLIST_MINUTES

    slot = int((now.toordinal() * 1440 + now.hour * 60 + now.minute) // every)
    if not playlist.get("shuffle") or len(modes) <= 2:  # shuffling two modes would only cause repeats
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
