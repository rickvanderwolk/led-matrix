# Pathfinder

A visual demonstration of classic pathfinding algorithms on an 8x8 LED matrix. Watch how different algorithms explore randomly generated mazes to find paths from start to goal.

## Visual Legend

- **Teal/Cyan**: Start position (typically top-left quadrant)
- **Soft Red**: Goal position (typically bottom-right quadrant)
- **Dark Gray**: Obstacles/walls (randomly generated)
- **Black**: Empty walkable cells (clean background)
- **Warm Amber**: Frontier nodes (currently being considered)
- **Deep Blue**: Explored nodes (already visited)
- **White**: Final path from start to goal

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

1. **Maze Generation**: A random maze is created with obstacles (15-30% density) while ensuring a valid path exists
2. **Start/Goal Placement**: Start spawns in top-left area, goal in bottom-right area
3. **Algorithm Comparison**: All 4 algorithms solve the SAME maze in sequence:
   - BFS runs first and shows its solution
   - DFS gets the same maze and shows its solution
   - Dijkstra gets the same maze and shows its solution
   - A* gets the same maze and shows its solution
4. **Path Visualization**: Each algorithm runs step-by-step with visual feedback, showing explored nodes (blue), frontier (yellow), and final path (white)
5. **New Maze**: After all 4 algorithms have completed, a completely new maze is generated and the cycle repeats

## Performance Comparison

Since all algorithms solve the SAME maze, you can directly compare their strategies:

- **BFS & Dijkstra**: Will find the exact same shortest path, explore similar numbers of nodes in a wave pattern
- **DFS**: May find a different (often longer) path, exploration pattern is more "snaky" and unpredictable
- **A***: Finds the same shortest path as BFS/Dijkstra but explores significantly fewer nodes thanks to its goal-directed heuristic

**Watch closely**: On the same maze, you'll see A* "aim" toward the goal while BFS spreads out evenly in all directions!

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
