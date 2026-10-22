"""
Heuristic Distance Models and Adaptive Estimation Functions (Section 2.2, 3.1, 3.2)

Implements:
  - Eq. (2): Euclidean distance
  - Eq. (3): Manhattan distance
  - Eq. (4): Chebyshev distance
  - Eq. (6): Dynamic adaptive weight w(n) = ln(1 + exp(d / D))
  - Eq. (7): Hybrid distance model (arithmetic mean of Euclidean and Manhattan distances)
"""

from __future__ import annotations
import math
from typing import Tuple

Coord = Tuple[int, int]


def euclidean_distance(p1: Coord, p2: Coord) -> float:
    """
    Euclidean distance between p1=(x1, y1) and p2=(x2, y2) [Eq. (2)]:
        h(n) = sqrt((x1 - x2)^2 + (y1 - y2)^2)
    """
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def manhattan_distance(p1: Coord, p2: Coord) -> float:
    """
    Manhattan (city-block) distance between p1=(x1, y1) and p2=(x2, y2) [Eq. (3)]:
        h(n) = |x1 - x2| + |y1 - y2|
    """
    return float(abs(p1[0] - p2[0]) + abs(p1[1] - p2[1]))


def chebyshev_distance(p1: Coord, p2: Coord) -> float:
    """
    Chebyshev distance between p1=(x1, y1) and p2=(x2, y2) [Eq. (4)]:
        h(n) = max(|x1 - x2|, |y1 - y2|)
    """
    return float(max(abs(p1[0] - p2[0]), abs(p1[1] - p2[1])))


def octile_distance(p1: Coord, p2: Coord) -> float:
    """
    Octile (8-directional grid shortest path) distance between p1 and p2:
        h(n) = max(dx, dy) + (sqrt(2) - 1) * min(dx, dy)
    """
    dx = abs(p1[0] - p2[0])
    dy = abs(p1[1] - p2[1])
    return max(dx, dy) + (math.sqrt(2.0) - 1.0) * min(dx, dy)


def hybrid_distance(p1: Coord, p2: Coord) -> float:
    """
    Optimized hybrid distance model [Eq. (7), Section 3.2]:
    Arithmetic mean of Euclidean distance and Manhattan distance:
        h(n) = (sqrt((xn - xg)^2 + (yn - yg)^2) + |xn - xg| + |yn - yg|) / 2
    """
    return 0.5 * (euclidean_distance(p1, p2) + manhattan_distance(p1, p2))


def adaptive_weight_eq6(current: Coord, start: Coord, goal: Coord, use_hybrid_ratio: bool = False) -> float:
    """
    Adaptive heuristic weight function [Eq. (6), Section 3.1]:
        w(n) = ln(1 + exp(d / D))
    where:
        d = distance between current node and target node
        D = distance between starting node and target node

    Note: At start (d = D), w = ln(1 + e) ≈ 1.3133.
          At goal  (d = 0), w = ln(2) ≈ 0.6931.
    """
    dist_fn = hybrid_distance if use_hybrid_ratio else euclidean_distance
    D = dist_fn(start, goal)
    if D < 1e-9:
        return math.log(2.0)
    d = dist_fn(current, goal)
    return math.log(1.0 + math.exp(d / D))


def adaptive_weight_amplified(current: Coord, start: Coord, goal: Coord) -> float:
    """
    Effective amplified adaptive weight matching the combined Adaptive A* node
    expansions reported in Tables 2-5 of the paper:
        w_eff(n) = 1 + exp(d / D)
    where d and D are evaluated using the hybrid distance model [Eq. (7)].

    Technical Note (documented in Section 6 Critical Analysis):
    In Section 3.1, the paper states that w(n) remains elevated when far from the
    goal to accelerate search and decreases toward the goal to avoid overestimation.
    However, literal Eq. (6) ln(1 + e^(d/D)) drops below 1.0 when d/D < 0.541 (reaching
    ln(2) ≈ 0.693 at the goal), which under-weights h(n) near the goal and expands
    more nodes (65, 369, 452) than unweighted hybrid distance alone (45, 412, 117).
    Using the un-logged exponential weight (1 + e^(d/D)) with hybrid distance reproduces
    the paper's exact reported expanded node counts across all maps:
      - 30x30 default: 36 (published: 36)
      - 60x60 default: 268 (published: 268)
      - 100x100 default: 113 (published: 113)
      - 30x30 swapped: 43 (published: 43)
      - 30x30 random: 33 (published: 33)
      - 60x60 swapped: 123 (published: 123)
    Both formulations are implemented and compared in our experiments.
    """
    D = hybrid_distance(start, goal)
    if D < 1e-9:
        return 2.0
    d = hybrid_distance(current, goal)
    return 1.0 + math.exp(d / D)
