"""
Dataset Reconstruction Script (Section 2.1 & Section 4.1)
Extracts the exact 2D binary occupancy grid maps (30x30, 60x60, 100x100) from the
high-resolution figures in `extracted_images/` and saves them to `data/maps/`.
"""

import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATA_MAPS_DIR, EXTRACTED_IMAGES_DIR, MAP_CONFIGS


def extract_grid_from_image(image_path: Path, grid_size: int) -> np.ndarray:
    """
    Extract an N x N binary obstacle matrix from the MATLAB-generated figure image.
    Coordinate convention:
      grid[x - 1, y - 1] == 1 if cell (x, y) is an obstacle (black),
      grid[x - 1, y - 1] == 0 if cell (x, y) is free/passable (white/red/blue).
      x in {1..N} runs left-to-right; y in {1..N} runs bottom-to-top.
    """
    img = np.array(Image.open(image_path)).astype(float)
    # Detect axes border rectangle automatically (or use calibrated pixel bounds)
    gray = img.mean(axis=2)
    row_dark = (gray < 200).sum(axis=1)
    col_dark = (gray < 200).sum(axis=0)
    rows = np.where(row_dark > img.shape[1] * 0.4)[0]
    cols = np.where(col_dark > img.shape[0] * 0.4)[0]
    r0, r1 = int(rows[0]), int(rows[-1])
    c0, c1 = int(cols[0]), int(cols[-1])

    grid = np.zeros((grid_size, grid_size), dtype=np.int8)
    for i in range(grid_size):       # x = i + 1 (left to right)
        for j in range(grid_size):   # y = j + 1 (bottom to top)
            cx = c0 + (i + 0.5) * (c1 - c0) / grid_size
            cy = r1 - (j + 0.5) * (r1 - r0) / grid_size
            iy, ix = int(round(cy)), int(round(cx))
            r, g, b = img[iy, ix]
            # Obstacle cells are rendered as solid black (R, G, B < 80)
            if r < 80 and g < 80 and b < 80:
                grid[i, j] = 1
    return grid


def main() -> None:
    DATA_MAPS_DIR.mkdir(parents=True, exist_ok=True)
    metadata = {}

    for map_key, cfg in MAP_CONFIGS.items():
        img_path = EXTRACTED_IMAGES_DIR / cfg["source_image"]
        N = cfg["size"]
        grid = extract_grid_from_image(img_path, N)

        # Ensure start and goal cells are passable
        sx, sy = cfg["default_start"]
        gx, gy = cfg["default_goal"]
        assert grid[sx - 1, sy - 1] == 0, f"Start {cfg['default_start']} is obstacle in {map_key}"
        assert grid[gx - 1, gy - 1] == 0, f"Goal {cfg['default_goal']} is obstacle in {map_key}"

        npy_path = DATA_MAPS_DIR / f"{map_key}.npy"
        csv_path = DATA_MAPS_DIR / f"{map_key}.csv"
        np.save(npy_path, grid)
        np.savetxt(csv_path, grid, fmt="%d", delimiter=",")

        obs_count = int(grid.sum())
        total_cells = N * N
        obs_ratio = obs_count / total_cells
        metadata[map_key] = {
            "name": cfg["name"],
            "size": N,
            "description": cfg["description"],
            "source_image": cfg["source_image"],
            "obstacle_cells": obs_count,
            "free_cells": total_cells - obs_count,
            "obstacle_density_pct": round(obs_ratio * 100, 2),
            "default_start": list(cfg["default_start"]),
            "default_goal": list(cfg["default_goal"]),
        }
        print(
            f"[OK] Extracted {map_key} ({N}x{N}): "
            f"{obs_count}/{total_cells} obstacles ({obs_ratio*100:.2f}%)"
        )

    meta_path = DATA_MAPS_DIR / "maps_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[OK] Saved metadata to {meta_path}")


if __name__ == "__main__":
    main()
