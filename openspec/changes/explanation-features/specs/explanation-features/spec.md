# Spec Delta

## Purpose

Define los rasgos por rosa, el texto de explicación en lenguaje del cortador y el mapa de calor de depuración. Toda salida de etapa de la Spec 4 sale acompañada de rasgos y porqué.

## ADDED Requirements

### Requirement: Rasgos base por rosa
Cada predicción de etapa SHALL incluir `rasgos[]` con, al menos, estos rasgos base: sépalos, caracol, tamaño de cabeza y tono. Cada rasgo MUST llevar un nombre y un valor descriptivo en términos de la ficha.

#### Scenario: Predicción con rasgos
- **WHEN** el sistema emite la etapa de una rosa
- **THEN** la salida trae `rasgos[]` con sépalos, caracol, tamaño de cabeza y tono

#### Scenario: Rasgo no determinable
- **WHEN** un rasgo no se puede leer en el recorte (por ejemplo, caracol tapado)
- **THEN** el rasgo se marca "no determinable" y no se inventa un valor

### Requirement: Explicación con terminología de la ficha
La `explicacion` MUST estar redactada con la terminología de la ficha: botón floral, pétalos, sépalos, caracol y copa. MUST NOT usar números de punto; usa los nombres inmaduro, óptimo y sobreabierto y las señales visuales.

#### Scenario: Rosa en punto óptimo
- **WHEN** la etapa es óptimo
- **THEN** el texto cita las señales de la ficha presentes: caracol definido que deja ver el centro, rojo vivo e intenso y forma de copa

#### Scenario: Rosa inmaduro
- **WHEN** la etapa es inmaduro
- **THEN** el texto cita las señales presentes: cabeza más pequeña, rojo más oscuro y sépalos pegados a los pétalos

#### Scenario: Sin numeración
- **WHEN** se genera cualquier explicación
- **THEN** el texto no contiene números de punto

### Requirement: Explicación basada en más de un rasgo
La explicación SHALL apoyarse en la lectura conjunta de varios rasgos y MUST NOT basarse en un solo rasgo, porque ninguno decide por sí solo.

#### Scenario: Un solo rasgo disponible
- **WHEN** solo un rasgo es determinable
- **THEN** la explicación lo indica como evidencia limitada y la salida baja su confianza o se deriva a zona gris según la Spec 4

### Requirement: Coherencia con etapa y confianza
La explicación MUST ser coherente con la etapa y la confianza de la Spec 4. En zona gris o reencuadrar, la explicación MUST decir por qué el sistema se abstiene.

#### Scenario: Zona gris
- **WHEN** la salida es zona gris
- **THEN** la explicación nombra las señales en conflicto y la acción es consultar

#### Scenario: Reencuadrar
- **WHEN** la salida es reencuadrar
- **THEN** la explicación dice que el recorte no es válido (por ejemplo, borroso o tapado) y la acción es repetir la captura

#### Scenario: Sobreabierto de baja confianza
- **WHEN** la etapa es sobreabierto
- **THEN** la explicación lo presenta como no concluyente, por tener pocos ejemplos

### Requirement: Tono independiente del color de imagen
El rasgo tono SHALL tomarse de un sensor de color aparte y MUST NOT inferirse del color de la imagen como regla. Mientras el sensor no exista, el tono se marca "no disponible".

#### Scenario: Sin sensor
- **WHEN** no hay lectura del sensor de color
- **THEN** el tono figura "no disponible" y la explicación no afirma nada sobre el rojo

### Requirement: Mapa de calor solo para el equipo
El sistema SHALL generar un mapa de calor de atención por predicción de prueba, destinado a depurar si el modelo mira el fondo, el cielo o los alambres. El mapa MUST NOT mostrarse al usuario final.

#### Scenario: Depuración
- **WHEN** el equipo corre predicciones de prueba
- **THEN** cada una puede acompañarse de su mapa de calor y se reportan los casos en que la atención cae fuera de la flor

#### Scenario: Salida al usuario
- **WHEN** la salida se presenta al cortador
- **THEN** no incluye el mapa de calor

### Requirement: Elección del método de mapa por prueba
Con DINOv2 congelado y clasificador sin gradientes, el método del mapa MUST elegirse con una prueba que compare atención del token CLS del último bloque y oclusión, y reporte el resultado en el chat. pytorch-grad-cam MAY usarse solo si el modelo elegido tiene gradientes.

#### Scenario: Prueba comparativa
- **WHEN** se compara CLS y oclusión sobre las mismas predicciones de prueba
- **THEN** se reporta qué se probó, cuántos casos, el criterio de comparación, el costo en CPU y los límites, y se elige un método

#### Scenario: Método no verificado
- **WHEN** el método de atención CLS no se ha verificado sobre el modelo elegido
- **THEN** no se adopta hasta que la prueba lo respalde

### Requirement: El mapa no es explicación causal
El mapa de calor MUST describirse como "dónde mira el modelo" y MUST NOT presentarse como explicación causal ni como prueba de razonamiento experto.

#### Scenario: Lectura del mapa
- **WHEN** el equipo reporta un mapa
- **THEN** el informe indica que muestra atención y no demuestra por qué decidió el modelo

### Requirement: Reglas de ángulos y proporciones sujetas a experto
El ángulo de sépalos (45°-90°) y la relación ancho/alto del botón MUST NOT usarse como regla de decisión ni aparecer en la explicación hasta que un experto los valide.

#### Scenario: Regla sin validar
- **WHEN** se propone un rasgo de ángulo o proporción
- **THEN** queda como hipótesis registrada y no entra en `rasgos[]` ni en la explicación

### Requirement: Evidencia de la explicación
Al terminar, el sistema MUST reportar en el chat predicciones de ejemplo con rasgos, explicación y, para el equipo, mapa de calor, junto con qué se probó, el resultado y los límites.

#### Scenario: Informe de ejemplos
- **WHEN** se cierra la implementación
- **THEN** el informe muestra ejemplos por etapa, incluidos zona gris y reencuadrar, cuya explicación es coherente con la ficha
