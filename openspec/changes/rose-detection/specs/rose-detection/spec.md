# Spec Delta

## Purpose

Define el detector de rosas del núcleo de percepción: contrato de entrada y salida, evaluación comparada de candidatos sobre un conjunto de prueba reservado por md5, criterio de selección por métrica medida y el informe con resultados.

## ADDED Requirements

### Requirement: Contrato del detector
El detector SHALL recibir un frame y devolver una lista de cajas, cada una con su confianza. El detector MUST ser independiente de cualquier interfaz o cliente.

#### Scenario: Frame con varias rosas
- **WHEN** se entrega un frame con varias rosas
- **THEN** la salida es una lista con una caja y una confianza por rosa detectada

#### Scenario: Frame sin rosas
- **WHEN** el frame no contiene rosas
- **THEN** la salida es una lista vacía y no un error

### Requirement: Datos originales de solo lectura
El sistema SHALL tratar `data/raw/` como solo lectura. Todo derivado (split, predicciones, métricas) MUST escribirse fuera de `data/raw/`.

#### Scenario: Evaluación sin tocar los originales
- **WHEN** se corre cualquier evaluación
- **THEN** ningún archivo de `data/raw/` cambia

### Requirement: Split por md5
El conjunto de entrenamiento y el de prueba MUST separarse por md5 de imagen, de modo que todas las flores de una misma foto queden del mismo lado. El conjunto de prueba MUST ser el mismo para todos los candidatos.

#### Scenario: Sin fuga entre lados
- **WHEN** se construye el split
- **THEN** ningún md5 aparece a la vez en entrenamiento y en prueba

#### Scenario: Mismo test para todos
- **WHEN** se evalúan dos candidatos
- **THEN** ambos se miden sobre la misma lista de md5 de prueba

### Requirement: Comparación medida de candidatos
La elección del modelo SHALL basarse en una comparación medida de al menos OWLv2, Grounding DINO y un YOLO pequeño afinado con `data/annotations/flowers.csv` (178 cajas), sobre el mismo conjunto de prueba. Las flores marcadas "no anotable" MUST tratarse de forma explícita y la misma para todos los candidatos. Un candidato que no se pueda medir MUST reportarse como no medido, con el motivo.

#### Scenario: Candidato sin entrenar
- **WHEN** se evalúa OWLv2 o Grounding DINO
- **THEN** se usa el texto "rose" sin entrenamiento y se miden las mismas métricas que los demás

#### Scenario: YOLO afinado
- **WHEN** se afina el YOLO en Colab
- **THEN** solo usa cajas de los md5 de entrenamiento y se evalúa en el test reservado

#### Scenario: Candidato no medido
- **WHEN** un candidato no puede evaluarse a tiempo
- **THEN** el informe lo lista como no medido y no se usa para elegir

### Requirement: Métricas por candidato
Para cada candidato el sistema MUST reportar el recall a IoU 0.5, las cajas falsas por imagen y la latencia en CPU. El sistema SHALL reportar mAP cuando aplique al candidato. La latencia MUST medirse en el portátil de la demo.

#### Scenario: Tabla comparativa
- **WHEN** termina la evaluación
- **THEN** existe una tabla con una fila por candidato y las métricas anteriores, calculadas sobre los mismos md5

#### Scenario: Latencia en el portátil
- **WHEN** se mide la velocidad
- **THEN** el valor proviene de inferencia en CPU del portátil de la demo, no de Colab

### Requirement: Casos difíciles reportados
La evaluación MUST reportar el desempeño por condición visible en el test: contraluz, flores pequeñas, oclusión por hojas o alambres y varias rosas por foto, indicando cuántas imágenes tiene cada condición.

#### Scenario: Límites por condición
- **WHEN** se publica el informe
- **THEN** incluye cómo rindió cada candidato en cada condición y el número de imágenes de esa condición

### Requirement: Selección por métrica medida
El modelo base SHALL elegirse por las métricas medidas y no por preferencia. El informe MUST justificar la elección frente a los demás candidatos y MUST indicar la brecha medida.

#### Scenario: Modelo elegido
- **WHEN** se decide el modelo base
- **THEN** el informe nombra el modelo, las métricas que lo respaldan y el motivo frente a cada alternativa

### Requirement: Umbral mínimo propuesto con la medición
El umbral mínimo aceptable MUST proponerse a partir de la medición del test y NO SHALL fijarse de antemano. Hasta que el usuario lo confirme, el umbral permanece como pregunta abierta.

#### Scenario: Propuesta de umbral
- **WHEN** hay resultados del test
- **THEN** el informe propone un umbral citando la medición que lo sustenta y pide confirmación

### Requirement: Registro de licencia
Antes de adoptar un modelo, el sistema MUST registrar su licencia verificada en el repositorio oficial. Si el candidato elegido usa Ultralytics (AGPL-3.0), el informe MUST anotar el riesgo de licencia.

#### Scenario: Candidato Ultralytics
- **WHEN** el YOLO elegido proviene de Ultralytics
- **THEN** el informe indica la licencia AGPL-3.0 y el riesgo para su uso

### Requirement: Informe con resultados en el chat
Al terminar cada prototipo se MUST reportar en el chat qué se probó, el resultado con métricas y los límites observados. El informe MUST incluir el piso de referencia de que no hay medición previa de detección y las limitaciones del test (tamaño, una sola variedad, un solo anotador).

#### Scenario: Informe completo
- **WHEN** se entrega el informe
- **THEN** contiene qué se probó, tabla de métricas por candidato, desempeño por condición, límites y el modelo elegido

### Requirement: Cómputo repartido
El entrenamiento y la evaluación pesada SHALL correr en Colab. La inferencia de la demo MUST correr en CPU.

#### Scenario: Inferencia en CPU
- **WHEN** el modelo elegido se prueba para la demo
- **THEN** corre en CPU sin requerir GPU
