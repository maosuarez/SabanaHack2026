"""Valida data/annotations/flowers.csv contra el spec per-flower-annotation."""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGES = {"inmaduro", "optimo", "sobreabierto"}


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/annotations/flowers.csv"
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with (ROOT / "data/raw/labels_imagen.csv").open(encoding="utf-8") as f:
        images = {r["md5"]: r["file"] for r in csv.DictReader(f)}
    errors: list[str] = []
    for i, r in enumerate(rows, start=2):
        loc = f"línea {i} ({images.get(r['md5'], r['md5'])})"
        x, y, w, h = (float(r[k]) for k in ("x", "y", "w", "h"))
        if r["md5"] not in images:
            errors.append(f"{loc}: md5 desconocido")
        if w <= 0 or h <= 0:
            errors.append(f"{loc}: w/h no positivos ({w}, {h})")
        if x < 0 or y < 0 or x + w > 1 + 1e-6 or y + h > 1 + 1e-6:
            errors.append(f"{loc}: caja fuera de imagen x={x} y={y} w={w} h={h}")
        if r["annotatable"] == "1":
            if r["stage"] not in STAGES:
                errors.append(f"{loc}: etapa inválida '{r['stage']}'")
        elif r["stage"]:
            errors.append(f"{loc}: no anotable con etapa '{r['stage']}'")
    covered = {r["md5"] for r in rows}
    for md5, name in images.items():
        if md5 not in covered:
            errors.append(f"{name}: sin anotaciones")
    print(f"filas={len(rows)} fotos_cubiertas={len(covered & set(images))}/{len(images)}")
    print("etapas:", dict(Counter(r["stage"] for r in rows)))
    for e in errors:
        print("ERROR", e)
    print("OK" if not errors else f"{len(errors)} errores")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
