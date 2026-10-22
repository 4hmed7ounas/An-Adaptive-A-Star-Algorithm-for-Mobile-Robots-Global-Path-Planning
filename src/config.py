"""
Central configuration, experimental parameters, and published benchmark data
from Cao et al., "An Adaptive A* Algorithm for Mobile Robots Global Path Planning",
Electronics 2026, 15, 2807.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTRACTED_IMAGES_DIR = PROJECT_ROOT / "extracted_images"
DATA_MAPS_DIR = PROJECT_ROOT / "data" / "maps"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
TABLES_DIR = RESULTS_DIR / "tables"
REPORT_DIR = PROJECT_ROOT / "report"

# Map specifications (Section 4.1, Figure 5)
# Coordinates follow the paper's 1-indexed Cartesian grid convention (x, y) in {1..N} x {1..N}
# where (1, 1) is the bottom-left cell and each grid cell is 1 m x 1 m.
MAP_CONFIGS = {
    "map1_30x30": {
        "name": "30x30",
        "size": 30,
        "source_image": "page_10_0_Im9.jpg",
        "description": "Irregular outdoor scene (30 m x 30 m)",
        "default_start": (2, 2),
        "default_goal": (28, 28),
        "swapped_start": (28, 28),
        "swapped_goal": (2, 2),
        "random_start": (4, 24),
        "random_goal": (29, 2),
    },
    "map2_60x60": {
        "name": "60x60",
        "size": 60,
        "source_image": "page_10_6_Im10.jpg",
        "description": "Structured indoor maze and corridors scene (60 m x 60 m)",
        "default_start": (2, 2),
        "default_goal": (58, 58),
        "swapped_start": (58, 58),
        "swapped_goal": (2, 2),
        "random_start": (4, 54),
        "random_goal": (59, 2),
    },
    "map3_100x100": {
        "name": "100x100",
        "size": 100,
        "source_image": "page_10_5_Im11.jpg",
        "description": "Large array-like photovoltaic/warehouse scene (100 m x 100 m)",
        "default_start": (2, 2),
        "default_goal": (99, 99),
    },
}

# Number of repeated runs to measure deterministic mean/std planning time (in seconds)
TIMING_RUNS = 50

# Published Results from the Original Paper (Tables 1 - 5) for direct quantitative comparison
PUBLISHED_TABLE1_ABLATION = {
    "30x30": {
        "A*": {"time_s": 0.04, "length_m": 40.41, "expanded_nodes": 130, "corners_ge_45": 9},
        "Adaptive estimation function": {"time_s": 0.03, "length_m": 40.20, "expanded_nodes": 118, "corners_ge_45": 13},
        "Distance model optimization": {"time_s": 0.02, "length_m": 41.45, "expanded_nodes": 45, "corners_ge_45": 9},
        "Redundant point deletion": {"time_s": 0.02, "length_m": 38.74, "expanded_nodes": 130, "corners_ge_45": 5},
    },
    "60x60": {
        "A*": {"time_s": 0.18, "length_m": 92.30, "expanded_nodes": 716, "corners_ge_45": 12},
        "Adaptive estimation function": {"time_s": 0.09, "length_m": 92.05, "expanded_nodes": 412, "corners_ge_45": 12},
        "Distance model optimization": {"time_s": 0.12, "length_m": 91.08, "expanded_nodes": 691, "corners_ge_45": 10},
        "Redundant point deletion": {"time_s": 0.12, "length_m": 87.49, "expanded_nodes": 691, "corners_ge_45": 7},
    },
}

PUBLISHED_TABLES_2_3_4_COMPARISON = {
    "30x30": {
        "A*": {"time_s": 0.04, "length_m": 40.41, "expanded_nodes": 130, "corners_ge_45": 9},
        "Dijkstra [28]": {"time_s": 0.14, "length_m": 40.30, "expanded_nodes": 632, "corners_ge_45": 11},
        "Chen et al. [29]": {"time_s": 0.03, "length_m": 41.69, "expanded_nodes": 129, "corners_ge_45": 9},
        "Bidirectional A* [30]": {"time_s": 0.03, "length_m": 42.65, "expanded_nodes": 156, "corners_ge_45": 9},
        "Zhang et al. [31]": {"time_s": 0.04, "length_m": 40.29, "expanded_nodes": 98, "corners_ge_45": 11},
        "Adaptive A*": {"time_s": 0.01, "length_m": 39.72, "expanded_nodes": 36, "corners_ge_45": 7},
    },
    "60x60": {
        "A*": {"time_s": 0.18, "length_m": 92.30, "expanded_nodes": 716, "corners_ge_45": 12},
        "Dijkstra [28]": {"time_s": 0.39, "length_m": 92.10, "expanded_nodes": 1740, "corners_ge_45": 13},
        "Chen et al. [29]": {"time_s": 0.12, "length_m": 92.08, "expanded_nodes": 696, "corners_ge_45": 12},
        "Bidirectional A* [30]": {"time_s": 0.18, "length_m": 93.91, "expanded_nodes": 704, "corners_ge_45": 12},
        "Zhang et al. [31]": {"time_s": 0.24, "length_m": 92.11, "expanded_nodes": 523, "corners_ge_45": 10},
        "Adaptive A*": {"time_s": 0.06, "length_m": 90.89, "expanded_nodes": 268, "corners_ge_45": 8},
    },
    "100x100": {
        "A*": {"time_s": 0.70, "length_m": 146.56, "expanded_nodes": 2191, "corners_ge_45": 34},
        "Dijkstra [28]": {"time_s": 1.93, "length_m": 146.41, "expanded_nodes": 7520, "corners_ge_45": 31},
        "Chen et al. [29]": {"time_s": 0.52, "length_m": 146.56, "expanded_nodes": 2168, "corners_ge_45": 34},
        "Bidirectional A* [30]": {"time_s": 0.38, "length_m": 148.38, "expanded_nodes": 1126, "corners_ge_45": 32},
        "Zhang et al. [31]": {"time_s": 0.45, "length_m": 146.56, "expanded_nodes": 891, "corners_ge_45": 30},
        "Adaptive A*": {"time_s": 0.25, "length_m": 140.67, "expanded_nodes": 113, "corners_ge_45": 14},
    },
}

PUBLISHED_TABLE5_START_END = {
    "30x30_swapped_(28,28)_to_(2,2)": {
        "A*": {"time_s": 0.03, "length_m": 40.30, "expanded_nodes": 202, "corners_ge_45": 13},
        "Adaptive A*": {"time_s": 0.01, "length_m": 39.92, "expanded_nodes": 43, "corners_ge_45": 6},
    },
    "30x30_random_(4,24)_to_(29,2)": {
        "A*": {"time_s": 0.04, "length_m": 38.21, "expanded_nodes": 250, "corners_ge_45": 14},
        "Adaptive A*": {"time_s": 0.01, "length_m": 37.68, "expanded_nodes": 33, "corners_ge_45": 5},
    },
    "60x60_swapped_(58,58)_to_(2,2)": {
        "A*": {"time_s": 0.25, "length_m": 92.08, "expanded_nodes": 898, "corners_ge_45": 19},
        "Adaptive A*": {"time_s": 0.04, "length_m": 88.81, "expanded_nodes": 123, "corners_ge_45": 7},
    },
    "60x60_random_(4,54)_to_(59,2)": {
        "A*": {"time_s": 0.41, "length_m": 118.49, "expanded_nodes": 1159, "corners_ge_45": 27},
        "Adaptive A*": {"time_s": 0.13, "length_m": 114.96, "expanded_nodes": 478, "corners_ge_45": 13},
    },
}
