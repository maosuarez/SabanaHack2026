"""Precalcula explicaciones de Kimi (solo explica, no decide) para las flores de la galería.

Uso: python tools/pipeline/make_explanations.py [--model kimi-k2.6] [--gap 21]
Salida: data/processed/pipeline/explanations_kimi.json (clave "imagen#n"); reanudable.
Recortes en data/processed/pipeline/explain_crops/. Nunca imprime la clave.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/pipeline"))
from predict import MARGIN, Pipeline, crop_box  # noqa: E402
from vlm_stage import explain_crop  # noqa: E402

IMAGES = ("rosa_18", "rosa_37", "rosa_61")
OUT = ROOT / "data/processed/pipeline/explanations_kimi.json"
CROPS = ROOT / "data/processed/pipeline/explain_crops"
MAX_SIDE = 1600  # igual que demo_app.analyze, para que el # coincida


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="kimi-k2.6")
    ap.add_argument("--gap", type=float, default=21.0)
    a = ap.parse_args()
    CROPS.mkdir(parents=True, exist_ok=True)
    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    pipe = Pipeline()
    last = 0.0
    for name in IMAGES:
        img = ImageOps.exif_transpose(Image.open(ROOT / "data/raw/images" / f"{name}.jpeg")).convert("RGB")
        img.thumbnail((MAX_SIDE, MAX_SIDE))
        flores, _ = pipe.run(img)
        for f in flores:
            key = f"{name}#{f['id'] + 1}"
            if data.get(key, {}).get("ok"):
                continue
            crop = CROPS / f"{name}_{f['id'] + 1}.jpg"
            crop_box(img, f["caja_norm"]).save(crop, "JPEG", quality=92)
            wait = a.gap - (time.time() - last)
            if wait > 0:
                time.sleep(wait)
            r = explain_crop(crop, f["etapa"], f["confianza"], a.model)
            last = time.time()
            res = r.get("result") or {}
            data[key] = {"imagen": name, "n": f["id"] + 1, "ok": bool(r.get("ok")),
                         "etapa_local": f["etapa"], "confianza": f["confianza"],
                         "explicacion": res.get("explicacion"), "rasgos": res.get("rasgos"),
                         "coherente": res.get("coherente"), "modelo": a.model,
                         "prompt_tokens": r.get("prompt_tokens"), "completion_tokens": r.get("completion_tokens"),
                         "error": r.get("error"), "fecha": datetime.now().isoformat(timespec="seconds")}
            OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
            print(key, f["etapa"], "ok" if r.get("ok") else r.get("error"), flush=True)
    print(f"{sum(v['ok'] for v in data.values())}/{len(data)} explicaciones en {OUT}")


if __name__ == "__main__":
    main()
