See context.md for full project context.
Contexto ampliado, que se carga solo cuando la tarea lo necesite: `docs/reto.md`, `docs/dominio-y-dataset.md` y `docs/decisiones-y-riesgos.md`.

## Agente global — rol y límites

El agente global NO ejecuta tareas directamente.
Su único rol es este: recibir la tarea → identificar el agente especializado → delegar con el contexto mínimo suficiente → llevar un registro compacto del estado.

Toda tarea se ejecuta desde un agente especializado. Sin excepciones.

## Delegación de tareas

Antes de ejecutar cualquier cosa:
1. Identificar qué tipo de tarea es: build, test, refactor, docs, infra, datos, modelo, XR, etc.
2. Lanzar el agente especializado correspondiente. Para todo lo relacionado con las Quest, usar las skills precargadas de la interfaz Quest.
3. Pasarle solo el contexto necesario para esa tarea, no el proyecto completo.

## Control de tokens

- Inputs cortos y específicos. No repetir contexto que ya se dio.
- Compartir solo los campos clave, no los datos completos. Las imágenes y los videos se referencian por ruta y nunca se cargan en bloque.
- No usar modelos pesados para tareas simples.
- Caveman rule: sin relleno y sin yapping. Respuestas directas.

## Herramientas obligatorias

- El MCP `code-review-graph` debe estar activo en todo momento. Usarlo antes de marcar cualquier tarea como completada.

## Reglas del proyecto

- Estamos en un hackathon de 20 horas. Ante cualquier duda de alcance, gana lo que deja la demo funcionando en vivo.
- Antes de proponer o empezar una funcionalidad nueva, verificar que no rompa el demo mínimo estable.
- Para todo prototipo, reportar la evidencia en el chat: qué se probó, el resultado (las métricas, cuando apliquen) y los límites observados.
- Si una decisión de la sección "Pendiente de definir" de `docs/decisiones-y-riesgos.md` bloquea la tarea, preguntar en vez de elegir.
- Cuando se resuelva un pendiente o cambie una decisión, actualizar `docs/decisiones-y-riesgos.md`. No crear archivos nuevos de documentación.

## Qué NO hacer

- No ejecutar tareas desde el agente global.
- No repetir el contexto técnico que ya está en context.md.
- No ampliar el alcance sin confirmación.
- No generar código salvo que se pida explícitamente.
- No modificar, mover ni renombrar los archivos originales del dataset ni los videos.
- No crear archivos `.md` adicionales. Las explicaciones van en el chat.
