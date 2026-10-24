"""Utilidades compartidas: carga de cajas de referencia y rutas."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLOWERS_CSV = ROOT / "data/annotations/flowers.csv"
LABELS_CSV = ROOT / "data/raw/labels_imagen.csv"
IMAGES_DIR = ROOT / "data/raw/images"
OUT_DIR = ROOT / "data/processed/detection"

Box = tuple[float, float, float, float]  # x1, y1, x2, y2 normalizados 0-1


def load_gt() -> dict[str, list[Box]]:
    """Cajas de referencia por md5 (x,y = esquina superior izquierda)."""
    gt: dict[str, list[Box]] = defaultdict(list)
    with FLOWERS_CSV.open() as f:
        for r in csv.DictReader(f):
            x, y, w, h = (float(r[k]) for k in "xywh")
            gt[r["md5"]].append((x, y, x + w, y + h))
    return dict(gt)


def load_stages() -> dict[str, list[str]]:
    st: dict[str, list[str]] = defaultdict(list)
    with FLOWERS_CSV.open() as f:
        for r in csv.DictReader(f):
            st[r["md5"]].append(r["stage"])
    return dict(st)


def md5_to_file() -> dict[str, Path]:
    with LABELS_CSV.open() as f:
        return {r["md5"]: IMAGES_DIR / r["file"] for r in csv.DictReader(f)}
