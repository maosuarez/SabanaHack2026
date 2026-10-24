"""Tareas 1.1-1.3: recortes por caja anotada, manifest y split train/val/test."""

from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FLOWERS_CSV = ROOT / "data/annotations/flowers.csv"
LABELS_CSV = ROOT / "data/raw/labels_imagen.csv"
IMAGES_DIR = ROOT / "data/raw/images"
DET_SPLIT = ROOT / "data/processed/detection/split.json"
OUT_DIR = ROOT / "data/processed/classification"
CROPS_DIR = ROOT / "outputs/classification/crops"
MARGIN = 0.10  # margen relativo al ancho/alto de la caja, por cada lado
SEED = 2026
N_VAL = 9


def make_val(train: list[str], stages: dict[str, set[str]]) -> list[str]:
    """Val desde train, estratificada por la clase más rara de cada foto."""
    rank = {"sobreabierto": 0, "optimo": 1, "inmaduro": 2}
    groups: dict[int, list[str]] = {0: [], 1: [], 2: []}
    for m in sorted(train):
        groups[min(rank[s] for s in stages[m])].append(m)
    rng = random.Random(SEED)
    val: list[str] = []
    for items in groups.values():
        items.sort(key=lambda m: hashlib.md5(f"{SEED}{m}".encode()).hexdigest())
        k = max(1, round(len(items) * N_VAL / len(train))) if items else 0
        val += items[:k]
    rng.shuffle(val)
    return sorted(val)


def main() -> None:
    rows = list(csv.DictReader(FLOWERS_CSV.open()))
    files = {r["md5"]: r["file"] for r in csv.DictReader(LABELS_CSV.open())}
    det = json.loads(DET_SPLIT.read_text())
    test = set(det["test"])
    stages: dict[str, set[str]] = {}
    for r in rows:
        stages.setdefault(r["md5"], set()).add(r["stage"])
    val = set(make_val(list(det["train"]), stages))
    train = set(det["train"]) - val
    split_of = {**dict.fromkeys(train, "train"), **dict.fromkeys(val, "val"),
                **dict.fromkeys(test, "test")}
    assert not (train & val) and not (train & test) and not (val & test)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CROPS_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "split.json").write_text(json.dumps(
        {"seed": SEED, "train": sorted(train), "val": sorted(val), "test": sorted(test)}, indent=1))
    manifest = []
    per_img: Counter[str] = Counter()
    for r in rows:
        m = r["md5"]
        if m not in split_of or r["annotatable"] != "1":
            continue
        per_img[m] += 1
        img = Image.open(IMAGES_DIR / files[m]).convert("RGB")
        W, H = img.size
        x, y, w, h = (float(r[k]) for k in "xywh")
        x1, y1 = max(0, (x - MARGIN * w) * W), max(0, (y - MARGIN * h) * H)
        x2, y2 = min(W, (x + w * (1 + MARGIN)) * W), min(H, (y + h * (1 + MARGIN)) * H)
        crop = img.crop((round(x1), round(y1), round(x2), round(y2)))
        rel = f"{split_of[m]}/{m[:8]}_{per_img[m]:02d}.png"
        (CROPS_DIR / rel).parent.mkdir(parents=True, exist_ok=True)
        crop.save(CROPS_DIR / rel)
        manifest.append({"md5": m, "flower_id": f"{m[:8]}_{per_img[m]:02d}", "stage": r["stage"],
                         "split": split_of[m], "crop": rel, "w_px": crop.width, "h_px": crop.height})
    with (OUT_DIR / "manifest.csv").open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(manifest[0]))
        wr.writeheader()
        wr.writerows(manifest)
    print("total", len(manifest), Counter(r["stage"] for r in manifest))
    for s in ("train", "val", "test"):
        sub = [r for r in manifest if r["split"] == s]
        print(s, "imgs", len({r["md5"] for r in sub}), "flores", len(sub),
              dict(Counter(r["stage"] for r in sub)))
    sizes = sorted(min(r["w_px"], r["h_px"]) for r in manifest)
    print("lado menor px: min", sizes[0], "mediana", sizes[len(sizes) // 2])
    print("crops en disco", len(list(CROPS_DIR.rglob("*.png"))))


if __name__ == "__main__":
    main()
