# Tasks

## 1. Línea base de conteos

- [x] 1.1 Calcular el conteo de flores por etapa y de fotos por etapa desde `data/annotations/flowers.csv`, y definir el split por md5 con los recortes de una misma foto del mismo lado. Responsable posible: persona de datos A. Verificar: tabla por etapa y por lado del split que suma 178 flores y 56 fotos, sin ningún md5 en dos lados.
- [x] 1.2 Escribir un chequeo de fuga que falle si un md5 aparece en más de un lado del split. Responsable posible: persona de datos A. Verificar: el chequeo pasa sobre el split real y falla en un caso de prueba construido a propósito.

## 2. Aumentación solo en entrenamiento

- [x] 2.1 Definir la configuración de aumentación con los límites globales (rotación ±30°, zoom, brillo y contraste leves, sin cambios fuertes de tono) y aplicarla solo al lado de entrenamiento. Responsable posible: persona de datos A. Verificar: la configuración se ve en un solo lugar y una muestra de 20 recortes aumentados no muestra cambios de tono fuertes.
- [x] 2.2 Agregar la validación que rechaza cualquier derivado de validación o prueba en entrenamiento. Responsable posible: persona de datos B. Verificar: el chequeo pasa y falla con un caso de prueba construido a propósito.
- [ ] 2.3 Generar el conjunto aumentado en `data/processed/` (o definirlo al vuelo) y reportar conteos antes y después por etapa. Responsable posible: persona de datos B. Verificar: los conteos reportados coinciden con los archivos generados y `git status -- data/raw` está vacío.
- [ ] 2.4 Evidencia de la aumentación: reportar en el chat qué se probó, los conteos antes y después, y los límites (9 flores de sobreabierto siguen siendo 9 ejemplos reales). Responsable posible: persona de datos B. Verificar: mensaje en el chat con las tres partes.

## 3. Decisión sobre externas

- [ ] 3.1 Con la medición del clasificador sobre flores propias y aumentación (cuando exista en la Spec 4), decidir si alguna clase sigue faltando y cuál. Responsable posible: usuario. Verificar: decisión escrita en el chat con la métrica por clase que la sustenta; sin esa medición, no se abren externas.
- [ ] 3.2 Verificar licencia y contenido de los candidatos (Mendeley Data 53vyvz5yyk y Roboflow "bud detection") en la fuente oficial, y confirmar el descarte de RoseBlooming y del dataset de Frontiers 2025. Responsable posible: persona de datos A. Verificar: por candidato, licencia y enlace anotados en el chat, y si sirve para etapa, para detector o para ninguno. Solo si 3.1 concluyó que falta una clase.

## 4. Imágenes externas (condicional a 3.1)

- [ ] 4.1 Crear el registro de externas en `data/annotations/` con las columnas URL, licencia, autor, fecha de acceso, etiqueta, md5 y estado. Responsable posible: persona de datos A. Verificar: el archivo existe con el encabezado y una fila de ejemplo válida.
- [ ] 4.2 Descargar y revisar a ojo hasta un tope de tiempo de 2 h por bloque; admitir solo rosa roja, vista comparable y licencia CC0, dominio público o CC BY; etiquetar con el criterio de la ficha. Responsable posible: personas de datos A y B (idealmente con experto). Verificar: cada imagen admitida tiene todos los campos del registro; las demás figuran descartadas con motivo.
- [ ] 4.3 Validar el registro y el split: ninguna fila sin licencia válida, ninguna externa en prueba. Responsable posible: persona de datos B. Verificar: el chequeo pasa sin errores.
- [ ] 4.4 Medir en validación con flores propias si las externas ayudan; conservarlas solo si mejoran la clase faltante. Responsable posible: usuario. Verificar: métricas por clase con y sin externas en el chat.

## 5. Evidencia y documentación

- [ ] 5.1 Informe final en el chat: conteo por clase antes y después (propias, aumentadas, externas), lista de atribuciones de las externas admitidas, sobreabierto marcado no concluyente y límites observados. Responsable posible: usuario. Verificar: los conteos coinciden con los archivos y cada externa tiene su fila de registro.
- [ ] 5.2 Actualizar `docs/decisiones-y-riesgos.md`: sobreabierto como clase de baja confianza, política de aumentación y de externas, y el resultado de la decisión 3.1. Responsable posible: persona de datos B. Verificar: revisar el diff del archivo y confirmar que no se creó ningún `.md` nuevo.
