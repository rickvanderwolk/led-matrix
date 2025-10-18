"""
Maze generation for pathfinding visualizer.
Generates random obstacles while ensuring a valid path exists.
"""
import random
from typing import List, Tuple, Set


class Maze:
    def __init__(self, width: int = 8, height: int = 8, obstacle_density: float = 0.20):
        """
        Initialize maze generator.

        Args:
            width: Width of the grid
            height: Height of the grid
            obstacle_density: Percentage of cells that should be obstacles (0.0 - 1.0)
        """
        self.width = width
        self.height = height
        self.obstacle_density = obstacle_density
        self.grid: List[List[bool]] = []  # True = obstacle, False = free
        self.start: Tuple[int, int] = (0, 0)
        self.goal: Tuple[int, int] = (width - 1, height - 1)

    def generate(self) -> Tuple[List[List[bool]], Tuple[int, int], Tuple[int, int]]:
        """
        Generate a new random maze with guaranteed path from start to goal.

        Returns:
            Tuple of (grid, start, goal) where grid[y][x] = True means obstacle
        """
        max_attempts = 100

        for attempt in range(max_attempts):
            # Generate random obstacles
            self.grid = [[False for _ in range(self.width)] for _ in range(self.height)]

            # Place start in top-left quadrant
            self.start = (random.randint(0, 2), random.randint(0, 2))

            # Place goal in bottom-right quadrant
            self.goal = (
                random.randint(self.width - 3, self.width - 1),
                random.randint(self.height - 3, self.height - 1)
            )

            # Make sure start and goal are different
            if self.start == self.goal:
                continue

            # Place random obstacles
            num_obstacles = int(self.width * self.height * self.obstacle_density)
            placed = 0

            while placed < num_obstacles:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)

                # Don't place obstacle on start or goal
                if (x, y) == self.start or (x, y) == self.goal:
                    continue

                # Don't place if already an obstacle
                if self.grid[y][x]:
                    continue

                self.grid[y][x] = True
                placed += 1

            # Verify that a path exists using simple BFS
            if self._path_exists():
                return self.grid, self.start, self.goal

        # Fallback: return empty maze if we couldn't generate valid one
        self.grid = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.start = (0, 0)
        self.goal = (self.width - 1, self.height - 1)
        return self.grid, self.start, self.goal

    def _path_exists(self) -> bool:
        """
        Check if a path exists from start to goal using simple BFS.

        Returns:
            True if path exists, False otherwise
        """
        visited: Set[Tuple[int, int]] = set()
        queue = [self.start]
        visited.add(self.start)

        while queue:
            x, y = queue.pop(0)

            if (x, y) == self.goal:
                return True

            # Check all 4 neighbors
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy

                # Check bounds
                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue

                # Check if already visited
                if (nx, ny) in visited:
                    continue

                # Check if obstacle
                if self.grid[ny][nx]:
                    continue

                visited.add((nx, ny))
                queue.append((nx, ny))

        return False

    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """
        Get valid (non-obstacle, in-bounds) neighbors of a cell.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            List of (x, y) tuples for valid neighbors
        """
        neighbors = []

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy

            # Check bounds
            if not (0 <= nx < self.width and 0 <= ny < self.height):
                continue

            # Check if obstacle
            if self.grid[ny][nx]:
                continue

            neighbors.append((nx, ny))

        return neighbors
