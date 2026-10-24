"""Evalúa la cadena completa en test: RT-DETR (cajas guardadas) -> recorte -> DINOv2-S + kNN."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image, ImageDraw
from sklearn.neighbors import KNeighborsClassifier
from transformers import AutoModel

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/detection"))
sys.path.insert(0, str(ROOT / "tools/classification"))
from common import Box, md5_to_file
from embed_train import BASE, CLASSES, EMB, embed
from evaluate import iou

DET = ROOT / "data/processed/detection"
CLS = ROOT / "data/processed/classification"
OUT = ROOT / "data/processed/pipeline"
MARGIN = 0.10  # igual que make_crops.py
K = 7
NONE, FALSE = 3, 3  # índice de fila "no detectada" / columna "caja falsa"


def crop_box(img: Image.Image, b: Box) -> Image.Image:
    """Recorte con margen relativo, idéntico a make_crops.py (b en x1,y1,x2,y2 normalizado)."""
    W, H = img.size
    w, h = b[2] - b[0], b[3] - b[1]
    x1, y1 = max(0, (b[0] - MARGIN * w) * W), max(0, (b[1] - MARGIN * h) * H)
    x2, y2 = (
        min(W, (b[0] + w * (1 + MARGIN)) * W),
        min(H, (b[1] + h * (1 + MARGIN)) * H),
    )
    return img.crop((round(x1), round(y1), round(x2), round(y2)))


def acc_bal(y: list[int], p: list[int]) -> tuple[float, float]:
    """Exactitud y exactitud balanceada (clases presentes en y)."""
    ya, pa = np.array(y), np.array(p)
    rec = [float((pa[ya == c] == c).mean()) for c in range(3) if (ya == c).any()]
    return float((ya == pa).mean()), float(np.mean(rec))


def main() -> None:
    torch.set_num_threads(4)
    thr = json.loads((DET / "thresholds.json").read_text())["rtdetr"]["threshold"]
    test = json.loads((DET / "split.json").read_text())["test"]
    files = md5_to_file()
    # verdad: solo anotables, mismo orden que el manifest de test
    man = [
        r for r in csv.DictReader((CLS / "manifest.csv").open()) if r["split"] == "test"
    ]
    gt: dict[str, list[tuple[Box, int, int]]] = {m: [] for m in test}
    for r in csv.DictReader((ROOT / "data/annotations/flowers.csv").open()):
        if r["md5"] in gt and r["annotatable"] == "1":
            x, y, w, h = (float(r[k]) for k in "xywh")
            gt[r["md5"]].append(
                ((x, y, x + w, y + h), CLASSES.index(r["stage"]), int(r["image_id"]))
            )
    assert sum(len(v) for v in gt.values()) == len(man) == 24
    # kNN solo con train (+train_aug), como en embed_train.py
    ytr = np.array(
        [
            CLASSES.index(r["stage"])
            for r in csv.DictReader((CLS / "manifest.csv").open())
            if r["split"] == "train"
        ]
    )
    xtr = np.concatenate(
        [np.load(EMB / "vit_s14_train.npy"), np.load(EMB / "vit_s14_train_aug.npy")]
    )
    yall = np.concatenate([ytr, np.tile(ytr, len(xtr) // len(ytr) - 1)])
    assert len(yall) == len(xtr)
    knn = KNeighborsClassifier(K, metric="cosine", weights="distance").fit(xtr, yall)
    # cota superior: cajas verdaderas (embeddings ya calculados, orden del manifest)
    ytest = np.array([CLASSES.index(r["stage"]) for r in man])
    pt = knn.predict_proba(np.load(EMB / "vit_s14_test.npy"))
    ub_pred = pt.argmax(1)
    ub = acc_bal(ytest.tolist(), ub_pred.tolist())
    # cajas predichas con score >= umbral
    preds = json.loads((DET / "preds_rtdetr_test.json").read_text())["predictions"]
    sel: list[dict[str, Any]] = []
    for m in test:
        for d in preds.get(m, []):
            if d["score"] >= thr:
                sel.append({"md5": m, "box": tuple(d["box"]), "score": d["score"]})
    model = AutoModel.from_pretrained("facebook/dinov2-small").eval()
    imgs = {m: Image.open(files[m]).convert("RGB") for m in test}
    crops = [crop_box(imgs[s["md5"]], s["box"]) for s in sel]
    pr = knn.predict_proba(embed(model, crops, BASE))
    for s, p in zip(sel, pr, strict=True):
        s["pred"], s["conf"] = int(p.argmax()), float(p.max())
    # emparejamiento voraz por score (como evaluate.match_image)
    for s in sel:
        s["gt"] = None
    for m in test:
        used: set[int] = set()
        for s in sorted((s for s in sel if s["md5"] == m), key=lambda s: -s["score"]):
            best, bj = 0.0, -1
            for j, (gb, _, _) in enumerate(gt[m]):
                v = iou(s["box"], gb)
                if j not in used and v > best:
                    best, bj = v, j
            if bj >= 0 and best >= 0.5:
                used.add(bj)
                s["gt"] = bj

    # matriz ampliada: filas = real (3 etapas + falsa), columnas = pred (3 etapas + no detectada)
    cm = np.zeros(
        (4, 4), int
    )  # fila 3 = caja falsa (real), col 3 = no detectada (pred)
    errors: list[dict[str, Any]] = []
    matched_rows: list[tuple[int, int, float]] = []
    for m in test:
        hit = {s["gt"] for s in sel if s["md5"] == m and s["gt"] is not None}
        for j, (_, y, iid) in enumerate(gt[m]):
            if j not in hit:
                cm[y, NONE] += 1
                errors.append(
                    {
                        "md5": m,
                        "image_id": iid,
                        "tipo": "no_detectada",
                        "real": CLASSES[y],
                    }
                )
        for s in (s for s in sel if s["md5"] == m):
            if s["gt"] is None:
                cm[FALSE, s["pred"]] += 1
                errors.append(
                    {
                        "md5": m,
                        "image_id": gt[m][0][2] if gt[m] else None,
                        "tipo": "caja_falsa",
                        "pred": CLASSES[s["pred"]],
                        "score": round(s["score"], 3),
                        "conf": round(s["conf"], 3),
                    }
                )
            else:
                _, y, iid = gt[m][s["gt"]]
                cm[y, s["pred"]] += 1
                matched_rows.append((y, s["pred"], s["conf"]))
                if y != s["pred"]:
                    errors.append(
                        {
                            "md5": m,
                            "image_id": iid,
                            "tipo": "etapa_errada",
                            "real": CLASSES[y],
                            "pred": CLASSES[s["pred"]],
                            "conf": round(s["conf"], 3),
                            "score": round(s["score"], 3),
                        }
                    )
    n_gt = 24
    ym = [r[0] for r in matched_rows]
    pm = [r[1] for r in matched_rows]
    det_recall = len(matched_rows) / n_gt
    acc_det, bal_det = acc_bal(ym, pm)
    per_class: dict[str, dict[str, float | int]] = {}
    for c, name in enumerate(CLASSES):
        n = int(cm[c].sum())
        npred = int(cm[:, c].sum())
        per_class[name] = {
            "n_gt": n,
            "e2e_recall": cm[c, c] / n if n else float("nan"),
            "n_pred": npred,
            "precision_con_falsas": cm[c, c] / npred if npred else float("nan"),
        }
    # tabla de confianza (solo cajas emparejadas)
    conf_tab = []
    cs = np.array([r[2] for r in matched_rows])
    ok = np.array([r[0] == r[1] for r in matched_rows])
    for cut in (0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        keep = cs >= cut
        conf_tab.append(
            {
                "corte": cut,
                "cobertura": float(keep.mean()),
                "n": int(keep.sum()),
                "exactitud": float(ok[keep].mean()) if keep.any() else None,
            }
        )
    res = {
        "umbral_detector": thr,
        "k": K,
        "n_cajas_pred": len(sel),
        "n_matched": len(matched_rows),
        "n_gt": n_gt,
        "n_falsas": int(cm[FALSE].sum()),
        "det_recall": det_recall,
        "knn_train": f"train({len(ytr)} recortes) + train_aug({len(xtr) - len(ytr)})",
        "etapa_sobre_detectadas": {
            "acc": acc_det,
            "bal_acc": bal_det,
            "cm_3x3": cm[:3, :3].tolist(),
        },
        "por_clase": per_class,
        "cm_ampliada": {
            "filas": CLASSES + ["caja_falsa"],
            "cols": CLASSES + ["no_detectada"],
            "m": cm.tolist(),
        },
        "cota_superior_cajas_verdaderas": {"acc": ub[0], "bal_acc": ub[1]},
        "conf_matched": {
            "conf_media_correctas": float(cs[ok].mean()),
            "conf_media_erroneas": float(cs[~ok].mean()) if (~ok).any() else None,
            "conf_erroneas": cs[~ok].round(3).tolist(),
            "conf_falsas": [round(s["conf"], 3) for s in sel if s["gt"] is None],
            "tabla": conf_tab,
        },
        "errores": errors,
        "cajas": [
            {
                "md5": s["md5"],
                "box": s["box"],
                "score": s["score"],
                "pred": CLASSES[s["pred"]],
                "conf": s["conf"],
                "gt_stage": CLASSES[gt[s["md5"]][s["gt"]][1]]
                if s["gt"] is not None
                else None,
            }
            for s in sel
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "chain_test.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "cajas"}, indent=1))
    # dibujo en scratchpad (fuera del repo)
    sc = Path(
        "/tmp/claude-1000/-home-maosuarez-sabana-hack-2026/577a49ce-28e5-4413-8be9-b1d6f0e3ab53/scratchpad"
    )
    col = {"inmaduro": "lime", "optimo": "yellow", "sobreabierto": "red"}
    for m in test:
        im = imgs[m].copy()
        W, H = im.size
        d = ImageDraw.Draw(im)
        lw = max(2, W // 400)
        for gb, _, _ in gt[m]:
            d.rectangle(
                [gb[0] * W, gb[1] * H, gb[2] * W, gb[3] * H], outline="white", width=1
            )
        for c in res["cajas"]:
            if c["md5"] != m:
                continue
            b = c["box"]
            tag = c["pred"][:3] + f" {c['conf']:.2f}" + ("" if c["gt_stage"] else " FP")
            d.rectangle(
                [b[0] * W, b[1] * H, b[2] * W, b[3] * H],
                outline=col[c["pred"]],
                width=lw,
            )
            d.text((b[0] * W, max(0, b[1] * H - 12)), tag, fill=col[c["pred"]])
        im.thumbnail((1000, 1000))
        im.save(sc / f"{m[:8]}.png")


if __name__ == "__main__":
    main()
