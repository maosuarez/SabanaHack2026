"""Zona gris: umbral sobre P(optimo) calibrado SOLO con OOF de CV agrupada por md5 (train+val).

Config: LogReg C=10, sin class_weight, 24 copias de sobreabierto (elegida en cv_eval.py).
Reglas: pred=optimo y P(optimo)>=TAU -> apto | pred=inmaduro -> no apto |
        pred=sobreabierto, u optimo con P<TAU -> zona gris (con motivo).
Test: una sola evaluación, con el TAU ya fijado. TAU = max prec_apto OOF con cobertura OOF>=0.5. Uso: python tools/classification/gray_zone.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold

sys.path.insert(0, str(Path(__file__).parent))
from cv_eval import EMB, SEEDS, build_train, check_no_leak  # noqa: E402
from embed_train import CLASSES, OUT_J  # noqa: E402

C, N_SOB, COB_MIN = 10, 24, 0.50  # prec_apto>=0.90 OOF no se alcanza con ningún tau
GRID = np.round(np.arange(0.30, 0.96, 0.05), 2)


def decide(p, tau):
    """p: (n,3) probabilidades -> (decisión, motivo)."""
    out = []
    for q in p:
        k = int(q.argmax())
        if k == 2:
            out.append(("gris", "sobreabierto predicho (se trata como no apto)"))
        elif k == 0:
            out.append(("no_apto", "inmaduro"))
        elif q[1] >= tau:
            out.append(("apto", "optimo con confianza suficiente"))
        else:
            out.append(("gris", f"optimo con confianza baja (P={q[1]:.2f}<{tau})"))
    return out


def metrics(y, dec):
    d = np.array([x[0] for x in dec])
    apto = d == "apto"
    n_apto = int(apto.sum())
    return {"n": len(y), "n_apto": n_apto,
            "prec_apto": float((y[apto] == 1).mean()) if n_apto else None,
            "colados_sob": int((y[apto] == 2).sum()), "colados_inm": int((y[apto] == 0).sum()),
            "cobertura_opt": float(apto[y == 1].mean()) if (y == 1).any() else None,
            "opt_perdidos_a_gris": int((d[y == 1] == "gris").sum()),
            "opt_a_no_apto": int((d[y == 1] == "no_apto").sum()),
            "frac_gris": float((d == "gris").mean()),
            "sob_evitados": int((d[y == 2] != "apto").sum()), "n_sob": int((y == 2).sum()),
            "inm_evitados": int((d[y == 0] != "apto").sum()), "n_inm": int((y == 0).sum())}


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(float(c - h), 3), round(float(c + h), 3)]


def fit(idx, base, aug, y):
    x, yy = build_train(idx, base, aug, y, N_SOB)
    return LogisticRegression(C=C, max_iter=3000).fit(x, yy)


def main():
    man = list(csv.DictReader((OUT_J / "manifest.csv").open()))
    split = json.loads((OUT_J / "split.json").read_text())
    pool = [r for r in man if r["split"] in ("train", "val")]
    test = [r for r in man if r["split"] == "test"]
    yp = np.array([CLASSES.index(r["stage"]) for r in pool])
    yt = np.array([CLASSES.index(r["stage"]) for r in test])
    groups = np.array([r["md5"] for r in pool])
    base, aug, xt = (np.load(EMB / f) for f in ("cv_pool_base.npy", "cv_pool_aug.npy", "cv_test.npy"))

    oofs = []
    for s in SEEDS:
        folds = list(StratifiedGroupKFold(5, shuffle=True, random_state=s).split(base, yp, groups))
        check_no_leak(folds, groups, set(split["test"]))
        oof = np.zeros((len(yp), 3))
        for tr, va in folds:
            oof[va] = fit(tr, base, aug, yp).predict_proba(base[va])
        oofs.append(oof)

    curve = []
    for tau in GRID:
        ms = [metrics(yp, decide(o, tau)) for o in oofs]
        row = {"tau": float(tau)}
        for k in ("prec_apto", "cobertura_opt", "frac_gris"):
            v = [m[k] for m in ms if m[k] is not None]
            row[k] = float(np.mean(v)) if v else None
        for k in ("colados_sob", "colados_inm", "opt_perdidos_a_gris", "n_apto"):
            row[k] = float(np.mean([m[k] for m in ms]))
        curve.append(row)
    print("CURVA OOF (media 3 repeticiones; pool 114/34/6): tau | prec_apto | cobertura_opt | opt->gris | colados sob/inm | frac_gris")
    for r in curve:
        pa = "  -  " if r["prec_apto"] is None else f"{r['prec_apto']:.3f}"
        print(f"{r['tau']:.2f} | {pa} | {r['cobertura_opt']:.3f} | {r['opt_perdidos_a_gris']:.1f}/34 | "
              f"{r['colados_sob']:.1f}/{r['colados_inm']:.1f} | {r['frac_gris']:.3f}")
    ok = [r for r in curve if r["prec_apto"] is not None and r["cobertura_opt"] >= COB_MIN]
    tau = max(ok, key=lambda r: r["prec_apto"])["tau"]
    print(f"TAU elegido (max prec_apto OOF con cobertura_opt OOF >= {COB_MIN}): {tau}")

    clf = fit(np.arange(len(yp)), base, aug, yp)
    pt = clf.predict_proba(xt)
    dec = decide(pt, tau)
    m = metrics(yt, dec)
    d = np.array([x[0] for x in dec])
    cols = ["apto", "no_apto", "gris"]
    cm = [[int((d[yt == k] == c).sum()) for c in cols] for k in range(3)]
    m["ic95"] = {"prec_apto": wilson(int((yt[d == "apto"] == 1).sum()), m["n_apto"]),
                 "cobertura_opt": wilson(int((d[yt == 1] == "apto").sum()), int((yt == 1).sum())),
                 "frac_gris": wilson(int((d == "gris").sum()), len(yt))}
    print("TEST (una vez):", json.dumps(m))
    print("matriz filas=real(inm,opt,sob) cols=", cols, cm)
    for i, (r, x) in enumerate(zip(test, dec)):
        if x[0] == "gris" or (x[0] == "apto") != (yt[i] == 1):
            print("  ", r["crop"], CLASSES[yt[i]], x)
    (OUT_J / "gray_zone_results.json").write_text(json.dumps(
        {"config": f"logreg C={C} sin cw sob_aug={N_SOB}", "cob_min": COB_MIN, "tau": tau,
         "curve_oof": curve, "test": m, "test_cm_rows_inm_opt_sob_cols_apto_noapto_gris": cm,
         "ejemplos_salida": [{"crop": r["crop"], "real": CLASSES[yt[i]], "dec": x[0], "motivo": x[1]}
                             for i, (r, x) in enumerate(zip(test, dec))]}, indent=1))


if __name__ == "__main__":
    main()
