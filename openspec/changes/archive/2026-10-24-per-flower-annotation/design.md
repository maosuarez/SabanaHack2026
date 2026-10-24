# Design

## Context

- `data/raw/images/rosa_XX.jpeg`: 56 JPEG únicos de 1200×1600; `data/raw/labels_imagen.csv` trae `image_id, file, etiquetas_origen, multiclase, md5`. `data/annotations/` está vacío (`.gitkeep`).
- Etiquetas de origen por escena; 8 fotos multiclase. Fotos desde abajo, a contraluz, rosas pequeñas, hojas y alambres que tapan.
- El usuario no tiene GPU funcional: todo cómputo pesado corre en Colab o en CPU.
- Motivación y alcance: ver `proposal.md`. Requisitos: ver `specs/per-flower-annotation/spec.md`.

## Goals / Non-Goals

**Goals:**
- Un formato de anotación simple que consuman directamente los futuros detector y clasificador y el split por md5.
- Flujo de anotación que quepa en la ventana de 20 h con dos personas.

**Non-Goals:**
- Entrenar o evaluar modelos.
- Etiquetar "reencuadrar" o "zona gris" (se deciden en la Spec 4).
- Anotar imágenes externas o fotogramas de video.

## Decisions

1. **Label Studio como herramienta** (decidido por el usuario). Una tarea por imagen única, con etiquetas de caja y una elección de etapa por caja; "no anotable" y "dudosa" como atributos de la caja. Se importan las imágenes por ruta local, de solo lectura.
2. **Pre-anotación de cajas con Grounding DINO u OWL-ViT** (texto "rose"), generando un JSON de predicciones que Label Studio importa. Alternativa: dibujar todo a mano. Se mantiene la alternativa como plan B explícito si la piloto no ahorra tiempo. Los dos modelos se confirman con licencia Apache 2.0 en sus repositorios oficiales antes de usarlos; la fuente actual es secundaria.
3. **La etapa nunca se pre-anota.** Evita que el sesgo del modelo contamine las etiquetas que luego lo evaluarán.
4. **Formato de salida:** exportación JSON de Label Studio conservada tal cual, más una tabla plana derivada (`data/annotations/flowers.csv`) con `md5, image_id, box (x, y, w, h normalizados), stage, doubtful, annotatable, annotator`. La tabla es lo que consumen las demás specs; el JSON es la fuente. Alternativa: solo JSON; se descarta porque obliga a cada consumidor a reimplementar el parseo.
5. **Identidad por md5** y no por nombre de archivo, para que las duplicadas entre clases no generen anotaciones repetidas y el split por md5 sea directo.
6. **Piloto en Colab** (supuesto). El usuario la corre con 5 fotos escogidas, entre ellas una multiclase y una con rosas muy pequeñas. Se mide: fracción de rosas encontradas, cajas falsas y tiempo con y sin pre-anotación. Si el usuario prefiere CPU, el flujo no cambia; solo cambia el tiempo de ejecución.
7. **Doble anotación en ~10 fotos** y acuerdo medido sobre cajas emparejadas por IoU. El umbral de IoU para emparejar se fija al ver los datos de la piloto; no se inventa de antemano.
8. **Guía de criterio de una página** dentro de la descripción de la tarea en Label Studio (no un archivo `.md` nuevo), con las señales de la ficha y la regla "ante la duda, dudosa".

## Risks / Trade-offs

- [Rosas pequeñas y a contraluz: el detector abierto pierde muchas] → La piloto mide la cobertura; si es baja, se anota a mano.
- [Anotar a mano 56 fotos con muchas rosas consume horas] → Priorizar las 8 multiclase y una muestra balanceada primero; reportar cuántas fotos alcanzaron a revisarse si se agota el tiempo.
- [Sin experto, las etapas son subjetivas] → Marca de dudosa, doble anotación en la muestra común y revisión con un experto si es posible.
- [Sobreabierto casi no aparece (2 fotos)] → Se anota lo que haya y se marca como no concluyente en el informe; el tratamiento se decide en la Spec 2.
- [Cajas del detector aceptadas sin cuidado] → Toda caja se revisa por una persona; no se confía en la confianza del detector.

## Open Questions

- ¿Colab o CPU para la piloto? Se asume Colab; no cambia los requisitos.
- Umbral de IoU para emparejar cajas entre anotadores: se fija con los datos de la piloto.
- Cuáles son las dos personas anotadoras: lo define el equipo.
