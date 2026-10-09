"""
Config loading and schedule resolution.

No hardware imports here, so main.py can use this without touching the LEDs.
"""

import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path():
    return os.environ.get("LEDMATRIX_CONFIG") or os.path.join(BASE_DIR, "config.json")


def load(config_path=None):
    config_path = config_path or path()
    if not os.path.exists(config_path):
        return {}
    with open(config_path) as f:
        return json.load(f)


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
    midnight. Without a schedule, the config is returned as-is.
    """
    base = {key: value for key, value in config.items() if key != "schedule"}
    entries = []
    for entry in config.get("schedule") or []:
        minutes = _minutes(entry) if isinstance(entry, dict) else None
        if minutes is None:
            print(f"Ignoring invalid schedule entry: {entry!r}")
            continue
        entries.append((minutes, {key: value for key, value in entry.items() if key != "from"}))

    if not entries:
        return base

    now = now or datetime.now()
    current = now.hour * 60 + now.minute
    entries.sort(key=lambda e: e[0])

    # Replay one full day ending now: entries after the current time ran "yesterday",
    # the rest ran today. The most recent entry for each key wins.
    replay = [e for e in entries if e[0] > current] + [e for e in entries if e[0] <= current]
    for _, override in replay:
        base = merge(base, override)
    return base
