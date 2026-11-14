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
import os
import sys
import random

# Add current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import Matrix
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


GRID_SIZE = 8

matrix = Matrix()

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


def draw_maze(matrix, grid, start, goal):
    """
    Draw the initial maze state.

    Args:
        matrix: Matrix object
        grid: 2D list where True = obstacle
        start: (x, y) tuple for start position
        goal: (x, y) tuple for goal position
    """
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if (x, y) == start:
                matrix[x, y] = COLOR_START
            elif (x, y) == goal:
                matrix[x, y] = COLOR_GOAL
            elif grid[y][x]:  # Obstacle
                matrix[x, y] = COLOR_OBSTACLE
            else:
                matrix[x, y] = COLOR_EMPTY

    matrix.show()


def run_algorithm(matrix, algorithm_class, algorithm_name, maze, start, goal):
    """
    Run a pathfinding algorithm and visualize it.

    Args:
        matrix: Matrix object
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
        pos = (step.x, step.y)

        if step.step_type == STEP_FRONTIER:
            frontier.add(pos)
            matrix[pos] = COLOR_FRONTIER

        elif step.step_type == STEP_EXPLORE:
            explored.add(pos)
            frontier.discard(pos)
            matrix[pos] = COLOR_EXPLORED

        elif step.step_type == STEP_PATH:
            matrix[pos] = COLOR_PATH

        # Keep start and goal visible
        matrix[start] = COLOR_START
        matrix[goal] = COLOR_GOAL

        matrix.show()
        time.sleep(STEP_DELAY)


def main():
    """Main loop."""
    # Algorithm sequence - cycles through all algorithms in order
    algorithms = [
        (BreadthFirstSearch, "BFS"),
        (DepthFirstSearch, "DFS"),
        (Dijkstra, "Dijkstra"),
        (AStar, "A*"),
    ]

    while True:
        # Generate ONE new maze for all algorithms to compare
        obstacle_density = random.uniform(0.15, 0.30)
        maze = Maze(width=GRID_SIZE, height=GRID_SIZE, obstacle_density=obstacle_density)
        grid, start, goal = maze.generate()

        # Run ALL algorithms on the SAME maze
        for algorithm_class, algorithm_name in algorithms:
            # Draw initial maze
            draw_maze(matrix, grid, start, goal)
            time.sleep(PAUSE_BEFORE_START)

            # Run this algorithm
            run_algorithm(matrix, algorithm_class, algorithm_name, maze, start, goal)

            # Pause to show result
            time.sleep(PAUSE_AFTER_PATH)


# Start the visualization immediately when module is imported
# (required for visualizer to work)
main()
