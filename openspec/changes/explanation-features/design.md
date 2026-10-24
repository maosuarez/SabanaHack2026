# Design

## Context

- La Spec 4 entrega por recorte: etapa (inmaduro / óptimo / sobreabierto / zona gris), salida separada reencuadrar y confianza. Esta spec añade `rasgos[]` y `explicacion` al contrato.
- Señales de la ficha (Freedom): óptimo = caracol definido que deja ver el centro, rojo vivo e intenso, forma de copa; inmaduro = cabeza más pequeña, rojo más oscuro, sépalos pegados a pétalos; sobreabierto = pétalos separados, se pierde la copa. Ningún rasgo decide por sí solo.
- 178 flores anotadas (inmaduro 128, óptimo 41, sobreabierto 9), sin anotación por rasgo. Inferencia en CPU; Colab para pruebas pesadas.
- Requisitos: ver `specs/explanation-features/spec.md`.

## Goals / Non-Goals

**Goals:**
- Rasgos y texto legibles para el cortador, coherentes con la ficha.
- Mapa de calor útil para depurar el modelo, solo para el equipo.

**Non-Goals:**
- Reglas de ángulo o proporción, medición de calibre o profundidad.
- Sensor de color.
- Mostrar el mapa al usuario o presentarlo como causa.

## Decisions

1. **Rasgos base fijos:** sépalos, caracol, tamaño de cabeza y tono, cada uno con valor descriptivo o "no determinable" / "no disponible". Alternativa: añadir más rasgos; se descarta hasta validarlos con experto.
2. **Explicación por plantilla sobre rasgos y etapa**, con la terminología de la ficha. Alternativa: texto libre de un VLM; solo si la Spec 4 lo elige y se verifica coherencia. La plantilla garantiza que no haya números de punto y que cite varios rasgos.
3. **Coherencia obligatoria con la Spec 4:** etapa, zona gris y reencuadrar determinan el tipo de texto. Abstención siempre con motivo.
4. **Mapa de calor solo para el equipo** (resuelto). Se genera en herramientas de depuración, fuera de la ruta de la demo.
5. **Método del mapa por prueba corta:** comparar atención CLS del último bloque (no verificada) y oclusión en el mismo conjunto de predicciones de prueba (incluidas las que acierten y las que fallen). Criterio: si resalta la flor y no fondo/cielo/alambres en los casos revisados a ojo, y costo en CPU. pytorch-grad-cam (MIT; ViT requiere `reshape_transform` y capa objetivo tipo `model.blocks[-1].norm1`) solo aplica si hay gradientes, que con DINOv2 congelado más kNN no hay.
6. **El mapa se describe como atención, no como causa.** Texto fijo en el informe.
7. **Tono desde sensor aparte;** hasta entonces "no disponible".

## Risks / Trade-offs

- [Rasgos calculados mal producen explicaciones falsas y convincentes] → Marcar "no determinable", revisar ejemplos contra la ficha y validar con experto.
- [El mapa se interpreta como razonamiento] → Solo equipo y aviso explícito.
- [Atención CLS poco informativa] → Oclusión como alternativa; costo en CPU medido.
- [Oclusión lenta en CPU] → Solo en depuración, nunca en la demo.
- [Sobreabierto con 9 flores] → Explicación marcada no concluyente.
- [Dependencia de la Spec 4] → No iniciar la implementación antes de que existan etapa y confianza.

## Open Questions

Requieren experto o decisión del equipo; no resolver sin ellos:

- ¿El ángulo de sépalos (45°-90°) y la relación ancho/alto del botón son reglas válidas? No están en la ficha.
- ¿La cámara entrega profundidad (RGB-D) para medir calibre? Se desconoce.
- ¿Cómo se calcula cada rasgo: visión clásica, VLM o aprendido? Pendiente.
- ¿Qué método de mapa gana, CLS u oclusión? Lo decide la prueba.
- ¿Qué experto valida la redacción y los ejemplos? Lo define el equipo.
