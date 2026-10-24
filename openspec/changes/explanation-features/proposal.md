# Proposal

## Why

El contrato por rosa exige `rasgos[]` y `explicacion`: el cortador no recibe órdenes ciegas, recibe la decisión con el porqué en su propio lenguaje. La Spec 4 entrega etapa y confianza por recorte; esta spec convierte esa salida en rasgos legibles y un texto coherente con la ficha técnica, y deja un mapa de calor para que el equipo depure qué mira el modelo.

## What Changes

- Definir los rasgos base por rosa: sépalos, caracol, tamaño de cabeza y tono.
- Generar la `explicacion` con la terminología de la ficha (botón floral, pétalos, sépalos, caracol, copa), apoyada en más de un rasgo y sin números de punto.
- Mapa de calor de atención por predicción de prueba, SOLO para el equipo (resuelto), para detectar si el modelo mira fondo, cielo o alambres. Elegir entre atención del token CLS del último bloque y oclusión con una prueba corta.
- El mapa no se presenta como explicación causal ni como razonamiento experto.
- El tono no depende del color de la imagen: llegará de un sensor aparte.
- Informe en el chat con ejemplos de predicciones: rasgos, explicación y mapa.

Fuera del alcance: ángulo de sépalos y relación ancho/alto del botón como reglas (no están en la ficha; requieren experto), medición de calibre o profundidad RGB-D, el sensor de color, mostrar el mapa al usuario final, otras variedades que no sean Freedom y servicio o cliente XR.

**Efecto sobre la demo mínima estable:** ninguno si la explicación se calcula sobre la salida existente de la Spec 4 y el mapa corre solo fuera de la demo. Si el cálculo de rasgos añade latencia en CPU, se mide y, de ser necesario, la demo muestra solo la explicación en texto.

**Dependencias pendientes:** depende de la Spec 4 (etapa, confianza y extractor elegido) y de validación con experto. Cómo se calcula cada rasgo, el uso de ángulos/proporciones y la profundidad son Open Questions; ver `design.md`.

## Capabilities

### New Capabilities
- `explanation-features`: rasgos por rosa, texto de explicación con terminología de la ficha y mapa de calor de depuración solo para el equipo.

### Modified Capabilities
<!-- Ninguna: openspec/specs/ está vacío. -->

## Impact

- Nuevos módulos de explicación y depuración (código en la implementación, no en esta planificación); consumen recortes y salida de la Spec 4.
- Posible dependencia nueva: pytorch-grad-cam (MIT) solo si se elige un método con gradientes; con DINOv2 congelado más kNN no hay gradientes.
- Alimenta el campo `rasgos[]` y `explicacion` del contrato y la evidencia de la Spec 6.
- Docs: al resolver las Open Questions, actualizar `docs/decisiones-y-riesgos.md`.
