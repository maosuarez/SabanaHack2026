# Decisiones y riesgos

## Decisiones tomadas
1. El núcleo es un servicio de percepción que no depende de la interfaz. Las Quest 3 son el primer cliente y el robot es un cliente futuro que usa el mismo contrato.
2. Dos problemas guían todo: la capacitación que se repite por la rotación y la incertidumbre del novato frente a la flor.
3. La realidad aumentada funciona como **tutor, no como juez**:
   - En modo Entrenar, la persona decide primero y después el sistema revela su lectura y el porqué.
   - En modo Asistir, el sistema confirma o advierte, siempre mostrando la confianza.
4. Hay tres salidas posibles: *cortar*, *no cortar* y *zona gris → consultar*.
5. Argumento de la parte robótica:
   - Un robot sobre rieles recorre las camas antes del turno y arma un mapa de qué flores están listas hoy y cuáles lo estarán mañana. El cortador llega guiado por ese mapa.
   - Lo que aporta: memoria temporal de cada flor, consistencia entre camas y datos que alimentan la capacitación.

## Prioridad de alcance (20 h)
1. Modelo de detección y clasificación por flor, con confianza y explicación, corriendo en el portátil con webcam.
2. Cliente AR/MR en las Quest 3 consumiendo ese modelo, con casting a pantalla para el jurado.
3. Modo Entrenar sobre rosas o fotos reales.
4. Riel físico mínimo: cámara sobre un slider con Arduino que genera el mapa de una fila.
5. Invernadero en VR inmersivo: solo si sobra tiempo. Si no, se presenta como concepto.

## Riesgos y mitigación
| Riesgo | Mitigación |
|---|---|
| Alcance demasiado grande (VR + AR + CV + robot) | Seguir la prioridad de arriba. Tener un demo mínimo estable antes de sumar funciones |
| El "visto bueno" crea dependencia en vez de criterio | Modo Entrenar (decidir primero, luego revelar) y explicación por rasgos |
| Dataset pequeño, etiquetado por escena, con 2 imágenes de sobreabierto | Re-anotar por flor; split por md5; aumentación; frames de los videos; comparar un VLM con prompt basado en la ficha técnica contra un modelo ajustado |
| Prueba en vivo desconocida (rosas reales, fotos impresas o en pantalla) | Probar los tres formatos; respaldo en portátil; conocer y exponer los límites |
| Cámara passthrough de las Quest: resolución y fidelidad del rojo limitadas | Probar con rosas rojas reales antes del evento; usar el tono como rasgo, nunca como único criterio |
| Latencia o Wi-Fi si la inferencia corre en un servidor | Red local propia (hotspot); medir la latencia; considerar inferencia en el dispositivo |
| Viabilidad en campo: Quest en invernadero (peso, unas 2 h de batería, calor, humedad, tijeras, equipos compartidos, costo) | Presentar las Quest como medio de capacitación y prototipo; en campo, migrar a un celular o una cámara de clip |
| El panel valora la pertinencia robótica (15 pts) | Arquitectura con varios clientes visible en el pitch; riel mínimo si alcanza el tiempo |
| La premisa de la rotación no está validada | Sustentarla con lo que salió de la sesión de preguntas (pendiente) |
| La novedad tecnológica es baja por separado | Vender lo original: aprender decidiendo, lectura temporal con el robot, ciclo campo → capacitación |

## Pendiente de definir
- El framework XR: Unity + Meta XR SDK, Meta Spatial SDK o WebXR.
- El modelo base: detector tipo YOLO, VLM o un enfoque híbrido.
- Dónde corre la inferencia: en el dispositivo o en un servidor local.
- Lo que salió de la sesión de preguntas con los expertos.
