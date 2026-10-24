# Proposal

## Why

El sistema debe decir, para cada rosa recortada, en qué etapa está y con qué confianza, y debe saber abstenerse. Hoy no existe ningún clasificador por flor ni una medición sobre estos datos: el único piso es sin aprendizaje profundo (histograma de color sobre la foto completa, 48 fotos): "siempre inmaduro" da exactitud 0.625, balanceada 0.250 y F1 macro 0.192; color+1NN da 0.438 / 0.260 / 0.260; color+LogReg da 0.271 / 0.454 / 0.317. Con las 178 flores anotadas (Spec 1: inmaduro 128, óptimo 41, sobreabierto 9) ya se puede comparar candidatos con evidencia.

## What Changes

- Comparar, sobre el mismo test reservado por md5, dos candidatos para clasificar recortes: (A) DINOv2 congelado + clasificador ligero (kNN o regresión logística) y (B) un VLM con prompt basado en la ficha técnica. Se elige por métrica medida, no de antemano.
- Medir la velocidad de DINOv2 (ViT-S/14 y ViT-B/14) en CPU sobre recortes, en el portátil de la demo, antes de escoger tamaño. El entrenamiento y la evaluación pesada corren en Colab.
- Definir la salida por recorte: etapa (inmaduro / óptimo / sobreabierto) con confianza, o una de dos abstenciones separadas: "reencuadrar" (recorte no válido: borroso, tapado o sin flor; acción: repetir captura) y "zona gris" (recorte válido con etapa ambigua; acción: consultar).
- Tratar sobreabierto (n=9) como clase de baja confianza / no concluyente, derivada a zona gris.
- Calibrar los umbrales de rechazo y de zona gris con validación, sin fijarlos de antemano.
- Reportar métricas por clase, matriz de confusión y clases con pocos ejemplos, y compararlas contra el piso anterior.
- El clasificador no usa el color de la imagen como señal de decisión del contrato: el color llegará de un sensor aparte (actividad fuera de estas specs). La aumentación solo en entrenamiento, sin cambios fuertes de hue.

Fuera del alcance: detección de cajas (Spec 3), rasgos y explicación (Spec 5), informe global de evaluación (Spec 6), expansión del dataset (Spec 2), el sensor de color, servicio FastAPI, cliente Quest/XR, robot, videos, otras variedades que no sean Freedom, y cualquier cambio en `data/raw/`. DINOv2 no detecta; no confundir con Grounding DINO.

**Efecto sobre la demo mínima estable:** ninguno hasta integrarse. Es trabajo de modelo sobre recortes; la inferencia en CPU del portátil de la demo es un requisito, y se mide para no romperla.

**Dependencias:** Spec 1 (`data/annotations/flowers.csv`, ya hecha) y Spec 3 (cajas/recortes del detector, para evaluar de extremo a extremo; el entrenamiento puede usar las cajas anotadas). La licencia de DINOv2 (Apache-2.0 según README) se confirma en el LICENSE oficial de facebookresearch/dinov2; la del VLM elegido se verifica antes de usarlo.

## Capabilities

### New Capabilities
- `stage-classification`: clasificación de etapa por recorte con confianza, abstención separada (reencuadrar / zona gris), medición de velocidad en CPU y evaluación contra el piso.

### Modified Capabilities
<!-- Ninguna. El contrato por rosa se amplía con "reencuadrar" (nombre pendiente), ver design.md. -->

## Impact

- Nuevos artefactos bajo `data/` (recortes derivados, tabla de resultados) sin tocar `data/raw/`; código de modelo en la fase de apply.
- Colab para entrenar/evaluar; CPU del portátil para inferir.
- Alimenta la Spec 5 (explicación) y la Spec 6 (evaluación).
- Docs: al resolver los pendientes, actualizar `docs/decisiones-y-riesgos.md`.
