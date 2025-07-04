import os
import json

DEFAULT_CONFIG = {
    "rotation": 0,
    "mirror_x": False,
    "mirror_y": False,
    "brightness": 0.2
}

def load_config():
    path = os.environ.get("LEDMATRIX_CONFIG", "config.json")
    with open(path) as f:
        raw = json.load(f)
    return {**DEFAULT_CONFIG, **raw}

def apply_transform(index, config, width=8, height=8):
    x = index % width
    y = index // width

    rotation = config.get("rotation", 0)
    mirror_x = config.get("mirror_x", False)
    mirror_y = config.get("mirror_y", False)

    if rotation == 90:
        x, y = y, width - 1 - x
    elif rotation == 180:
        x, y = width - 1 - x, height - 1 - y
    elif rotation == 270:
        x, y = height - 1 - y, x

    if mirror_x:
        x = width - 1 - x
    if mirror_y:
        y = height - 1 - y

    return y * width + x
