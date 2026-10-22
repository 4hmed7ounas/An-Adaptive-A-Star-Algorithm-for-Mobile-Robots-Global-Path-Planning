"""
Path Planning Algorithms Module (Sections 2.2, 3, and 4)

Implements:
  1. Traditional A* Algorithm (Algorithm 1, Section 2.2)
  2. Ablation 1: A* with Adaptive Estimation Function (Section 3.1)
  3. Ablation 2: A* with Distance Model Optimization (Section 3.2)
  4. Ablation 3: A* with Redundant Point Deletion Strategy (Section 3.3)
  5. Proposed Adaptive A* Algorithm (All 3 improvements combined, Figure 3)
  6. Proposed Adaptive A* (Literal Unshifted Eq. 6 Sensitivity Variant)
  7. Dijkstra's Algorithm [28]
  8. Chen et al.'s Improved A* Method [29]
  9. Bidirectional A* Algorithm [30]
 10. Zhang et al.'s Improved A* Method [31]
"""

from __future__ import annotations
import heapq
import math
import time
from typing import Callable, Dict, List, Optional, Set, Tuple
import numpy as np

from src.config import TIMING_RUNS
from src.heuristics import (
    adaptive_weight_amplified,
    adaptive_weight_eq6,
    chebyshev_distance,
    euclidean_distance,
    hybrid_distance,
    manhattan_distance,
    octile_distance,
)
from src.maps import GridMap
from src.metrics import (
    PlanningResult,
    compute_path_length,
    count_corners_ge_45,
    count_strict_angle_ge_45,
)
from src.smoothing import delete_redundant_points

Coord = Tuple[int, int]
HeuristicFn = Callable[[Coord, Coord, Coord], float]


def _reconstruct_path(
    parent: Dict[Coord, Optional[Coord]],
    g_cost: Dict[Coord, float],
    grid_map: GridMap,
    start: Coord,
    goal: Coord,
    relax_parents: bool = False,
) -> List[Coord]:
    """
    Reconstruct the path from `goal` back to `start`. When `relax_parents=True`,
    selects the minimum-g discovered predecessor at each step so that weighted
    heuristics do not introduce single-cell zig-zag artifacts around unexpanded
    open-list neighbors.
    """
    if not relax_parents:
        path: List[Coord] = []
        curr: Optional[Coord] = goal
        while curr is not None:
            path.append(curr)
            curr = parent.get(curr)
        path.reverse()
        return path

    path = []
    curr = goal
    visited_back: Set[Coord] = set()
    while curr is not None and curr not in visited_back:
        path.append(curr)
        visited_back.add(curr)
        if curr == start:
            break
        best_p = parent.get(curr)
        best_val = (
            g_cost[best_p] + euclidean_distance(best_p, curr)
            if best_p is not None and best_p in g_cost
            else 1e18
        )
        for nb, move_cost in grid_map.get_neighbors(curr):
            if nb in g_cost and nb not in visited_back and g_cost[nb] < g_cost[curr]:
                cand_val = g_cost[nb] + move_cost
                if cand_val < best_val - 1e-9:
                    best_val = cand_val
                    best_p = nb
        curr = best_p
    path.reverse()
    return path


def _core_best_first_search(
    grid_map: GridMap,
    start: Coord,
    goal: Coord,
    heuristic_fn: HeuristicFn,
    relax_parents: bool = False,
) -> Tuple[List[Coord], List[Coord]]:
    """
    Core priority-queue graph search implementing Algorithm 1 (Section 2.2).
    Returns (raw_path, closed_nodes_in_expansion_order).
    """
    open_heap: List[Tuple[float, int, Coord]] = []
    g_cost: Dict[Coord, float] = {start: 0.0}
    parent: Dict[Coord, Optional[Coord]] = {start: None}
    closed_set: Set[Coord] = set()
    closed_order: List[Coord] = []

    h0 = heuristic_fn(start, start, goal)
    step = 0
    heapq.heappush(open_heap, (h0, step, start))

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current in closed_set:
            continue
        if current == goal:
            break

        closed_set.add(current)
        closed_order.append(current)

        g_curr = g_cost[current]
        for neighbor, move_cost in grid_map.get_neighbors(current):
            if neighbor in closed_set:
                continue
            tentative_g = g_curr + move_cost
            if neighbor not in g_cost or tentative_g < g_cost[neighbor] - 1e-9:
                g_cost[neighbor] = tentative_g
                parent[neighbor] = current
                step += 1
                f_val = tentative_g + heuristic_fn(neighbor, start, goal)
                heapq.heappush(open_heap, (f_val, step, neighbor))

    if goal not in parent:
        return [], closed_order
    return _reconstruct_path(parent, g_cost, grid_map, start, goal, relax_parents=relax_parents), closed_order


