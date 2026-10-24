# Design

## Context

- Entrada: `data/annotations/flowers.csv` (178 flores: inmaduro 128, óptimo 41, sobreabierto 9; 0 dudosas; un solo anotador) y recortes por caja. Fotos 1200x1600 desde abajo, a contraluz, rosas pequeñas, hojas y alambres.
- Sin GPU local: Colab entrena/evalúa; CPU del portátil de la demo infiere.
- Piso medido sin DL en foto completa (48 fotos): ver `specs/stage-classification/spec.md`. DINOv2 aún no medido en estos datos.
- Etiqueta por foto no coincide con lo anotado por flor: se usa siempre la etapa por flor.

## Goals / Non-Goals

**Goals:**
- Elegir con evidencia el clasificador de etapa y su tamaño.
- Salida con confianza y dos abstenciones separadas.
- Informe honesto contra el piso.

**Non-Goals:**
- Detectar rosas (Spec 3), explicar (Spec 5), informe global (Spec 6), ampliar el dataset (Spec 2), sensor de color.

## Decisions

1. **Candidato A: DINOv2 congelado + kNN o regresión logística** sobre embeddings de recortes. Barato de entrenar, sin gradientes, rápido en CPU. DINOv2 no detecta; no se confunde con Grounding DINO.
2. **Candidato B: VLM con prompt** construido con la terminología de la ficha, sin números de punto. Sirve de comparación; se descarta si es lento en CPU o peor medido.
3. **Elección por métricas** (F1 macro, exactitud balanceada, recall por clase, ms/recorte en CPU) en el mismo test por md5. Alternativa descartada: elegir por reputación del modelo.
4. **Tamaño ViT-S/14 vs ViT-B/14** se decide tras medir velocidad en CPU del portátil.
5. **Abstenciones separadas:** "reencuadrar" por un detector de recorte no válido (entrenado con `04_Casos_Dificiles_Ruido` más negativos) y "zona gris" por confianza del clasificador entre umbrales. Ambos umbrales se calibran en validación.
6. **Sobreabierto:** se entrena con lo que hay, pero la salida se marca baja confianza y va a consulta. Posible agrupar su predicción en zona gris.
7. **Color:** no se agrega al contrato; la aumentación evita cambios fuertes de hue para no sesgar al modelo con el color, que vendrá de un sensor aparte.
8. **Split por md5** compartido con las Specs 3 y 6.

## Risks / Trade-offs

- [Solo 9 sobreabiertos y 41 óptimos: métricas ruidosas] → Reportar n por clase; clases <5 no concluyentes; validación cruzada por md5 si el test es muy pequeño.
- [Un solo anotador, etapas subjetivas] → Declarar el límite en el informe; revisar con experto si es posible.
- [Contraluz y recortes diminutos degradan embeddings] → Revisar errores por recorte; "reencuadrar" absorbe los inválidos.
- [VLM lento en CPU] → Medir antes de comprometerlo en la demo.
- [Test pequeño sobreajusta la elección de umbrales] → Calibrar en validación, no en test.

## Open Questions

- Umbral de rechazo ("reencuadrar") y umbral de zona gris: se calibran con validación; no se fija ningún número.
- Nombre y forma de "reencuadrar" en el contrato por rosa {bbox, clase, confianza, rasgos[], explicacion}: ¿valor de `clase`, campo aparte o banderas? Pendiente de confirmar.
- Tamaño de DINOv2 (S/14 o B/14): depende de la velocidad medida en CPU.
- Qué VLM concreto y su licencia.
- Cómo reparte la demo el tiempo: ¿se acepta latencia del VLM o solo DINOv2?
