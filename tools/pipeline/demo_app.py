"""Demo web local: sube/captura una imagen -> cajas, etapa, veredicto por flor. Solo stdlib + modelos locales.

Arranque: python tools/pipeline/demo_app.py [--port 8000]  ->  http://localhost:8000
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import queue
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

os.environ.setdefault("HF_HUB_OFFLINE", "1")  # sin internet: usa la caché local
import torch  # noqa: E402
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/pipeline"))
from predict import COLORS, Pipeline, annotate, crop_box  # noqa: E402
import vlm_stage  # noqa: E402

MAX_SIDE = 1600
EXAMPLES = {n: ROOT / "data/raw/images" / f"{n}.jpeg" for n in ("rosa_18", "rosa_37", "rosa_61")}
EXAMPLES = {k: v for k, v in EXAMPLES.items() if v.exists()}
LABELS = {"rosa_18": "Finca (test)", "rosa_37": "Finca (test)", "rosa_61": "Finca (test)"}
EXPL_PATH = ROOT / "data/processed/pipeline/explanations_kimi.json"
LOCK = threading.Lock()
PIPE: Pipeline | None = None


def thumb(path: Path) -> bytes:
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    im.thumbnail((320, 320))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=80)
    return b.getvalue()


def load_expl(name: str | None) -> dict:
    """Explicaciones precalculadas (Kimi, solo galería). Sin JSON o sin nombre -> {}."""
    if not name:
        return {}
    try:
        d = json.loads(EXPL_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {v["n"]: v for v in d.values() if v.get("imagen") == name and v.get("ok")}


# ---- Segunda opinión de Kimi en segundo plano: una llamada por imagen, cola global (concurrencia 1) ----
JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()
QUEUE: "queue.Queue[str]" = queue.Queue()
PRECIO_USD_M = (0.95, 4.0)  # SUPUESTO sin verificar (entrada, salida por millón de tokens): solo orden de magnitud


# Kimi configurable por entorno: KIMI_MODEL (default kimi-k2.6) y KIMI_TIMEOUT_S (default 40 s por llamada;
# subirlo si el modelo es mas lento, p. ej. KIMI_TIMEOUT_S=120). La interfaz espera timeout + 5 s antes de rendirse.
KIMI_MODEL = os.environ.get("KIMI_MODEL", "kimi-k2.6")
KIMI_TIMEOUT_S = float(os.environ.get("KIMI_TIMEOUT_S", "40"))
LIMITE_UI_S = KIMI_TIMEOUT_S + 5


def _sa(e: str) -> str:
    return e.replace("ó", "o")


def aviso_kimi(etapa_local: str, k: dict | None) -> str | None:
    """Aviso SUAVE: solo informa. NUNCA cambia el veredicto local (sin zona gris ni 'con respaldo')."""
    if not k:
        return None
    if _sa(k["etapa"]) != _sa(etapa_local):
        return f"Kimi opina {k['etapa']}"
    return "Kimi coincide (con duda)" if k["duda"] else "Kimi coincide"


def kimi_view(job: dict) -> dict:
    v = {"estado": job["estado"], "fuente": job.get("fuente"), "error": job.get("error"),
         "tokens": job.get("tokens"), "latencia_s": job.get("latencia_s"), "respaldo": job.get("respaldo"), "modelo": KIMI_MODEL, "limite_s": LIMITE_UI_S,
         "en_ejecucion_s": round(time.time() - job["t_run"], 1) if job.get("t_run") and job["estado"] == "running" else 0}
    if job["estado"] == "done":
        fl, disc = [], 0
        for r in job["rows"]:
            k = job["resultado"].get(r["n"])
            if k and _sa(k["etapa"]) != _sa(r["etapa"]):
                disc += 1
            fl.append({"n": r["n"], "etapa_kimi": k["etapa"] if k else None, "duda": k["duda"] if k else None,
                       "confianza_kimi": k["confianza"] if k else None, "explicacion": k["explicacion"] if k else None,
                       "aviso": aviso_kimi(r["etapa"], k)})
        v["flores"] = fl
        v["discrepan"] = disc
    return v


def kimi_worker() -> None:
    while True:
        jid = QUEUE.get()
        with JOBS_LOCK:
            job = JOBS[jid]
            job.update(estado="running", t_run=time.time())
        try:
            r = vlm_stage.explain_batch(job["items"], model=KIMI_MODEL, timeout=KIMI_TIMEOUT_S)
        except Exception as e:  # nunca tumbar el hilo
            r = {"ok": False, "error": type(e).__name__}
        with JOBS_LOCK:
            job["tokens"] = {"entrada": r.get("prompt_tokens"), "salida": r.get("completion_tokens")}
            job["latencia_s"] = r.get("latencia_s") or r.get("latency_s")
            if r.get("ok"):
                job.update(estado="done", resultado=r["result"], fuente="Kimi (en vivo)")
            else:
                job.update(estado="error", error=r.get("error") or "falló")
            job.pop("items", None)
            job["t_fin"] = time.time()


def submit_kimi(jid: str, rows: list[dict], items: list[dict], name: str | None) -> str:
    """Registra el trabajo (o reutiliza caché por hash). Galería con precálculo coincidente: sin llamada."""
    with JOBS_LOCK:
        old = JOBS.get(jid)
        if old and not (old["estado"] == "error" and time.time() - old.get("t_fin", 0) > 60):
            return jid
        job = {"estado": "queued", "rows": rows, "items": items}
        ex = load_expl(name)
        if ex:  # texto de respaldo (generado con la etapa local conocida), solo si Kimi falla
            job["respaldo"] = {n: e["explicacion"] for n, e in ex.items() if e.get("etapa_local") == next(
                (r["etapa"] for r in rows if r["n"] == n), None) and e.get("coherente") is True}
        if not rows:
            job.update(estado="done", fuente="sin flores", items=None, resultado={})
        JOBS[jid] = job
        if job["estado"] == "queued":
            QUEUE.put(jid)
    return jid


def analyze(img: Image.Image, name: str | None = None, raw: bytes = b"") -> dict:
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    with LOCK:
        fl, t = PIPE.run(img)
    b = io.BytesIO()
    annotate(img, fl).save(b, "JPEG", quality=88)
    cnt = {k: sum(f["veredicto_clave"] == k for f in fl) for k in COLORS}
    rows = [{"n": f["id"] + 1, "etapa": f["etapa"], "confianza": f["confianza"], "veredicto": f["veredicto"],
             "clave": f["veredicto_clave"], "motivo": f["motivo"], "probabilidades": f["probabilidades"],
             "score_detector": f["score_detector"]} for f in fl]
    jid = hashlib.sha1(raw).hexdigest()[:16]
    items = [{"n": f["id"] + 1, "score": f["score_detector"],
              "img": crop_box(img, f["caja_norm"])} for f in fl]
    submit_kimi(jid, rows, items, name)
    return {"imagen": "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode(),
            "resumen": {"aptas": cnt["apto"], "no_aptas": cnt["no_apto"], "zona_gris": cnt["gris"], "total": len(fl)},
            "flores": rows, "es_ejemplo": bool(name), "tiempo_ms": round(t["total_ms"]), "tamano": list(img.size),
            "kimi_id": jid, "kimi_disponible": bool(vlm_stage.api_key())}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silencioso
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        p = urlparse(self.path).path
        if p == "/":
            self._send(200, PAGE.encode(), "text/html; charset=utf-8")
        elif p == "/examples":
            self._send(200, json.dumps([{"id": k, "grupo": LABELS.get(k, "Externa")} for k in EXAMPLES]).encode(),
                       "application/json")
        elif p.startswith("/kimi/"):
            with JOBS_LOCK:
                job = JOBS.get(p[6:])
                v = kimi_view(job) if job else {"estado": "desconocido"}
            self._send(200, json.dumps(v, ensure_ascii=False).encode(), "application/json")
        elif p.startswith("/thumb/") and p[7:] in EXAMPLES:
            self._send(200, thumb(EXAMPLES[p[7:]]), "image/jpeg")
        else:
            self._send(404, b"no encontrado", "text/plain")

    def do_POST(self) -> None:
        p = urlparse(self.path).path
        try:
            if p.startswith("/analyze/") and p[9:] in EXAMPLES:
                name = p[9:]
                raw = EXAMPLES[name].read_bytes()
                img = Image.open(io.BytesIO(raw))
            elif p == "/analyze":
                name = None
                raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                img = Image.open(io.BytesIO(raw))
            else:
                return self._send(404, b"{}", "application/json")
            self._send(200, json.dumps(analyze(img, name, raw), ensure_ascii=False).encode(), "application/json")
        except Exception as e:  # imagen inválida, etc.
            self._send(400, json.dumps({"error": f"No se pudo procesar la imagen: {e}"}).encode(), "application/json")


PAGE = r"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rosas: estado de apertura</title><style>
:root{--bg:#f6f4f0;--card:#fff;--ink:#1d2327;--mut:#5d6870;--ln:#dcd8d0;--ok:#1e9e3c;--no:#e6501e;--gr:#f0be00;--ac:#8e2a4a}
@media(prefers-color-scheme:dark){:root{--bg:#161a1d;--card:#20262a;--ink:#eef1f3;--mut:#a3adb4;--ln:#35404a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:18px/1.45 system-ui,Segoe UI,Arial,sans-serif}
header{padding:18px 28px;border-bottom:1px solid var(--ln);display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
h1{margin:0;font-size:26px}h2{font-size:20px;margin:0 0 10px}.aviso{background:#fff4cc;color:#3b3000;padding:8px 14px;border-radius:8px;font-weight:600;font-size:16px}
main{max-width:1500px;margin:0 auto;padding:20px 28px;display:grid;grid-template-columns:340px 1fr;gap:24px}
@media(max-width:900px){main{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--ln);border-radius:12px;padding:16px}
button,.btn{font:inherit;font-weight:600;background:var(--ac);color:#fff;border:0;border-radius:8px;padding:12px 18px;cursor:pointer;display:block;width:100%;margin-bottom:10px;text-align:center}
button.sec,.btn.sec{background:transparent;color:var(--ac);border:2px solid var(--ac)}
.gal{display:grid;grid-template-columns:1fr 1fr;gap:8px}.gal figure{margin:0;cursor:pointer}.gal img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:8px;border:2px solid transparent;display:block}
.gal figure:hover img{border-color:var(--ac)}.gal figcaption{font-size:13px;color:var(--mut);text-align:center}
.sum{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:14px}.pill{flex:1;min-width:150px;border-radius:10px;padding:12px 16px;color:#fff;font-weight:700;font-size:22px}
.pill small{display:block;font-weight:500;font-size:14px;opacity:.95}.p-ok{background:var(--ok)}.p-no{background:var(--no)}.p-gr{background:var(--gr);color:#222}
#out img{width:100%;border-radius:10px;display:block}table{width:100%;border-collapse:collapse;margin-top:14px;font-size:17px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--ln)}th{color:var(--mut);font-weight:600}
.tag{display:inline-block;padding:2px 10px;border-radius:12px;font-weight:700;color:#fff;font-size:15px}.t-apto{background:var(--ok)}.t-no_apto{background:var(--no)}.t-gris{background:var(--gr);color:#222}
#load{display:none;align-items:center;gap:12px;padding:14px;font-weight:600;margin-bottom:12px}.spin.s2{display:inline-block;width:16px;height:16px;border-width:3px;vertical-align:middle}.spin{width:26px;height:26px;border:4px solid var(--ln);border-top-color:var(--ac);border-radius:50%;animation:s 1s linear infinite}@keyframes s{to{transform:rotate(360deg)}}
#cam{display:none}#cam video{width:100%;border-radius:10px;background:#000}.mut{color:var(--mut);font-size:15px}.aviso-k{font-weight:600;color:var(--mut)}.aviso-k.dis{color:#8a6500}#err{color:#c0392b;font-weight:600}
</style></head><body>
<header><h1>Rosas: estado de apertura</h1><div class="aviso">Ayuda, decide la persona. ZONA GRIS = no cortar sin revisar.<br><small>Los recortes se envían a un servicio externo (Moonshot) para la segunda opinión.</small></div></header>
<main><aside>
<div class="card"><h2>1. Elegir imagen</h2>
<label class="btn">Subir imagen<input id="file" type="file" accept="image/*" hidden></label>
<button class="sec" id="btnCam">Tomar foto (webcam)</button>
<div id="cam"><video id="vid" autoplay playsinline muted></video><button id="snap" style="margin-top:10px">Capturar y analizar</button></div>
<p id="err"></p></div>
<div class="card" style="margin-top:16px"><h2>Ejemplos</h2><div class="gal" id="gal"></div></div>
</aside><section>
<div class="card" id="load"><div class="spin"></div>Analizando...</div>
<div class="card" id="out"><p class="mut">Elige una imagen, toma una foto o pulsa un ejemplo.</p></div>
</section></main>
<script>
const $=id=>document.getElementById(id);let stream=null;
function stopCam(){if(stream){stream.getTracks().forEach(t=>t.stop());stream=null}$('cam').style.display='none'}
async function run(p,body){$('err').textContent='';$('load').style.display='flex';$('out').style.opacity=.4;
 try{const r=await fetch(p,{method:'POST',body});const d=await r.json();if(d.error)throw new Error(d.error);show(d)}
 catch(e){$('err').textContent=e.message}finally{$('load').style.display='none';$('out').style.opacity=1}}
let CUR=null,KV=null,TOK=0;
function avisoKimi(k){if(!k||!k.aviso)return '—';const dis=k.aviso.startsWith('Kimi opina');
 return `<span class="aviso-k${dis?' dis':''}">${k.aviso}${k.duda&&dis?' (con duda)':''}</span>`}
function kimiEstado(){if(!CUR.kimi_disponible)return '<p class="mut">Sin segunda opinión (Kimi no respondió: sin clave).</p>';
 if(!KV||KV.estado==='queued')return '<p class="mut"><span class="spin s2"></span> Kimi en cola…</p>';
 if(KV.estado==='running')return `<p class="mut"><span class="spin s2"></span> Kimi analizando… (${KV.en_ejecucion_s|0} s)</p>`;
 if(KV.estado==='done'){const t=KV.tokens&&KV.tokens.entrada?` · ${KV.tokens.entrada}+${KV.tokens.salida} tokens`:'';return `<p class="mut">Segunda opinión independiente (Kimi): ${KV.latencia_s?KV.latencia_s+' s':''}${t} · discrepan en etapa: ${KV.discrepan} de ${KV.flores.length}</p>`}
 return '<p class="mut"><b>sin segunda opinión (Kimi no respondió)</b>. El resultado local sigue siendo válido.</p>'}
function renderTable(){const d=CUR,km={};if(KV&&KV.flores)KV.flores.forEach(x=>km[x.n]=x);const done=KV&&KV.estado==='done',err=KV&&KV.estado==='error';
 return `<div id="kst">${kimiEstado()}</div><table><tr><th>#</th><th>Etapa local</th><th>Confianza</th><th>Veredicto local</th><th>Motivo</th><th>Aviso de Kimi (no cambia el veredicto)</th><th>Explicación (Kimi)</th></tr>`+
 d.flores.map(f=>{const k=km[f.n];let ex='…';
  if(done)ex=k&&k.explicacion?k.explicacion:'flor no enviada a Kimi';
  else if(err)ex=(KV.respaldo&&KV.respaldo[f.n])?KV.respaldo[f.n]+' <i>(generada previamente, con la etapa local conocida; no es segunda opinión)</i>':'sin segunda opinión';
 return `<tr><td>${f.n}</td><td>${f.etapa}</td><td>${(f.confianza*100).toFixed(0)}%</td><td><span class="tag t-${f.clave}">${f.veredicto}</span></td><td>${f.motivo}</td><td>${done?avisoKimi(k):'<span class="mut">—</span>'}</td><td class="mut">${ex}</td></tr>`}).join('')+'</table>'}
function show(d){CUR=d;KV=null;const s=d.resumen;let h=`<div class="sum"><div class="pill p-ok">${s.aptas}<small>aptas</small></div><div class="pill p-no">${s.no_aptas}<small>no aptas</small></div><div class="pill p-gr">${s.zona_gris}<small>en zona gris</small></div></div>
<img src="${d.imagen}" alt="Imagen anotada"><p class="mut">${s.total} flores detectadas en ${(d.tiempo_ms/1000).toFixed(1)} s (clasificador local)</p>`;
 if(d.flores.length){h+='<div id="tbl"></div><p class="mut">Los recortes se envían a un servicio externo (Moonshot) para la segunda opinión. Kimi: IA, no verificada por experto; describe, no decide. Clasifica sin ver la etapa local y su opinión es solo un aviso: el veredicto lo fija el clasificador local.</p>'}
 else h+='<p>No se detectaron flores.</p>';$('out').innerHTML=h;if(d.flores.length){$('tbl').innerHTML=renderTable();poll(++TOK,Date.now(),0)}}
async function poll(tok,t0,runMs){if(tok!==TOK||!CUR.kimi_disponible)return;let v;
 try{v=await (await fetch('/kimi/'+CUR.kimi_id)).json()}catch(e){v={estado:'error'}}
 if(tok!==TOK)return;KV=v;
 if(v.estado==='running'&&v.en_ejecucion_s>(v.limite_s||45))KV={estado:'error'};
 if(Date.now()-t0>(((KV&&KV.limite_s)||45)*2+240)*1000&&KV.estado!=='done')KV={estado:'error'};
 $('tbl').innerHTML=renderTable();
 if(KV.estado==='queued'||KV.estado==='running')setTimeout(()=>poll(tok,t0,0),1500)}
$('file').onchange=e=>{const f=e.target.files[0];if(f)run('/analyze',f);e.target.value=''};
$('btnCam').onclick=async()=>{try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}});$('vid').srcObject=stream;$('cam').style.display='block'}catch(e){$('err').textContent='No se pudo abrir la camara: '+e.message}};
$('snap').onclick=()=>{const v=$('vid'),c=document.createElement('canvas');c.width=v.videoWidth;c.height=v.videoHeight;c.getContext('2d').drawImage(v,0,0);stopCam();c.toBlob(b=>run('/analyze',b),'image/jpeg',.92)};
fetch('/examples').then(r=>r.json()).then(l=>{$('gal').innerHTML=l.map(e=>`<figure data-id="${e.id}"><img src="/thumb/${e.id}" alt="${e.id}"><figcaption>${e.id} - ${e.grupo}</figcaption></figure>`).join('');
 document.querySelectorAll('#gal figure').forEach(f=>f.onclick=()=>{stopCam();run('/analyze/'+f.dataset.id,'')})});
</script></body></html>"""


def main() -> None:
    global PIPE
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()
    torch.set_num_threads(4)
    print("Cargando modelos...", flush=True)
    PIPE = Pipeline()
    threading.Thread(target=kimi_worker, daemon=True).start()
    print(f"Listo: http://localhost:{a.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), H).serve_forever()


if __name__ == "__main__":
    main()