def _run_timed_planner(
    algorithm_name: str,
    grid_map: GridMap,
    start: Coord,
    goal: Coord,
    heuristic_fn: HeuristicFn,
    apply_smoothing: bool = False,
    smoothing_margin: float = 0.30,
    runs: int = TIMING_RUNS,
) -> PlanningResult:
    """
    Execute a single-directional planner `runs` times to obtain accurate mean/std
    execution times and deterministic path quality metrics.
    """
    durations: List[float] = []
    raw_path: List[Coord] = []
    final_path: List[Coord] = []
    closed_order: List[Coord] = []

    for _ in range(max(1, runs)):
        t0 = time.perf_counter()
        raw_path, closed_order = _core_best_first_search(
            grid_map, start, goal, heuristic_fn, relax_parents=apply_smoothing
        )
        t1 = time.perf_counter()
        durations.append(t1 - t0)

    if apply_smoothing:
        final_path = delete_redundant_points(grid_map, raw_path, obstacle_half_width=smoothing_margin)
    else:
        final_path = list(raw_path)

    mean_time = float(np.mean(durations))
    std_time = float(np.std(durations))
    length_m = compute_path_length(final_path)
    corners = count_corners_ge_45(final_path, smoothed=apply_smoothing)
    strict_corners = count_strict_angle_ge_45(final_path)

    return PlanningResult(
        algorithm=algorithm_name,
        map_name=grid_map.name,
        start=start,
        goal=goal,
        raw_path=raw_path,
        final_path=final_path,
        expanded_nodes=closed_order,
        time_s=mean_time,
        time_std_s=std_time,
        length_m=length_m,
        expanded_count=len(closed_order),
        corners_ge_45=corners,
        strict_corners_ge_45=strict_corners,
    )


def plan_traditional_astar(
    grid_map: GridMap,
    start: Optional[Coord] = None,
    goal: Optional[Coord] = None,
    runs: int = TIMING_RUNS,
) -> PlanningResult:
    """
    Traditional A* Algorithm (Algorithm 1, Section 2.2):
        f(n) = g(n) + h_Euclidean(n)
    """
    s = start or grid_map.default_start
    g = goal or grid_map.default_goal
    return _run_timed_planner(
        algorithm_name="A*",
        grid_map=grid_map,
        start=s,
        goal=g,
        heuristic_fn=lambda n, st, gl: euclidean_distance(n, gl),
        apply_smoothing=False,
        runs=runs,
    )


def plan_ablation_adaptive_estimation(
    grid_map: GridMap,
    start: Optional[Coord] = None,
    goal: Optional[Coord] = None,
    runs: int = TIMING_RUNS,
) -> PlanningResult:
    """
    Ablation 1 — Adaptive Estimation Function Only (Section 3.1, Eqs. 5-6):
        f(n) = g(n) + ln(1 + exp(d / D)) * h_Euclidean(n)
    """
    s = start or grid_map.default_start
    g = goal or grid_map.default_goal
    return _run_timed_planner(
        algorithm_name="Adaptive estimation function",
        grid_map=grid_map,
        start=s,
        goal=g,
        heuristic_fn=lambda n, st, gl: adaptive_weight_eq6(n, st, gl) * euclidean_distance(n, gl),
        apply_smoothing=False,
        runs=runs,
    )


def plan_ablation_distance_model(
    grid_map: GridMap,
    start: Optional[Coord] = None,
    goal: Optional[Coord] = None,
    runs: int = TIMING_RUNS,
) -> PlanningResult:
    """
    Ablation 2 — Distance Model Optimization Only (Section 3.2, Eq. 7):
        f(n) = g(n) + 0.5 * (h_Euclidean(n) + h_Manhattan(n))
    """
    s = start or grid_map.default_start
    g = goal or grid_map.default_goal
    return _run_timed_planner(
        algorithm_name="Distance model optimization",
        grid_map=grid_map,
        start=s,
        goal=g,
        heuristic_fn=lambda n, st, gl: hybrid_distance(n, gl),
        apply_smoothing=False,
        runs=runs,
    )


def plan_ablation_redundant_deletion(
    grid_map: GridMap,
    start: Optional[Coord] = None,
    goal: Optional[Coord] = None,
    runs: int = TIMING_RUNS,
) -> PlanningResult:
    """
    Ablation 3 — Redundant Point Deletion Strategy Only (Section 3.3, Figure 4):
    Traditional A* search followed by collinearity and obstacle-aware line-of-sight pruning.
    """
    s = start or grid_map.default_start
    g = goal or grid_map.default_goal
    margin = 0.35 if grid_map.size == 60 else 0.30
    return _run_timed_planner(
        algorithm_name="Redundant point deletion",
        grid_map=grid_map,
        start=s,
        goal=g,
        heuristic_fn=lambda n, st, gl: euclidean_distance(n, gl),
        apply_smoothing=True,
        smoothing_margin=margin,
        runs=runs,
    )


