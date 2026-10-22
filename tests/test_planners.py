"""
Automated Verification and Unit Tests for the Independent Re-Implementation
of "An Adaptive A* Algorithm for Mobile Robots Global Path Planning" (Electronics 2026).
"""

from __future__ import annotations
import math
import unittest

from src.heuristics import (
    adaptive_weight_amplified,
    adaptive_weight_eq6,
    chebyshev_distance,
    euclidean_distance,
    hybrid_distance,
    manhattan_distance,
)
from src.maps import GridMap
from src.planners import (
    plan_ablation_adaptive_estimation,
    plan_ablation_distance_model,
    plan_ablation_redundant_deletion,
    plan_adaptive_astar,
    plan_bidirectional_astar,
    plan_chen_method,
    plan_dijkstra,
    plan_traditional_astar,
    plan_zhang_method,
)
from src.smoothing import are_collinear, line_of_sight_clear


class TestAdaptiveAStarReImplementation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.map30 = GridMap.load("map1_30x30")
        cls.map60 = GridMap.load("map2_60x60")
        cls.map100 = GridMap.load("map3_100x100")

    def test_map_dimensions_and_obstacles(self) -> None:
        self.assertEqual(self.map30.size, 30)
        self.assertEqual(self.map60.size, 60)
        self.assertEqual(self.map100.size, 100)
        self.assertEqual(int(self.map30.grid.sum()), 248)
        self.assertEqual(int(self.map60.grid.sum()), 711)
        self.assertEqual(int(self.map100.grid.sum()), 2475)

    def test_distance_models(self) -> None:
        p1, p2 = (2, 2), (5, 6)
        self.assertAlmostEqual(euclidean_distance(p1, p2), 5.0)
        self.assertAlmostEqual(manhattan_distance(p1, p2), 7.0)
        self.assertAlmostEqual(chebyshev_distance(p1, p2), 4.0)
        self.assertAlmostEqual(hybrid_distance(p1, p2), 6.0)

    def test_adaptive_weights_bounds(self) -> None:
        start, goal = (2, 2), (28, 28)
        w_start = adaptive_weight_eq6(start, start, goal)
        w_goal = adaptive_weight_eq6(goal, start, goal)
        self.assertAlmostEqual(w_start, math.log(1.0 + math.e), places=6)
        self.assertAlmostEqual(w_goal, math.log(2.0), places=6)
        self.assertGreater(w_start, w_goal)

        w_amp_start = adaptive_weight_amplified(start, start, goal)
        w_amp_goal = adaptive_weight_amplified(goal, start, goal)
        self.assertAlmostEqual(w_amp_start, 1.0 + math.e, places=6)
        self.assertAlmostEqual(w_amp_goal, 2.0, places=6)

    def test_collinearity(self) -> None:
        self.assertTrue(are_collinear((2, 2), (5, 5), (8, 8)))
        self.assertTrue(are_collinear((3, 4), (3, 7), (3, 10)))
        self.assertFalse(are_collinear((2, 2), (2, 3), (3, 4)))

    def test_exact_expanded_nodes_reproduction(self) -> None:
        # Traditional A* exact published counts: 130, 716, 2191
        r30 = plan_traditional_astar(self.map30, runs=1)
        r60 = plan_traditional_astar(self.map60, runs=1)
        r100 = plan_traditional_astar(self.map100, runs=1)
        self.assertEqual(r30.expanded_count, 130)
        self.assertEqual(r60.expanded_count, 716)
        self.assertEqual(r100.expanded_count, 2191)

        # Dijkstra exact published counts: 632, 1740, 7520
        d30 = plan_dijkstra(self.map30, runs=1)
        d60 = plan_dijkstra(self.map60, runs=1)
        d100 = plan_dijkstra(self.map100, runs=1)
        self.assertEqual(d30.expanded_count, 632)
        self.assertEqual(d60.expanded_count, 1740)
        self.assertEqual(d100.expanded_count, 7520)

        # Proposed Adaptive A* exact published counts: 36, 268, 113
        ad30 = plan_adaptive_astar(self.map30, runs=1)
        ad60 = plan_adaptive_astar(self.map60, runs=1)
        ad100 = plan_adaptive_astar(self.map100, runs=1)
        self.assertEqual(ad30.expanded_count, 36)
        self.assertEqual(ad60.expanded_count, 268)
        self.assertEqual(ad100.expanded_count, 113)
        self.assertAlmostEqual(ad100.length_m, 140.67, places=2)

    def test_ablation_study_metrics(self) -> None:
        ab_w_30 = plan_ablation_adaptive_estimation(self.map30, runs=1)
        ab_d_30 = plan_ablation_distance_model(self.map30, runs=1)
        ab_s_30 = plan_ablation_redundant_deletion(self.map30, runs=1)
        self.assertEqual(ab_w_30.expanded_count, 118)
        self.assertEqual(ab_d_30.expanded_count, 45)
        self.assertEqual(ab_s_30.corners_ge_45, 5)

        ab_s_60 = plan_ablation_redundant_deletion(self.map60, runs=1)
        self.assertAlmostEqual(ab_s_60.length_m, 87.49, places=2)
        self.assertEqual(ab_s_60.corners_ge_45, 7)

    def test_paths_are_collision_free_and_valid(self) -> None:
        for gmap in (self.map30, self.map60, self.map100):
            for planner in (
                plan_traditional_astar,
                plan_adaptive_astar,
                plan_dijkstra,
                plan_chen_method,
                plan_bidirectional_astar,
                plan_zhang_method,
            ):
                res = planner(gmap, runs=1)
                self.assertEqual(res.final_path[0], gmap.default_start)
                self.assertEqual(res.final_path[-1], gmap.default_goal)
                for x, y in res.final_path:
                    self.assertTrue(gmap.is_free(x, y))
                for i in range(len(res.final_path) - 1):
                    self.assertTrue(
                        line_of_sight_clear(
                            gmap, res.final_path[i], res.final_path[i + 1], obstacle_half_width=0.25
                        )
                    )


if __name__ == "__main__":
    unittest.main()
