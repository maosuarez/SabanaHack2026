# Proposal

## Why

`data/annotations/flowers.csv` (Spec 1) tiene 178 flores: inmaduro 128, óptimo 41, sobreabierto 9 (solo 2 fotos). Con tan pocos ejemplos, el clasificador por recorte (Spec 4) no puede aprender ni evaluarse en sobreabierto, y óptimo es corto. No se pueden tomar fotos nuevas ni usar videos. Esta spec define cómo ampliar los ejemplos por etapa con lo que sí se permite: más aprovechamiento de las imágenes del reto (aumentación) y, solo si hace falta, imágenes externas con licencia abierta.

## What Changes

- Contar las flores por etapa antes y después de cada paso de expansión, sobre el split por md5.
- Aumentar solo el conjunto de entrenamiento, con límites globales: rotación ±30°, zoom, brillo y contraste leves, sin cambios fuertes de tono (hue). Nunca aumentar validación ni prueba.
- Fuente externa opcional (CC0, dominio público o CC BY con atribución), solo después de medir con las flores propias y solo para la clase que siga faltando. Cada imagen externa registra URL, licencia, autor, fecha de acceso y la etiqueta asignada con el criterio de la ficha. Las externas quedan fuera del test y se revisan a ojo (rosa roja, vista comparable). Licencia distinta o ausente: se descarta.
- Sobreabierto se trata como clase de baja confianza: se entrena con lo que haya, se marca no concluyente y se deriva a zona gris / consulta (decisión del usuario).
- Evidencia en el chat: conteo por clase antes y después, registro de licencia por imagen externa, límites observados.

Orden de trabajo: primero la anotación por flor (ya hecha), luego la aumentación, y las externas solo si, tras medir con flores propias, sigue faltando una clase.

Fuera del alcance: fotos nuevas, videos y fotogramas, entrenar los modelos finales (Specs 3 y 4), el sensor de color, otras variedades distintas de Freedom, cualquier cambio en `data/raw/`, y los candidatos descartados (RoseBlooming sin licencia; dataset de Frontiers 2025 no público salvo permiso y licencia).

**Efecto sobre la demo mínima estable:** ninguno. Es trabajo de datos fuera del servicio de percepción. Riesgo de tiempo: la búsqueda y revisión de externas puede consumir horas; por eso va al final y con tope de tiempo.

**Dependencias pendientes:** ninguna decisión bloqueante abierta; ver Open Questions en `design.md` (cantidad objetivo por clase, uso de los candidatos externos).

## Capabilities

### New Capabilities
- `dataset-expansion`: reglas de aumentación solo en entrenamiento, admisión y registro de imágenes externas con licencia abierta, tratamiento de sobreabierto como clase de baja confianza y conteo antes/después por clase.

### Modified Capabilities
<!-- Ninguna: openspec/specs/ no contiene capacidades previas que cambien. -->

## Impact

- Nuevos derivados bajo `data/processed/` y `data/annotations/` (registro de externas, conteos). `data/raw/` no se modifica.
- Alimenta las Specs 3 (detector) y 4 (clasificador). La Spec 6 usa el mismo split por md5.
- Docs: actualizar `docs/decisiones-y-riesgos.md` con el tratamiento de sobreabierto y la política de externas.
