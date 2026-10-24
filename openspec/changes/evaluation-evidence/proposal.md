# Proposal

## Why

Con 178 flores, 56 fotos y clases muy desbalanceadas (inmaduro 128, óptimo 41, sobreabierto 9), la exactitud engaña: "siempre inmaduro" da 0.625 de exactitud y solo 0.250 balanceada. Sin un protocolo de evaluación honesto (split sin fuga, métricas por clase, matriz de confusión, comparación contra un piso) cualquier número del detector o del clasificador sería poco confiable. Esta spec define cómo medir y qué evidencia dejar tras cada prototipo.

## What Changes

- Split de evaluación por md5, con todos los recortes de una misma foto en el mismo lado (train, validación o test), para evitar fuga.
- Métricas por clase (precisión, recall, F1) y matriz de confusión; la exactitud sola no se acepta como resultado.
- Clases con menos de 5 ejemplos de prueba se reportan como no concluyentes (hoy: sobreabierto).
- Comparación obligatoria contra el piso sin aprendizaje profundo (histograma de color, foto completa, 48 fotos): siempre-inmaduro 0.625 / 0.250 / 0.192; color+1NN 0.438 / 0.260 / 0.260; color+LogReg 0.271 / 0.454 / 0.317 (exactitud / balanceada / F1 macro).
- Evidencia en el chat tras cada prototipo: qué se probó, resultado y límites observados.
- Prueba de la demo con casos desconocidos: rosas reales, fotos impresas y fotos en pantalla.
- Registrar como límite de validez que el etiquetado actual tiene una sola cuenta de anotación (`user1`) y ningún acuerdo entre anotadores medido.

Fuera del alcance: entrenar modelos (Specs 3 y 4), conseguir más datos (Spec 2), servicio FastAPI, cliente Quest/XR, robot, videos, otra variedad que no sea Freedom y reabrir la numeración de puntos.

**Efecto sobre la demo mínima estable:** ninguno. Es protocolo de medición; no toca código de demo.

**Dependencias pendientes:** los umbrales de aceptación y la forma de la prueba en vivo del jurado dependen de una sesión con expertos; quedan como Open Questions en `design.md`.

## Capabilities

### New Capabilities
- `evaluation-evidence`: protocolo de split, métricas, comparación contra el piso y reporte de evidencia de cada prototipo.

### Modified Capabilities
<!-- Ninguna. -->

## Impact

- Consume `data/annotations/flowers.csv` y los md5 de `data/raw/labels_imagen.csv`; no modifica `data/raw/`.
- Define el split compartido que usarán las Specs 3 y 4, y la forma del informe en el chat.
- Puede ir en paralelo con la Spec 2; el piso ya está medido.
