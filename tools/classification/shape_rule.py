"""Prueba descriptiva de forma (sin entrenar): razon ancho/alto y ensanchamiento arriba/abajo.

Criterio usuario SOBREABIERTO: ancho >= alto y forma de trapecio (arriba mas ancha que abajo).
Umbrales elegidos solo con train+val (CV agrupada por md5). Test solo con --test (una vez).
Uso: python tools/classification/shape_rule.py [--test]
"""
from __future__ import annotations
import csv, colorsys, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/processed/classification"
CROPS = ROOT / "outputs/classification/crops"
IMGS = ROOT / "data/raw/images"
M = 0.10
CL = ("inmaduro", "optimo", "sobreabierto")


def segment(path):
    a = np.asarray(Image.open(path).convert("RGB").resize((96, 96)) if False else Image.open(path).convert("RGB"), float) / 255
    mx, mn = a.max(2), a.min(2)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # rojo/granate: R domina sobre G y B, saturado, no muy oscuro
    m = (r > g * 1.12) & (r > b * 0.95) & (s > 0.15) & (mx > 0.08)
    m = ndi.binary_opening(m, iterations=1)
    lab, n = ndi.label(m)
    if n == 0:
        return None
    big = np.argmax(ndi.sum(m, lab, range(1, n + 1))) + 1
    m = ndi.binary_fill_holes(lab == big)
    if m.sum() < 0.04 * m.size:
        return None
    return m


def feats(path):
    m = segment(path)
    if m is None:
        return None
    ys, xs = np.where(m)
    y0, y1 = ys.min(), ys.max() + 1
    h = y1 - y0
    if h < 6:
        return None
    wid = m.sum(1)[y0:y1].astype(float)
    top, bot = wid[: h // 2].mean(), wid[h - h // 2:].mean()
    return dict(ratio_mask=(xs.max() + 1 - xs.min()) / h, ens=top / max(bot, 1e-6))


def load():
    man = {r["flower_id"]: r for r in csv.DictReader((OUT / "manifest.csv").open())}
    lab = {r["md5"]: r["file"] for r in csv.DictReader((ROOT / "data/raw/labels_imagen.csv").open())}
    cnt, rows = {}, []
    for r in csv.DictReader((ROOT / "data/annotations/flowers.csv").open()):
        if r["annotatable"] != "1" or r["md5"] not in {v["md5"] for v in man.values()}:
            continue
        cnt[r["md5"]] = cnt.get(r["md5"], 0) + 1
        fid = f"{r['md5'][:8]}_{cnt[r['md5']]:02d}"
        if fid not in man:
            continue
        W, H = Image.open(IMGS / lab[r["md5"]]).size
        d = dict(md5=r["md5"], fid=fid, stage=man[fid]["stage"], split=man[fid]["split"],
                 ratio_box=float(r["w"]) * W / (float(r["h"]) * H))
        f = feats(CROPS / man[fid]["crop"])
        d.update(f or dict(ratio_mask=np.nan, ens=np.nan))
        rows.append(d)
    return rows


def stats(rows, key):
    out = {}
    for c in CL:
        v = np.array([r[key] for r in rows if r["stage"] == c], float)
        v = v[~np.isnan(v)]
        out[c] = dict(n=len(v), media=round(float(v.mean()), 3), mediana=round(float(np.median(v)), 3),
                      min=round(float(v.min()), 3), max=round(float(v.max()), 3)) if len(v) else dict(n=0)
    s = [(r[key], r["stage"]) for r in rows if r["stage"] in ("optimo", "sobreabierto") and not np.isnan(r[key])]
    y = [c == "sobreabierto" for _, c in s]
    out["AUC_sob_vs_optimo"] = round(roc_auc_score(y, [v for v, _ in s]), 3) if len(set(y)) == 2 else None
    s = [(r[key], r["stage"]) for r in rows if not np.isnan(r[key])]
    y = [c == "sobreabierto" for _, c in s]
    out["AUC_sob_vs_resto"] = round(roc_auc_score(y, [v for v, _ in s]), 3) if len(set(y)) == 2 else None
    return out


def rule(r, x, y, kr):
    return (r[kr] >= x) & (r["ens"] >= y)


def fit(tr, kr):
    best = (-1, 1.0, 1.0)
    for x in np.arange(0.8, 1.5, 0.05):
        for y in np.arange(0.9, 1.6, 0.05):
            p = [bool(rule(r, x, y, kr)) for r in tr]
            f = f1_score([r["stage"] == "sobreabierto" for r in tr], p, zero_division=0)
            if f > best[0] + 1e-9:
                best = (f, x, y)
    return best


def cv(rows, kr, seeds=(0, 1, 2)):
    rows = [r for r in rows if not np.isnan(r["ens"])]
    g = np.array([r["md5"] for r in rows]); y = np.array([r["stage"] for r in rows])
    f1s, allp = [], []
    for s in seeds:
        pred = np.zeros(len(rows), bool)
        for tr, va in StratifiedGroupKFold(5, shuffle=True, random_state=s).split(rows, y, g):
            assert not set(g[tr]) & set(g[va])
            _, x, yy = fit([rows[i] for i in tr], kr)
            for i in va:
                pred[i] = bool(rule(rows[i], x, yy, kr))
        t = y == "sobreabierto"
        f1s.append(f1_score(t, pred, zero_division=0)); allp.append(pred)
    # IC95 bootstrap por md5 sobre prediccion de la semilla 0
    rng = np.random.default_rng(0); ug = np.unique(g); bs = []
    t = y == "sobreabierto"
    for _ in range(1000):
        ch = rng.choice(ug, len(ug)); idx = np.concatenate([np.where(g == k)[0] for k in ch])
        bs.append(f1_score(t[idx], allp[0][idx], zero_division=0))
    return dict(f1_cv_por_semilla=[round(f, 3) for f in f1s], f1_media=round(float(np.mean(f1s)), 3),
                ic95_bootstrap=[round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)],
                n_sob=int(t.sum()), tp_s0=int((allp[0] & t).sum()), fp_s0=int((allp[0] & ~t).sum()), n=len(rows))


