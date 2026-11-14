"""Small color helpers. Colors are (r, g, b) tuples with values 0-255."""

import colorsys

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def scale(color, factor):
    """Multiply a color by factor (dim below 1, brighten above 1), clamped to 0-255."""
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def mix(color1, color2, t=0.5):
    """Blend from color1 (t=0) to color2 (t=1)."""
    return tuple(int(a + (b - a) * t) for a, b in zip(color1, color2))


def hsv(h, s=1.0, v=1.0):
    """Color from hue (0-1, wraps), saturation (0-1) and value (0-1)."""
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))
