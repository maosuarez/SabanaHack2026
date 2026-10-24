# Design

## Context

- Anotaciones por flor: `data/annotations/flowers.csv` (178 flores; inmaduro 128, óptimo 41, sobreabierto 9; una sola cuenta de anotación `user1`). Imágenes: 56 únicas de 1200×1600 en `data/raw/` (solo lectura).
- Condiciones difíciles: fotos desde abajo, contraluz, rosas pequeñas, hojas y alambres.
- GPU dañada: Colab entrena y evalúa; CPU infiere en el portátil de la demo.
- Requisitos: ver `specs/rose-detection/spec.md`.

## Goals / Non-Goals

**Goals:**
- Elegir el detector por métrica medida sobre el mismo test por md5 y entregar el informe con resultados.
- Dejar un detector independiente de la interfaz, usable en CPU.

**Non-Goals:**
- Clasificar etapa, rasgos o explicación; servicio FastAPI; cliente XR; datos externos; videos.

## Decisions

1. **Candidatos:** OWLv2 y Grounding DINO sin entrenar (texto "rose"); YOLO pequeño afinado en Colab con las 178 cajas; opcional híbrido (p. ej. propuestas de un modelo abierto filtradas por otro). Se descarta elegir uno a priori porque el usuario pidió mayor certeza demostrada.
2. **Split por md5 compartido:** una lista fija de md5 de prueba, generada una vez y guardada, usada por todos los candidatos. Con 56 imágenes el test es pequeño; se reporta el número de imágenes y flores y se advierte la varianza. Alternativa: validación cruzada por md5, solo si el tiempo lo permite.
3. **Métricas:** recall a IoU 0.5, cajas falsas por imagen, mAP si aplica, latencia en CPU. Los modelos sin entrenar no tienen mAP comparable sin umbral de confianza; se usa un barrido de umbrales y se indica cómo se eligió el punto de operación (solo sobre entrenamiento o validación, nunca sobre el test).
4. **"No anotable":** se excluyen de recall y de falsas positivas con la misma regla para todos, y se reporta cuántas son. Alternativa: contarlas como positivas; se difiere a Open Questions.
5. **Desglose por condición:** etiquetar a mano en el test cada imagen con condiciones (contraluz, pequeñas, oclusión, varias rosas) para reportar límites; es barato y evita promedios que esconden fallas.
6. **Latencia:** medir en el portátil de la demo con CPU, en frío y en caliente, tamaño de entrada declarado. Si un candidato es demasiado lento para la demo, se reporta aunque su recall sea mayor.
7. **Licencias:** OWLv2 y Grounding DINO Apache-2.0 (verificadas). El YOLO elegido se verifica antes de adoptarlo; Ultralytics es AGPL-3.0 y puede obligar a abrir el código del servicio. Alternativa a evaluar si se elige: otra implementación YOLO con licencia permisiva.
8. **Informe en el chat:** tabla por candidato, desglose por condición, límites, modelo elegido, umbral propuesto y licencias.

## Risks / Trade-offs

- [Test pequeño: pocas imágenes y una sola variedad] → Reportar intervalos o varianza y no sobreinterpretar diferencias pequeñas.
- [YOLO sobreajusta con 178 cajas] → Aumentación solo en entrenamiento (rotación ±30°, zoom, brillo/contraste leves, sin cambios fuertes de hue) y validación por md5.
- [Anotaciones de un solo anotador, sin doble anotación] → Las cajas de referencia pueden tener sesgo; se anota como límite.
- [Licencia AGPL de Ultralytics] → Anotar el riesgo y considerar alternativa permisiva si gana.
- [Modelos grandes lentos en CPU] → Medir latencia desde el inicio; tamaño reducido si hace falta.
- [Tiempo de Colab] → Medir primero los candidatos sin entrenar; afinar YOLO después.

## Open Questions

- Umbral mínimo aceptable: [PEND]. Se propone con la medición; no se fija un número.
- Tratamiento de "no anotable" en recall (excluir o contar): por decidir con los datos.
- Qué portátil de la demo se usa para la latencia: lo confirma el equipo.
- ¿Se intenta el híbrido? Solo si sobra tiempo tras los tres candidatos.
