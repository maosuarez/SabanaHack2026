# Design

## Context

- `data/annotations/flowers.csv`: 178 flores sobre 56 fotos únicas de 1200×1600. Inmaduro 128, óptimo 41, sobreabierto 9 (2 fotos). 0 dudosas. Una sola cuenta de anotación (`user1`).
- Piso sin aprendizaje profundo (histograma de color, foto completa): siempre-inmaduro exactitud 0.625 / balanceada 0.250 / F1 macro 0.192. Es la referencia a superar.
- Sin robot, sin fotos nuevas, sin videos. GPU dañada: Colab para el cómputo pesado, CPU para inferir.
- Esta spec alimenta el clasificador (Spec 4) y el detector (Spec 3).

## Goals / Non-Goals

**Goals:**
- Más ejemplos útiles por etapa, sobre todo sobreabierto, sin contaminar validación ni prueba.
- Trazabilidad completa de cualquier imagen externa.

**Non-Goals:**
- Entrenar los modelos finales, tomar fotos, usar videos, cubrir otras variedades.

## Decisions

- **Aumentación al vuelo o precalculada, solo en train.** Se aplica después del split por md5. Límites: rotación ±30°, zoom, brillo y contraste leves, sin hue fuerte (decisión del usuario). Alternativa descartada: aumentar antes del split, porque filtra variantes de una misma foto al test.
- **Orden fijo:** anotación por flor, aumentación, externas. Las externas se abren solo con una medición que muestre una clase corta con flores propias (propuesto).
- **Registro de externas en un CSV propio** en `data/annotations/` con URL, licencia, autor, fecha de acceso, etiqueta, md5 del archivo y estado (admitida / descartada y motivo). Propuesto: un archivo aparte del de flores propias para que el origen nunca se confunda.
- **Revisión a ojo de cada externa** (rosa roja, vista comparable) y etiqueta asignada con el criterio de la ficha, con nombres de clase y señales visuales, sin números de punto (propuesto).
- **Sobreabierto = clase de baja confianza** (decisión del usuario): se entrena con lo que haya, se marca no concluyente y se deriva a zona gris / consulta. No se promete rendimiento en esa clase.
- **Candidatos externos, sin verificar** (búsqueda limitada): Mendeley Data 53vyvz5yyk (565 fotos de plantas de rosa en 3 etapas de crecimiento, CC BY 4.0; no es punto de corte, así que su utilidad para etapa es dudosa); Roboflow "bud detection" (591 imágenes flower/bud, CC BY 4.0; más útil para el detector que para etapas). RoseBlooming (sin licencia) y el dataset de Frontiers 2025 de rosas cortadas en 5 clases (no público) se descartan, salvo permiso y licencia explícitos. Antes de usar cualquiera hay que verificar licencia y contenido en la fuente oficial.
- **Evidencia con el mismo split** que usarán las Specs 3, 4 y 6, para que los conteos sean comparables.

## Risks / Trade-offs

- [Aumentar 9 flores no crea información nueva] → La aumentación reduce sobreajuste, no sustituye ejemplos reales; sobreabierto sigue no concluyente.
- [Externas de otro dominio (cultivo, variedad, ángulo)] → Revisión a ojo, fuera del test, y medir si ayudan en validación con flores propias antes de conservarlas.
- [Etiquetar externas sin experto es subjetivo] → Criterio de la ficha, marca de dudosa y descarte ante la duda.
- [Licencias mal leídas] → Registro por imagen y descarte si hay cualquier ambigüedad.
- [Fuga entre train y test por recortes de una misma foto] → Split por md5 antes de aumentar y verificación automática.

## Open Questions

- ¿Cuántos ejemplos por clase se consideran suficientes para dejar de buscar externas? No se fija un número sin medición; se propone a partir del resultado en validación.
- ¿Se usan los candidatos Mendeley Data 53vyvz5yyk y Roboflow "bud detection"? Dependen de verificar licencia y de que el contenido sirva; no se decide ahora.
- ¿Quién revisa las externas a ojo y quién las etiqueta? Lo define el equipo; idealmente un experto o una segunda persona.
- ¿Aumentación al vuelo en Colab o archivos precalculados? Depende del tamaño y de la herramienta de entrenamiento de las Specs 3 y 4.
