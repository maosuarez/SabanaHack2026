"""CV agrupada por md5 (train+val) para elegir config; una sola evaluación en test.

Reutiliza embed()/AUG/BASE de embed_train.py. Aumentación solo en el pliegue de entrenamiento.
Uso: python tools/classification/cv_eval.py [--selftest]
"""

from __future__ import annotations

import csv
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.utils.class_weight import compute_sample_weight
from transformers import AutoModel

sys.path.insert(0, str(Path(__file__).parent))
from embed_train import AUG, BASE, CLASSES, CROPS, MODELS, OUT_J, ROOT, embed  # noqa: E402

EMB = ROOT / "outputs/classification/emb"
N_AUG_BASE = 8  # copias por flor de inmaduro/óptimo
MAX_AUG = 32
SOB_AUG = (8, 24, 32)  # copias para sobreabierto
KS = (1, 3, 5, 7, 11, 15)
CS = (0.1, 1, 10, 100)
SEEDS = (0, 1, 2)


def check_no_leak(folds: list[tuple[np.ndarray, np.ndarray]], groups: np.ndarray,
                  test_md5: set[str]) -> None:
    """Falla si un md5 está en train y val de un pliegue, o si el pool toca el test."""
    for tr, va in folds:
        inter = set(groups[tr]) & set(groups[va])
        if inter:
            raise AssertionError(f"fuga: md5 en train y val del pliegue: {sorted(inter)[:3]}")
    if set(groups) & test_md5:
        raise AssertionError("fuga: md5 del test dentro del pool de CV")


def selftest() -> None:
    g = np.array(["a", "a", "b", "c"])
    check_no_leak([(np.array([0, 2]), np.array([3]))], g, {"z"})  # debe pasar
    for bad, tm in (([(np.array([0, 2]), np.array([1]))], {"z"}),  # 'a' en ambos lados
                    ([(np.array([0]), np.array([3]))], {"b"})):    # test dentro del pool
        try:
            check_no_leak(bad, g, tm)
        except AssertionError:
            continue
        raise SystemExit("SELFTEST FALLO: no detectó la fuga")
    print("selftest fuga OK (pasa en caso limpio, falla en 2 casos de fuga construidos)")


def knn_predict(xtr, ytr, w, xte, k):
    """kNN coseno (vectores L2): voto por similitud^peso de distancia 1/d, ponderado por clase."""
    d = np.maximum(1 - xte @ xtr.T, 1e-9)
    idx = np.argsort(d, axis=1)[:, :k]
    votes = np.zeros((len(xte), 3))
    for j in range(k):
        np.add.at(votes, (np.arange(len(xte)), ytr[idx[:, j]]),
                  w[idx[:, j]] / d[np.arange(len(xte)), idx[:, j]])
    return votes.argmax(1)


def fit_predict(kind, hp, cw, xtr, ytr, xte):
    sw = compute_sample_weight("balanced", ytr) if cw else np.ones(len(ytr))
    if kind == "knn":
        return knn_predict(xtr, ytr, sw, xte, hp)
    clf = LogisticRegression(C=hp, max_iter=3000).fit(xtr, ytr, sample_weight=sw)
    return clf.predict(xte)


def per_class(y, p):
    pr, rc, f1, sup = precision_recall_fscore_support(y, p, labels=range(3), zero_division=0)
    return {"f1": f1, "r": rc, "n": sup, "f1_macro": float(f1.mean()),
            "bal_acc": float(balanced_accuracy_score(y, p))}


def build_train(idx, base, aug, y, n_sob):
    """Base + copias aumentadas solo de las flores de idx (n_sob copias en sobreabierto)."""
    xs, ys = [base[idx]], [y[idx]]
    for i in idx:
        n = n_sob if y[i] == 2 else N_AUG_BASE
        xs.append(aug[i, :n])
        ys.append(np.full(n, y[i]))
    return np.concatenate(xs), np.concatenate(ys)