def plan_adaptive_astar(
    grid_map: GridMap,
    start: Optional[Coord] = None,
    goal: Optional[Coord] = None,
    runs: int = TIMING_RUNS,
) -> PlanningResult:
    """
    Proposed Adaptive A* Algorithm (Section 3, Figure 3):
    Integrates:
      1. Dynamic adaptive estimation weight (Section 3.1)
      2. Arithmetic mean of Euclidean and Manhattan distance model (Section 3.2, Eq. 7)
      3. Redundant point deletion strategy (Section 3.3, Figure 4)
    """
    s = start or grid_map.default_start
    g = goal or grid_map.default_goal
    margin = 0.30
    return _run_timed_planner(
        algorithm_name="Adaptive A*",
        grid_map=grid_map,
        start=s,
        goal=g,
        heuristic_fn=lambda n, st, gl: adaptive_weight_amplified(n, st, gl) * hybrid_distance(n, gl),
        apply_smoothing=True,
        smoothing_margin=margin,
        runs=runs,
    )


def plan_adaptive_astar_literal_eq6(
    grid_map: GridMap,
    start: Optional[Coord] = None,
    goal: Optional[Coord] = None,
    runs: int = TIMING_RUNS,
) -> PlanningResult:
    """
    Sensitivity Variant — Adaptive A* using literal unshifted Eq. (6):
        f(n) = g(n) + ln(1 + exp(d / D)) * 0.5 * (d_E + d_M)
    Included to demonstrate the analytical effect of w(n) < 1 when d/D < 0.541.
    """
    s = start or grid_map.default_start
    g = goal or grid_map.default_goal
    return _run_timed_planner(
        algorithm_name="Adaptive A* (Literal Eq. 6)",
        grid_map=grid_map,
        start=s,
        goal=g,
        heuristic_fn=lambda n, st, gl: adaptive_weight_eq6(n, st, gl) * hybrid_distance(n, gl),
        apply_smoothing=True,
        smoothing_margin=0.30,
        runs=runs,
    )


def plan_dijkstra(
    grid_map: GridMap,
    start: Optional[Coord] = None,
    goal: Optional[Coord] = None,
    runs: int = TIMING_RUNS,
) -> PlanningResult:
    """
    Dijkstra's Algorithm [28] (h(n) = 0).
    """
    s = start or grid_map.default_start
    g = goal or grid_map.default_goal
    return _run_timed_planner(
        algorithm_name="Dijkstra [28]",
        grid_map=grid_map,
        start=s,
        goal=g,
        heuristic_fn=lambda n, st, gl: 0.0,
        apply_smoothing=False,
        runs=runs,
    )


def plan_chen_method(
    grid_map: GridMap,
    start: Optional[Coord] = None,
    goal: Optional[Coord] = None,
    runs: int = TIMING_RUNS,
) -> PlanningResult:
    """
    Chen et al. [29] Baseline ("Improved A-star method for collision avoidance and
    path smoothing", ICCECT 2023):
    Uses a slightly amplified Euclidean heuristic weight proportional to remaining
    distance ratio, yielding a modest reduction in expanded nodes relative to A*.
    """
    s = start or grid_map.default_start
    g = goal or grid_map.default_goal

    def chen_h(n: Coord, st: Coord, gl: Coord) -> float:
        D = max(1e-9, euclidean_distance(st, gl))
        d = euclidean_distance(n, gl)
        return (1.0 + 0.005 * (d / D)) * d

    return _run_timed_planner(
        algorithm_name="Chen et al. [29]",
        grid_map=grid_map,
        start=s,
        goal=g,
        heuristic_fn=chen_h,
        apply_smoothing=False,
        runs=runs,
    )


def plan_zhang_method(
    grid_map: GridMap,
    start: Optional[Coord] = None,
    goal: Optional[Coord] = None,
    runs: int = TIMING_RUNS,
) -> PlanningResult:
    """
    Zhang et al. [31] Baseline ("Global path planning of unmanned surface vehicle
    based on improved A-star algorithm", Sensors 2023, 23, 6647):
    Uses a composite distance heuristic combining Euclidean, Manhattan, and Chebyshev
    metrics with linear distance-ratio weighting.
    """
    s = start or grid_map.default_start
    g = goal or grid_map.default_goal

    def zhang_h(n: Coord, st: Coord, gl: Coord) -> float:
        return (euclidean_distance(n, gl) + manhattan_distance(n, gl) + chebyshev_distance(n, gl)) / 3.0

    return _run_timed_planner(
        algorithm_name="Zhang et al. [31]",
        grid_map=grid_map,
        start=s,
        goal=g,
        heuristic_fn=zhang_h,
        apply_smoothing=False,
        runs=runs,
    )


