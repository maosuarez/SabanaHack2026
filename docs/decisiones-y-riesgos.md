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
10. Decisión del usuario (2026-10-24): la **versión VR** del ambiente completo del invernadero vive en `tools/ar-flores/index.html` (Three.js 0.160 + WebXR `immersive-vr`/`immersive-ar`, ya con modo Entrenar). Matiza la decisión 9 en lo que toca a la página HTML: sí está en este repo.
   - Toda ampliación es **solo aditiva**: no se quita ni se rompe nada de lo que ya funciona.
   - Adiciones previstas: tallos con diámetro y longitud + calibrador; corte con tijeras por mando (gatillo, ángulo, háptica); desnuque, duplicación y tinta; puntaje por criterios (100 pts, niveles básico/intermedio/avanzado); tarjetas didácticas de los 10 ítems de control.
   - Los valores [estimado] (calibre 7 mm, bisel 45° ±15°, distribución de diámetros, pesos del puntaje) son configurables.
11. Datos de la sesión con los expertos de la finca:
   - Tocón ≤ 0,5 cm sobre la yema (largo alarga el ciclo y trae problemas de sanidad).
   - Zona de corte: franja de 110–140 cm del suelo; producción continua (planta perenne, hasta 20 años).
   - Tallo cortado ≥ 47 cm con cabeza (puede llegar a 60–80 cm); cuerdas guía para que crezca derecho (torcido no exporta).
   - Desnuque: la hoja de la yema no se corta, se desprende parcialmente para activar la yema.
   - Duplicación: en tallo grueso, desnuque a dos hojas → dos flores.
   - Tinta: cubrir completamente el corte (desinfección).
   - Desgarre: el corte debe ser limpio, de un solo movimiento, con tijera en buen estado.
   - Calibre: se mide con un calibrador ("un lápiz amarillo"); a tallos bajo calibre no se les pone la tijera.
   - Hoja verdadera = 5 folíolos (referencia para ubicar el corte).
   - Cortar en zigzag, alternando lados, para no desequilibrar la planta.
   - La finca usa 10 ítems de control del corte en un programa interno (nombre transcrito como "Meteor", dudoso).
12. Modelo base del detector (2026-10-24): RT-DETR r50vd afinado (PekingU/rtdetr_r50vd, Apache-2.0 en código y checkpoint; evita AGPL de Ultralytics). Test de 11 imágenes / 24 flores: recall 0,79, 0,82 falsas por imagen, AP 0,92, ~1,4 s por imagen en CPU de esta máquina; Grounding DINO 0,62 / 0,55 / 0,71 / 5,9 s; OWLv2 0,50 / 1,00 / 0,49 / 7,8 s. Umbral PROPUESTO 0,48 (fijado con 9 imágenes de validación; ruidoso) — PENDIENTE de confirmación del usuario. Límites: test pequeño, una cuenta de anotación, una variedad, sobreajuste desde la época 20, checkpoint (164 MB) solo en outputs/ local, sin generalización probada.

## Prioridad de alcance (20 h)
1. Modelo de detección y clasificación por flor, con confianza y explicación, corriendo en el portátil con webcam.
2. Cliente AR/MR en las Quest 3 consumiendo ese modelo, con casting a pantalla para el jurado. *(obsoleto por decisión 2026-10-24)*
3. Modo Entrenar sobre rosas o fotos reales. *(fuera de este repo: página HTML aparte; decisión 2026-10-24)* *(obsoleto por decisión 10: vive en `tools/ar-flores/index.html`)*
4. Riel físico mínimo: cámara sobre un slider con Arduino que genera el mapa de una fila.
5. Invernadero en VR inmersivo: solo si sobra tiempo. Si no, se presenta como concepto. *(obsoleto por decisión 10)*
6. Versión VR en `tools/ar-flores/index.html` (decisión 10): primero lo que ya funciona estable; luego, en orden y solo aditivo: tallos y calibrador → corte con tijeras y puntaje (nivel básico) → tocón/ángulo/desgarre → desnuque, duplicación y tinta → tarjetas didácticas.

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
| Las adiciones VR rompen la escena que ya funciona | Cambios solo aditivos; probar el flujo existente tras cada adición; valores [estimado] configurables |
| La novedad tecnológica es baja por separado | Vender lo original: aprender decidiendo, lectura temporal con el robot, ciclo campo → capacitación |

## Pendiente de definir
- ~~El framework XR: Unity + Meta XR SDK, Meta Spatial SDK o WebXR.~~ Descartado: sin Quest/Unity (decisión 2026-10-24).
- ~~El modelo base: detector tipo YOLO, VLM o un enfoque híbrido.~~ Resuelto: RT-DETR r50vd afinado (decisión 12).
- Umbral mínimo de confianza del detector: propuesto 0,48, pendiente de confirmación del usuario (decisión 12).
- ~~Dónde corre la inferencia: en el dispositivo o en un servidor local.~~ Obsoleto: sin inferencia en vivo (decisión 2026-10-24).
- Lo que salió de la sesión de preguntas con los expertos. Resuelto en parte: criterios del corte registrados en la decisión 11.
- Ángulo de corte esperado por la finca (hoy supuesto: bisel de 45° alejado de la yema).
- Calibre mínimo exacto en mm (hoy supuesto: unos 7 mm, el diámetro de un lápiz).
- Cuántas hojas verdaderas deben quedar por encima o por debajo del corte.
- Si un tallo bajo calibre con la flor en punto se corta o no.
- Nombre correcto del programa interno de los 10 ítems de control.
- Confirmar DINOv2 como extractor y el sensor de color aparte (hoy solo propuestos).
- Doble anotación: cerrada por decisión del usuario (no se hará). Se trabaja con lo anotado por la primera cuenta y, si hace falta, se contrasta con los modelos.