def main():
    rows = load()
    pool = [r for r in rows if r["split"] != "test"]
    res = dict(n_pool=len(pool), segmentacion_fallida_pool=sum(np.isnan(r["ens"]) for r in pool),
               segmentacion_fallida_por_clase={c: int(sum(np.isnan(r["ens"]) for r in pool if r["stage"] == c)) for c in CL})
    for k in ("ratio_box", "ratio_mask", "ens"):
        res["stats_" + k] = stats(pool, k)
    for kr in ("ratio_box", "ratio_mask"):
        res["cv_regla_" + kr] = cv(pool, kr)
        res["umbrales_pool_" + kr] = dict(zip(("f1", "x_ratio", "y_ens"), map(lambda v: round(float(v), 3), fit([r for r in pool if not np.isnan(r["ens"])], kr))))
    solo = [dict(r, ens=9.0) for r in pool]  # sin segmentacion: ens neutro, solo proporcion de la caja
    res["cv_regla_solo_ratio_box_154"] = cv(solo, "ratio_box")
    res["umbral_solo_ratio_box"] = round(float(fit(solo, "ratio_box")[1]), 3)
    if "--test" in sys.argv:
        kr = "ratio_box"; _, x, y = fit([r for r in pool if not np.isnan(r["ens"])], kr)
        te = [r for r in rows if r["split"] == "test" and not np.isnan(r["ens"])]
        res["test"] = dict(regla=f"{kr}>={x:.2f} & ens>={y:.2f}", n=len(te), filas=[
            dict(fid=r["fid"], stage=r["stage"], ratio=round(r[kr], 2), ens=round(r["ens"], 2), pred_sob=bool(rule(r, x, y, kr))) for r in te],
            nota="sobreabierto n=3 (<5): NO concluyente")
    (OUT / "shape_rule_results.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=int))
    print(json.dumps(res, indent=1, ensure_ascii=False, default=int))


if __name__ == "__main__":
    main()
