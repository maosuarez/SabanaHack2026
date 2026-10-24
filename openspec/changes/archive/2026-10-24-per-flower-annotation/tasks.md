# Tasks

## 1. Preparación del anotador

- [x] 1.1 Instalar Label Studio y crear el proyecto con una tarea por imagen única (56), leyendo `data/raw/images/` sin modificarla. Responsable posible: anotador A. Verificar: el proyecto muestra 56 tareas y `git status` no reporta cambios en `data/raw/`.
- [x] 1.2 Configurar la interfaz: caja por rosa, elección de etapa (inmaduro / óptimo / sobreabierto) y atributos "dudosa" y "no anotable". Responsable posible: anotador A. Verificar: anotar una rosa de prueba y comprobar que el JSON exportado trae caja, etapa y ambos atributos.
- [x] 1.3 Escribir la guía de criterio (señales de la ficha y regla "ante la duda, dudosa") en la descripción del proyecto de Label Studio, con nombres de clase y sin números de punto. Responsable posible: anotador B. Verificar: la guía se ve en la pantalla de anotación.
- [x] 1.4 Confirmar en los repositorios oficiales la licencia de Grounding DINO y OWL-ViT. Responsable posible: usuario. Verificar: licencia anotada en el chat con enlace al LICENSE.

## 2. Prueba piloto de pre-anotación (5 fotos)

- [x] 2.1 Escoger 5 fotos para la piloto: una multiclase, una con rosas muy pequeñas y tres típicas. Responsable posible: usuario. Verificar: lista de 5 md5 en el chat.
- [ ] 2.2 Correr el detector de vocabulario abierto con el texto "rose" en Colab (o CPU, si el usuario lo prefiere) sobre las 5 fotos y generar el JSON de predicciones. Responsable posible: usuario. Verificar: el JSON se importa en Label Studio y las cajas aparecen sobre las imágenes. **No realizada como se describe:** el script y la importación en 5 fotos quedaron hechos (OWLv2, CPU), pero no se verificó en la interfaz ni se adoptó la pre-anotación.
- [ ] 2.3 Medir en las 5 fotos: fracción de rosas encontradas, cajas falsas y tiempo de revisar las propuestas frente a dibujar a mano. Responsable posible: usuario. Verificar: tabla con las tres medidas por foto. **No realizada:** la anotación se hizo a mano sin cronometrar ni medir cobertura del detector.
- [ ] 2.4 Evidencia de la piloto: reportar en el chat qué se probó, las medidas, los límites observados y la decisión (adoptar la pre-anotación o anotar a mano). Responsable posible: usuario. Verificar: mensaje en el chat con las cuatro partes y la decisión explícita. **No realizada:** sin medidas no hay decisión formal; se anotó a mano.

## 3. Anotación

- [ ] 3.1 Si la piloto adoptó la pre-anotación, generar el JSON de predicciones del resto de las fotos e importarlo en Label Studio. Responsable posible: usuario. Verificar: las 56 tareas muestran cajas propuestas y ninguna trae etapa. Omitir si se anota a mano. **No realizada:** se anotó a mano.
- [ ] 3.2 Anotar la muestra común (~10 fotos, incluidas las multiclase posibles) de forma independiente por dos personas y sin cajas del detector. Responsable posible: anotadores A y B. Verificar: dos exportaciones separadas de las mismas ~10 fotos, sin cajas del detector. **Cerrada por decisión del usuario:** no se hará doble anotación; se trabaja con lo anotado por la primera cuenta.
- [ ] 3.3 Medir el acuerdo en etapa entre A y B sobre las cajas que coinciden por IoU y listar los desacuerdos. Responsable posible: anotador B. Verificar: reporte con el acuerdo, el IoU de emparejamiento usado y la lista de desacuerdos. **No realizada:** sin segunda anotación no hay acuerdo medible. **Cerrada por decisión del usuario:** no se hará doble anotación; se trabaja con lo anotado por la primera cuenta.
- [ ] 3.4 Anotar las fotos restantes repartidas entre A y B, empezando por las 8 multiclase (5 si ya se cubrieron en 3.2). Máximo 2 h por bloque. Responsable posible: anotadores A y B. Verificar: las 56 imágenes tienen sus cajas revisadas por una persona. **Cubierta (decisión del usuario: se trabaja con la primera cuenta):** las 56 fotos fueron anotadas con ayuda del equipo, pero todo quedó bajo una sola cuenta de Label Studio (`user1`); no se sabe quién anotó qué ni hubo doble anotación.
- [ ] 3.5 Revisar las flores dudosas y los desacuerdos con un experto si es posible; si no, resolver entre A y B. Responsable posible: anotadores A y B. Verificar: cada elemento de la lista tiene una etapa final o queda marcado dudoso. **No realizada:** sin experto ni segundo anotador; 0 dudosas marcadas. **Cerrada por decisión del usuario:** no se hará doble anotación; se trabaja con lo anotado por la primera cuenta.

## 4. Exportación y control de calidad

- [x] 4.1 Exportar el JSON de Label Studio a `data/annotations/` y generar `data/annotations/flowers.csv` con md5, image_id, caja, etapa, dudosa, anotable y anotador. Responsable posible: usuario. Verificar: todo md5 del CSV existe en `data/raw/labels_imagen.csv`.
- [x] 4.2 Validar las anotaciones: etapas dentro del vocabulario, cajas dentro de la imagen, "no anotable" sin etapa y ninguna foto de las 56 sin anotaciones. Responsable posible: usuario. Verificar: el chequeo corre sin errores sobre `flowers.csv`.
- [x] 4.3 Confirmar que `data/raw/` no cambió. Responsable posible: usuario. Verificar: `git status` y `git diff --stat -- data/raw` vacíos.

## 5. Evidencia y documentación

- [x] 5.1 Informe final en el chat: flores por etapa, no anotables, dudosas, acuerdo entre anotadores, clases con menos de 5 flores marcadas como no concluyentes y límites observados. Responsable posible: usuario. Verificar: mensaje con todos los conteos que coincidan con `flowers.csv`.
- [x] 5.2 Actualizar `docs/decisiones-y-riesgos.md` y `docs/dominio-y-dataset.md`: Label Studio como herramienta, anotación por flor completada, videos y fotogramas excluidos, vocabulario sin numeración de puntos. Responsable posible: anotador B. Verificar: revisar el diff de ambos archivos y confirmar que no quedan frases sobre fotogramas de video como fuente.
