# Pathfinder

A visual demonstration of classic pathfinding algorithms on an 8x8 LED matrix. Watch how different algorithms explore randomly generated mazes to find paths from start to goal.

## Visual Legend

- **Green**: Start position (typically top-left quadrant)
- **Red**: Goal position (typically bottom-right quadrant)
- **Black**: Obstacles/walls (randomly generated)
- **Yellow**: Frontier nodes (currently being considered)
- **Blue**: Explored nodes (already visited)
- **White**: Final path from start to goal
- **Dim white**: Empty walkable cells

## Algorithms

The mode cycles through 4 different pathfinding algorithms:

### 1. Breadth-First Search (BFS)

**How it works**: BFS explores the maze level by level, visiting all neighbors at distance `n` before moving to distance `n+1`.

**Characteristics**:
- **Guarantee**: Always finds the shortest path
- **Exploration pattern**: Expands outward in a circular/wave pattern from start
- **Performance**: Explores many nodes but guaranteed optimal
- **Use case**: Best when you need the shortest path and all edges have equal cost

**What you'll see**: The blue exploration expands uniformly outward like ripples in water.

---

### 2. Depth-First Search (DFS)

**How it works**: DFS explores as far as possible along each branch before backtracking.

**Characteristics**:
- **Guarantee**: Finds *a* path, but NOT necessarily the shortest
- **Exploration pattern**: Goes deep into one direction before trying alternatives
- **Performance**: Can be fast if lucky, but may explore unnecessary areas
- **Use case**: Good for maze generation or when any path is acceptable

**What you'll see**: The blue exploration snakes deeply in one direction, creating long tendrils.

---

### 3. Dijkstra's Algorithm

**How it works**: Dijkstra's explores nodes in order of their total distance from the start, always picking the closest unexplored node.

**Characteristics**:
- **Guarantee**: Always finds the shortest path
- **Exploration pattern**: Similar to BFS but handles weighted edges (all edges = 1 in our case)
- **Performance**: Slightly more overhead than BFS but handles varying costs
- **Use case**: Best for weighted graphs (roads with different speeds, terrain costs)

**What you'll see**: Very similar to BFS - expands outward uniformly. On an unweighted grid, Dijkstra and BFS behave identically.

---

### 4. A* (A-Star) Algorithm

**How it works**: A* is like Dijkstra but uses a heuristic (Manhattan distance to goal) to guide exploration toward the target.

**Characteristics**:
- **Guarantee**: Finds the shortest path (when using an admissible heuristic)
- **Exploration pattern**: Focused toward the goal, explores fewer nodes
- **Performance**: Most efficient of the four algorithms
- **Use case**: Industry standard for game AI, robotics, GPS navigation

**What you'll see**: Blue exploration is biased toward the goal direction, exploring fewer nodes than BFS/Dijkstra.

---

## How the Visualization Works

1. **Maze Generation**: Random obstacles (15-30% density) are placed while ensuring a valid path exists
2. **Start/Goal Placement**: Start spawns in top-left area, goal in bottom-right area
3. **Algorithm Execution**: Each algorithm runs step-by-step with visual feedback
4. **Path Reconstruction**: Once the goal is found, the optimal path is highlighted in white
5. **Algorithm Cycle**: Cycles through BFS → DFS → Dijkstra → A* → repeat
6. **New Maze**: Each algorithm gets a fresh maze with different obstacles and positions

## Performance Comparison

On a typical 8x8 maze, you'll notice:

- **BFS & Dijkstra**: Explore many nodes but guaranteed shortest path
- **DFS**: Unpredictable - sometimes fast, sometimes explores almost everything
- **A***: Usually explores the fewest nodes thanks to its heuristic guidance

## Configuration

The mode runs automatically in sequence. To customize timing, edit `main.py`:

```python
STEP_DELAY = 0.05  # Seconds between each step (faster = harder to see)
PAUSE_AFTER_PATH = 2.0  # How long to show the final path
PAUSE_BEFORE_START = 1.0  # How long to show maze before algorithm starts
```

Maze difficulty varies automatically (15-30% obstacles). To change the range, edit `main.py`:

```python
obstacle_density = random.uniform(0.15, 0.30)  # Random between 15% and 30%
```

## Educational Value

This visualization demonstrates:

- **Algorithm behavior**: See how different algorithms make decisions
- **Trade-offs**: Speed vs optimality, exploration vs exploitation
- **Heuristics**: How A* uses domain knowledge (distance to goal) for efficiency
- **Graph theory**: Practical application of fundamental CS concepts

## Technical Details

- Grid size: 8x8 (64 LEDs)
- Maze validation: BFS check ensures path exists before visualization
- Neighbor exploration: 4-directional (up, down, left, right - no diagonals)
- Path reconstruction: Uses `came_from` dictionary to trace optimal path backward
- Update rate: ~20 steps/second (configurable)
