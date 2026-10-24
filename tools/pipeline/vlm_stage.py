"""Etapa de apertura con un VLM (API compatible con OpenAI chat completions).

Proveedor intercambiable: base_url, modelo y clave (KIMI_API_KEY en .env o argumentos).
Nunca imprime ni registra la clave.
"""
from __future__ import annotations

import base64
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_URL = "https://api.moonshot.ai/v1"
STAGES = ("inmaduro", "óptimo", "sobreabierto")

PROMPT_V1 = (
    "Eres un asistente de capacitación para cortadores de rosa de exportación, variedad Freedom (rosa roja). "
    "La imagen es el recorte de UNA flor, tomada desde abajo y a contraluz en el invernadero. "
    "Clasifica su etapa de apertura con esta ficha técnica:\n"
    "- inmaduro (cerrado): botón floral pequeño, rojo más oscuro, sépalos pegados a los pétalos. No cortar.\n"
    "- óptimo: el caracol (espiral de pétalos) está definido y deja ver el centro; rojo vivo e intenso; "
    "forma de copa; los sépalos ya se separan del botón. Cortar.\n"
    "- sobreabierto: los pétalos se separan y se pierde la forma de copa; ya pasó su punto.\n"
    "Ningún rasgo decide por sí solo: léelos en conjunto. Si la imagen es pequeña, borrosa u ocluida, baja la confianza.\n"
    'Responde SOLO con JSON, sin texto extra: {"etapa": "inmaduro|óptimo|sobreabierto", '
    '"confianza": número entre 0 y 1, "rasgos": ["rasgo observado", ...], "motivo": "una o dos frases"}'
)


# PROMPT_V2: estructurado por rol, tarea, etapas, reglas y formato (criterio del usuario, variedad Freedom).
PROMPT_V2 = """ROL
Eres un asistente que ayuda a cortadores novatos de rosa de exportación, variedad Freedom (rosa roja). Analizas UNA rosa recortada (vista desde abajo, a contraluz, en el invernadero) y decides su etapa de apertura.

TAREA
Elige exactamente una etapa y justifícala con rasgos visibles en la imagen. Primero describe los rasgos que observas y luego decide.

ETAPAS
inmaduro (cerrado): la cabeza se ve más pequeña, el rojo es más oscuro, los sépalos están pegados a los pétalos y la forma es alargada (más alta que ancha). Decisión: no cortar. Es el error más común.
óptimo (PUNTO DE CORTE, el único que se corta): el caracol (espiral de pétalos internos) está definido y deja ver el centro; el rojo es vivo e intenso; la forma es de copa, aproximadamente tan ancha como alta; los pétalos externos empiezan a separarse pero la copa se mantiene. Decisión: cortar.
sobreabierto (ya pasó su punto): los pétalos están separados y se pierde la forma de copa; la flor se ve más ancha que alta, abierta y ensanchada hacia arriba (forma de paralelogramo o trapecio con la parte superior más ancha que la inferior). Decisión: no cortar.

REGLAS
- Ningún rasgo decide por sí solo; léelos en conjunto.
- La flor sigue abriendo en poscosecha: decide pensando en cómo se verá varios días después.
- Ante la duda entre óptimo y sobreabierto, o si el recorte está borroso, cortado u ocluido, responde duda=true y baja la confianza. Nunca inventes rasgos que no ves.
- La forma depende del ángulo de la cámara: no la uses sola.

FORMATO
Responde solo con JSON estricto, sin texto fuera del JSON:
{"etapa": "inmaduro|óptimo|sobreabierto", "duda": true|false, "confianza": 0-1, "rasgos": {"sepalos": "pegados|separados|no visible", "caracol": "definido|poco definido|no visible", "forma": "alargada|copa|ensanchada", "tono": "oscuro|vivo|apagado"}, "motivo": "1-2 frases con el razonamiento breve"}"""
PROMPT = PROMPT_V2
PROMPTS = {"v1": PROMPT_V1, "v2": PROMPT_V2}


