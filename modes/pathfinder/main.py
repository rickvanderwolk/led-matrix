"""
Pathfinding Visualizer Mode for LED Matrix

Visualizes different pathfinding algorithms (BFS, DFS, Dijkstra, A*) on an 8x8 LED grid.
Each algorithm finds a path through a randomly generated maze with obstacles.

Color coding:
- Green: Start position
- Red: Goal position
- Black: Obstacles/walls
- Blue: Explored nodes
- Yellow: Frontier nodes (being considered)
- White: Final path
"""

import time
import json
import os
import sys
import random

# Add current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import board
    import neopixel
except (ImportError, NotImplementedError):
    # Allow imports to work in visualizer environment
    pass

from maze import Maze
from algorithms import (
    BreadthFirstSearch,
    DepthFirstSearch,
    Dijkstra,
    AStar,
    STEP_EXPLORE,
    STEP_FRONTIER,
    STEP_PATH,
)


# LED Configuration
LED_COUNT = 64
PIN = board.D18
GRID_SIZE = 8

# Load config
CONFIG_PATH = os.environ.get("LEDMATRIX_CONFIG", "config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

BRIGHTNESS = config.get("brightness", 0.2)

# Initialize LED strip at module level (required for visualizer)
pixels = neopixel.NeoPixel(
    PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False
)

# Colors (R, G, B) - Modern, elegant palette
COLOR_START = (0, 200, 100)  # Teal/cyan (fresh, distinct)
COLOR_GOAL = (255, 80, 80)  # Soft red (clear but not harsh)
COLOR_OBSTACLE = (60, 60, 60)  # Dark gray (subtle walls)
COLOR_EMPTY = (0, 0, 0)  # Pure black (clean background)
COLOR_FRONTIER = (200, 150, 0)  # Warm amber (exploration edge)
COLOR_EXPLORED = (40, 40, 120)  # Deep blue (visited areas)
COLOR_PATH = (255, 255, 255)  # Pure white (final path stands out)

# Timing
STEP_DELAY = 0.05  # Seconds between visualization steps
PAUSE_AFTER_PATH = 2.0  # Seconds to show final path before next algorithm
PAUSE_BEFORE_START = 1.0  # Seconds to show maze before algorithm starts


def coord_to_index(x: int, y: int) -> int:
    """Convert grid coordinates to LED index."""
    return y * GRID_SIZE + x


def draw_maze(pixels, grid, start, goal):
    """
    Draw the initial maze state.

    Args:
        pixels: NeoPixel object
        grid: 2D list where True = obstacle
        start: (x, y) tuple for start position
        goal: (x, y) tuple for goal position
    """
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            idx = coord_to_index(x, y)

            if (x, y) == start:
                pixels[idx] = COLOR_START
            elif (x, y) == goal:
                pixels[idx] = COLOR_GOAL
            elif grid[y][x]:  # Obstacle
                pixels[idx] = COLOR_OBSTACLE
            else:
                pixels[idx] = COLOR_EMPTY

    pixels.show()


def run_algorithm(pixels, algorithm_class, algorithm_name, maze, start, goal):
    """
    Run a pathfinding algorithm and visualize it.

    Args:
        pixels: NeoPixel object
        algorithm_class: Class of the algorithm to run
        algorithm_name: Name for display/debugging
        maze: Maze object
        start: Start position tuple
        goal: Goal position tuple
    """
    # Initialize algorithm
    algorithm = algorithm_class(maze, start, goal)

    # Track explored nodes for visualization
    explored = set()
    frontier = set()

    # Run algorithm and visualize steps
    for step in algorithm.find_path():
        idx = coord_to_index(step.x, step.y)

        if step.step_type == STEP_FRONTIER:
            frontier.add((step.x, step.y))
            pixels[idx] = COLOR_FRONTIER

        elif step.step_type == STEP_EXPLORE:
            explored.add((step.x, step.y))
            if (step.x, step.y) in frontier:
                frontier.remove((step.x, step.y))
            pixels[idx] = COLOR_EXPLORED

        elif step.step_type == STEP_PATH:
            pixels[idx] = COLOR_PATH

        # Keep start and goal visible
        pixels[coord_to_index(*start)] = COLOR_START
        pixels[coord_to_index(*goal)] = COLOR_GOAL

        pixels.show()
        time.sleep(STEP_DELAY)


def main():
    """Main loop."""
    global pixels  # Use the module-level pixels instance

    # Algorithm sequence - cycles through all algorithms in order
    algorithms = [
        (BreadthFirstSearch, "BFS"),
        (DepthFirstSearch, "DFS"),
        (Dijkstra, "Dijkstra"),
        (AStar, "A*"),
    ]

    try:
        while True:
            # Generate ONE new maze for all algorithms to compare
            obstacle_density = random.uniform(0.15, 0.30)
            maze = Maze(width=GRID_SIZE, height=GRID_SIZE, obstacle_density=obstacle_density)
            grid, start, goal = maze.generate()

            # Run ALL algorithms on the SAME maze
            for algorithm_class, algorithm_name in algorithms:
                # Draw initial maze
                draw_maze(pixels, grid, start, goal)
                time.sleep(PAUSE_BEFORE_START)

                # Run this algorithm
                run_algorithm(pixels, algorithm_class, algorithm_name, maze, start, goal)

                # Pause to show result
                time.sleep(PAUSE_AFTER_PATH)

    except KeyboardInterrupt:
        print("\nShutting down...")
        pixels.fill((0, 0, 0))
        pixels.show()


# Start the visualization immediately when module is imported
# (required for visualizer to work)
main()
