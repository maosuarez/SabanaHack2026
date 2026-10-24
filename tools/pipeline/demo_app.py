"""Demo web local: sube/captura una imagen -> cajas, etapa, veredicto por flor. Solo stdlib + modelos locales.

Arranque: python tools/pipeline/demo_app.py [--port 8000]  ->  http://localhost:8000
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

os.environ.setdefault("HF_HUB_OFFLINE", "1")  # sin internet: usa la caché local
import torch  # noqa: E402
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/pipeline"))
from predict import COLORS, Pipeline, annotate  # noqa: E402

MAX_SIDE = 1600
EXAMPLES = {n: ROOT / "data/raw/images" / f"{n}.jpeg" for n in ("rosa_18", "rosa_37", "rosa_61")}
EXAMPLES = {k: v for k, v in EXAMPLES.items() if v.exists()}
LABELS = {"rosa_18": "Finca (test)", "rosa_37": "Finca (test)", "rosa_61": "Finca (test)"}
LOCK = threading.Lock()
PIPE: Pipeline | None = None


def thumb(path: Path) -> bytes:
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    im.thumbnail((320, 320))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=80)
    return b.getvalue()


def analyze(img: Image.Image) -> dict:
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
    return {"imagen": "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode(),
            "resumen": {"aptas": cnt["apto"], "no_aptas": cnt["no_apto"], "zona_gris": cnt["gris"], "total": len(fl)},
            "flores": rows, "tiempo_ms": round(t["total_ms"]), "tamano": list(img.size)}


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
        elif p.startswith("/thumb/") and p[7:] in EXAMPLES:
            self._send(200, thumb(EXAMPLES[p[7:]]), "image/jpeg")
        else:
            self._send(404, b"no encontrado", "text/plain")

    def do_POST(self) -> None:
        p = urlparse(self.path).path
        try:
            if p.startswith("/analyze/") and p[9:] in EXAMPLES:
                img = Image.open(EXAMPLES[p[9:]])
            elif p == "/analyze":
                img = Image.open(io.BytesIO(self.rfile.read(int(self.headers.get("Content-Length", 0)))))
            else:
                return self._send(404, b"{}", "application/json")
            self._send(200, json.dumps(analyze(img), ensure_ascii=False).encode(), "application/json")
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
#load{display:none;align-items:center;gap:12px;padding:14px;font-weight:600;margin-bottom:12px}.spin{width:26px;height:26px;border:4px solid var(--ln);border-top-color:var(--ac);border-radius:50%;animation:s 1s linear infinite}@keyframes s{to{transform:rotate(360deg)}}
#cam{display:none}#cam video{width:100%;border-radius:10px;background:#000}.mut{color:var(--mut);font-size:15px}#err{color:#c0392b;font-weight:600}
</style></head><body>
<header><h1>Rosas: estado de apertura</h1><div class="aviso">Ayuda, decide la persona. ZONA GRIS = no cortar sin revisar.</div></header>
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
function show(d){const s=d.resumen;let h=`<div class="sum"><div class="pill p-ok">${s.aptas}<small>aptas</small></div><div class="pill p-no">${s.no_aptas}<small>no aptas</small></div><div class="pill p-gr">${s.zona_gris}<small>en zona gris</small></div></div>
<img src="${d.imagen}" alt="Imagen anotada"><p class="mut">${s.total} flores detectadas en ${(d.tiempo_ms/1000).toFixed(1)} s</p>`;
 if(d.flores.length){h+='<table><tr><th>#</th><th>Etapa</th><th>Confianza</th><th>Veredicto</th><th>Motivo</th></tr>'+d.flores.map(f=>`<tr><td>${f.n}</td><td>${f.etapa}</td><td>${(f.confianza*100).toFixed(0)}%</td><td><span class="tag t-${f.clave}">${f.veredicto}</span></td><td>${f.motivo}</td></tr>`).join('')+'</table>'}
 else h+='<p>No se detectaron flores.</p>';$('out').innerHTML=h}
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
    print(f"Listo: http://localhost:{a.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), H).serve_forever()


if __name__ == "__main__":
    main()
