"""
Visualization Module
Renders MATLAB-style 2D occupancy grid maps, expanded node regions, and planned
paths matching Figures 5-12 of Cao et al. (Electronics 2026, 15, 2807), as well
as comparative bar charts between published and reproduced metrics.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from src.maps import GridMap
from src.metrics import PlanningResult

Coord = Tuple[int, int]


def draw_grid_result(
    ax: plt.Axes,
    grid_map: GridMap,
    result: Optional[PlanningResult] = None,
    start: Optional[Coord] = None,
    goal: Optional[Coord] = None,
    title: str = "",
) -> None:
    """
    Render a single 2D grid map onto `ax` using the visual conventions of the paper:
      - White cell: passable free space
      - Black cell: obstacle
      - Light gray cell: expanded nodes (or yellow for backward frontier in Bidirectional A*)
      - Red cell: start node
      - Blue cell: goal node
      - Red line: planned path
    """
    N = grid_map.size
    s = start or (result.start if result else grid_map.default_start)
    g = goal or (result.goal if result else grid_map.default_goal)

    # Create RGB image array of shape (N, N, 3) where row 0 is y=1 (bottom)
    # Using origin='lower' in imshow with extent=[0, N, 0, N]
    canvas = np.ones((N, N, 3), dtype=float)

    # Obstacles in black
    obs_mask = grid_map.grid.T == 1  # shape (y, x)
    canvas[obs_mask] = [0.0, 0.0, 0.0]

    if result is not None:
        # Forward expanded nodes in light gray [0.80, 0.80, 0.80]
        for x, y in result.expanded_nodes:
            if (x, y) != s and (x, y) != g and grid_map.is_free(x, y):
                canvas[y - 1, x - 1] = [0.80, 0.80, 0.80]

        # Backward expanded nodes (Bidirectional A*) in yellow [1.0, 1.0, 0.15]
        if result.aux_closed_secondary:
            for x, y in result.aux_closed_secondary:
                if (x, y) != s and (x, y) != g and grid_map.is_free(x, y):
                    canvas[y - 1, x - 1] = [1.0, 1.0, 0.15]

        # Meeting node in cyan [0.0, 1.0, 1.0]
        if result.meeting_node:
            mx, my = result.meeting_node
            if (mx, my) != s and (mx, my) != g:
                canvas[my - 1, mx - 1] = [0.0, 1.0, 1.0]

    # Start cell in red, Goal cell in blue
    canvas[s[1] - 1, s[0] - 1] = [1.0, 0.0, 0.0]
    canvas[g[1] - 1, g[0] - 1] = [0.0, 0.1, 1.0]

    ax.imshow(canvas, origin="lower", extent=[0, N, 0, N], interpolation="nearest")

    # Draw grid lines
    lw = 0.45 if N <= 30 else (0.30 if N <= 60 else 0.18)
    for k in range(N + 1):
        ax.axhline(k, color="#666666", linewidth=lw)
        ax.axvline(k, color="#666666", linewidth=lw)

    # Draw planned path in red connecting cell centers (x - 0.5, y - 0.5)
    if result is not None and len(result.final_path) >= 2:
        xs = [pt[0] - 0.5 for pt in result.final_path]
        ys = [pt[1] - 0.5 for pt in result.final_path]
        path_lw = 1.8 if N <= 60 else 1.4
        ax.plot(xs, ys, color="#ee0000", linewidth=path_lw, zorder=5)

    # Configure ticks to match paper
    step = 5 if N == 30 else (10 if N == 60 else 20)
    ticks = list(range(step, N + 1, step))
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.tick_params(axis="both", labelsize=8)
    ax.set_xlim(0, N)
    ax.set_ylim(0, N)
    ax.set_aspect("equal")
    if title:
        ax.set_title(title, fontsize=9.5, pad=6)


def plot_three_maps(maps: Sequence[GridMap], out_path: Path) -> None:
    """Reproduce Figure 5: Three different sizes of maps (30x30, 60x60, 100x100)."""
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.5), dpi=220)
    labels = ["(a) map1: 30 × 30", "(b) map2: 60 × 60", "(c) map3: 100 × 100"]
    for ax, gmap, label in zip(axes, maps, labels):
        draw_grid_result(ax, gmap, result=None, title=label)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def plot_ablation_row(
    grid_map: GridMap,
    results: Sequence[PlanningResult],
    out_path: Path,
    fig_title: str,
) -> None:
    """Reproduce Figure 6 (30x30) or Figure 7 (60x60) ablation study (4 subplots)."""
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.3), dpi=220)
    sub_labels = [
        "(a) A* algorithm",
        "(b) Adaptive estimation function",
        "(c) Distance model optimization",
        "(d) Redundant point deletion",
    ]
    for ax, res, sub in zip(axes, results, sub_labels):
        subtitle = f"{sub}\nL={res.length_m:.2f}m, Nodes={res.expanded_count}, Corners={res.corners_ge_45}"
        draw_grid_result(ax, grid_map, result=res, title=subtitle)
    fig.suptitle(fig_title, fontsize=11, fontweight="bold", y=1.02)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def plot_six_algorithms_grid(
    grid_map: GridMap,
    results: Sequence[PlanningResult],
    out_path: Path,
    fig_title: str,
) -> None:
    """Reproduce Figures 8, 9, 10: 6-algorithm comparison (2x3 grid)."""
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 9.2), dpi=220)
    sub_labels = [
        "(a) A*",
        "(b) Dijkstra",
        "(c) Chen's method",
        "(d) Bidirectional A*",
        "(e) Zhang's method",
        "(f) Adaptive A*",
    ]
    for ax, res, sub in zip(axes.flat, results, sub_labels):
        subtitle = f"{sub}\nL={res.length_m:.2f}m, Nodes={res.expanded_count}, Corners={res.corners_ge_45}"
        draw_grid_result(ax, grid_map, result=res, title=subtitle)
    fig.suptitle(fig_title, fontsize=12, fontweight="bold", y=1.01)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def plot_start_end_comparison(
    grid_map: GridMap,
    results: Sequence[PlanningResult],
    out_path: Path,
    fig_title: str,
) -> None:
    """Reproduce Figures 11 & 12: Swapped and random start/end point comparisons (1x4 grid)."""
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.3), dpi=220)
    sub_labels = [
        f"(a) A* {results[0].start}→{results[0].goal}",
        f"(b) Adaptive A* {results[1].start}→{results[1].goal}",
        f"(c) A* {results[2].start}→{results[2].goal}",
        f"(d) Adaptive A* {results[3].start}→{results[3].goal}",
    ]
    for ax, res, sub in zip(axes, results, sub_labels):
        subtitle = f"{sub}\nL={res.length_m:.2f}m, Nodes={res.expanded_count}, Corners={res.corners_ge_45}"
        draw_grid_result(ax, grid_map, result=res, title=subtitle)
    fig.suptitle(fig_title, fontsize=11, fontweight="bold", y=1.02)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def plot_published_vs_reproduced_summary(
    comp_results: Dict[str, Dict[str, PlanningResult]],
    published_data: Dict[str, Dict[str, dict]],
    out_path: Path,
) -> None:
    """
    Generate a 3-panel grouped bar chart comparing Published vs. Reproduced
    Path Length (m), Expanded Nodes, and Corners >= 45° for Traditional A* and
    Proposed Adaptive A* across all three map sizes.
    """
    map_names = ["30x30", "60x60", "100x100"]
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.4), dpi=220)

    metrics_cfg = [
        ("length_m", "Path Length (m)"),
        ("expanded_nodes", "Expanded Nodes (count)"),
        ("corners_ge_45", "Turning Corners (≥ 45°)"),
    ]

    x = np.arange(len(map_names))
    width = 0.19

    for ax, (m_key, m_label) in zip(axes, metrics_cfg):
        pub_a = [published_data[m]["A*"][m_key] for m in map_names]
        rep_a = [
            getattr(comp_results[m]["A*"], "expanded_count" if m_key == "expanded_nodes" else m_key)
            for m in map_names
        ]
        pub_ad = [published_data[m]["Adaptive A*"][m_key] for m in map_names]
        rep_ad = [
            getattr(comp_results[m]["Adaptive A*"], "expanded_count" if m_key == "expanded_nodes" else m_key)
            for m in map_names
        ]

        b1 = ax.bar(x - 1.5 * width, pub_a, width, label="A* (Published)", color="#4c72b0")
        b2 = ax.bar(x - 0.5 * width, rep_a, width, label="A* (Reproduced)", color="#81a1c1")
        b3 = ax.bar(x + 0.5 * width, pub_ad, width, label="Adaptive A* (Published)", color="#dd8452")
        b4 = ax.bar(x + 1.5 * width, rep_ad, width, label="Adaptive A* (Reproduced)", color="#e8a87c")

        ax.set_xticks(x)
        ax.set_xticklabels([f"Map {m}" for m in map_names], fontsize=9)
        ax.set_ylabel(m_label, fontsize=9.5)
        ax.set_title(f"{m_label}: Published vs. Reproduced", fontsize=10, fontweight="bold")
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.legend(fontsize=7.5)

        for bars in (b1, b2, b3, b4):
            for bar in bars:
                h = bar.get_height()
                txt = f"{h:.1f}" if m_key == "length_m" else f"{int(round(h))}"
                ax.annotate(
                    txt,
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 2),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=6.8,
                )

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