def load_env_key(name: str = "KIMI_API_KEY", env_path: Path = ROOT / ".env") -> str | None:
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            if k.strip() == name:
                return v.strip().strip('"').strip("'").strip()
    return None


def parse_stage_json(text: str) -> dict | None:
    """Extrae y normaliza el JSON aunque venga con cercas de código o texto alrededor."""
    if not text:
        return None
    text = re.sub(r"```(?:json)?", "", text)
    obj = None
    for m in re.finditer(r"\{.*\}", text, re.S):
        try:
            obj = json.loads(m.group(0))
            break
        except json.JSONDecodeError:
            continue
    if obj is None:
        s, e = text.find("{"), text.rfind("}")
        if s >= 0 and e > s:
            try:
                obj = json.loads(text[s : e + 1])
            except json.JSONDecodeError:
                return None
    if not isinstance(obj, dict):
        return None
    et = str(obj.get("etapa", "")).strip().lower()
    et = et.replace("ó", "o")
    mapa = {"inmaduro": "inmaduro", "optimo": "óptimo", "sobreabierto": "sobreabierto"}
    if et not in mapa:
        return None
    try:
        conf = max(0.0, min(1.0, float(obj.get("confianza", 0))))
    except (TypeError, ValueError):
        conf = 0.0
    rasgos = obj.get("rasgos", [])
    if not isinstance(rasgos, (list, dict)):
        rasgos = [str(rasgos)]
    duda = obj.get("duda", False)
    duda = duda if isinstance(duda, bool) else str(duda).lower() == "true"
    return {"etapa": mapa[et], "duda": duda, "confianza": conf, "rasgos": rasgos,
            "motivo": str(obj.get("motivo", ""))}


def _mime(path: Path) -> str:
    return "image/png" if path.suffix.lower() == ".png" else "image/jpeg"


def classify_crop(path: str | Path, model: str, api_key: str | None = None,
                  base_url: str = DEFAULT_BASE_URL, timeout: float = 60.0, retries: int = 2,
                  extra: dict | None = None, prompt: str = PROMPT_V2, parser=None,
                  backoff: float = 1.5) -> dict:
    """Devuelve {ok, result, latency_s, prompt_tokens, completion_tokens, error, raw}."""
    path = Path(path)
    key = api_key or load_env_key()
    if not key:
        return {"ok": False, "error": "sin clave", "result": None}
    b64 = base64.b64encode(path.read_bytes()).decode()
    body = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:{_mime(path)};base64,{b64}"}},
            {"type": "text", "text": prompt},
        ]}],
    }
    body.update(extra or {})
    out: dict = {"ok": False, "result": None, "error": None, "latency_s": None,
                 "prompt_tokens": None, "completion_tokens": None, "raw": None, "attempts": 0}
    for attempt in range(retries + 1):
        out["attempts"] = attempt + 1
        req = urllib.request.Request(
            base_url.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read())
            out["latency_s"] = round(time.time() - t0, 2)
            usage = data.get("usage", {})
            out["prompt_tokens"] = usage.get("prompt_tokens")
            out["completion_tokens"] = usage.get("completion_tokens")
            msg = data["choices"][0]["message"]
            out["raw"] = msg.get("content") or ""
            out["result"] = (parser or parse_stage_json)(out["raw"])
            out["ok"] = out["result"] is not None
            out["error"] = None if out["ok"] else "JSON inválido"
            if out["ok"]:
                return out
        except urllib.error.HTTPError as e:
            out["latency_s"] = round(time.time() - t0, 2)
            detail = e.read().decode("utf-8", "ignore")[:300]
            out["error"] = f"HTTP {e.code}: {detail}"
            if e.code not in (429, 500, 502, 503, 504):
                return out
        except Exception as e:  # red, tiempo límite
            out["latency_s"] = round(time.time() - t0, 2)
            out["error"] = f"{type(e).__name__}: {e}"[:300]
        time.sleep(backoff * (attempt + 1))
    return out


