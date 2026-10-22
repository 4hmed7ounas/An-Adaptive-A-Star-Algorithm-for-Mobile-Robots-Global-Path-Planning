"""
Redundant Point Deletion Strategy (Section 3.3, Figure 4)

Implements the 4-step path post-processing and smoothing method:
  Step 1: Acquire the collection of path nodes generated through the algorithm.
  Step 2: Collinearity determination: if three consecutive nodes (A, B, C) are
          collinear and obstacle-free, delete intermediate node B.
  Step 3: If (A, B, C) are not collinear, connect A and C and check whether the
          connection line traverses any obstacle. If obstacle-free, eliminate
          intermediate node B; otherwise preserve B and advance to the next node.
  Step 4: Link all remaining path nodes to form the smoothed path.
"""

from __future__ import annotations
import math
from typing import List, Tuple

from src.maps import GridMap

Coord = Tuple[int, int]


def are_collinear(a: Coord, b: Coord, c: Coord) -> bool:
    """
    Return True if 2D points a, b, c are collinear (cross product == 0)
    and b lies monotonically between a and c.
    """
    abx, aby = b[0] - a[0], b[1] - a[1]
    bcx, bcy = c[0] - b[0], c[1] - b[1]
    cross = abx * bcy - aby * bcx
    dot = abx * bcx + aby * bcy
    return cross == 0 and dot >= 0


def remove_collinear_nodes(path: List[Coord]) -> List[Coord]:
    """
    Step 2 only: Eliminate collinear intermediate points along the grid path.
    """
    if len(path) <= 2:
        return list(path)
    cleaned: List[Coord] = [path[0]]
    for i in range(1, len(path) - 1):
        if not are_collinear(cleaned[-1], path[i], path[i + 1]):
            cleaned.append(path[i])
    cleaned.append(path[-1])
    return cleaned


def line_of_sight_clear(
    grid_map: GridMap,
    p1: Coord,
    p2: Coord,
    obstacle_half_width: float = 0.30,
    samples_per_unit: int = 20,
) -> bool:
    """
    Step 3 collision check: Determine whether the straight line segment from p1 to p2
    traverses any environmental obstacle cell.

    Each obstacle cell centered at integer coordinate (ix, iy) is modeled with an
    effective collision bounding box [ix - r, ix + r] x [iy - r, iy + r] where
    r = `obstacle_half_width` (< 0.5). Since r < 0.5, at most one integer grid cell
    (ix = int(x + 0.5), iy = int(y + 0.5)) can lie within L_infinity distance r of
    any sampled point (x, y).
    """
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    dist = math.hypot(dx, dy)
    if dist < 1e-9:
        return True

    steps = max(2, int(math.ceil(dist * samples_per_unit)))
    grid = grid_map.grid
    r = obstacle_half_width
    inv_steps = 1.0 / steps

    for s in range(1, steps):
        t = s * inv_steps
        x = x1 + t * dx
        y = y1 + t * dy
        ix = int(x + 0.5)
        iy = int(y + 0.5)
        if abs(x - ix) <= r and abs(y - iy) <= r:
            if grid[ix - 1, iy - 1] == 1:
                return False
    return True


def delete_redundant_points(
    grid_map: GridMap,
    path: List[Coord],
    obstacle_half_width: float = 0.30,
) -> List[Coord]:
    """
    Execute Steps 1-4 of the Redundant Point Deletion Strategy (Section 3.3, Figure 4).

    Starting from the origin node A = path[i], iteratively test subsequent nodes
    C = path[j+1]. If (A, B, C) is collinear or the line segment AC does not
    traverse any obstacle, eliminate the intermediate node B and continue testing
    the next node; when an obstacle is encountered along AC, preserve the last valid
    node B as the new anchor A and repeat until the goal node is reached.
    """
    if len(path) <= 2:
        return list(path)

    nodes = list(path)
    smoothed: List[Coord] = [nodes[0]]
    i = 0
    n = len(nodes)
    while i < n - 1:
        j = i + 1
        while j + 1 < n:
            a, c = nodes[i], nodes[j + 1]
            if line_of_sight_clear(grid_map, a, c, obstacle_half_width, samples_per_unit=20):
                j += 1
            else:
                break
        smoothed.append(nodes[j])
        i = j

    return smoothed
