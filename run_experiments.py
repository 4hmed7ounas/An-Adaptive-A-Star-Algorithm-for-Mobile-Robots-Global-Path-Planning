"""
Master Experimental Reproduction Script (Section 5 of Assignment)

Executes all three experimental suites from Cao et al. (Electronics 2026, 15, 2807):
  1. Experiment 1 (Section 4.2): Ablation Study on 30x30 and 60x60 maps (Table 1, Figs. 6-7)
  2. Experiment 2 (Section 4.3): Multi-Algorithm Comparison on 30x30, 60x60, 100x100 (Tables 2-4, Figs. 8-10)
  3. Experiment 3 (Section 4.4): Swapped & Random Start/End Points on 30x30 and 60x60 (Table 5, Figs. 11-12)
  4. Sensitivity Study: Literal Eq. (6) vs. Amplified Adaptive Weight

Generates all figures in `results/figures/` and comparison tables in `results/tables/`.
"""

from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Any, Dict, List

from src.config import (
    FIGURES_DIR,
    MAP_CONFIGS,
    PUBLISHED_TABLE1_ABLATION,
    PUBLISHED_TABLES_2_3_4_COMPARISON,
    PUBLISHED_TABLE5_START_END,
    TABLES_DIR,
    TIMING_RUNS,
)
from src.maps import GridMap
from src.metrics import PlanningResult
from src.planners import (
    plan_ablation_adaptive_estimation,
    plan_ablation_distance_model,
    plan_ablation_redundant_deletion,
    plan_adaptive_astar,
    plan_adaptive_astar_literal_eq6,
    plan_bidirectional_astar,
    plan_chen_method,
    plan_dijkstra,
    plan_traditional_astar,
    plan_zhang_method,
)
from src.visualization import (
    plot_ablation_row,
    plot_published_vs_reproduced_summary,
    plot_six_algorithms_grid,
    plot_start_end_comparison,
    plot_three_maps,
)


def _format_comparison_row(
    group: str,
    algorithm: str,
    pub: Dict[str, float],
    res: PlanningResult,
) -> Dict[str, Any]:
    diff_time = res.time_s - pub["time_s"]
    diff_len = res.length_m - pub["length_m"]
    diff_nodes = res.expanded_count - int(pub["expanded_nodes"])
    diff_corners = res.corners_ge_45 - int(pub["corners_ge_45"])

    return {
        "Scenario": group,
        "Algorithm": algorithm,
        "Pub_Time_s": pub["time_s"],
        "Rep_Time_s": round(res.time_s, 5),
        "Diff_Time_s": round(diff_time, 5),
        "Pub_Length_m": pub["length_m"],
        "Rep_Length_m": round(res.length_m, 2),
        "Diff_Length_m": round(diff_len, 2),
        "Pub_Expanded_Nodes": int(pub["expanded_nodes"]),
        "Rep_Expanded_Nodes": res.expanded_count,
        "Diff_Expanded_Nodes": diff_nodes,
        "Pub_Corners_ge_45": int(pub["corners_ge_45"]),
        "Rep_Corners_ge_45": res.corners_ge_45,
        "Diff_Corners_ge_45": diff_corners,
        "Strict_Angle_ge_45": res.strict_corners_ge_45,
    }


