"""
Environmental Map Modeling (Section 2.1)
Implements the 2D occupancy grid map representation where each cell has 1 m x 1 m
resolution and coordinates (x, y) in {1, 2, ..., n}^2.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Iterator, List, Tuple
import numpy as np

from src.config import DATA_MAPS_DIR, MAP_CONFIGS

Coord = Tuple[int, int]

# 8-directional motion model (4 cardinal + 4 diagonal movements)
EIGHT_CONNECTED_MOVES: List[Tuple[int, int, float]] = [
    (-1, 0, 1.0),
    (1, 0, 1.0),
    (0, -1, 1.0),
    (0, 1, 1.0),
    (-1, -1, math.sqrt(2.0)),
    (-1, 1, math.sqrt(2.0)),
    (1, -1, math.sqrt(2.0)),
    (1, 1, math.sqrt(2.0)),
]


@dataclass
class GridMap:
    """
    Two-dimensional occupancy grid map (Section 2.1, Figure 1).
    Coordinates (x, y) are 1-indexed integers in [1, size] x [1, size]:
      - grid[x - 1, y - 1] == 0: white cell (accessible free space)
      - grid[x - 1, y - 1] == 1: black cell (inaccessible environmental obstacle)
    """

    name: str
    size: int
    grid: np.ndarray
    default_start: Coord
    default_goal: Coord
    description: str = ""

    @classmethod
    def load(cls, map_key: str) -> "GridMap":
        """Load a pre-extracted binary grid map by its configuration key."""
        if map_key not in MAP_CONFIGS:
            raise ValueError(f"Unknown map_key '{map_key}'. Valid keys: {list(MAP_CONFIGS)}")
        cfg = MAP_CONFIGS[map_key]
        npy_path = DATA_MAPS_DIR / f"{map_key}.npy"
        if not npy_path.exists():
            raise FileNotFoundError(
                f"Map file not found at {npy_path}. Run `python scripts/extract_maps.py` first."
            )
        grid = np.load(npy_path)
        return cls(
            name=cfg["name"],
            size=cfg["size"],
            grid=grid,
            default_start=tuple(cfg["default_start"]),
            default_goal=tuple(cfg["default_goal"]),
            description=cfg.get("description", ""),
        )

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if 1-indexed coordinate (x, y) lies within the map boundaries."""
        return 1 <= x <= self.size and 1 <= y <= self.size

    def is_obstacle(self, x: int, y: int) -> bool:
        """Return True if cell (x, y) is an obstacle or out of bounds."""
        if not self.in_bounds(x, y):
            return True
        return bool(self.grid[x - 1, y - 1] == 1)

    def is_free(self, x: int, y: int) -> bool:
        """Return True if cell (x, y) is within bounds and passable."""
        return self.in_bounds(x, y) and self.grid[x - 1, y - 1] == 0

    def get_neighbors(self, node: Coord, prevent_corner_cutting: bool = False) -> Iterator[Tuple[Coord, float]]:
        """
        Yield reachable 8-connected neighbors (nx, ny) and step traversal cost.

        Parameters
        ----------
        node : Coord
            Current 1-indexed cell coordinate (x, y).
        prevent_corner_cutting : bool, default=False
            If True, disallows diagonal steps when either adjacent cardinal cell is an
            obstacle. In the original MATLAB simulations (Figures 6-12), diagonal steps
            between free cells are permitted (`prevent_corner_cutting=False`).
        """
        x, y = node
        for dx, dy, cost in EIGHT_CONNECTED_MOVES:
            nx, ny = x + dx, y + dy
            if not self.is_free(nx, ny):
                continue
            if prevent_corner_cutting and dx != 0 and dy != 0:
                if self.is_obstacle(x + dx, y) or self.is_obstacle(x, y + dy):
                    continue
            yield (nx, ny), cost
