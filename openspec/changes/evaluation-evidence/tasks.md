# Tasks

## 1. Split y reglas de evaluación

- [ ] 1.1 Generar el split por md5 con recortes de una foto del mismo lado y guardarlo (semilla y md5 por lado) en `data/annotations/`. Responsable posible: modelo/datos. Verificar: ningún md5 en dos lados y conteo de flores por clase y lado.
- [ ] 1.2 Marcar clases con menos de 5 ejemplos de prueba como no concluyentes. Responsable posible: modelo/datos. Verificar: el conteo por clase del test muestra la marca en sobreabierto si n < 5.

## 2. Métricas y piso

- [ ] 2.1 Preparar el cálculo de precisión, recall, F1 por clase, exactitud balanceada, F1 macro y matriz de confusión. Responsable posible: modelo/datos. Verificar: corre sobre predicciones de ejemplo y produce todas las salidas.
- [ ] 2.2 Reevaluar el piso (siempre-inmaduro, color+1NN, color+LogReg) sobre el nuevo split por flor, o documentar la diferencia con la medición por foto. Responsable posible: modelo/datos. Verificar: tabla del piso con las tres métricas.

## 3. Plantilla de evidencia

- [ ] 3.1 Fijar la plantilla de informe para el chat (qué se probó, resultado con tabla y matriz, límites) con la advertencia de anotación única sin acuerdo medido. Responsable posible: modelo/datos. Verificar: un informe de ejemplo sobre el piso cumple la plantilla.
- [ ] 3.2 Aplicar la plantilla tras cada prototipo de las Specs 3 y 4. Responsable posible: quien entregue el prototipo. Verificar: mensaje en el chat con las tres partes antes de cerrar la tarea.

## 4. Casos desconocidos

- [ ] 4.1 Reunir casos desconocidos de rosas reales, fotos impresas y fotos en pantalla (origen según Open Questions). Responsable posible: usuario. Verificar: lista de casos por tipo.
- [ ] 4.2 Correr la demo sobre los casos y reportar resultados separados por tipo. Responsable posible: usuario. Verificar: informe en el chat con resultados y límites por tipo.

## 5. Pendientes con expertos

- [ ] 5.1 Tras la sesión con expertos, fijar los umbrales de aceptación y la forma de la prueba del jurado, y actualizar `docs/decisiones-y-riesgos.md`. Responsable posible: usuario. Verificar: umbrales y forma de la prueba escritos en ese documento.
