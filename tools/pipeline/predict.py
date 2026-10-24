"""Demo "RA": detector RT-DETR + clasificador DINOv2-S/LogReg -> caja y veredicto por flor.

Uso: python tools/pipeline/predict.py ruta_imagen_o_video --out salida [--checkpoint dir] [--thr 0.152]
Salida: <out>/<nombre>_anotada.(png|mp4) + <out>/<nombre>.json (por flor: caja, etapa, probs, veredicto, motivo).
Video: 1 fotograma por segundo; el original no se modifica.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont
from sklearn.linear_model import LogisticRegression
from transformers import AutoModel, RTDetrForObjectDetection

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/classification"))
from cv_eval import build_train  # noqa: E402
from embed_train import BASE, CLASSES, EMB, OUT_J, embed  # noqa: E402
from gray_zone import C, N_SOB, decide  # noqa: E402

TAU = 0.55
MARGIN = 0.10  # igual que make_crops.py
IMG_SIZE = 640  # igual que el entrenamiento del detector
CKPT = ROOT / "outputs/rtdetr_final/checkpoint"
THR = 0.152
CLF_PATH = ROOT / "outputs/pipeline/clf_logreg_c10_sob24.joblib"
VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
COLORS = {"apto": (30, 160, 60), "no_apto": (230, 80, 30), "gris": (240, 190, 0)}
NAMES = {"apto": "APTO", "no_apto": "NO APTO", "gris": "ZONA GRIS"}
ABBR = {"inmaduro": "inmaduro", "optimo": "optimo", "sobreabierto": "sobreabierto"}


def get_classifier() -> LogisticRegression:
    """LogReg C=10, sin class_weight, 24 copias de sobreabierto; train+val. Cacheado en disco."""
    if CLF_PATH.exists():
        return joblib.load(CLF_PATH)
    man = list(csv.DictReader((OUT_J / "manifest.csv").open()))
    pool = [r for r in man if r["split"] in ("train", "val")]
    y = np.array([CLASSES.index(r["stage"]) for r in pool])
    base, aug = np.load(EMB / "cv_pool_base.npy"), np.load(EMB / "cv_pool_aug.npy")
    x, yy = build_train(np.arange(len(y)), base, aug, y, N_SOB)
    clf = LogisticRegression(C=C, max_iter=3000).fit(x, yy)
    CLF_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, CLF_PATH)
    return clf


@torch.no_grad()
def detect(det, img: Image.Image, thr: float) -> list[tuple[list[float], float]]:
    arr = np.asarray(img.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.BILINEAR), dtype=np.float32)
    x = torch.from_numpy(arr / 255.0).permute(2, 0, 1)[None]
    out = det(pixel_values=x)
    sc = out.logits[0].sigmoid().max(-1).values
    res = []
    for (cx, cy, w, h), s in zip(out.pred_boxes[0].tolist(), sc.tolist()):
        if s >= thr:
            res.append(([max(0., cx - w / 2), max(0., cy - h / 2), min(1., cx + w / 2), min(1., cy + h / 2)], s))
    return sorted(res, key=lambda r: -r[1])


def crop_box(img: Image.Image, b) -> Image.Image:
    W, H = img.size
    w, h = b[2] - b[0], b[3] - b[1]
    return img.crop((round(max(0, (b[0] - MARGIN * w) * W)), round(max(0, (b[1] - MARGIN * h) * H)),
                     round(min(W, (b[0] + w * (1 + MARGIN)) * W)), round(min(H, (b[1] + h * (1 + MARGIN)) * H))))


def font(size: int) -> ImageFont.FreeTypeFont:
    for f in ("arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def annotate(img: Image.Image, flowers: list[dict]) -> Image.Image:
    im = img.copy()
    W, H = im.size
    d = ImageDraw.Draw(im)
    fs = max(11, round(W / 70))
    f = font(fs)
    lw = max(1, W // 700)
    for fl in flowers:
        b = fl["caja_norm"]
        x1, y1, x2, y2 = b[0] * W, b[1] * H, b[2] * W, b[3] * H
        col = COLORS[fl["veredicto_clave"]]
        d.rectangle([x1, y1, x2, y2], outline=col, width=lw)
        l1 = f"#{fl['id'] + 1} {NAMES[fl['veredicto_clave']]} | {ABBR[fl['etapa']]} {fl['confianza']:.2f}"
        lines = [l1] + ([fl["motivo_corto"]] if fl["veredicto_clave"] == "gris" else [])
        sizes = [d.textbbox((0, 0), t, font=f) for t in lines]
        tw = max(s[2] - s[0] for s in sizes) + 6
        th = sum(s[3] - s[1] + 4 for s in sizes) + 2
        ty = y1 - th - 1
        if ty < 0:  # sin espacio arriba: debajo de la caja
            ty = min(y2 + 1, H - th)
        tx = min(max(0, x1), W - tw)
        d.rectangle([tx, ty, tx + tw, ty + th], fill=col)
        yy = ty + 2
        for t, s in zip(lines, sizes):
            d.text((tx + 3, yy - s[1]), t, fill=(0, 0, 0) if fl["veredicto_clave"] == "gris" else (255, 255, 255), font=f)
            yy += s[3] - s[1] + 4
    # leyenda + aviso
    lf = font(max(12, round(W / 60)))
    items = [("APTO", COLORS["apto"]), ("NO APTO", COLORS["no_apto"]), ("ZONA GRIS", COLORS["gris"])]
    pad = 6
    bh = lf.size + 2 * pad
    d.rectangle([0, H - 2 * bh, W, H], fill=(20, 20, 20))
    x = pad
    for t, c in items:
        d.rectangle([x, H - 2 * bh + pad, x + lf.size, H - 2 * bh + pad + lf.size], fill=c)
        d.text((x + lf.size + 4, H - 2 * bh + pad - 1), t, fill=(255, 255, 255), font=lf)
        x += lf.size + 4 + int(d.textlength(t, font=lf)) + 3 * pad
    d.text((pad, H - bh + pad - 1), "Ayuda, decide la persona (modelo parcial, no es un veredicto final)",
           fill=(220, 220, 220), font=lf)
    return im


def process(det, dino, clf, img: Image.Image, thr: float) -> tuple[list[dict], dict]:
    t0 = time.perf_counter()
    dets = detect(det, img, thr)
    t1 = time.perf_counter()
    flowers = []
    if dets:
        probs = clf.predict_proba(embed(dino, [crop_box(img, b) for b, _ in dets], BASE))
        for i, ((b, s), p) in enumerate(zip(dets, probs)):
            dec, motivo = decide(p[None], TAU)[0]
            k = int(p.argmax())
            short = {"apto": "", "no_apto": "inmaduro",
                     "gris": "sobreabierto" if k == 2 else f"optimo P={p[1]:.2f}<{TAU}"}[dec]
            flowers.append({"id": i, "caja_norm": [round(v, 4) for v in b], "score_detector": round(s, 3),
                            "etapa": CLASSES[k], "confianza": round(float(p[k]), 3),
                            "probabilidades": {c: round(float(p[j]), 3) for j, c in enumerate(CLASSES)},
                            "veredicto_clave": dec, "veredicto": NAMES[dec], "motivo": motivo,
                            "motivo_corto": short})
    t2 = time.perf_counter()
    return flowers, {"detector_ms": (t1 - t0) * 1e3, "clasificador_ms": (t2 - t1) * 1e3, "total_ms": (t2 - t0) * 1e3}


class Pipeline:
    """Carga detector, DINOv2 y clasificador UNA vez; run(img) -> (flores, tiempos_ms)."""

    def __init__(self, checkpoint: str | Path = CKPT, thr: float = THR):
        self.thr, self.checkpoint = thr, str(checkpoint)
        self.det = RTDetrForObjectDetection.from_pretrained(checkpoint).eval()
        self.dino = AutoModel.from_pretrained("facebook/dinov2-small").eval()
        self.clf = get_classifier()
        self.run(Image.new("RGB", (64, 64)))  # calentamiento

    def run(self, img: Image.Image, thr: float | None = None) -> tuple[list[dict], dict]:
        return process(self.det, self.dino, self.clf, img.convert("RGB"), self.thr if thr is None else thr)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--out", required=True)
    ap.add_argument("--checkpoint", default=str(CKPT))
    ap.add_argument("--thr", type=float, default=THR)
    a = ap.parse_args()
    torch.set_num_threads(4)
    src, out = Path(a.input), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    det = RTDetrForObjectDetection.from_pretrained(a.checkpoint).eval()
    dino = AutoModel.from_pretrained("facebook/dinov2-small").eval()
    clf = get_classifier()
    meta = {"checkpoint": a.checkpoint, "umbral_detector": a.thr, "tau": TAU,
            "clasificador": f"DINOv2-S/14 + LogReg C={C} sin cw, sob_aug={N_SOB}, train+val"}
    if src.suffix.lower() in VIDEO_EXT:
        import cv2
        cap = cv2.VideoCapture(str(src))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        n_tot = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        vw, res, times = None, [], []
        for sec in range(int(n_tot / fps) + 1):
            cap.set(cv2.CAP_PROP_POS_FRAMES, round(sec * fps))
            ok, fr = cap.read()
            if not ok:
                break
            img = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
            fl, t = process(det, dino, clf, img, a.thr)
            times.append(t["total_ms"])
            res.append({"t_s": sec, "flores": fl, "tiempos_ms": t})
            ann = cv2.cvtColor(np.asarray(annotate(img, fl)), cv2.COLOR_RGB2BGR)
            if vw is None:
                vw = cv2.VideoWriter(str(out / f"{src.stem}_anotada.mp4"), cv2.VideoWriter_fourcc(*"mp4v"),
                                     1, (ann.shape[1], ann.shape[0]))
            vw.write(ann)
        if vw:
            vw.release()
        (out / f"{src.stem}.json").write_text(json.dumps({**meta, "fotogramas": res}, indent=1, ensure_ascii=False))
        print(f"{src.name}: {len(res)} fotogramas, media {np.mean(times):.0f} ms/fotograma")
    else:
        img = Image.open(src).convert("RGB")
        process(det, dino, clf, img.resize((64, 64)), a.thr)  # calentamiento (no se cuenta)
        fl, t = process(det, dino, clf, img, a.thr)
        annotate(img, fl).save(out / f"{src.stem}_anotada.png")
        (out / f"{src.stem}.json").write_text(json.dumps(
            {**meta, "imagen": str(src), "tamano": img.size, "tiempos_ms": {k: round(v, 1) for k, v in t.items()},
             "flores": fl}, indent=1, ensure_ascii=False))
        cnt = {k: sum(f["veredicto_clave"] == k for f in fl) for k in COLORS}
        print(f"{src.name}: {len(fl)} flores {cnt} | {t['total_ms']:.0f} ms "
              f"(det {t['detector_ms']:.0f} + clf {t['clasificador_ms']:.0f})")


if __name__ == "__main__":
    main()
