#!/usr/bin/env python3
"""
LED Matrix Visualizer GUI
Displays a virtual 8x8 LED matrix using PyGame
"""

import pygame
import sys
import threading
import time

class LEDMatrixVisualizer:
    """PyGame-based visualizer for 8x8 LED matrix"""

    def __init__(self, width=8, height=8, led_size=60, spacing=5, title="LED Matrix Visualizer"):
        """
        Initialize the visualizer

        Args:
            width: Number of LEDs horizontally (default 8)
            height: Number of LEDs vertically (default 8)
            led_size: Size of each LED in pixels (default 60)
            spacing: Spacing between LEDs in pixels (default 5)
            title: Window title
        """
        self.width = width
        self.height = height
        self.led_count = width * height
        self.led_size = led_size
        self.spacing = spacing

        # Calculate window size
        self.window_width = width * (led_size + spacing) + spacing
        self.window_height = height * (led_size + spacing) + spacing + 40  # +40 for status bar

        # Initialize PyGame
        pygame.init()
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption(title)

        # LED states (RGB tuples)
        self.pixels = [(0, 0, 0)] * self.led_count

        # Control flags
        self.running = True
        self.paused = False
        self.brightness = 1.0

        # Font for status text
        self.font = pygame.font.Font(None, 24)

        # FPS tracking
        self.clock = pygame.time.Clock()
        self.fps = 60

    def set_pixels(self, pixels):
        """Update all pixel colors"""
        if len(pixels) == self.led_count:
            self.pixels = [self._apply_brightness(p) for p in pixels]

    def set_pixel(self, index, color):
        """Update a single pixel color"""
        if 0 <= index < self.led_count:
            self.pixels[index] = self._apply_brightness(color)

    def _apply_brightness(self, color):
        """Apply brightness adjustment to a color"""
        return tuple(int(c * self.brightness) for c in color)

    def set_brightness(self, brightness):
        """Set display brightness (0.0 - 1.0)"""
        self.brightness = max(0.0, min(1.0, brightness))

    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused

    def draw(self):
        """Draw the LED matrix"""
        # Clear screen with dark background
        self.screen.fill((20, 20, 20))

        # Draw each LED
        for y in range(self.height):
            for x in range(self.width):
                # Convert x,y to LED index (left to right, top to bottom)
                index = y * self.width + x

                # Calculate position
                px = self.spacing + x * (self.led_size + self.spacing)
                py = self.spacing + y * (self.led_size + self.spacing)

                # Get color
                color = self.pixels[index] if index < len(self.pixels) else (0, 0, 0)

                # Draw LED background (dark circle)
                pygame.draw.circle(
                    self.screen,
                    (40, 40, 40),
                    (px + self.led_size // 2, py + self.led_size // 2),
                    self.led_size // 2
                )

                # Draw LED (colored circle)
                if color != (0, 0, 0):
                    pygame.draw.circle(
                        self.screen,
                        color,
                        (px + self.led_size // 2, py + self.led_size // 2),
                        self.led_size // 2 - 2
                    )

        # Draw status bar
        status_y = self.height * (self.led_size + self.spacing) + self.spacing + 10

        status_text = f"FPS: {int(self.clock.get_fps())} | "
        status_text += f"Brightness: {int(self.brightness * 100)}% | "
        status_text += "PAUSED" if self.paused else "Running"
        status_text += " | Q:Quit SPACE:Pause +/-:Brightness"

        text_surface = self.font.render(status_text, True, (200, 200, 200))
        self.screen.blit(text_surface, (10, status_y))

        # Update display
        pygame.display.flip()
        self.clock.tick(self.fps)

    def handle_events(self):
        """Handle PyGame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.toggle_pause()
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    self.set_brightness(self.brightness + 0.1)
                elif event.key == pygame.K_MINUS:
                    self.set_brightness(self.brightness - 0.1)

    def run(self):
        """Main visualization loop (blocking)"""
        while self.running:
            self.handle_events()
            self.draw()

        pygame.quit()

    def update(self):
        """Single update cycle (for non-blocking usage)"""
        if not self.running:
            return False

        self.handle_events()
        self.draw()
        return True

    def close(self):
        """Close the visualizer"""
        self.running = False
        pygame.quit()


class ThreadedVisualizer:
    """Wrapper to run visualizer in a separate thread"""

    def __init__(self, **kwargs):
        self.visualizer = LEDMatrixVisualizer(**kwargs)
        self.thread = None
        self.started = False

    def start(self):
        """Start the visualizer in a background thread"""
        if not self.started:
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            self.started = True
            time.sleep(0.1)  # Give PyGame time to initialize

    def _run(self):
        """Run the visualizer loop"""
        self.visualizer.run()

    def set_pixels(self, pixels):
        """Update pixel colors"""
        if self.started:
            self.visualizer.set_pixels(pixels)

    def is_running(self):
        """Check if visualizer is still running"""
        return self.visualizer.running

    def close(self):
        """Close the visualizer"""
        self.visualizer.close()
        if self.thread:
            self.thread.join(timeout=1.0)


if __name__ == "__main__":
    # Test the visualizer with a simple animation
    viz = LEDMatrixVisualizer()

    # Create a test pattern
    import random

    frame = 0
    while viz.running:
        # Random sparkle effect
        pixels = [(0, 0, 0)] * 64
        for _ in range(10):
            idx = random.randint(0, 63)
            pixels[idx] = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )

        viz.set_pixels(pixels)
        viz.handle_events()
        viz.draw()

        frame += 1

    viz.close()
