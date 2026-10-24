"""Métricas del VLM y acuerdo con el clasificador local. Uso: python tools/pipeline/vlm_analyze.py <modelo>"""
import json, sys
from math import sqrt
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
C = ["inmaduro", "optimo", "sobreabierto"]
norm = lambda s: s.replace("ó", "o")
TAU = 0.55
model = sys.argv[1]
vlm = json.loads((ROOT / f"data/processed/classification/vlm_results_{model}.json").read_text(encoding="utf-8"))
loc = json.loads((ROOT / "data/processed/classification/local_oof_probs.json").read_text())

def wil(k, n):
    if n == 0: return (None, None)
    z = 1.96; p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d; h = z*sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (round(max(0, c-h), 2), round(min(1, c+h), 2))

def prf(y, p):
    out = {}
    for i, c in enumerate(C):
        tp = sum(1 for a, b in zip(y, p) if a == i and b == i); fp = sum(1 for a, b in zip(y, p) if a != i and b == i)
        fn = sum(1 for a, b in zip(y, p) if a == i and b != i)
        pr = tp/(tp+fp) if tp+fp else 0; rc = tp/(tp+fn) if tp+fn else 0
        out[c] = dict(precision=round(pr, 2), recall=round(rc, 2), f1=round(2*pr*rc/(pr+rc), 2) if pr+rc else 0, n=sum(1 for a in y if a == i))
    out["f1_macro"] = round(np.mean([out[c]["f1"] for c in C]), 3)
    return out

rows = []
for fid, o in vlm.items():
    if not o.get("ok"): continue
    r = o["result"]; p = np.array(loc[fid]["p"])
    rows.append(dict(id=fid, split=o["split"], y=C.index(o["true"]), v=C.index(norm(r["etapa"])), duda=r.get("duda", False),
                     vc=r["confianza"], l=int(p.argmax()), lp_opt=p[1], lat=o["latency_s"], tok=(o["prompt_tokens"] or 0)+(o["completion_tokens"] or 0)))
n = len(rows); y = [r["y"] for r in rows]; pv = [r["v"] for r in rows]
rep = dict(modelo=model, n_ok=n, n_total=len(vlm), json_valido=round(n/len(vlm), 3),
           latencia_media_s=round(np.mean([r["lat"] for r in rows]), 2), tokens_total=int(sum(r["tok"] for r in rows)),
           accuracy=round(np.mean([a == b for a, b in zip(y, pv)]), 3), vlm=prf(y, pv))
cm = np.zeros((3, 3), int)
for a, b in zip(y, pv): cm[a, b] += 1
rep["matriz_vlm_filas_real"] = cm.tolist()
def apto_stats(sel, ys):
    k = sum(1 for s, a in zip(sel, ys) if s and a == 1); m = sum(sel); no = sum(1 for a in ys if a == 1)
    return dict(n_apto=m, precision_apto=round(k/m, 2) if m else None, ic95=wil(k, m), cobertura_optimos=f"{k}/{no}",
                inmaduros_colados=sum(1 for s, a in zip(sel, ys) if s and a == 0), sobreabiertos_colados=sum(1 for s, a in zip(sel, ys) if s and a == 2))
def analiza(rs, nombre):
    ys = [r["y"] for r in rs]
    loc_apto = [r["l"] == 1 and r["lp_opt"] >= TAU for r in rs]
    # regla: coinciden en óptimo (VLM sin duda) -> APTO; el resto de coincidencias en inmaduro -> NO APTO
    regla = [r["l"] == 1 and r["v"] == 1 and not r["duda"] and r["lp_opt"] >= TAU for r in rs]
    regla_sin_duda = [r["l"] == 1 and r["v"] == 1 and r["lp_opt"] >= TAU for r in rs]
    coin = [r["l"] == r["v"] for r in rs]
    d = dict(n=len(rs), solo_local=apto_stats(loc_apto, ys), regla_acuerdo_con_duda=apto_stats(regla, ys), regla_acuerdo_sin_duda=apto_stats(regla_sin_duda, ys))
    kc = sum(1 for c, r in zip(coin, rs) if c and r["l"] == r["y"]); nc = sum(coin)
    kd = sum(1 for c, r in zip(coin, rs) if not c and r["l"] == r["y"]); nd = len(rs)-nc
    d["exactitud_local_si_coinciden"] = dict(k=kc, n=nc, p=round(kc/nc, 2) if nc else None, ic95=wil(kc, nc))
    d["exactitud_local_si_discrepan"] = dict(k=kd, n=nd, p=round(kd/nd, 2) if nd else None, ic95=wil(kd, nd))
    t = {}
    for r in rs:
        key = f"local={C[r['l']]}|vlm={C[r['v']]}"; t.setdefault(key, [0, 0, 0])[r["y"]] += 1
    d["tabla_local_x_vlm_x_real[inm,opt,sob]"] = t
    d["vlm_duda_n"] = sum(r["duda"] for r in rs)
    d["no_apto_acuerdo_inmaduro"] = dict(n=sum(1 for r in rs if r["l"] == 0 and r["v"] == 0), inmaduro_real=sum(1 for r in rs if r["l"] == 0 and r["v"] == 0 and r["y"] == 0))
    return d
rep["acuerdo_pool_OOF"] = analiza([r for r in rows if r["split"] != "test"], "pool")
rep["acuerdo_test"] = analiza([r for r in rows if r["split"] == "test"], "test")
rep["vlm_test"] = prf([r["y"] for r in rows if r["split"] == "test"], [r["v"] for r in rows if r["split"] == "test"])
rep["vlm_pool"] = prf([r["y"] for r in rows if r["split"] != "test"], [r["v"] for r in rows if r["split"] != "test"])
(ROOT / f"data/processed/classification/vlm_analysis_{model}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
print(json.dumps(rep, ensure_ascii=False, indent=1, default=float))
