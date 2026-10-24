# Tasks

## 1. Preparación

- [x] 1.1 Generar el split por md5 a partir de `data/annotations/flowers.csv` y guardar la lista de md5 de prueba fuera de `data/raw/`. Responsable posible: persona de datos. Verificar: ningún md5 está en ambos lados y el conteo de imágenes y flores por lado queda en el chat.
- [ ] 1.2 Etiquetar a mano las condiciones de cada imagen de prueba (contraluz, pequeñas, oclusión, varias rosas). Responsable posible: persona de datos. Verificar: tabla con el número de imágenes por condición.
- [x] 1.3 Escribir el evaluador: recall a IoU 0.5, cajas falsas por imagen y mAP si aplica, con la regla de "no anotable" elegida. Responsable posible: persona de modelo. Verificar: prueba con cajas de referencia como predicción da recall 1 y 0 falsas.
- [x] 1.4 Confirmar licencias de OWLv2, Grounding DINO y del YOLO candidato en sus repositorios oficiales. Responsable posible: usuario. Verificar: licencias y enlaces al LICENSE en el chat; si es Ultralytics, anotar AGPL-3.0.

## 2. Candidatos sin entrenar

- [x] 2.1 Correr OWLv2 con el texto "rose" sobre el test y guardar predicciones. Responsable posible: persona de modelo (Colab). Verificar: archivo de predicciones por md5 y métricas calculadas.
- [x] 2.2 Correr Grounding DINO con el texto "rose" sobre el mismo test. Responsable posible: persona de modelo (Colab). Verificar: archivo de predicciones por md5 y métricas calculadas.
- [x] 2.3 Fijar el umbral de confianza de cada uno sin usar el test. Responsable posible: persona de modelo. Verificar: el umbral y la imagen o conjunto usado para fijarlo quedan escritos.

## 3. Candidato afinado

- [ ] 3.1 Afinar un YOLO pequeño en Colab con las cajas de los md5 de entrenamiento y aumentación solo en entrenamiento. Responsable posible: persona de modelo. Verificar: curva de entrenamiento y que ningún md5 de prueba se usó.
- [ ] 3.2 Evaluar el YOLO en el test y guardar predicciones. Responsable posible: persona de modelo. Verificar: mismas métricas que 2.1 y 2.2.
- [ ] 3.3 (Opcional) Probar un híbrido si sobra tiempo. Responsable posible: persona de modelo. Verificar: mismas métricas o marcado como no medido.

## 4. Velocidad y elección

- [ ] 4.1 Medir la latencia en CPU de cada candidato en el portátil de la demo, en frío y en caliente. Responsable posible: persona de integración. Verificar: tabla con tiempo por frame y tamaño de entrada.
- [ ] 4.2 Armar la tabla comparativa y el desglose por condición. Responsable posible: persona de modelo. Verificar: una fila por candidato sobre los mismos md5 y conteo por condición.
- [ ] 4.3 Elegir el modelo base por la métrica medida y proponer el umbral mínimo con la medición. Responsable posible: usuario. Verificar: elección justificada frente a cada alternativa y umbral propuesto pendiente de confirmación.

## 5. Evidencia y documentación

- [ ] 5.1 Informe con resultados en el chat: qué se probó, tabla de métricas, desempeño por condición, límites (test pequeño, una variedad, un anotador), licencias, riesgo AGPL si aplica y modelo elegido. Responsable posible: usuario. Verificar: mensaje con todas las partes y cifras que coincidan con los archivos de resultados.
- [ ] 5.2 Confirmar que `data/raw/` no cambió. Responsable posible: usuario. Verificar: `git status` y `git diff --stat -- data/raw` vacíos.
- [ ] 5.3 Actualizar `docs/decisiones-y-riesgos.md` con el modelo elegido, la licencia y el estado del umbral. Responsable posible: usuario. Verificar: revisar el diff y confirmar que no se crean archivos `.md` nuevos.