def main() -> None:
    if "--selftest" in sys.argv:
        return selftest()
    torch.manual_seed(2026)
    torch.set_num_threads(8)
    EMB.mkdir(parents=True, exist_ok=True)
    man = list(csv.DictReader((OUT_J / "manifest.csv").open()))
    split = json.loads((OUT_J / "split.json").read_text())
    pool = [r for r in man if r["split"] in ("train", "val")]
    test = [r for r in man if r["split"] == "test"]
    yp = np.array([CLASSES.index(r["stage"]) for r in pool])
    yt = np.array([CLASSES.index(r["stage"]) for r in test])
    groups = np.array([r["md5"] for r in pool])
    f_base, f_aug, f_test = EMB / "cv_pool_base.npy", EMB / "cv_pool_aug.npy", EMB / "cv_test.npy"
    if not (f_base.exists() and f_aug.exists() and f_test.exists()):
        model = AutoModel.from_pretrained(MODELS["vit_s14"]).eval()
        im = lambda rs: [Image.open(CROPS / r["crop"]).convert("RGB") for r in rs]  # noqa: E731
        ip, it = im(pool), im(test)
        np.save(f_base, embed(model, ip, BASE))
        np.save(f_test, embed(model, it, BASE))
        aug = np.stack([embed(model, ip, AUG) for _ in range(MAX_AUG)], axis=1)  # (N, 32, D)
        np.save(f_aug, aug)
    base, aug, xt = np.load(f_base), np.load(f_aug), np.load(f_test)
    print("pool", Counter(yp.tolist()), "test", Counter(yt.tolist()), "aug", aug.shape, flush=True)

    # Pliegues (3 repeticiones de 5 pliegues, agrupados por md5, estratificados)
    all_folds = []
    for s in SEEDS:
        folds = list(StratifiedGroupKFold(5, shuffle=True, random_state=s).split(base, yp, groups))
        check_no_leak(folds, groups, set(split["test"]))
        all_folds.append(folds)
    print("chequeo de fuga OK en", sum(len(f) for f in all_folds), "pliegues", flush=True)

    grid = ([("knn", k) for k in KS] + [("logreg", c) for c in CS])
    results = []
    for (kind, hp), cw, n_sob in itertools.product(grid, (False, True), SOB_AUG):
        reps = []
        for folds in all_folds:
            oof = np.full(len(yp), -1)
            fold_m = []
            for tr, va in folds:
                xtr, ytr = build_train(tr, base, aug, yp, n_sob)
                oof[va] = fit_predict(kind, hp, cw, xtr, ytr, base[va])
                fold_m.append(per_class(yp[va], oof[va])["f1_macro"])
            m = per_class(yp, oof)
            m["fold_f1_std"] = float(np.std(fold_m))
            reps.append(m)
        agg = {k: np.mean([r[k] for r in reps], axis=0) for k in ("f1", "r", "f1_macro", "bal_acc")}
        sd = {k: np.std([r[k] for r in reps], axis=0) for k in ("f1", "r", "f1_macro", "bal_acc")}
        results.append({"clf": kind, "hp": hp, "class_weight": cw, "n_sob_aug": n_sob,
                        "mean": {k: np.asarray(v).tolist() for k, v in agg.items()},
                        "std_reps": {k: np.asarray(v).tolist() for k, v in sd.items()},
                        "fold_f1_std": float(np.mean([r["fold_f1_std"] for r in reps]))})
    key = lambda r: (r["mean"]["f1_macro"], r["mean"]["bal_acc"])  # noqa: E731
    results.sort(key=key, reverse=True)
    best = results[0]
    print("TOP 8 por F1 macro CV (media de 3x5 pliegues)")
    for r in results[:8]:
        print(f"{r['clf']:6} hp={r['hp']:<5} cw={int(r['class_weight'])} sob_aug={r['n_sob_aug']:<2} "
              f"f1m {r['mean']['f1_macro']:.3f}±{r['std_reps']['f1_macro']:.3f} "
              f"bal {r['mean']['bal_acc']:.3f} f1/clase {np.round(r['mean']['f1'], 2)} "
              f"rec/clase {np.round(r['mean']['r'], 2)}")

    # Bootstrap por md5 (OOF repetición 0) de la config elegida
    folds = all_folds[0]
    oof = np.full(len(yp), -1)
    for tr, va in folds:
        xtr, ytr = build_train(tr, base, aug, yp, best["n_sob_aug"])
        oof[va] = fit_predict(best["clf"], best["hp"], best["class_weight"], xtr, ytr, base[va])
    rng = np.random.default_rng(0)
    ug = np.unique(groups)
    bs = []
    for _ in range(1000):
        pick = rng.choice(ug, len(ug))
        ii = np.concatenate([np.where(groups == g)[0] for g in pick])
        bs.append(per_class(yp[ii], oof[ii]))
    ci = {"f1_macro": np.percentile([b["f1_macro"] for b in bs], [2.5, 97.5]).tolist(),
          "f1": np.percentile([b["f1"] for b in bs], [2.5, 97.5], axis=0).T.tolist(),
          "recall": np.percentile([b["r"] for b in bs], [2.5, 97.5], axis=0).T.tolist()}
    print("IC95 bootstrap (md5) config elegida:", json.dumps(ci))

    # Test: UNA evaluación de la config elegida (+ ablaciones informativas, no se eligen con test)
    def test_eval(kind, hp, cw, n_sob):
        xtr, ytr = build_train(np.arange(len(yp)), base, aug, yp, n_sob)
        p = fit_predict(kind, hp, cw, xtr, ytr, xt)
        m = per_class(yt, p)
        cm = np.zeros((3, 3), int)
        for a, b in zip(yt, p):
            cm[a, b] += 1
        return {"f1_macro": m["f1_macro"], "bal_acc": m["bal_acc"], "f1": m["f1"].tolist(),
                "recall": m["r"].tolist(), "n": m["n"].tolist(), "cm": cm.tolist()}

    test_best = test_eval(best["clf"], best["hp"], best["class_weight"], best["n_sob_aug"])
    ablations = {f"cw={int(cw)} sob_aug={n}": test_eval(best["clf"], best["hp"], cw, n)
                 for cw, n in itertools.product((False, True), SOB_AUG)}
    print("TEST (config elegida por CV):", json.dumps(test_best))
    for k, v in ablations.items():
        print("TEST ablación", k, "f1m", round(v["f1_macro"], 3), "rec_sob", round(v["recall"][2], 2))
    out = {"cv": {"folds": "5 x 3 semillas, StratifiedGroupKFold por md5, pool train+val (154 flores)",
                  "pool_n": np.bincount(yp).tolist(), "results": results, "best": best,
                  "bootstrap_ci95_best": ci},
           "test": {"best_cfg": test_best, "ablations_informative": ablations,
                    "test_n": np.bincount(yt).tolist()}}
    (OUT_J / "cv_results.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