# ---- Modo EXPLICAR: Kimi describe, NO decide. La etapa la fija el clasificador local. ----
NOMBRE_ETAPA = {"inmaduro": "inmaduro (no cortar)", "óptimo": "óptimo (punto de corte)",
                "optimo": "óptimo (punto de corte)", "sobreabierto": "sobreabierto (no cortar)"}

PROMPT_EXPLICAR = """ROL
Eres un asistente que explica a cortadores novatos de rosa de exportación, variedad Freedom (rosa roja), por qué una rosa recibió cierta etapa de apertura. Describes, no decides: la etapa ya la fijó un clasificador local y NO debes cambiarla.

ENTRADA
La imagen es el recorte de UNA flor (vista desde abajo, a contraluz). Etapa asignada por el clasificador local: {etapa} (probabilidad {prob}%).

FICHA
inmaduro (cerrado): botón floral más pequeño y alargado (más alto que ancho), rojo más oscuro, sépalos pegados a los pétalos. No cortar.
óptimo (PUNTO DE CORTE, el único que se corta): el caracol (espiral de pétalos internos) está definido y deja ver el centro; rojo vivo e intenso; forma de copa; los sépalos ya se separan. Cortar.
sobreabierto: pétalos separados, se pierde la copa, flor más ancha que alta y ensanchada hacia arriba. No cortar.

TAREA
Explica en 2 o 3 frases, en español sencillo, qué rasgos visibles respaldan la etapa dada. Cita más de un rasgo (botón floral, pétalos, sépalos, caracol, copa, tono). No uses números de punto ni ángulos. No inventes rasgos que no ves. Si lo que ves NO respalda la etapa dada, pon coherente=false y di brevemente qué ves.

FORMATO
Solo JSON estricto: {{"explicacion": "2-3 frases", "rasgos": {{"sepalos": "pegados|separados|no visible", "caracol": "definido|poco definido|no visible", "forma": "alargada|copa|ensanchada", "tono": "oscuro|vivo|apagado"}}, "coherente": true|false}}"""

CABECERA_EXPLICACION = "Describe, no decide: "


def parse_explain_json(text: str) -> dict | None:
    if not text:
        return None
    text = re.sub(r"```(?:json)?", "", text)
    s, e = text.find("{"), text.rfind("}")
    if s < 0 or e <= s:
        return None
    try:
        obj = json.loads(text[s : e + 1])
    except json.JSONDecodeError:
        return None
    exp = str(obj.get("explicacion", "")).strip()
    if not isinstance(obj, dict) or not exp:
        return None
    coh = obj.get("coherente", True)
    coh = coh if isinstance(coh, bool) else str(coh).lower() == "true"
    rasgos = obj.get("rasgos", {})
    return {"explicacion": exp, "rasgos": rasgos if isinstance(rasgos, dict) else {}, "coherente": coh}


def explain_crop(path: str | Path, etapa: str, prob: float, model: str = "kimi-k2.6", **kw) -> dict:
    """Explica (no decide) la etapa del clasificador local. Thinking desactivado, igual que el piloto."""
    prompt = PROMPT_EXPLICAR.format(etapa=NOMBRE_ETAPA.get(etapa, etapa), prob=round(prob * 100))
    kw.setdefault("extra", {"thinking": {"type": "disabled"}})
    kw.setdefault("backoff", 25.0)
    kw.setdefault("retries", 4)
    out = classify_crop(path, model, prompt=prompt, parser=parse_explain_json, **kw)
    if out.get("ok"):
        out["result"]["explicacion"] = CABECERA_EXPLICACION + out["result"]["explicacion"][:1].lower() + out["result"]["explicacion"][1:]
    return out
