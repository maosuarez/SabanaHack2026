# per-flower-annotation Specification

## Purpose

Define cómo se anotan las rosas de las imágenes únicas del reto (caja + etapa por flor), con qué vocabulario y criterio, y cómo se controla la calidad. Estas anotaciones alimentan el detector, el clasificador y la evaluación.

## Requirements

### Requirement: Datos originales de solo lectura
El sistema SHALL tratar `data/raw/` como solo lectura. Toda anotación y todo derivado MUST escribirse en `data/annotations/`.

#### Scenario: Anotación guardada fuera de data/raw
- **WHEN** se exportan las anotaciones de una imagen
- **THEN** los archivos resultantes quedan en `data/annotations/` y ningún archivo de `data/raw/` cambia

### Requirement: Unidad de anotación por rosa
Cada rosa visible MUST tener una caja y una etapa. Las 56 imágenes únicas, incluidas las 8 fotos multiclase, MUST anotarse por flor y no por escena.

#### Scenario: Foto multiclase anotada por flor
- **WHEN** se anota una foto que aparece en más de una clase de origen (por ejemplo, la foto 26)
- **THEN** cada rosa recibe su propia caja y su propia etapa, sin heredar la etiqueta de la carpeta de origen

#### Scenario: Cobertura completa
- **WHEN** termina la anotación
- **THEN** las 56 imágenes únicas tienen al menos una revisión humana de sus cajas

### Requirement: Vocabulario de etapas
La etapa de cada rosa MUST ser una de: inmaduro, óptimo o sobreabierto. La anotación MUST usar estos nombres de clase y las señales visuales, y no los números de punto de la ficha técnica.

#### Scenario: Etapa válida
- **WHEN** una persona asigna una etapa a una rosa
- **THEN** el valor guardado es inmaduro, óptimo o sobreabierto

#### Scenario: Valor fuera del vocabulario
- **WHEN** una anotación tiene una etapa distinta de las tres permitidas y no está marcada "no anotable"
- **THEN** la validación de las anotaciones la rechaza

### Requirement: Registro por anotación
Cada anotación SHALL guardar el md5 de la imagen, la caja, la etapa, quién anotó y una marca de "dudosa".

#### Scenario: Anotación completa
- **WHEN** se guarda una anotación
- **THEN** contiene md5, caja, etapa, anotador y la marca de dudosa (verdadero o falso)

#### Scenario: Trazabilidad con el dataset
- **WHEN** se busca la imagen de una anotación
- **THEN** el md5 coincide con una fila de `data/raw/labels_imagen.csv`

### Requirement: Rosas no anotables
Una rosa demasiado pequeña o tapada para decidir su etapa SHALL marcarse "no anotable" y MUST NOT recibir una etapa forzada.

#### Scenario: Rosa tapada por hojas
- **WHEN** una rosa visible está tan tapada que no permite leer sus señales
- **THEN** conserva su caja, se marca "no anotable" y no tiene etapa

#### Scenario: Exclusión del entrenamiento de etapa
- **WHEN** se exportan las anotaciones para clasificar etapas
- **THEN** las rosas "no anotable" quedan identificables y separadas de las que tienen etapa

### Requirement: Marca de duda
Cuando una persona no pueda decidir entre dos etapas con las señales visibles, MUST marcar la flor como "dudosa" y SHALL asignar su mejor lectura.

#### Scenario: Flor dudosa
- **WHEN** las señales visibles no bastan para decidir con seguridad
- **THEN** la anotación lleva la etapa elegida y la marca de dudosa en verdadero

#### Scenario: Revisión de dudosas
- **WHEN** termina la anotación
- **THEN** existe una lista de las flores dudosas y de las que tienen desacuerdo entre anotadores, para revisarlas con un experto si es posible

### Requirement: Etapa asignada por una persona
La etapa de cada rosa MUST ser asignada por una persona. Un modelo MAY proponer cajas, pero MUST NOT proponer ni rellenar etapas.

#### Scenario: Cajas pre-anotadas sin etapa
- **WHEN** se importan al anotador cajas propuestas por el detector
- **THEN** llegan sin etapa y ninguna se da por válida hasta que una persona la revisa

### Requirement: Prueba piloto de pre-anotación
Antes de aplicar la pre-anotación a todo el dataset, el sistema MUST evaluarla en 5 fotos y registrar la fracción de rosas encontradas, el número de cajas falsas y el tiempo frente a dibujar a mano. Solo se adopta si resulta más rápida que dibujar a mano.

#### Scenario: Pre-anotación adoptada
- **WHEN** la piloto muestra que revisar las cajas propuestas es más rápido que dibujarlas a mano
- **THEN** la pre-anotación se usa en las demás fotos

#### Scenario: Pre-anotación descartada
- **WHEN** la piloto no muestra ahorro de tiempo
- **THEN** todas las cajas se dibujan a mano y no se usan las propuestas del detector

#### Scenario: Evidencia de la piloto
- **WHEN** termina la piloto
- **THEN** se reportan en el chat qué se probó, las tres medidas y los límites observados

### Requirement: Acuerdo entre anotadores
Dos personas SHALL anotar de forma independiente una muestra común de unas 10 fotos, sin sugerencias del detector, y se MUST reportar el acuerdo entre ellas. El resto de las fotos se reparte entre ambas.

#### Scenario: Muestra común sin sugerencias
- **WHEN** se anotan las fotos de la muestra común
- **THEN** ninguna caja proviene del detector y cada persona trabaja sin ver la anotación de la otra

#### Scenario: Reporte del acuerdo
- **WHEN** ambas terminan la muestra común
- **THEN** se informa el acuerdo en etapa sobre las cajas que coinciden, y los desacuerdos quedan en la lista de revisión

### Requirement: Informe de anotación
Al terminar, el sistema MUST informar en el chat el número de flores por etapa, el de "no anotable" y el de "dudosa", y marcar como no concluyente toda clase con menos de 5 flores.

#### Scenario: Informe final
- **WHEN** las 56 fotos están revisadas
- **THEN** el informe incluye el conteo por etapa, no anotables y dudosas, y señala las clases con menos de 5 flores
