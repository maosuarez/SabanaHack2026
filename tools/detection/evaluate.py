"""Evaluador de detección: recall@IoU, falsas por imagen, AP, desglose por condición."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np
from common import OUT_DIR, Box, load_gt

Pred = tuple[Box, float]  # (caja, score)
CONDITIONS = ("contraluz", "pequenas", "oclusion", "varias_rosas")


def iou(a: Box, b: Box) -> float:
    """IoU entre dos cajas x1,y1,x2,y2 (invariante a escala por eje)."""
    iw = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    ih = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = iw * ih
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def match_image(
    gts: Sequence[Box], preds: Sequence[Pred], iou_thr: float = 0.5
) -> list[tuple[float, bool]]:
    """Emparejamiento voraz por score descendente. Devuelve (score, es_TP) por predicción."""
    used = [False] * len(gts)
    res: list[tuple[float, bool]] = []
    for box, score in sorted(preds, key=lambda p: -p[1]):
        best, bj = 0.0, -1
        for j, g in enumerate(gts):
            if used[j]:
                continue
            v = iou(box, g)
            if v > best:
                best, bj = v, j
        if bj >= 0 and best >= iou_thr:
            used[bj] = True
            res.append((score, True))
        else:
            res.append((score, False))
    return res


def average_precision(matches: list[tuple[float, bool]], n_gt: int) -> float:
    """AP de todos los puntos (estilo VOC) a partir de predicciones emparejadas."""
    if n_gt == 0 or not matches:
        return 0.0
    m = sorted(matches, key=lambda t: -t[0])
    tp = np.cumsum([t[1] for t in m])
    fp = np.cumsum([not t[1] for t in m])
    rec = tp / n_gt
    prec = tp / np.maximum(tp + fp, 1e-9)
    mrec = np.concatenate([[0.0], rec, [1.0]])
    mpre = np.concatenate([[0.0], prec, [0.0]])
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])
    idx = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[idx + 1] - mrec[idx]) * mpre[idx + 1]))


def evaluate(
    gt: dict[str, list[Box]],
    preds: dict[str, list[Pred]],
    md5s: Sequence[str],
    thr: float,
    iou_thr: float = 0.5,
) -> dict[str, float]:
    """Métricas sobre md5s. Recall/falsas con umbral thr; AP con todas las cajas (sin umbral)."""
    n_gt = tp = fp = 0
    all_m: list[tuple[float, bool]] = []
    for m in md5s:
        g, p = gt.get(m, []), preds.get(m, [])
        n_gt += len(g)
        all_m += match_image(g, p, iou_thr)
        kept = [x for x in match_image(g, p, iou_thr) if x[0] >= thr]
        tp += sum(t for _, t in kept)
        fp += sum(not t for _, t in kept)
    return {
        "images": len(md5s),
        "gt": n_gt,
        "tp": tp,
        "fp": fp,
        "recall": tp / n_gt if n_gt else float("nan"),
        "fp_per_image": fp / len(md5s) if md5s else float("nan"),
        "ap": average_precision(all_m, n_gt),
    }


def best_f1_threshold(
    gt: dict[str, list[Box]],
    preds: dict[str, list[Pred]],
    md5s: Sequence[str],
    iou_thr: float = 0.5,
) -> tuple[float, float]:
    """Umbral que maximiza F1 en md5s (usar solo train). Devuelve (umbral, f1)."""
    scores = sorted({s for m in md5s for _, s in preds.get(m, [])})
    best = (0.0, -1.0)
    for t in scores:
        r = evaluate(gt, preds, md5s, t, iou_thr)
        p = r["tp"] / (r["tp"] + r["fp"]) if r["tp"] + r["fp"] else 0.0
        f1 = 2 * p * r["recall"] / (p + r["recall"]) if p + r["recall"] else 0.0
        if f1 > best[1]:
            best = (t, f1)
    return best


def by_condition(
    gt: dict[str, list[Box]],
    preds: dict[str, list[Pred]],
    md5s: Sequence[str],
    conds: dict[str, dict[str, int]],
    thr: float,
) -> dict[str, dict[str, float]]:
    out = {"todas": evaluate(gt, preds, md5s, thr)}
    for c in CONDITIONS:
        sub = [m for m in md5s if conds.get(m, {}).get(c)]
        if sub:
            out[c] = evaluate(gt, preds, sub, thr)
    return out


def load_preds(path: Path) -> dict[str, list[Pred]]:
    raw = json.loads(path.read_text())["predictions"]
    return {m: [(tuple(d["box"]), d["score"]) for d in v] for m, v in raw.items()}  # type: ignore[misc]


def load_conditions() -> dict[str, dict[str, int]]:
    return json.loads((OUT_DIR / "test_conditions.json").read_text())["conditions"]


def sanity_check() -> None:
    """Cajas de referencia como predicción: recall 1 y 0 falsas."""
    gt = load_gt()
    preds = {m: [(b, 1.0) for b in v] for m, v in gt.items()}
    r = evaluate(gt, preds, list(gt), 0.5)
    assert r["recall"] == 1.0 and r["fp"] == 0 and abs(r["ap"] - 1.0) < 1e-9, r
    print("sanity OK", r)


if __name__ == "__main__":
    sanity_check()
