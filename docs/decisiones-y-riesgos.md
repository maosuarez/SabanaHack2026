# Decisiones y riesgos

## Decisiones tomadas
1. El núcleo es un servicio de percepción que no depende de la interfaz. Las Quest 3 son el primer cliente y el robot es un cliente futuro que usa el mismo contrato. *(obsoleto por decisión 2026-10-24)*
2. Dos problemas guían todo: la capacitación que se repite por la rotación y la incertidumbre del novato frente a la flor.
3. La realidad aumentada funciona como **tutor, no como juez**:
   - En modo Entrenar, la persona decide primero y después el sistema revela su lectura y el porqué.
   - En modo Asistir, el sistema confirma o advierte, siempre mostrando la confianza.
4. Hay tres salidas posibles: *cortar*, *no cortar* y *zona gris → consultar*.
5. Herramienta de anotación: Label Studio en proyecto local (config en `tools/annotation/label_config.xml`). Anotación por flor completada en `data/annotations/flowers.csv`: 178 flores en 56 fotos (inmaduro 128, óptimo 41, sobreabierto 9; dudosas 0; no anotables 0). Una sola cuenta de anotación (`user1`; el equipo ayudó, sin registro por persona), sin experto. La pre-anotación con OWLv2 solo se probó en 5 fotos, sin medir; la anotación final es a mano.
6. Los videos y los fotogramas quedan excluidos como fuente de datos. El vocabulario de etapas no usa numeración de puntos: inmaduro / optimo / sobreabierto.
7. Propuesta, no confirmada: DINOv2 como extractor para el clasificador por flor; el color vendrá de un sensor aparte (actividad separada). Sobreabierto (9 flores) es poco concluyente.
8. Argumento de la parte robótica:
   - Un robot sobre rieles recorre las camas antes del turno y arma un mapa de qué flores están listas hoy y cuáles lo estarán mañana. El cortador llega guiado por ese mapa.
   - Lo que aporta: memoria temporal de cada flor, consistencia entre camas y datos que alimentan la capacitación.
9. Decisión del usuario (2026-10-24): Quest y Unity ya NO se usan.
   - La capacitación (VR / modo Entrenar) se hace con una página HTML que el usuario construye aparte, fuera de este repo.
   - Este repo queda solo con la sección del modelo de detección y clasificación de rosas. Su rol: subsanar la inseguridad incluso de una persona ya capacitada (modo Asistir). Es análisis de resultados y propuesta de la AR futura, no una demo AR en vivo.
   - Consecuencias: ya no hay cliente Quest/MRUK ni requisito de inferencia en vivo; el pendiente "framework XR" queda descartado; la latencia en CPU es un dato para la propuesta de AR, no un requisito de demo.
   - Specs vigentes: 3 (detector), 4 (clasificador), 6 (evaluación). Spec 2 (ampliar dataset) condicional. Spec 5 (rasgos/explicación) se mantiene como parte del contrato, sin interfaz propia.

## Prioridad de alcance (20 h)
1. Modelo de detección y clasificación por flor, con confianza y explicación, corriendo en el portátil con webcam.
2. Cliente AR/MR en las Quest 3 consumiendo ese modelo, con casting a pantalla para el jurado. *(obsoleto por decisión 2026-10-24)*
3. Modo Entrenar sobre rosas o fotos reales. *(fuera de este repo: página HTML aparte; decisión 2026-10-24)*
4. Riel físico mínimo: cámara sobre un slider con Arduino que genera el mapa de una fila.
5. Invernadero en VR inmersivo: solo si sobra tiempo. Si no, se presenta como concepto.

## Riesgos y mitigación
| Riesgo | Mitigación |
|---|---|
| Alcance demasiado grande (VR + AR + CV + robot) | Seguir la prioridad de arriba. Tener un demo mínimo estable antes de sumar funciones |
| El "visto bueno" crea dependencia en vez de criterio | Modo Entrenar (decidir primero, luego revelar) y explicación por rasgos |
| Dataset pequeño (56 fotos, 178 flores; sobreabierto solo 9, poco concluyente) | Anotación por flor ya hecha; split por md5; aumentación; comparar un VLM con prompt basado en la ficha técnica contra un modelo ajustado. Los videos y fotogramas quedan fuera como fuente de datos |
| Anotación hecha por el equipo bajo una sola cuenta (`user1`, sin registro de quién anotó qué), sin experto, sin doble anotación ni acuerdo entre anotadores medido; 0 dudosas y 0 no anotables es sospechoso (posible sobreconfianza) | Doble anotación descartada por decisión del usuario; pendiente revisión por experto y contraste con los modelos. Mientras tanto, reportar los límites |
| Prueba en vivo desconocida (rosas reales, fotos impresas o en pantalla) | Probar los tres formatos; respaldo en portátil; conocer y exponer los límites |
| Cámara passthrough de las Quest: resolución y fidelidad del rojo limitadas *(obsoleto por decisión 2026-10-24)* | Probar con rosas rojas reales antes del evento; usar el tono como rasgo, nunca como único criterio |
| Latencia o Wi-Fi si la inferencia corre en un servidor *(obsoleto por decisión 2026-10-24)*; la latencia en CPU queda como dato para la propuesta | Red local propia (hotspot); medir la latencia; considerar inferencia en el dispositivo |
| Viabilidad en campo: Quest en invernadero (peso, unas 2 h de batería, calor, humedad, tijeras, equipos compartidos, costo) *(obsoleto por decisión 2026-10-24)* | Presentar las Quest como medio de capacitación y prototipo; en campo, migrar a un celular o una cámara de clip |
| El panel valora la pertinencia robótica (15 pts) | Arquitectura con varios clientes visible en el pitch; riel mínimo si alcanza el tiempo |
| La premisa de la rotación no está validada | Sustentarla con lo que salió de la sesión de preguntas (pendiente) |
| La novedad tecnológica es baja por separado | Vender lo original: aprender decidiendo, lectura temporal con el robot, ciclo campo → capacitación |

## Pendiente de definir
- ~~El framework XR: Unity + Meta XR SDK, Meta Spatial SDK o WebXR.~~ Descartado: sin Quest/Unity (decisión 2026-10-24).
- El modelo base: detector tipo YOLO, VLM o un enfoque híbrido (la anotación por flor ya está; falta elegir).
- ~~Dónde corre la inferencia: en el dispositivo o en un servidor local.~~ Obsoleto: sin inferencia en vivo (decisión 2026-10-24).
- Lo que salió de la sesión de preguntas con los expertos.
- Confirmar DINOv2 como extractor y el sensor de color aparte (hoy solo propuestos).
- Doble anotación: cerrada por decisión del usuario (no se hará). Se trabaja con lo anotado por la primera cuenta y, si hace falta, se contrasta con los modelos.
