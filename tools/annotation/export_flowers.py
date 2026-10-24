"""Convierte el export JSON de Label Studio en data/annotations/flowers.csv."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
COLUMNS = ["md5", "image_id", "x", "y", "w", "h", "stage", "doubtful", "annotatable", "annotator"]


def annotator_of(ann: dict[str, Any]) -> str:
    """Identifica al anotador a partir de completed_by (id o dict)."""
    by = ann.get("completed_by")
    if isinstance(by, dict):
        return str(by.get("email") or by.get("id"))
    return f"user{by}"


def rows_of_task(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Filas (una por caja) de la anotación enviada de una tarea."""
    anns = [a for a in task.get("annotations", []) if not a.get("was_cancelled")]
    if not anns:
        return []
    ann = anns[0]
    regions: dict[str, dict[str, Any]] = {}
    flags: dict[str, set[str]] = {}
    for r in ann["result"]:
        if r["type"] == "rectanglelabels":
            regions[r["id"]] = r
        elif r["type"] == "choices":
            flags.setdefault(r["id"], set()).update(r["value"].get("choices", []))
    out: list[dict[str, Any]] = []
    for rid, r in regions.items():
        v = r["value"]
        fl = flags.get(rid, set())
        annotatable = "no_anotable" not in fl
        labels = v.get("rectanglelabels", [])
        out.append({
            "md5": task["data"]["md5"],
            "image_id": task["data"]["image_id"],
            "x": round(v["x"] / 100, 6), "y": round(v["y"] / 100, 6),
            "w": round(v["width"] / 100, 6), "h": round(v["height"] / 100, 6),
            "stage": labels[0] if (labels and annotatable) else "",
            "doubtful": int("dudosa" in fl),
            "annotatable": int(annotatable),
            "annotator": annotator_of(ann),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=ROOT / "data/annotations/labelstudio_export.json")
    ap.add_argument("--output", type=Path, default=ROOT / "data/annotations/flowers.csv")
    args = ap.parse_args()
    tasks = json.loads(args.input.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for t in tasks:
        n = len([a for a in t.get("annotations", []) if not a.get("was_cancelled")])
        if n > 1:
            print(f"AVISO: tarea {t['id']} ({t['data'].get('file')}) tiene {n} anotaciones; se usa la primera")
        rows += rows_of_task(t)
    with (ROOT / "data/raw/labels_imagen.csv").open(encoding="utf-8") as f:
        known = {r["md5"] for r in csv.DictReader(f)}
    bad = sorted({r["md5"] for r in rows} - known)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} filas -> {args.output}; md5 desconocidos: {len(bad)} {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
