"""
Shared building blocks for LED matrix modes.

    from core import Matrix, hsv

    matrix = Matrix()
    for frame in matrix.frames(fps=30):
        matrix.clear()
        matrix[frame % 8, 3] = hsv(frame / 64)
"""

from .color import BLACK, WHITE, hsv, mix, scale


def __getattr__(name):
    # Imported lazily so main.py can use core.config without loading the LED hardware libraries
    if name == "Matrix":
        from .matrix import Matrix
        return Matrix
    raise AttributeError(f"module 'core' has no attribute {name!r}")


__all__ = ["Matrix", "BLACK", "WHITE", "hsv", "mix", "scale"]
