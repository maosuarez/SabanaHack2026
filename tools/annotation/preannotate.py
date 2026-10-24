"""Pre-anota rosas con un detector de vocabulario abierto (OWLv2) y escribe
predicciones de Label Studio SIN etapa (la etapa nunca se pre-anota).

Uso:
    python preannotate.py --md5 <md5> [<md5> ...] [--threshold 0.1] \
        [--out data/annotations/preannotations_pilot.json]
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any

import torch
from PIL import Image
from transformers import Owlv2ForObjectDetection, Owlv2Processor

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
MODEL_ID = "google/owlv2-base-patch16-ensemble"
# Deben coincidir con tools/annotation/label_config.xml
FROM_NAME = "stage"
TO_NAME = "image"
RESULT_TYPE = "rectanglelabels"


def load_index() -> dict[str, dict[str, str]]:
    """md5 -> fila de labels_imagen.csv."""
    with (RAW_DIR / "labels_imagen.csv").open(newline="", encoding="utf-8") as fh:
        return {row["md5"]: row for row in csv.DictReader(fh)}


def detect(
    image: Image.Image,
    processor: Owlv2Processor,
    model: Owlv2ForObjectDetection,
    threshold: float,
) -> list[tuple[list[float], float]]:
    """Devuelve [(caja [x1,y1,x2,y2] en % de la imagen, score)]."""
    inputs = processor(text=[["a photo of a rose"]], images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    w, h = image.size
    side = max(w, h)  # OWLv2 rellena a cuadrado: las cajas salen en esa escala
    res = processor.post_process_grounded_object_detection(
        outputs, threshold=threshold, target_sizes=torch.tensor([[side, side]])
    )[0]
    out: list[tuple[list[float], float]] = []
    for box, score in zip(res["boxes"].tolist(), res["scores"].tolist()):
        x1, y1, x2, y2 = box
        x1, x2 = max(0.0, x1), min(float(w), x2)
        y1, y2 = max(0.0, y1), min(float(h), y2)
        if x2 <= x1 or y2 <= y1:
            continue
        out.append(([x1 / w * 100, y1 / h * 100, x2 / w * 100, y2 / h * 100], score))
    return out


def to_prediction(boxes: list[tuple[list[float], float]], w: int, h: int) -> dict[str, Any]:
    """Predicción de Label Studio con cajas sin etiqueta de etapa."""
    results: list[dict[str, Any]] = []
    for i, (b, score) in enumerate(boxes):
        results.append(
            {
                "id": f"det{i}",
                "from_name": FROM_NAME,
                "to_name": TO_NAME,
                "type": RESULT_TYPE,
                "original_width": w,
                "original_height": h,
                "image_rotation": 0,
                "value": {
                    "x": b[0],
                    "y": b[1],
                    "width": b[2] - b[0],
                    "height": b[3] - b[1],
                    "rotation": 0,
                    "rectanglelabels": [],  # sin etapa
                },
                "score": score,
            }
        )
    mean = sum(s for _, s in boxes) / len(boxes) if boxes else 0.0
    return {"model_version": MODEL_ID, "score": mean, "result": results}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md5", nargs="+", required=True)
    ap.add_argument("--threshold", type=float, default=0.1)
    ap.add_argument(
        "--out", type=Path, default=REPO_ROOT / "data/annotations/preannotations_pilot.json"
    )
    args = ap.parse_args()

    index = load_index()
    processor = Owlv2Processor.from_pretrained(MODEL_ID)
    model = Owlv2ForObjectDetection.from_pretrained(MODEL_ID).eval()

    # Formato: lista de {"image": ruta de Label Studio, "md5", "predictions": [...]}
    tasks: list[dict[str, Any]] = []
    for md5 in args.md5:
        row = index[md5]
        image = Image.open(RAW_DIR / "images" / row["file"]).convert("RGB")
        t0 = time.perf_counter()
        boxes = detect(image, processor, model, args.threshold)
        dt = time.perf_counter() - t0
        print(f"{row['file']} md5={md5} boxes={len(boxes)} t={dt:.1f}s")
        tasks.append(
            {
                "data": {
                    "image": f"/data/local-files/?d=images/{row['file']}",
                    "md5": md5,
                    "image_id": int(row["image_id"]),
                },
                "predictions": [to_prediction(boxes, *image.size)],
            }
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(tasks, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"escrito {args.out}")


if __name__ == "__main__":
    main()
