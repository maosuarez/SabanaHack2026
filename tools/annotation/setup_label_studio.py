"""Crea el proyecto de Label Studio con una tarea por imagen única (md5).

Las imágenes se sirven por ruta local en solo lectura desde data/raw/images/ (raíz del documento: data/raw)
(LOCAL_FILES_SERVING_ENABLED + LOCAL_FILES_DOCUMENT_ROOT=data/raw). No se copia ni
modifica nada en data/raw/.

Uso:
    LS_URL=http://localhost:8080 LS_API_KEY=<token> python setup_label_studio.py
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

from label_studio_sdk.client import LabelStudio

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGES_DIR = REPO_ROOT / "data" / "raw" / "images"
LABELS_CSV = REPO_ROOT / "data" / "raw" / "labels_imagen.csv"
CONFIG_XML = Path(__file__).with_name("label_config.xml")
PROJECT_TITLE = "Rosas Freedom - anotación por flor"

# Guía de criterio (se muestra en la descripción del proyecto)
GUIDE = """\
GUÍA DE CRITERIO (variedad Freedom, rosa roja)

Dibuja UNA caja por cada rosa visible y elige su etapa. Ningún rasgo decide por sí solo: lee las señales en conjunto.

- inmaduro (cerrado, no cortar; es el error más común): cabeza más pequeña, rojo más oscuro, sépalos pegados a los pétalos.
- optimo (cortar): caracol (espiral de pétalos) definido que deja ver el centro, rojo vivo e intenso, forma de copa.
- sobreabierto (ya pasó su punto): pétalos separados, se pierde la forma de copa.

Atributos por caja (selecciona la caja y marca):
- dudosa: no estás seguro de la etapa. REGLA: ante la duda, dudosa.
- no_anotable: la rosa no se puede juzgar (muy tapada por hojas o alambres, contraluz extremo, muy pequeña). Sin etapa fiable.

Recuerda: la flor sigue abriendo en poscosecha; piensa en cómo se verá días después. Solo aplica a Freedom.
"""


def load_tasks() -> list[dict[str, object]]:
    """Una tarea por imagen única, con el md5 como metadato."""
    tasks: list[dict[str, object]] = []
    seen: set[str] = set()
    with LABELS_CSV.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            md5 = row["md5"]
            if md5 in seen:
                continue
            seen.add(md5)
            path = IMAGES_DIR / row["file"]
            if not path.is_file():
                raise FileNotFoundError(path)
            tasks.append(
                {
                    "image": f"/data/local-files/?d=images/{row['file']}",
                    "md5": md5,
                    "image_id": int(row["image_id"]),
                    "file": row["file"],
                }
            )
    return tasks


def main() -> None:
    client = LabelStudio(
        base_url=os.environ.get("LS_URL", "http://localhost:8080"),
        api_key=os.environ["LS_API_KEY"],
    )
    project = client.projects.create(
        title=PROJECT_TITLE,
        description=GUIDE,
        label_config=CONFIG_XML.read_text(encoding="utf-8"),
    )
    # Almacenamiento local requerido para servir las imágenes; no se sincroniza
    # (las tareas ya se importan abajo, una por md5)
    client.import_storage.local.create(
        project=project.id,
        title="raw-images (solo lectura)",
        path=str(IMAGES_DIR),
        use_blob_urls=False,
    )
    tasks = load_tasks()
    client.projects.import_tasks(id=project.id, request=tasks)
    print(f"project_id={project.id} tasks={len(tasks)}")


if __name__ == "__main__":
    main()
