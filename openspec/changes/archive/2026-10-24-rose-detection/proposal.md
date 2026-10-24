# Proposal

## Why

El núcleo de percepción necesita, dado un frame, la caja de cada rosa. Sin ese detector no hay recortes para clasificar la etapa (Spec 4) ni contrato por rosa. El usuario pidió "el modelo con mayor certeza" y un informe con resultados, así que el modelo no se fija de antemano: se elige por medición sobre el mismo conjunto de prueba. El reto: contraluz, hojas y alambres que tapan, flores pequeñas y varias rosas por foto.

## What Changes

- Comparar candidatos de detección sobre el mismo conjunto de prueba reservado por md5: OWLv2 y Grounding DINO (sin entrenar, texto "rose"), un YOLO pequeño afinado en Colab con las 178 cajas de `data/annotations/flowers.csv`, y opcionalmente un híbrido.
- Medir por candidato: recall a IoU 0.5, cajas falsas por imagen, mAP si aplica y latencia en CPU en el portátil de la demo.
- Elegir el candidato por la métrica medida y proponer, a partir de esa medición, el umbral mínimo aceptable.
- Entregar el informe con resultados en el chat: qué se probó, métricas, límites y el modelo elegido.
- Dejar el detector como núcleo independiente de la interfaz: entrada un frame, salida lista de cajas con confianza.
- Registrar la licencia del candidato elegido; si es Ultralytics (AGPL-3.0), anotar el riesgo.

Fuera del alcance: clasificar la etapa (Spec 4), rasgos y explicación (Spec 5), servicio FastAPI, cliente Quest o XR, robot, videos, fotos nuevas, datos externos (Spec 2) y cualquier cambio en `data/raw/`.

**Efecto sobre la demo mínima estable:** ninguno hasta que se elija un modelo; es evaluación offline. Riesgo de tiempo: afinar YOLO en Colab y medir tres candidatos cabe en la ventana de 20 h solo si el split y la métrica se fijan primero. Si un candidato no entrena a tiempo, se reporta como no medido en vez de omitirse.

**Dependencias:** Spec 1 (hecha: `flowers.csv`, 178 flores: inmaduro 128, óptimo 41, sobreabierto 9). El umbral mínimo es una pregunta abierta; ver `design.md`.

## Capabilities

### New Capabilities
- `rose-detection`: contrato del detector de rosas, evaluación comparada de candidatos por md5, criterio de selección y evidencia de resultados.

### Modified Capabilities
<!-- Ninguna. -->

## Impact

- Nuevos artefactos de evaluación bajo `data/annotations/` o carpeta de resultados fuera de `data/raw/` (lista de split por md5, predicciones, tabla de métricas).
- Cómputo: Colab para entrenar y evaluar; CPU del portátil de la demo para medir latencia.
- Desbloquea la Spec 4 (recortes) y alimenta la Spec 6 (evidencia).
- Licencias: OWLv2 y Grounding DINO Apache-2.0 verificadas; la del YOLO elegido se verifica antes de adoptarlo.
