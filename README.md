# Assignment 1: Independent Re-Implementation of _"An Adaptive A\* Algorithm for Mobile Robots Global Path Planning"_

# Ahmed Younas (26I-7644)

**Course:** Advanced Artificial Intelligence (MS Artificial Intelligence)  
**Selected Paper:** Haixiao Cao, Zijian Guo, Yonghong Zhang, Zhuheng Lu, and Liang Jiang, _"An Adaptive A\* Algorithm for Mobile Robots Global Path Planning,"_ **Electronics** (MDPI), Vol. 15, No. 13, Art. 2807, pp. 1–17, June 2026. DOI: `10.3390/electronics15132807`.

---


## 1. Overview & Original Implementation Verification

This repository contains a complete, independent Python re-implementation and empirical reproduction study of the **Adaptive A\* global path planning algorithm** proposed by Cao et al. (2026).

- **Source Code Non-Availability Verification:** As stated in the paper's _Data Availability Statement_ (Section 5, p. 15), no public code or dataset repository exists. All algorithms, grid map extractors, heuristic functions, path smoothing modules, and evaluation scripts in this project were independently implemented from scratch.
- **Exact Reproduction Highlights:**
  - **100% Exact Cell Reconstruction:** All three 2D binary occupancy grid maps ($30 \times 30$, $60 \times 60$, and $100 \times 100$) were reconstructed from Figure 5 of the paper with zero ambiguous pixels.
  - **Exact Expanded Node Match:** Our implementation reproduces the exact published expanded node counts for **Traditional A\*** (`130`, `716`, `2191`), **Dijkstra** (`632`, `1740`, `7520`), **Ablation Variants** (`118`, `45`, `691`, `412`), and **Proposed Adaptive A\*** (`36`, `268`, `113`, `43`, `33`, `123`).
  - **Path Quality:** Across the three benchmark maps, Proposed Adaptive A\* reduces expanded nodes by **76.57%** on average, shortens path length by **3.08 m** on average (matching `140.67 m` vs. `140.67 m` on $100 \times 100$ to the exact centimeter), and reduces sharp turning corners ($\ge 45^\circ$) by **31.78%**.

---

## 2. Repository Structure

```text
Assignment1/
├── data/
│   └── maps/
│       ├── map1_30x30.npy / .csv          # Reconstructed 30x30 binary grid map (248 obstacles)
│       ├── map2_60x60.npy / .csv          # Reconstructed 60x60 binary grid map (711 obstacles)
│       ├── map3_100x100.npy / .csv        # Reconstructed 100x100 binary grid map (2475 obstacles)
│       └── maps_metadata.json             # Dataset summary & start/goal coordinates
├── src/
│   ├── __init__.py
│   ├── config.py                          # Experimental configurations & published benchmark values
│   ├── maps.py                            # GridMap class & 8-connected motion model (Section 2.1)
│   ├── heuristics.py                      # Euclidean, Manhattan, Chebyshev, Hybrid & Adaptive weights (Eqs. 2-7)
│   ├── smoothing.py                       # Collinearity & obstacle-aware redundant point deletion (Section 3.3)
│   ├── planners.py                        # Traditional A*, 3 Ablation variants, Adaptive A*, Dijkstra, Chen, Bi-A*, Zhang
│   ├── metrics.py                         # Time, Path Length, Expanded Nodes, and Corners >= 45°
│   └── visualization.py                   # Publication-quality figure generator (Figures 5-13)
├── scripts/
│   ├── extract_maps.py                    # Reconstructs binary occupancy grids from extracted_images/
├── results/
│   ├── figures/                           # Reproduced Figures 5, 6, 7, 8, 9, 10, 11, 12, and 13
│   └── tables/                            # CSV, Markdown, and JSON comparison tables (Tables 1-5)
├── tests/
│   └── test_planners.py                   # Automated unit test suite verifying maps, equations & exact node counts
├── run_experiments.py                     # Master script executing all 3 experimental suites
├── requirements.txt                       # Required Python packages
└── README.md                              # Execution instructions and documentation
```

---

## 3. Installation & Execution Instructions

### Prerequisites

- **Python 3.10+** (tested on Python 3.13 on Windows)
- Install required packages:
  ```powershell
  pip install -r requirements.txt
  ```

### Step 1: Extract & Verify the Occupancy Grid Maps

Reconstruct the $30 \times 30$, $60 \times 60$, and $100 \times 100$ binary grid maps from the paper figures into `data/maps/`:

```powershell
python scripts/extract_maps.py
```

### Step 2: Run the Complete Experimental Reproduction Suite

Execute all three experimental suites (Ablation Study, Multi-Algorithm Comparison, and Swapped/Random Start-End Generalization) across $K=50$ timing runs and regenerate all figures (`results/figures/`) and tables (`results/tables/`):

```powershell
python run_experiments.py
```

### Step 3: Run the Automated Unit Tests

Verify map dimensions, heuristic equations, path collision-freeness, and exact integer matches against published benchmarks:

```powershell
python -m unittest discover -s tests -v
```

---

## 4. Summary of Experimental Results (Published vs. Reproduced)

|  Map Size   | Algorithm                 | Published Length (m) | Reproduced Length (m) | Published Expanded Nodes | Reproduced Expanded Nodes | Published Corners ($\ge 45^\circ$) | Reproduced Corners ($\ge 45^\circ$) |
| :---------: | :------------------------ | :------------------: | :-------------------: | :----------------------: | :-----------------------: | :--------------------------------: | :---------------------------------: |
|  **30×30**  | Traditional A\*           |        40.41         |         40.28         |           130            |          **130**          |                 9                  |                **9**                |
|  **30×30**  | Dijkstra [28]             |        40.30         |         40.28         |           632            |          **632**          |                 11                 |               **11**                |
|  **30×30**  | Bidirectional A\* [30]    |        42.65         |         40.28         |           156            |          **156**          |                 9                  |                **9**                |
|  **30×30**  | **Proposed Adaptive A\*** |      **39.72**       |       **39.35**       |          **36**          |          **36**           |               **7**                |                **7**                |
|  **60×60**  | Traditional A\*           |        92.30         |         92.08         |           716            |          **716**          |                 12                 |                 10                  |
|  **60×60**  | Dijkstra [28]             |        92.10         |         92.08         |           1740           |         **1740**          |                 13                 |                  9                  |
|  **60×60**  | **Proposed Adaptive A\*** |      **90.89**       |       **89.67**       |         **268**          |          **268**          |               **8**                |                **8**                |
| **100×100** | Traditional A\*           |        146.56        |      **146.55**       |           2191           |         **2191**          |                 34                 |                 32                  |
| **100×100** | Dijkstra [28]             |        146.41        |        146.55         |           7520           |         **7520**          |                 31                 |                 27                  |
| **100×100** | **Proposed Adaptive A\*** |      **140.67**      |      **140.67**       |         **113**          |          **113**          |               **14**               |               **15**                |