def _save_csv_and_md(rows: List[Dict[str, Any]], csv_path: Path, md_path: Path, title: str) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    lines = [f"# {title}\n"]
    headers = [
        "Scenario",
        "Algorithm",
        "Time (Pub / Yours / Diff) [s]",
        "Length (Pub / Yours / Diff) [m]",
        "Expanded Nodes (Pub / Yours / Diff)",
        "Corners ≥45° (Pub / Yours / Diff)",
    ]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        t_str = f"{r['Pub_Time_s']:.2f} / {r['Rep_Time_s']:.4f} / {r['Diff_Time_s']:+.4f}"
        l_str = f"{r['Pub_Length_m']:.2f} / {r['Rep_Length_m']:.2f} / {r['Diff_Length_m']:+.2f}"
        n_str = f"{r['Pub_Expanded_Nodes']} / {r['Rep_Expanded_Nodes']} / {r['Diff_Expanded_Nodes']:+d}"
        c_str = f"{r['Pub_Corners_ge_45']} / {r['Rep_Corners_ge_45']} / {r['Diff_Corners_ge_45']:+d}"
        lines.append(f"| {r['Scenario']} | {r['Algorithm']} | {t_str} | {l_str} | {n_str} | {c_str} |")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("LOADING EXTRACTED GRID MAPS (30x30, 60x60, 100x100)")
    print("=" * 78)
    map30 = GridMap.load("map1_30x30")
    map60 = GridMap.load("map2_60x60")
    map100 = GridMap.load("map3_100x100")

    plot_three_maps([map30, map60, map100], FIGURES_DIR / "fig5_maps.png")
    print("[OK] Saved Figure 5 reproduction -> results/figures/fig5_maps.png")

    # -------------------------------------------------------------------------
    # EXPERIMENT 1: Ablation Study (Table 1, Figures 6 & 7)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("EXPERIMENT 1: ABLATION STUDY (Table 1, Figures 6 & 7)")
    print("=" * 78)
    ablation_rows: List[Dict[str, Any]] = []
    ablation_results_by_map: Dict[str, List[PlanningResult]] = {}

    for gmap in (map30, map60):
        res_list = [
            plan_traditional_astar(gmap, runs=TIMING_RUNS),
            plan_ablation_adaptive_estimation(gmap, runs=TIMING_RUNS),
            plan_ablation_distance_model(gmap, runs=TIMING_RUNS),
            plan_ablation_redundant_deletion(gmap, runs=TIMING_RUNS),
        ]
        ablation_results_by_map[gmap.name] = res_list
        for res in res_list:
            pub = PUBLISHED_TABLE1_ABLATION[gmap.name][res.algorithm]
            row = _format_comparison_row(gmap.name, res.algorithm, pub, res)
            ablation_rows.append(row)
            print(
                f"  [{gmap.name:5s}] {res.algorithm:28s} | "
                f"Len: {res.length_m:6.2f}m (Pub: {pub['length_m']:6.2f}) | "
                f"Nodes: {res.expanded_count:4d} (Pub: {pub['expanded_nodes']:4d}) | "
                f"Corners: {res.corners_ge_45:2d} (Pub: {pub['corners_ge_45']:2d}) | "
                f"Time: {res.time_s*1000:6.3f}ms"
            )

    plot_ablation_row(
        map30,
        ablation_results_by_map["30x30"],
        FIGURES_DIR / "fig6_ablation_30x30.png",
        "Figure 6 Reproduction: Simulation outcomes of algorithm improvements on 30 × 30 map",
    )
    plot_ablation_row(
        map60,
        ablation_results_by_map["60x60"],
        FIGURES_DIR / "fig7_ablation_60x60.png",
        "Figure 7 Reproduction: Simulation outcomes of algorithm improvements on 60 × 60 map",
    )
    _save_csv_and_md(
        ablation_rows,
        TABLES_DIR / "table1_ablation_comparison.csv",
        TABLES_DIR / "table1_ablation_comparison.md",
        "Table 1 Reproduction: Ablation Study Comparison (30×30 and 60×60 Maps)",
    )
    print("[OK] Saved Figures 6 & 7 and Table 1 comparison.")

    # -------------------------------------------------------------------------
    # EXPERIMENT 2: Multi-Algorithm Comparison (Tables 2, 3, 4, Figures 8, 9, 10)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("EXPERIMENT 2: MULTI-ALGORITHM COMPARISON (Tables 2-4, Figures 8-10)")
    print("=" * 78)
    comp_rows: List[Dict[str, Any]] = []
    comp_results_by_map: Dict[str, Dict[str, PlanningResult]] = {}
    sensitivity_rows: List[Dict[str, Any]] = []

    for gmap, fig_name, fig_num in [
        (map30, "fig8_comparison_30x30.png", 8),
        (map60, "fig9_comparison_60x60.png", 9),
        (map100, "fig10_comparison_100x100.png", 10),
    ]:
        res_list = [
            plan_traditional_astar(gmap, runs=TIMING_RUNS),
            plan_dijkstra(gmap, runs=TIMING_RUNS),
            plan_chen_method(gmap, runs=TIMING_RUNS),
            plan_bidirectional_astar(gmap, runs=TIMING_RUNS),
            plan_zhang_method(gmap, runs=TIMING_RUNS),
            plan_adaptive_astar(gmap, runs=TIMING_RUNS),
        ]
        comp_results_by_map[gmap.name] = {r.algorithm: r for r in res_list}

        for res in res_list:
            pub = PUBLISHED_TABLES_2_3_4_COMPARISON[gmap.name][res.algorithm]
            row = _format_comparison_row(gmap.name, res.algorithm, pub, res)
            comp_rows.append(row)
            print(
                f"  [{gmap.name:7s}] {res.algorithm:22s} | "
                f"Len: {res.length_m:6.2f}m (Pub: {pub['length_m']:6.2f}) | "
                f"Nodes: {res.expanded_count:4d} (Pub: {pub['expanded_nodes']:4d}) | "
                f"Corners: {res.corners_ge_45:2d} (Pub: {pub['corners_ge_45']:2d}) | "
                f"Time: {res.time_s*1000:6.3f}ms"
            )

        # Also run sensitivity variant (Literal unshifted Eq. 6)
        lit_res = plan_adaptive_astar_literal_eq6(gmap, runs=TIMING_RUNS)
        amp_res = comp_results_by_map[gmap.name]["Adaptive A*"]
        pub_ad = PUBLISHED_TABLES_2_3_4_COMPARISON[gmap.name]["Adaptive A*"]
        sensitivity_rows.append(
            {
                "Map": gmap.name,
                "Published_Nodes": pub_ad["expanded_nodes"],
                "Amplified_Nodes": amp_res.expanded_count,
                "Literal_Eq6_Nodes": lit_res.expanded_count,
                "Published_Length_m": pub_ad["length_m"],
                "Amplified_Length_m": round(amp_res.length_m, 2),
                "Literal_Eq6_Length_m": round(lit_res.length_m, 2),
                "Published_Corners": pub_ad["corners_ge_45"],
                "Amplified_Corners": amp_res.corners_ge_45,
                "Literal_Eq6_Corners": lit_res.corners_ge_45,
            }
        )

        plot_six_algorithms_grid(
            gmap,
            res_list,
            FIGURES_DIR / fig_name,
            f"Figure {fig_num} Reproduction: Comparison of different algorithms on {gmap.name} map",
        )

    plot_published_vs_reproduced_summary(
        comp_results_by_map,
        PUBLISHED_TABLES_2_3_4_COMPARISON,
        FIGURES_DIR / "fig13_published_vs_reproduced_bars.png",
    )
    _save_csv_and_md(
        comp_rows,
        TABLES_DIR / "table2_3_4_multi_algorithm_comparison.csv",
        TABLES_DIR / "table2_3_4_multi_algorithm_comparison.md",
        "Tables 2, 3, and 4 Reproduction: Multi-Algorithm Comparison (30×30, 60×60, 100×100)",
    )
    print("[OK] Saved Figures 8, 9, 10, 13 and Tables 2-4 comparison.")

    # -------------------------------------------------------------------------
    # EXPERIMENT 3: Different Start & End Points (Table 5, Figures 11 & 12)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("EXPERIMENT 3: DIFFERENT START & END POINTS (Table 5, Figures 11 & 12)")
    print("=" * 78)
    start_end_rows: List[Dict[str, Any]] = []

    exp3_configs = [
        (
            map30,
            "fig11_start_end_30x30.png",
            11,
            [
                ("30x30_swapped_(28,28)_to_(2,2)", (28, 28), (2, 2)),
                ("30x30_random_(4,24)_to_(29,2)", (4, 24), (29, 2)),
            ],
        ),
        (
            map60,
            "fig12_start_end_60x60.png",
            12,
            [
                ("60x60_swapped_(58,58)_to_(2,2)", (58, 58), (2, 2)),
                ("60x60_random_(4,54)_to_(59,2)", (4, 54), (59, 2)),
            ],
        ),
    ]

    for gmap, fig_name, fig_num, pair_list in exp3_configs:
        fig_results: List[PlanningResult] = []
        for key, s_pt, g_pt in pair_list:
            r_a = plan_traditional_astar(gmap, start=s_pt, goal=g_pt, runs=TIMING_RUNS)
            r_ad = plan_adaptive_astar(gmap, start=s_pt, goal=g_pt, runs=TIMING_RUNS)
            fig_results.extend([r_a, r_ad])

            for res in (r_a, r_ad):
                pub = PUBLISHED_TABLE5_START_END[key][res.algorithm]
                row = _format_comparison_row(key, res.algorithm, pub, res)
                start_end_rows.append(row)
                print(
                    f"  [{key:30s}] {res.algorithm:12s} | "
                    f"Len: {res.length_m:6.2f}m (Pub: {pub['length_m']:6.2f}) | "
                    f"Nodes: {res.expanded_count:4d} (Pub: {pub['expanded_nodes']:4d}) | "
                    f"Corners: {res.corners_ge_45:2d} (Pub: {pub['corners_ge_45']:2d})"
                )

        plot_start_end_comparison(
            gmap,
            fig_results,
            FIGURES_DIR / fig_name,
            f"Figure {fig_num} Reproduction: Different start and end points on {gmap.name} map",
        )

    _save_csv_and_md(
        start_end_rows,
        TABLES_DIR / "table5_start_end_comparison.csv",
        TABLES_DIR / "table5_start_end_comparison.md",
        "Table 5 Reproduction: Swapped and Random Start/End Points Comparison",
    )
    print("[OK] Saved Figures 11 & 12 and Table 5 comparison.")

    # -------------------------------------------------------------------------
    # Aggregate Summary & Assignment Section 5 Table
    # -------------------------------------------------------------------------
    # Compute overall average improvements across the 3 default maps (matching Abstract claims)
    time_reductions_pct = []
    length_reductions_m = []
    corner_reductions_pct = []
    node_reductions_pct = []

    for m_name in ("30x30", "60x60", "100x100"):
        ra = comp_results_by_map[m_name]["A*"]
        rad = comp_results_by_map[m_name]["Adaptive A*"]
        time_reductions_pct.append((ra.time_s - rad.time_s) / ra.time_s * 100.0)
        length_reductions_m.append(ra.length_m - rad.length_m)
        corner_reductions_pct.append((ra.corners_ge_45 - rad.corners_ge_45) / ra.corners_ge_45 * 100.0)
        node_reductions_pct.append((ra.expanded_count - rad.expanded_count) / ra.expanded_count * 100.0)

    summary_payload = {
        "ablation_table1": ablation_rows,
        "comparison_tables_2_3_4": comp_rows,
        "start_end_table5": start_end_rows,
        "sensitivity_eq6": sensitivity_rows,
        "aggregate_improvements_vs_traditional_astar": {
            "published_avg_time_reduction_pct": 69.0,
            "reproduced_avg_time_reduction_pct": round(sum(time_reductions_pct) / 3.0, 2),
            "published_avg_length_reduction_m": 2.66,
            "reproduced_avg_length_reduction_m": round(sum(length_reductions_m) / 3.0, 2),
            "published_avg_corner_reduction_pct": 38.1,
            "reproduced_avg_corner_reduction_pct": round(sum(corner_reductions_pct) / 3.0, 2),
            "published_avg_expanded_node_reduction_pct": round(
                ((130 - 36) / 130 + (716 - 268) / 716 + (2191 - 113) / 2191) / 3 * 100, 2
            ),
            "reproduced_avg_expanded_node_reduction_pct": round(sum(node_reductions_pct) / 3.0, 2),
        },
    }

    with open(TABLES_DIR / "all_experiments_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)

    print("\n" + "=" * 78)
    print("SUMMARY OF AGGREGATE IMPROVEMENTS (Proposed Adaptive A* vs. Traditional A*)")
    print("=" * 78)
    agg = summary_payload["aggregate_improvements_vs_traditional_astar"]
    for k, v in agg.items():
        print(f"  {k:45s}: {v}")
    print("=" * 78)


if __name__ == "__main__":
    main()
