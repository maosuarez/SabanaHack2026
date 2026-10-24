# Proposal

## Why

El dataset tiene 56 imágenes únicas etiquetadas por escena, no por flor: cada foto muestra varias rosas en puntos distintos y 8 fotos aparecen en más de una clase. Con esas etiquetas no se puede entrenar ni evaluar un detector ni un clasificador por flor. La anotación por rosa (caja + etapa) desbloquea las specs de detección, clasificación y evaluación, así que va primero.

## What Changes

- Anotar cada rosa visible de las 56 imágenes únicas con una caja y una etapa (inmaduro / óptimo / sobreabierto), en Label Studio.
- Guardar las anotaciones en `data/annotations/` con: md5 de la imagen, caja, etapa, anotador y marca de "dudosa". Las rosas demasiado pequeñas o tapadas se marcan "no anotable" en lugar de forzar una etapa.
- Anotar por flor las 8 fotos multiclase (5, 16, 25, 28, 47 entre inmaduro/óptimo; 45; 63; 26).
- Pre-anotar cajas con un detector de vocabulario abierto (Grounding DINO u OWL-ViT, texto "rose") e importarlas en Label Studio como predicciones. La etapa la asigna siempre una persona.
- Prueba piloto previa en 5 fotos, corrida por el usuario, que decide si la pre-anotación se adopta o se anota todo a mano.
- Doble anotación independiente de ~10 fotos comunes, sin sugerencias del detector, para medir el acuerdo entre anotadores.
- Guía de criterio visual con las señales de la ficha técnica (caracol definido, centro visible, rojo vivo u oscuro, forma de copa o cabeza pequeña, sépalos pegados o abiertos).
- Informe en el chat: flores por etapa, cuántas "no anotable", resultado de la piloto y acuerdo entre anotadores.

Fuera del alcance: tomar fotos nuevas, usar videos o fotogramas, imágenes externas (Spec 2), entrenar modelos (Specs 3 y 4), la clase "reencuadrar" del contrato y cualquier cambio en `data/raw/`.

**Efecto sobre la demo mínima estable:** ninguno. Es trabajo de datos fuera del servicio de percepción; no toca código de demo ni clientes. Riesgo de tiempo: la anotación manual es el cuello de botella de la ventana de 20 h, por eso se prueba la pre-anotación antes de comprometer el flujo y se limita la doble anotación a ~10 fotos.

**Dependencias pendientes:** la piloto necesita decidir si corre en Colab o en CPU (el usuario no tiene GPU funcional). Se asume Colab hasta que el usuario indique otra cosa; ver `design.md`. Las líneas de `docs/dominio-y-dataset.md` y `docs/decisiones-y-riesgos.md` que mencionan los videos como fuente de fotogramas quedan obsoletas por la decisión del usuario y deben actualizarse.

## Capabilities

### New Capabilities
- `per-flower-annotation`: formato, vocabulario, criterio y control de calidad de las anotaciones por rosa (caja + etapa) sobre las imágenes únicas del reto, incluida la pre-anotación asistida de cajas.

### Modified Capabilities
<!-- Ninguna: openspec/specs/ está vacío. -->

## Impact

- Nuevos archivos bajo `data/annotations/` (exportación de Label Studio, tabla por flor, registro de la piloto). `data/raw/` no se modifica.
- Herramientas nuevas, solo para el equipo: Label Studio; Grounding DINO u OWL-ViT para pre-anotar (Colab).
- Desbloquea las Specs 3 (detector), 4 (clasificador) y 6 (evaluación), que consumen estas anotaciones y el split por md5.
- Docs: actualizar `docs/dominio-y-dataset.md` y `docs/decisiones-y-riesgos.md` (videos excluidos, herramienta de anotación, vocabulario sin numeración de puntos).
