# Punto de Corte XR — Sabana Hack 2026

## Descripción
Sistema que ayuda a cortadores novatos de rosa de exportación (variedad Freedom) a aprender y decidir el punto de corte. Un núcleo de visión por computador detecta cada rosa en cámara, estima su punto de apertura y explica el porqué. Ese mismo núcleo alimenta varias interfaces: Meta Quest 3 hoy (capacitación y asistencia en realidad mixta) y, a futuro, un robot de inspección (sobre rieles, móvil de pasillo o dron).

## Stack
- Visión e inferencia: Python. Servicio de inferencia con FastAPI. El modelo concreto está por definir (ver Restricciones).
- Cliente XR: Meta Quest 3, acceso a cámara con la Passthrough Camera API. **Framework sin definir**: Unity + Meta XR SDK, Meta Spatial SDK o WebXR. No asumir uno.
- Robot (concepto / prototipo mínimo opcional): cámara sobre un riel lineal (Arduino + motor paso a paso) que consume el mismo servicio.
- Respaldo para la demo: el mismo modelo corriendo en un portátil con webcam.

## Arquitectura
- `percepción` (núcleo, sin interfaz):
  - Entrada: un frame.
  - Pasos: detecta las rosas, clasifica cada una (inmaduro / óptimo / sobreabierto / zona gris) y calcula una confianza.
  - Salida: rasgos que explican la decisión (sépalos, caracol, tamaño de cabeza, tono).
- `clientes`: Quest (AR/MR), portátil (respaldo), robot (futuro). Todos consumen el mismo contrato.
- Contrato por rosa: `{bbox, clase, confianza, rasgos[], explicacion}`.
- Modos de uso:
  - **Entrenar**: primero decide la persona y luego el sistema revela su lectura.
  - **Asistir**: el sistema confirma o advierte en campo.

## Convenciones
- El código y los identificadores van en inglés. Los comentarios y la documentación, en español.
- Python: tipado, `ruff`, gestión con `uv` o `pip`, sin notebooks en el flujo final.
- `data/raw/` es de solo lectura: tiene las 56 imágenes únicas y `labels_imagen.csv`. Lo derivado va en `data/annotations/`, `data/processed/` y `outputs/`.
- Las aclaraciones al usuario se dan en el chat, no en archivos `.md` nuevos.

## Restricciones técnicas
- El sistema **no da órdenes ciegas**: siempre muestra la confianza y el porqué. La salida "zona gris → consulta" es válida.
- El dataset está etiquetado **por imagen**, no por flor, y cada foto tiene varias rosas. Clasificar la imagen completa no sirve: se necesita detección más clasificación por flor. Ver `docs/dominio-y-dataset.md`.
- El dataset es pequeño (56 imágenes únicas), tiene una sola variedad y casi no trae ejemplos de flores sobreabiertas. No prometer generalización.
- La demo se evalúa en vivo, con casos que no conocemos de antemano. Priorizar la robustez sobre las funciones nuevas.
- Hay 20 horas y 5 personas. La VR inmersiva completa (un invernadero en 3D) no entra en el alcance base.
- Los jurados dijeron de palabra que no es obligatorio construir el robot, pero la rúbrica escrita evalúa su pertinencia. La parte robótica debe quedar visible en la arquitectura y en el pitch.

## Contexto de negocio
- Dominio: floricultura de exportación en Colombia. El cortador decide hoy cómo se verá la flor días después, durante la poscosecha y el transporte.
- Usuarios:
  - El cortador novato, que vive mucha rotación y poca confianza en sus decisiones.
  - El cortador experto que capacita.
  - La finca, que necesita uniformidad en la calidad.
- Problemas que identificamos:
  1. Hay que capacitar una y otra vez por la rotación.
  2. El novato no tiene certeza frente a la rosa.
- Lo que aporta la parte robótica: memoria temporal (ve la misma flor día a día y anticipa su punto de corte), consistencia entre camas y generación de datos que alimentan la capacitación.
- Reto completo y rúbrica: `docs/reto.md`. Decisiones y riesgos: `docs/decisiones-y-riesgos.md`.
