"""Tareas 3.1-3.2: embeddings DINOv2 congelados (CLS, L2) + kNN y regresión logística."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.neighbors import KNeighborsClassifier
from torchvision import transforms as T
from transformers import AutoModel

ROOT = Path(__file__).resolve().parents[2]
OUT_J = ROOT / "data/processed/classification"
CROPS = ROOT / "outputs/classification/crops"
EMB = ROOT / "outputs/classification/emb"
MODELS = {"vit_s14": "facebook/dinov2-small", "vit_b14": "facebook/dinov2-base"}
CLASSES = ["inmaduro", "optimo", "sobreabierto"]
N_AUG = 8  # copias aumentadas por recorte de train
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
BASE = T.Compose([T.Resize((224, 224)), T.ToTensor(), T.Normalize(MEAN, STD)])
# Aumentación solo en train: rotación ±30°, zoom, brillo/contraste leves, sin hue
AUG = T.Compose([
    T.RandomRotation(30), T.RandomResizedCrop(224, scale=(0.7, 1.0), ratio=(0.85, 1.18)),
    T.ColorJitter(brightness=0.2, contrast=0.2), T.ToTensor(), T.Normalize(MEAN, STD)])


def embed(model: torch.nn.Module, imgs: list[Image.Image], tf: T.Compose) -> np.ndarray:
    out = []
    with torch.inference_mode():
        for i in range(0, len(imgs), 16):
            x = torch.stack([tf(im) for im in imgs[i:i + 16]])
            cls = model(pixel_values=x).last_hidden_state[:, 0]
            out.append(torch.nn.functional.normalize(cls, dim=-1).numpy())
    return np.concatenate(out)


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    pr, rc, f1, sup = precision_recall_fscore_support(y, p, labels=range(3), zero_division=0)
    return {"acc": accuracy_score(y, p), "bal_acc": balanced_accuracy_score(y, p),
            "f1_macro": float(f1.mean()),
            "per_class": {c: {"p": float(pr[i]), "r": float(rc[i]), "f1": float(f1[i]),
                              "n": int(sup[i])} for i, c in enumerate(CLASSES)},
            "cm": confusion_matrix(y, p, labels=range(3)).tolist()}


def main() -> None:
    torch.manual_seed(2026)
    torch.set_num_threads(8)
    EMB.mkdir(parents=True, exist_ok=True)
    man = list(csv.DictReader((OUT_J / "manifest.csv").open()))
    data = {s: [r for r in man if r["split"] == s] for s in ("train", "val", "test")}
    y = {s: np.array([CLASSES.index(r["stage"]) for r in rs]) for s, rs in data.items()}
    imgs = {s: [Image.open(CROPS / r["crop"]).convert("RGB") for r in rs] for s, rs in data.items()}
    results: dict = {}
    feats: dict = {}
    for name, hub in MODELS.items():
        model = AutoModel.from_pretrained(hub).eval()
        f = {s: embed(model, imgs[s], BASE) for s in imgs}
        aug = np.concatenate([embed(model, imgs["train"], AUG) for _ in range(N_AUG)])
        for s, a in f.items():
            np.save(EMB / f"{name}_{s}.npy", a)
        np.save(EMB / f"{name}_train_aug.npy", aug)
        feats[name] = (f, aug)
        print(name, "embeddings", {s: a.shape for s, a in f.items()}, aug.shape, flush=True)
    ytr_aug = np.tile(y["train"], N_AUG)
    cands = []  # (modelo, clf, hiperparam, métricas val)
    for name, (f, aug) in feats.items():
        xtr = np.concatenate([f["train"], aug])
        ytr = np.concatenate([y["train"], ytr_aug])
        for k in (1, 3, 5, 7, 11, 15):
            clf = KNeighborsClassifier(k, metric="cosine", weights="distance").fit(xtr, ytr)
            cands.append((name, "knn", k, metrics(y["val"], clf.predict(f["val"]))))
        for c in (0.1, 1, 10, 100):
            clf = LogisticRegression(C=c, class_weight="balanced", max_iter=5000).fit(xtr, ytr)
            cands.append((name, "logreg", c, metrics(y["val"], clf.predict(f["val"]))))
    for n, t, h, m in cands:
        print(f"VAL {n} {t} {h}: acc {m['acc']:.3f} bal {m['bal_acc']:.3f} f1m {m['f1_macro']:.3f}")
    results["val"] = [{"model": n, "clf": t, "hp": h, **m} for n, t, h, m in cands]
    # mejor config por modelo/clasificador en val (criterio: acc. balanceada, luego F1 macro)
    best = max(cands, key=lambda c: (c[3]["bal_acc"], c[3]["f1_macro"]))
    results["best_val"] = {"model": best[0], "clf": best[1], "hp": best[2]}
    # evaluación única en test con la mejor configuración elegida en val
    name, kind, hp, _ = best
    f, aug = feats[name]
    xtr = np.concatenate([f["train"], aug])
    ytr = np.concatenate([y["train"], ytr_aug])
    clf = (KNeighborsClassifier(hp, metric="cosine", weights="distance") if kind == "knn"
           else LogisticRegression(C=hp, class_weight="balanced", max_iter=5000)).fit(xtr, ytr)
    results["test"] = {"model": name, "clf": kind, "hp": hp,
                       **metrics(y["test"], clf.predict(f["test"]))}
    (OUT_J / "stage_results.json").write_text(json.dumps(results, indent=1))
    print("BEST", results["best_val"])
    print("TEST", json.dumps(results["test"]))


if __name__ == "__main__":
    sys.exit(main())
