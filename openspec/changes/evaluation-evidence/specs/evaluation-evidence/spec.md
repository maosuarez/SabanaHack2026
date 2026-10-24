# Spec Delta

## Purpose

Define cómo se mide y se reporta el rendimiento de cada prototipo (detector y clasificador) de forma honesta: split sin fuga, métricas por clase, comparación con el piso y evidencia en el chat.

## ADDED Requirements

### Requirement: Split por md5 sin fuga
El conjunto de evaluación MUST dividirse por md5 de imagen. Todos los recortes (flores) de una misma foto SHALL quedar en el mismo lado del split. Los datos externos MUST quedar fuera del test. El split MUST ser reproducible (semilla y lista de md5 por lado guardadas en `data/annotations/`).

#### Scenario: Recortes de una foto juntos
- **WHEN** se arma el split
- **THEN** ningún md5 aparece en más de un lado y todas las flores de ese md5 están en el mismo lado

#### Scenario: Split reproducible
- **WHEN** se vuelve a generar el split con la misma semilla
- **THEN** la asignación de md5 por lado es idéntica

### Requirement: Métricas por clase y matriz de confusión
Todo resultado de clasificación MUST reportar precisión, recall y F1 por clase, exactitud balanceada, F1 macro y la matriz de confusión sobre el test. La exactitud sola MUST NOT presentarse como resultado.

#### Scenario: Reporte completo
- **WHEN** se evalúa un clasificador sobre el test
- **THEN** el informe incluye las tres métricas por clase y la matriz de confusión

#### Scenario: Solo exactitud
- **WHEN** un informe trae únicamente la exactitud
- **THEN** se considera incompleto y no cuenta como evidencia

### Requirement: Clases con pocos ejemplos no concluyentes
Una clase con menos de 5 ejemplos en el test MUST marcarse como no concluyente, con su n visible. Sus métricas MUST NOT usarse para decidir entre modelos.

#### Scenario: Sobreabierto con n bajo
- **WHEN** la clase sobreabierto tiene menos de 5 ejemplos de prueba
- **THEN** el informe la marca no concluyente y muestra su n

### Requirement: Comparación contra el piso
Todo prototipo MUST compararse con el piso sin aprendizaje profundo: siempre-inmaduro, color+1NN y color+LogReg. Si el piso se reevalúa sobre el nuevo split, el informe MUST indicarlo; si no, MUST aclarar que el piso se midió a nivel de foto completa y no de flor.

#### Scenario: Prototipo frente al piso
- **WHEN** se reporta un prototipo
- **THEN** el informe muestra sus métricas junto a las del piso y dice si lo supera en exactitud balanceada y F1 macro

### Requirement: Evidencia en el chat tras cada prototipo
Tras cada prototipo se MUST reportar en el chat: qué se probó, el resultado (métricas) y los límites observados.

#### Scenario: Prototipo terminado
- **WHEN** termina un prototipo
- **THEN** el chat recibe un mensaje con las tres partes antes de marcar la tarea como completada

### Requirement: Prueba con casos desconocidos
La demo MUST evaluarse con casos desconocidos de tres tipos: rosas reales, fotos impresas y fotos en pantalla. El informe SHALL separar los resultados por tipo.

#### Scenario: Tres tipos de caso
- **WHEN** se corre la prueba de casos desconocidos
- **THEN** el informe muestra los resultados por separado para rosas reales, impresas y en pantalla

### Requirement: Límites de validez declarados
Todo informe MUST declarar que el etiquetado actual tiene una sola cuenta de anotación (`user1`) y ningún acuerdo entre anotadores medido, y que por eso las métricas miden coincidencia con esa anotación y no con una verdad de campo.

#### Scenario: Informe con advertencia
- **WHEN** se publica un informe de métricas
- **THEN** incluye la advertencia de anotación única y sin acuerdo medido
