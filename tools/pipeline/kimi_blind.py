"""Medicion a ciegas de un modelo Kimi sobre las 178 flores anotadas (lotes de <=16, semilla 2026).
Uso: python tools/pipeline/kimi_blind.py <modelo> [timeout_s]. Reanudable. Sin etapa local ni etiqueta en el prompt."""
import csv, json, random, sys, time
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
import vlm_stage as v

ROOT = Path(__file__).resolve().parents[2]
CL = ROOT / "data/processed/classification"
model = sys.argv[1]
tmo = float(sys.argv[2]) if len(sys.argv) > 2 else 150.0
out_p = CL / f"kimi_blind_batch_{model}.json"
rows = list(csv.DictReader(open(CL / "manifest.csv", encoding="utf-8")))
loc = json.loads((CL / "local_oof_probs.json").read_text())
ids = [r["flower_id"] for r in rows]
random.Random(2026).shuffle(ids)
nb = 12
lotes = [ids[i::nb] for i in range(nb)]  # 12 lotes de 14-15
by = {r["flower_id"]: r for r in rows}
st = json.loads(out_p.read_text(encoding="utf-8")) if out_p.exists() else {"modelo": model, "lotes": {}}
for bi, lote in enumerate(lotes):
    if st["lotes"].get(str(bi), {}).get("ok"):
        continue
    for t in (tmo, tmo * 2):  # si falla (timeout), repite con timeout mayor
        items = [{"n": k + 1, "score": 0, "img": Image.open(ROOT / "outputs/classification/crops" / by[f]["crop"])} for k, f in enumerate(lote)]
        t0 = time.time()
        r = v.explain_batch(items, model=model, timeout=t, retries=2)
        rec = {"ok": r["ok"], "error": r["error"], "wall_s": round(time.time() - t0, 1), "timeout_usado": t,
               "tokens_in": r["prompt_tokens"], "tokens_out": r["completion_tokens"], "ids": lote,
               "res": {lote[n - 1]: x for n, x in (r["result"] or {}).items()}}
        st["lotes"][str(bi)] = rec
        out_p.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
        print(bi, rec["ok"], rec["error"], rec["wall_s"], rec["tokens_in"], rec["tokens_out"], len(rec["res"]), flush=True)
        if r["ok"]:
            break
