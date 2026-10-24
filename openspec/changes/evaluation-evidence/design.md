# Design

## Context

- `data/annotations/flowers.csv`: 178 flores en 56 fotos (inmaduro 128, óptimo 41, sobreabierto 9; 0 dudosas). Una sola cuenta de anotación (`user1`), sin doble anotación ni acuerdo medido.
- Piso sin aprendizaje profundo (histograma de color, foto completa, 48 fotos), exactitud / balanceada / F1 macro: siempre-inmaduro 0.625 / 0.250 / 0.192; color+1NN 0.438 / 0.260 / 0.260; color+LogReg 0.271 / 0.454 / 0.317. DINOv2 no se ha medido en estos datos.
- Cómputo pesado en Colab; inferencia en CPU. Motivación y alcance: ver `proposal.md`. Requisitos: ver `specs/evaluation-evidence/spec.md`.

## Goals / Non-Goals

**Goals:**
- Un split único y reproducible que usen las Specs 3 y 4.
- Un formato de informe fijo para el chat, comparable entre prototipos.

**Non-Goals:**
- Entrenar modelos o conseguir datos.
- Fijar umbrales de aceptación (dependen de expertos).

## Decisions

1. **Split por md5, con flores agrupadas por foto.** Evita que recortes de una misma foto (mismo fondo y luz) estén en train y test. Con 56 fotos, se valida con validación cruzada agrupada por md5 y un test reservado pequeño; el tamaño exacto se fija al ver cuántas flores por clase caen en cada lado.
2. **Estratificación aproximada por clase a nivel de foto**, sin romper la regla de grupo. Con sobreabierto (9 flores, 2 fotos) el test probablemente tendrá menos de 5: se reporta como no concluyente, no se fuerza.
3. **Métricas:** precisión, recall y F1 por clase, exactitud balanceada, F1 macro y matriz de confusión. Exactitud simple solo como dato secundario.
4. **El piso se compara en el mismo split** cuando sea posible, porque fue medido a nivel de foto completa y no de flor; si no se reevalúa, se aclara.
5. **Plantilla de informe en el chat:** qué se probó (datos, split, modelo), resultado (tabla por clase, matriz, piso), límites (n por clase, anotación única, tipo de caso).
6. **Casos desconocidos:** conjunto aparte de rosas reales, fotos impresas y fotos en pantalla, sin fotos nuevas del reto si no existen; el origen de estos casos se define en Open Questions.
7. **Advertencia fija de validez:** las métricas miden coincidencia con una sola anotación sin acuerdo medido.

## Risks / Trade-offs

- [Test chico: métricas con mucha varianza] → Mostrar n por clase y, si se puede, validación cruzada agrupada; no declarar victorias por diferencias pequeñas.
- [Anotación única, posibles errores de etiqueta] → Advertencia fija; revisar con experto los errores más claros de la matriz de confusión.
- [Piso medido a nivel de foto, no de flor] → Reevaluarlo en el nuevo split o aclarar la diferencia.
- [Sobreabierto no concluyente] → Se reporta tal cual; se trata como clase de baja confianza.

## Open Questions

- Umbrales de aceptación (por ejemplo, F1 mínimo por clase o exactitud balanceada mínima): pendiente de la sesión con expertos; no se inventan números.
- Forma de la prueba en vivo del jurado (cuántos casos, quién los elige, qué se mide): pendiente de la sesión con expertos.
- Tamaño del test y número de pliegues del split agrupado: se fija al ver la distribución de flores por foto.
- Origen de las fotos impresas y en pantalla para los casos desconocidos (¿se imprimen imágenes del reto o externas con licencia?).
