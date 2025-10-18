"""
Pathfinding algorithms for visualization.
Each algorithm yields visualization steps for smooth animation.
"""
from typing import List, Tuple, Set, Dict, Optional, Generator
from collections import deque
import heapq


# Visualization step types
STEP_EXPLORE = "explore"  # Algorithm is exploring this node
STEP_FRONTIER = "frontier"  # Node added to frontier/queue
STEP_PATH = "path"  # Node is part of final path


class VisualizationStep:
    """Represents a single step in the pathfinding visualization."""

    def __init__(self, x: int, y: int, step_type: str):
        self.x = x
        self.y = y
        self.step_type = step_type


class PathfindingAlgorithm:
    """Base class for pathfinding algorithms."""

    def __init__(self, maze, start: Tuple[int, int], goal: Tuple[int, int]):
        self.maze = maze
        self.start = start
        self.goal = goal
        self.width = maze.width
        self.height = maze.height

    def find_path(self) -> Generator[VisualizationStep, None, None]:
        """
        Find path from start to goal, yielding visualization steps.

        Yields:
            VisualizationStep objects for animation
        """
        raise NotImplementedError

    def _reconstruct_path(
        self, came_from: Dict[Tuple[int, int], Tuple[int, int]]
    ) -> List[Tuple[int, int]]:
        """
        Reconstruct path from came_from dict.

        Args:
            came_from: Dict mapping node to its predecessor

        Returns:
            List of (x, y) coordinates from start to goal
        """
        path = []
        current = self.goal

        while current in came_from:
            path.append(current)
            current = came_from[current]

        path.append(self.start)
        path.reverse()
        return path


class BreadthFirstSearch(PathfindingAlgorithm):
    """Breadth-First Search - explores level by level."""

    def find_path(self) -> Generator[VisualizationStep, None, None]:
        visited: Set[Tuple[int, int]] = set()
        queue = deque([self.start])
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        visited.add(self.start)

        while queue:
            current = queue.popleft()
            x, y = current

            # Visualize exploration
            if current != self.start and current != self.goal:
                yield VisualizationStep(x, y, STEP_EXPLORE)

            # Check if we reached the goal
            if current == self.goal:
                # Reconstruct and visualize path
                path = self._reconstruct_path(came_from)
                for px, py in path:
                    if (px, py) != self.start and (px, py) != self.goal:
                        yield VisualizationStep(px, py, STEP_PATH)
                return

            # Explore neighbors
            for neighbor in self.maze.get_neighbors(x, y):
                if neighbor not in visited:
                    visited.add(neighbor)
                    came_from[neighbor] = current
                    queue.append(neighbor)

                    # Visualize frontier
                    nx, ny = neighbor
                    if neighbor != self.goal:
                        yield VisualizationStep(nx, ny, STEP_FRONTIER)


class DepthFirstSearch(PathfindingAlgorithm):
    """Depth-First Search - explores deeply before backtracking."""

    def find_path(self) -> Generator[VisualizationStep, None, None]:
        visited: Set[Tuple[int, int]] = set()
        stack = [self.start]
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        visited.add(self.start)

        while stack:
            current = stack.pop()
            x, y = current

            # Visualize exploration
            if current != self.start and current != self.goal:
                yield VisualizationStep(x, y, STEP_EXPLORE)

            # Check if we reached the goal
            if current == self.goal:
                # Reconstruct and visualize path
                path = self._reconstruct_path(came_from)
                for px, py in path:
                    if (px, py) != self.start and (px, py) != self.goal:
                        yield VisualizationStep(px, py, STEP_PATH)
                return

            # Explore neighbors (reversed for more natural DFS)
            neighbors = self.maze.get_neighbors(x, y)
            neighbors.reverse()

            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    came_from[neighbor] = current
                    stack.append(neighbor)

                    # Visualize frontier
                    nx, ny = neighbor
                    if neighbor != self.goal:
                        yield VisualizationStep(nx, ny, STEP_FRONTIER)


class Dijkstra(PathfindingAlgorithm):
    """Dijkstra's algorithm - finds shortest path using uniform cost."""

    def find_path(self) -> Generator[VisualizationStep, None, None]:
        visited: Set[Tuple[int, int]] = set()
        # Priority queue: (cost, node)
        pq = [(0, self.start)]
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        cost_so_far: Dict[Tuple[int, int], int] = {self.start: 0}

        while pq:
            current_cost, current = heapq.heappop(pq)
            x, y = current

            if current in visited:
                continue

            visited.add(current)

            # Visualize exploration
            if current != self.start and current != self.goal:
                yield VisualizationStep(x, y, STEP_EXPLORE)

            # Check if we reached the goal
            if current == self.goal:
                # Reconstruct and visualize path
                path = self._reconstruct_path(came_from)
                for px, py in path:
                    if (px, py) != self.start and (px, py) != self.goal:
                        yield VisualizationStep(px, py, STEP_PATH)
                return

            # Explore neighbors
            for neighbor in self.maze.get_neighbors(x, y):
                new_cost = current_cost + 1  # All edges have cost 1

                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    came_from[neighbor] = current
                    heapq.heappush(pq, (new_cost, neighbor))

                    # Visualize frontier
                    nx, ny = neighbor
                    if neighbor != self.goal and neighbor not in visited:
                        yield VisualizationStep(nx, ny, STEP_FRONTIER)


class AStar(PathfindingAlgorithm):
    """A* algorithm - finds shortest path using heuristic (Manhattan distance)."""

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        """Manhattan distance heuristic."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def find_path(self) -> Generator[VisualizationStep, None, None]:
        visited: Set[Tuple[int, int]] = set()
        # Priority queue: (f_score, node) where f_score = g_score + heuristic
        pq = [(0, self.start)]
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], int] = {self.start: 0}

        while pq:
            _, current = heapq.heappop(pq)
            x, y = current

            if current in visited:
                continue

            visited.add(current)

            # Visualize exploration
            if current != self.start and current != self.goal:
                yield VisualizationStep(x, y, STEP_EXPLORE)

            # Check if we reached the goal
            if current == self.goal:
                # Reconstruct and visualize path
                path = self._reconstruct_path(came_from)
                for px, py in path:
                    if (px, py) != self.start and (px, py) != self.goal:
                        yield VisualizationStep(px, py, STEP_PATH)
                return

            # Explore neighbors
            for neighbor in self.maze.get_neighbors(x, y):
                tentative_g = g_score[current] + 1

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self._heuristic(neighbor, self.goal)
                    heapq.heappush(pq, (f_score, neighbor))

                    # Visualize frontier
                    nx, ny = neighbor
                    if neighbor != self.goal and neighbor not in visited:
                        yield VisualizationStep(nx, ny, STEP_FRONTIER)
