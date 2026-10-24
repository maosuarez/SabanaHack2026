# Tasks

## 1. Prerrequisitos

- [ ] 1.1 Confirmar que la Spec 4 entrega etapa, confianza, zona gris y reencuadrar sobre un conjunto de prueba. Responsable posible: usuario. Verificar: salidas de ejemplo disponibles.
- [ ] 1.2 Registrar en `docs/decisiones-y-riesgos.md` las Open Questions de `design.md` (ángulos/proporciones, profundidad, cálculo de rasgos). Responsable posible: usuario. Verificar: diff del archivo, sin crear `.md` nuevos.

## 2. Rasgos

- [ ] 2.1 Definir el esquema de `rasgos[]` (sépalos, caracol, tamaño de cabeza, tono; valores descriptivos, "no determinable", "no disponible"). Responsable posible: anotador A. Verificar: esquema revisado contra la ficha, sin ángulos ni proporciones.
- [ ] 2.2 Elegir con el equipo y el experto el cálculo de cada rasgo (visión clásica, VLM o aprendido). Bloqueada por la Open Question. Verificar: decisión registrada.
- [ ] 2.3 Implementar el cálculo de rasgos y probarlo en recortes de prueba. Responsable posible: usuario. Verificar: tabla de rasgos por recorte revisada a ojo.

## 3. Explicación

- [ ] 3.1 Redactar plantillas con la terminología de la ficha para inmaduro, óptimo, sobreabierto, zona gris y reencuadrar. Responsable posible: anotador B. Verificar: sin números de punto, cita más de un rasgo.
- [ ] 3.2 Integrar `rasgos[]` y `explicacion` al contrato por rosa y verificar coherencia con etapa y confianza. Responsable posible: usuario. Verificar: casos de abstención con motivo.
- [ ] 3.3 Medir latencia de la explicación en CPU del portátil de la demo. Responsable posible: usuario. Verificar: tiempo reportado.

## 4. Mapa de calor

- [ ] 4.1 Implementar atención CLS del último bloque y oclusión como herramientas de depuración. Responsable posible: usuario. Verificar: ambos mapas para las mismas predicciones.
- [ ] 4.2 Prueba comparativa: revisar a ojo si cada mapa resalta la flor o el fondo, cielo y alambres; medir costo en CPU. Responsable posible: anotadores A y B. Verificar: tabla por método y método elegido.
- [ ] 4.3 Comprobar que la salida al usuario no incluye el mapa. Responsable posible: usuario. Verificar: salida de ejemplo sin mapa.

## 5. Evidencia y validación

- [ ] 5.1 Revisar ejemplos de explicaciones con un experto, si es posible. Responsable posible: usuario. Verificar: comentarios registrados o límite anotado.
- [ ] 5.2 Informe en el chat: predicciones de ejemplo por etapa (con zona gris y reencuadrar), rasgos, explicación, mapa para el equipo, método elegido, resultados y límites, incluida la aclaración de que el mapa no es causal. Responsable posible: usuario. Verificar: mensaje con las partes completas.
- [ ] 5.3 Actualizar `docs/decisiones-y-riesgos.md` con decisiones resueltas. Verificar: diff del archivo.
