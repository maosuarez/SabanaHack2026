"""Tarea 2.2: ms por recorte de DINOv2 ViT-S/14 y ViT-B/14 en esta CPU (224 px)."""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModel

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/processed/classification/speed.json"
MODELS = {"vit_s14": "facebook/dinov2-small", "vit_b14": "facebook/dinov2-base"}
N_WARM = 50


def main() -> None:
    torch.set_num_threads(8)
    x = torch.randn(1, 3, 224, 224)
    res: dict[str, dict[str, float]] = {}
    for name, hub in MODELS.items():
        model = AutoModel.from_pretrained(hub).eval()
        times: list[float] = []
        with torch.inference_mode():
            for _ in range(N_WARM + 1):
                t = time.perf_counter()
                model(pixel_values=x)
                times.append((time.perf_counter() - t) * 1000)
        cold, warm = times[0], times[1:]
        res[name] = {"cold_ms": round(cold, 1),
                     "warm_median_ms": round(statistics.median(warm), 1),
                     "warm_p95_ms": round(float(np.percentile(warm, 95)), 1), "n_warm": len(warm)}
        print(name, res[name])
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
