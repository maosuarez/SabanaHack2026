"""Metricas de kimi_blind_batch_<modelo>.json. Uso: python tools/pipeline/kimi_blind_analyze.py <modelo>"""
import csv, json, sys
from math import sqrt
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; CL = ROOT / "data/processed/classification"
C = ["inmaduro", "optimo", "sobreabierto"]; sa = lambda s: s.replace("ó", "o")
m = sys.argv[1]
st = json.loads((CL / f"kimi_blind_batch_{m}.json").read_text(encoding="utf-8"))
true = {r["flower_id"]: r["stage"] for r in csv.DictReader(open(CL / "manifest.csv", encoding="utf-8"))}
loc = json.loads((CL / "local_oof_probs.json").read_text())
K = {}
for b in st["lotes"].values():
    for i, x in b["res"].items(): K[i] = x
ids = [i for i in true if i in K]
L = {i: C[max(range(3), key=lambda j: loc[i]["p"][j])] for i in ids}
def wil(k, n):
    if not n: return (0, 0)
    z = 1.96; p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)
def rep(name, pred):
    ok = sum(pred[i] == true[i] for i in ids); lo, hi = wil(ok, len(ids))
    print(f"{name}: exactitud {ok/len(ids):.2f} [{lo:.2f}-{hi:.2f}] n={len(ids)}")
    for c in C:
        tp = sum(pred[i] == c and true[i] == c for i in ids); pp = sum(pred[i] == c for i in ids); n = sum(true[i] == c for i in ids)
        P = tp / pp if pp else 0; R = tp / n if n else 0; F = 2 * P * R / (P + R) if P + R else 0
        print(f"  {c} n={n}: P {P:.2f} R {R:.2f} F1 {F:.2f}")
    print("  matriz (filas verdad, cols pred):", [[sum(true[i] == a and pred[i] == b for i in ids) for b in C] for a in C])
kp = {i: sa(K[i]["etapa"]) for i in ids}
rep("Kimi " + m, kp); rep("local", L)
a = [i for i in ids if kp[i] == L[i]]; d = [i for i in ids if kp[i] != L[i]]
print(f"coincide n={len(a)}: local acierta {sum(L[i]==true[i] for i in a)/max(1,len(a)):.2f}; discrepa n={len(d)}: local {sum(L[i]==true[i] for i in d)/max(1,len(d)):.2f}, Kimi {sum(kp[i]==true[i] for i in d)/max(1,len(d)):.2f}")
err = [i for i in ids if L[i] != true[i]]; fa = [i for i in ids if L[i] == true[i]]
print(f"discrepancia detecta {sum(i in d for i in err)}/{len(err)} errores locales, falsas alarmas {sum(i in d for i in fa)}/{len(fa)}")
dd = [i for i in ids if kp[i] != L[i] or K[i]["duda"]]
print(f"discrepa o duda: {sum(i in dd for i in err)}/{len(err)}, falsas {sum(i in dd for i in fa)}/{len(fa)}; duda total {sum(K[i]['duda'] for i in ids)}")
ap = [i for i in ids if L[i] == "optimo" and loc[i]["p"][1] >= 0.55]
def prec(S): return f"{sum(true[i]=='optimo' for i in S)}/{len(S)}"
res = [i for i in ap if kp[i] == "optimo" and not K[i]["duda"]]
print(f"APTO local {prec(ap)}; con Kimi coincide sin duda {prec(res)}; aviso opina otra: {sum(kp[i]!='optimo' for i in ap)} de {len(ap)}, de ellas optimo real {sum(kp[i]!='optimo' and true[i]=='optimo' for i in ap)}")
bs = [b for b in st["lotes"].values()]
print("lotes ok", sum(b["ok"] for b in bs), "/", len(bs), "wall_s por lote", [b["wall_s"] for b in bs], "timeouts usados", [b["timeout_usado"] for b in bs if b["timeout_usado"] != bs[0]["timeout_usado"]])
ti = sum(b["tokens_in"] or 0 for b in bs); to = sum(b["tokens_out"] or 0 for b in bs)
print("tokens in/out", ti, to, "errores", [b["error"] for b in bs if b["error"]])
print("kimi bien/local mal", sum(kp[i]==true[i] and L[i]!=true[i] for i in ids), " local bien/kimi mal", sum(L[i]==true[i] and kp[i]!=true[i] for i in ids))
