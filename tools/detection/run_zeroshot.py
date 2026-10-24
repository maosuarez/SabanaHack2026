"""Corre OWLv2 / Grounding DINO con texto 'rose' sobre train y test. Guarda scores crudos."""

from __future__ import annotations

import json
import sys
import time

import torch
from common import OUT_DIR, md5_to_file
from PIL import Image

torch.set_num_threads(8)
OWL_ID = "google/owlv2-base-patch16-ensemble"
GD_ID = "IDEA-Research/grounding-dino-tiny"
FLOOR = (
    0.01  # piso técnico de score para no guardar ruido puro; no es el umbral operativo
)


def run_owl(files: dict[str, str]) -> tuple[dict, dict]:
    from transformers import Owlv2ForObjectDetection, Owlv2Processor

    proc = Owlv2Processor.from_pretrained(OWL_ID)
    model = Owlv2ForObjectDetection.from_pretrained(OWL_ID).eval()
    preds, times = {}, {}
    for m, p in files.items():
        im = Image.open(p).convert("RGB")
        w, h = im.size
        t0 = time.perf_counter()
        inp = proc(text=[["a photo of a rose"]], images=im, return_tensors="pt")
        with torch.no_grad():
            out = model(**inp)
        side = max(w, h)  # OWLv2 rellena a cuadrado
        res = proc.image_processor.post_process_object_detection(
            out, threshold=FLOOR, target_sizes=torch.tensor([[side, side]])
        )[0]
        times[m] = (time.perf_counter() - t0) * 1000
        preds[m] = [
            {
                "box": [
                    max(0, b[0] / w),
                    max(0, b[1] / h),
                    min(1, b[2] / w),
                    min(1, b[3] / h),
                ],
                "score": float(s),
            }
            for b, s in zip(res["boxes"].tolist(), res["scores"].tolist())
        ]
    return preds, times


def run_gd(files: dict[str, str]) -> tuple[dict, dict]:
    from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

    proc = AutoProcessor.from_pretrained(GD_ID)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(GD_ID).eval()
    preds, times = {}, {}
    for m, p in files.items():
        im = Image.open(p).convert("RGB")
        w, h = im.size
        t0 = time.perf_counter()
        inp = proc(images=im, text="rose.", return_tensors="pt")
        with torch.no_grad():
            out = model(**inp)
        res = proc.post_process_grounded_object_detection(
            out,
            inp.input_ids,
            threshold=FLOOR,
            text_threshold=FLOOR,
            target_sizes=[(h, w)],
        )[0]
        times[m] = (time.perf_counter() - t0) * 1000
        preds[m] = [
            {
                "box": [
                    max(0, b[0] / w),
                    max(0, b[1] / h),
                    min(1, b[2] / w),
                    min(1, b[3] / h),
                ],
                "score": float(s),
            }
            for b, s in zip(res["boxes"].tolist(), res["scores"].tolist())
        ]
    return preds, times


def main() -> None:
    which = sys.argv[1]
    split = json.loads((OUT_DIR / "split.json").read_text())
    f2 = md5_to_file()
    fn = {"owlv2": run_owl, "gdino": run_gd}[which]
    for part in ("test", "train"):
        files = {m: str(f2[m]) for m in split[part]}
        preds, times = fn(files)
        ms = sorted(times.values())
        meta = {
            "model": OWL_ID if which == "owlv2" else GD_ID,
            "text": "rose",
            "score_floor": FLOOR,
            "device": "cpu",
            "threads": torch.get_num_threads(),
            "ms_per_image_mean": sum(ms) / len(ms),
            "ms_per_image_median": ms[len(ms) // 2],
            "ms_first_image_cold": next(iter(times.values())),
            "input": "1200x1600 -> processor default",
        }
        (OUT_DIR / f"preds_{which}_{part}.json").write_text(
            json.dumps({"meta": meta, "times_ms": times, "predictions": preds})
        )
        print(which, part, meta["ms_per_image_mean"], flush=True)


if __name__ == "__main__":
    main()