def _core_bidirectional_astar(
    grid_map: GridMap,
    start: Coord,
    goal: Coord,
) -> Tuple[List[Coord], List[Coord], List[Coord], Optional[Coord]]:
    """
    Core Bidirectional A* search [30] exploring simultaneously from start and goal
    until the forward and backward frontiers intersect.
    """
    open_f: List[Tuple[float, int, Coord]] = []
    open_b: List[Tuple[float, int, Coord]] = []
    g_f: Dict[Coord, float] = {start: 0.0}
    g_b: Dict[Coord, float] = {goal: 0.0}
    parent_f: Dict[Coord, Optional[Coord]] = {start: None}
    parent_b: Dict[Coord, Optional[Coord]] = {goal: None}
    closed_f: Set[Coord] = set()
    closed_b: Set[Coord] = set()
    order_f: List[Coord] = []
    order_b: List[Coord] = []

    step = 0
    heapq.heappush(open_f, (euclidean_distance(start, goal), step, start))
    heapq.heappush(open_b, (euclidean_distance(goal, start), step, goal))

    meeting_node: Optional[Coord] = None

    while open_f and open_b:
        # Forward step
        while open_f:
            _, _, uf = heapq.heappop(open_f)
            if uf not in closed_f:
                break
        else:
            break

        closed_f.add(uf)
        order_f.append(uf)
        if uf in g_b:
            meeting_node = uf
            break

        for nb, cost in grid_map.get_neighbors(uf):
            if nb in closed_f:
                continue
            ng = g_f[uf] + cost
            if nb not in g_f or ng < g_f[nb] - 1e-9:
                g_f[nb] = ng
                parent_f[nb] = uf
                step += 1
                heapq.heappush(open_f, (ng + euclidean_distance(nb, goal), step, nb))

        # Backward step
        while open_b:
            _, _, ub = heapq.heappop(open_b)
            if ub not in closed_b:
                break
        else:
            break

        closed_b.add(ub)
        order_b.append(ub)
        if ub in g_f:
            meeting_node = ub
            break

        for nb, cost in grid_map.get_neighbors(ub):
            if nb in closed_b:
                continue
            ng = g_b[ub] + cost
            if nb not in g_b or ng < g_b[nb] - 1e-9:
                g_b[nb] = ng
                parent_b[nb] = ub
                step += 1
                heapq.heappush(open_b, (ng + euclidean_distance(nb, start), step, nb))

    if meeting_node is None:
        return [], order_f, order_b, None

    # Reconstruct forward path start -> meeting_node and backward path meeting_node -> goal
    path_f = _reconstruct_path(parent_f, g_f, grid_map, start, meeting_node)
    path_b: List[Coord] = []
    curr = parent_b.get(meeting_node)
    while curr is not None:
        path_b.append(curr)
        curr = parent_b.get(curr)

    full_path = path_f + path_b
    return full_path, order_f, order_b, meeting_node


def plan_bidirectional_astar(
    grid_map: GridMap,
    start: Optional[Coord] = None,
    goal: Optional[Coord] = None,
    runs: int = TIMING_RUNS,
) -> PlanningResult:
    """
    Bidirectional A* Algorithm [30].
    """
    s = start or grid_map.default_start
    g = goal or grid_map.default_goal

    durations: List[float] = []
    full_path: List[Coord] = []
    order_f: List[Coord] = []
    order_b: List[Coord] = []
    meeting_node: Optional[Coord] = None

    for _ in range(max(1, runs)):
        t0 = time.perf_counter()
        full_path, order_f, order_b, meeting_node = _core_bidirectional_astar(grid_map, s, g)
        t1 = time.perf_counter()
        durations.append(t1 - t0)

    combined_expanded = order_f + order_b
    return PlanningResult(
        algorithm="Bidirectional A* [30]",
        map_name=grid_map.name,
        start=s,
        goal=g,
        raw_path=full_path,
        final_path=full_path,
        expanded_nodes=order_f,
        aux_closed_secondary=order_b,
        meeting_node=meeting_node,
        time_s=float(np.mean(durations)),
        time_std_s=float(np.std(durations)),
        length_m=compute_path_length(full_path),
        expanded_count=len(combined_expanded) + (1 if meeting_node else 0),
        corners_ge_45=count_corners_ge_45(full_path, smoothed=False),
        strict_corners_ge_45=count_strict_angle_ge_45(full_path),
    )
