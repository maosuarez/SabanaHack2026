"""Evalúa el VLM sobre las 178 flores (secuencial: la cuenta tiene RPM 3 y concurrencia 1).
Reanudable. Uso: python tools/pipeline/vlm_eval.py <modelo> [v1|v2]"""
import csv, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import vlm_stage as v

ROOT = v.ROOT
model = sys.argv[1]
pv = sys.argv[2] if len(sys.argv) > 2 else "v2"
out_f = ROOT / f"data/processed/classification/vlm_results_{model}.json"
man = list(csv.DictReader((ROOT / "data/processed/classification/manifest.csv").open()))
res = json.loads(out_f.read_text(encoding="utf-8")) if out_f.exists() else {}
INTERVAL = 21.0  # RPM 3 -> una llamada cada ~20 s
last = 0.0
for r in man:
    fid = r["flower_id"]
    if fid in res and res[fid].get("ok"):
        continue
    for _ in range(6):
        wait = INTERVAL - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
        last = time.time()
        o = v.classify_crop(ROOT / "outputs/classification/crops" / r["crop"], model, prompt=v.PROMPTS[pv],
                            extra={"thinking": {"type": "disabled"}}, retries=0)
        if o["ok"] or "429" not in (o["error"] or ""):
            break
    o.update(true=r["stage"], split=r["split"], prompt=pv)
    res[fid] = o
    out_f.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    print(len(res), fid, o["ok"], flush=True)
