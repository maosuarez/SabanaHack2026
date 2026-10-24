# Spec Delta

## Purpose

Define cómo se amplían los ejemplos por etapa sin fotos nuevas ni videos: aumentación solo en entrenamiento, imágenes externas con licencia abierta como último recurso, y tratamiento de sobreabierto como clase de baja confianza.

## ADDED Requirements

### Requirement: Fuentes permitidas
El conjunto de datos SHALL provenir solo de las imágenes del reto y de imágenes externas CC0, dominio público o CC BY con atribución. El sistema MUST NOT usar videos, fotogramas de video ni fotos nuevas tomadas por el equipo.

#### Scenario: Fuente no permitida
- **WHEN** se propone añadir un fotograma de video o una foto nueva
- **THEN** se rechaza y no entra a ningún conjunto

### Requirement: Datos originales de solo lectura
`data/raw/` MUST tratarse como solo lectura. Todo derivado (aumentados, externas, registros, conteos) MUST escribirse en `data/processed/` o `data/annotations/`.

#### Scenario: Derivados fuera de data/raw
- **WHEN** se generan imágenes aumentadas o se descargan externas
- **THEN** quedan fuera de `data/raw/` y `git status` no reporta cambios allí

### Requirement: Aumentación solo en entrenamiento
La aumentación MUST aplicarse solo al conjunto de entrenamiento, después del split por md5. Los límites globales MUST ser: rotación hasta ±30°, zoom, y brillo y contraste leves. La aumentación SHALL NOT aplicar cambios fuertes de tono (hue), porque el color es una señal de la etapa.

#### Scenario: Validación y prueba intactas
- **WHEN** se genera el conjunto aumentado
- **THEN** ningún recorte de validación o prueba, ni derivado de ellos, aparece en entrenamiento

#### Scenario: Cambio de tono fuera de límite
- **WHEN** una transformación desplaza el tono más allá de lo leve
- **THEN** la validación del pipeline la rechaza

### Requirement: Split por md5 sin fuga
Todos los recortes y aumentos derivados de una misma foto (mismo md5) MUST quedar en el mismo lado del split.

#### Scenario: Recortes de una misma foto
- **WHEN** una foto tiene varias flores
- **THEN** todas sus flores y sus aumentos caen en entrenamiento, o todas en validación, o todas en prueba

### Requirement: Orden de expansión
La expansión SHALL seguir este orden: anotación por flor, aumentación, y por último imágenes externas. Las externas MUST usarse solo si, tras medir con las flores propias y la aumentación, una clase sigue faltando.

#### Scenario: Externas sin necesidad medida
- **WHEN** no existe una medición que muestre una clase insuficiente con flores propias
- **THEN** no se descarga ni se añade ninguna imagen externa

### Requirement: Registro de imágenes externas
Cada imagen externa MUST registrar URL, licencia, autor, fecha de acceso y la etiqueta asignada con el criterio de la ficha, con nombres de clase y señales visuales. Una imagen con otra licencia o sin licencia MUST descartarse.

#### Scenario: Externa con licencia válida
- **WHEN** se admite una imagen CC BY
- **THEN** su fila del registro tiene URL, licencia, autor, fecha de acceso y etiqueta, y la atribución queda disponible para el informe

#### Scenario: Licencia ausente o distinta
- **WHEN** la imagen no tiene licencia, o su licencia no es CC0, dominio público ni CC BY
- **THEN** se descarta y se anota el motivo en el registro

### Requirement: Externas fuera del test y revisadas
Las imágenes externas MUST NOT entrar al conjunto de prueba. Cada una SHOULD revisarse a ojo antes de admitirse: rosa roja, vista comparable con las fotos del reto, etapa clara.

#### Scenario: Externa en el test
- **WHEN** una imagen externa aparece en el conjunto de prueba
- **THEN** la validación del split falla

### Requirement: Sobreabierto como clase de baja confianza
Sobreabierto MUST entrenarse con los ejemplos disponibles y reportarse como no concluyente mientras tenga menos de 5 ejemplos independientes por md5 en prueba o su evidencia sea insuficiente. Las predicciones de sobreabierto SHOULD derivarse a zona gris / consulta y no presentarse como orden.

#### Scenario: Informe de sobreabierto
- **WHEN** se reportan resultados por clase
- **THEN** sobreabierto aparece marcado no concluyente, con su conteo de flores y de fotos

### Requirement: Conteo por clase antes y después
Cada paso de expansión MUST reportar el conteo de flores por etapa (inmaduro, óptimo, sobreabierto) antes y después, separando flores propias, aumentadas y externas, y por lado del split.

#### Scenario: Conteo tras aumentar
- **WHEN** termina la aumentación
- **THEN** el informe muestra los conteos antes y después por clase y por lado del split, y coinciden con los archivos generados
