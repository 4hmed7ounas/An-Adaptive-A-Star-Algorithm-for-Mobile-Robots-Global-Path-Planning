# Table 1 Reproduction: Ablation Study Comparison (30×30 and 60×60 Maps)

| Scenario | Algorithm | Time (Pub / Yours / Diff) [s] | Length (Pub / Yours / Diff) [m] | Expanded Nodes (Pub / Yours / Diff) | Corners ≥45° (Pub / Yours / Diff) |
| --- | --- | --- | --- | --- | --- |
| 30x30 | A* | 0.04 / 0.0009 / -0.0391 | 40.41 / 40.28 / -0.13 | 130 / 130 / +0 | 9 / 9 / +0 |
| 30x30 | Adaptive estimation function | 0.03 / 0.0011 / -0.0289 | 40.20 / 40.28 / +0.08 | 118 / 118 / +0 | 13 / 9 / -4 |
| 30x30 | Distance model optimization | 0.02 / 0.0003 / -0.0197 | 41.45 / 41.46 / +0.01 | 45 / 45 / +0 | 9 / 13 / +4 |
| 30x30 | Redundant point deletion | 0.02 / 0.0014 / -0.0186 | 38.74 / 38.72 / -0.02 | 130 / 130 / +0 | 5 / 5 / +0 |
| 60x60 | A* | 0.18 / 0.0050 / -0.1750 | 92.30 / 92.08 / -0.22 | 716 / 716 / +0 | 12 / 10 / -2 |
| 60x60 | Adaptive estimation function | 0.09 / 0.0058 / -0.0842 | 92.05 / 92.08 / +0.03 | 412 / 691 / +279 | 12 / 10 / -2 |
| 60x60 | Distance model optimization | 0.12 / 0.0034 / -0.1166 | 91.08 / 92.08 / +1.00 | 691 / 412 / -279 | 10 / 9 / -1 |
| 60x60 | Redundant point deletion | 0.12 / 0.0076 / -0.1124 | 87.49 / 87.49 / -0.00 | 691 / 716 / +25 | 7 / 7 / +0 |
