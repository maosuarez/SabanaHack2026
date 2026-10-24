# Spec Delta

## Purpose

Define cómo se clasifica la etapa de cada rosa recortada, cómo se expresa la confianza y la abstención, y cómo se evalúa el clasificador de forma honesta frente a un piso medido.

## ADDED Requirements

### Requirement: Salida por recorte con confianza
El clasificador MUST devolver, por recorte, una etapa (inmaduro, óptimo o sobreabierto) junto con una confianza, o una abstención. La salida SHALL NOT ser nunca solo una clase sin confianza.

#### Scenario: Recorte claro
- **WHEN** el recorte es válido y el modelo está seguro
- **THEN** la salida trae la etapa y su confianza

#### Scenario: Sin números de punto
- **WHEN** se muestra cualquier salida
- **THEN** usa los nombres de clase y no números de punto de la ficha

### Requirement: Abstención separada
El sistema MUST ofrecer dos salidas de abstención distintas y no intercambiables: "reencuadrar" (recorte no válido: borroso, tapado o sin flor; acción: repetir captura) y "zona gris" (recorte válido con etapa ambigua; acción: consultar). En ambas el sistema SHALL abstenerse de dar una etapa.

#### Scenario: Recorte no válido
- **WHEN** el recorte está borroso, tapado o no contiene flor
- **THEN** la salida es "reencuadrar" y no incluye etapa

#### Scenario: Etapa ambigua
- **WHEN** el recorte es válido pero la confianza queda en la zona intermedia
- **THEN** la salida es "zona gris" y no incluye etapa

### Requirement: Umbrales calibrados con validación
Los umbrales de rechazo ("reencuadrar") y de zona gris MUST calibrarse con el conjunto de validación y NOT fijarse de antemano. El valor elegido SHALL registrarse junto con la evidencia que lo respalda.

#### Scenario: Umbral con evidencia
- **WHEN** se fija un umbral
- **THEN** el informe muestra la curva o tabla de validación que lo justifica

### Requirement: Sobreabierto como clase de baja confianza
Sobreabierto (9 flores en 2 fotos) SHALL tratarse como clase de baja confianza y no concluyente. Una predicción de sobreabierto MUST derivarse a zona gris/consulta, y sus métricas MUST marcarse como no concluyentes.

#### Scenario: Predicción sobreabierto
- **WHEN** el modelo predice sobreabierto
- **THEN** la salida lo marca como baja confianza y lo deriva a consulta

#### Scenario: Informe de la clase
- **WHEN** se reportan métricas de sobreabierto
- **THEN** se indica n=9 y que el resultado no es concluyente

### Requirement: Comparación de candidatos
Se MUST comparar DINOv2 congelado + clasificador ligero (kNN o regresión logística) contra un VLM con prompt basado en la ficha, sobre el mismo test reservado por md5. La elección SHALL basarse en las métricas medidas.

#### Scenario: Misma base de comparación
- **WHEN** se evalúan ambos candidatos
- **THEN** usan los mismos recortes de test y se reportan las mismas métricas

#### Scenario: Licencia
- **WHEN** se elige un modelo
- **THEN** su licencia queda verificada en el repositorio oficial y anotada

### Requirement: Medición de velocidad en CPU
Antes de escoger el tamaño de DINOv2 (ViT-S/14 o ViT-B/14), MUST medirse el tiempo de inferencia por recorte en CPU del portátil de la demo.

#### Scenario: Velocidad reportada
- **WHEN** se compara el tamaño del modelo
- **THEN** el informe incluye ms por recorte en CPU para cada tamaño y la exactitud asociada

### Requirement: Independencia del color de imagen
El contrato de etapa SHALL NOT depender del color de la imagen como señal propia del sistema: el color llegará de un sensor aparte. La aumentación MUST aplicarse solo en entrenamiento, con rotación ±30°, zoom y brillo/contraste leves, sin cambios fuertes de hue.

#### Scenario: Aumentación limitada
- **WHEN** se aumentan datos
- **THEN** solo se hace en el conjunto de entrenamiento y sin alterar fuertemente el hue

#### Scenario: Sin sensor de color
- **WHEN** se ejecuta el clasificador
- **THEN** no requiere ninguna entrada del sensor de color para producir su salida

### Requirement: Split por md5
Train, validación y test MUST dividirse por md5 de imagen, de modo que los recortes de una misma foto queden del mismo lado.

#### Scenario: Sin fuga
- **WHEN** se arman los conjuntos
- **THEN** ningún md5 aparece en más de un conjunto

### Requirement: Evaluación contra el piso
La evaluación SHALL reportar precisión, recall y F1 por clase, matriz de confusión y las clases con pocos ejemplos, y MUST compararse contra el piso sin aprendizaje profundo (siempre-inmaduro 0.625 / 0.250 / 0.192; color+1NN 0.438 / 0.260 / 0.260; color+LogReg 0.271 / 0.454 / 0.317 en exactitud / balanceada / F1 macro). Una clase con menos de 5 ejemplos MUST marcarse no concluyente.

#### Scenario: Informe en el chat
- **WHEN** termina la evaluación
- **THEN** el chat recibe qué se probó, métricas por clase, matriz de confusión, comparación con el piso y límites observados

#### Scenario: Entrenamiento de reencuadrar
- **WHEN** se entrena o calibra "reencuadrar"
- **THEN** se usan los casos de `04_Casos_Dificiles_Ruido` y la evaluación indica cuántos ejemplos hubo
