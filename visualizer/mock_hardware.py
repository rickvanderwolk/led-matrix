#!/usr/bin/env python3
"""
Mock hardware modules for LED matrix visualization.
This allows running the original LED scripts without actual hardware.
"""

class MockBoard:
    """Mock board module"""
    pass

# Add all common GPIO pins as module-level attributes
D18 = 18  # GPIO pin number (not used in visualization)

class MockNeoPixel:
    """Mock NeoPixel class that stores LED states for visualization"""

    _instances = []  # Track all instances for visualization access

    def __init__(self, pin, n, brightness=1.0, auto_write=True, pixel_order=None):
        self.pin = pin
        self.n = n
        self._brightness = brightness
        self.auto_write = auto_write
        self.pixel_order = pixel_order
        self._pixels = [(0, 0, 0)] * n
        self._callback = None
        MockNeoPixel._instances.append(self)

    def __len__(self):
        return self.n

    def __setitem__(self, index, val):
        """Set a pixel color"""
        if isinstance(index, slice):
            # Handle slice assignment
            start, stop, step = index.indices(self.n)
            for i in range(start, stop, step):
                self._pixels[i] = self._ensure_tuple(val)
        else:
            if 0 <= index < self.n:
                self._pixels[index] = self._ensure_tuple(val)

        if self.auto_write:
            self.show()

    def __getitem__(self, index):
        """Get a pixel color"""
        if isinstance(index, slice):
            return [self._pixels[i] for i in range(*index.indices(self.n))]
        return self._pixels[index]

    def _ensure_tuple(self, val):
        """Ensure value is a 3-tuple of integers"""
        if isinstance(val, (list, tuple)):
            r, g, b = val[0], val[1], val[2]
        else:
            r = g = b = val
        return (int(r), int(g), int(b))

    def fill(self, color):
        """Fill all pixels with the same color"""
        color = self._ensure_tuple(color)
        for i in range(self.n):
            self._pixels[i] = color
        if self.auto_write:
            self.show()

    def show(self):
        """Update the display (triggers visualization callback)"""
        if self._callback:
            self._callback(self._pixels.copy())

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, val):
        self._brightness = max(0.0, min(1.0, float(val)))

    def set_update_callback(self, callback):
        """Set a callback function to be called when pixels are updated"""
        self._callback = callback

    def get_pixels(self):
        """Get current pixel state"""
        return self._pixels.copy()

    @classmethod
    def get_latest_instance(cls):
        """Get the most recently created NeoPixel instance"""
        return cls._instances[-1] if cls._instances else None

    @classmethod
    def clear_instances(cls):
        """Clear all tracked instances"""
        cls._instances.clear()

# Create mock modules that scripts can import
board = MockBoard()

# Mock pixel order constants (actual values don't matter for visualization)
GRB = "GRB"
RGB = "RGB"
RGBW = "RGBW"
GRBW = "GRBW"

def NeoPixel(*args, **kwargs):
    """Factory function to create MockNeoPixel instances"""
    return MockNeoPixel(*args, **kwargs)
