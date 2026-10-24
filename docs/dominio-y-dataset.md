# Dominio y dataset

## Anatomía de la rosa (según la ficha técnica del reto)
- **Botón floral**: la cabeza de la flor.
- **Pétalos**.
- **Sépalos**: las hojitas verdes que envuelven el botón. El conjunto de sépalos forma el **cáliz**.
- **Pedúnculo**: el tramo del tallo que va justo debajo de la flor.
- **Tallo** y **hojas**.
- **Invernadero**: estructura de plástico que protege el cultivo.
- **Cama**: franja donde se siembran las plantas, en suelo o en hidroponía.

## Criterio de corte — variedad Freedom (rosa roja)
| Etapa | Estado | Señales visuales | Decisión |
|---|---|---|---|
| inmaduro | Cerrado | La cabeza se ve más pequeña, el rojo es más oscuro y los sépalos están pegados a los pétalos | No cortar. **Es el error más común.** |
| optimo | Óptimo | El caracol (espiral de pétalos) está definido y deja ver el centro; el rojo es vivo e intenso; la flor tiene forma de copa | Cortar |
| sobreabierto | Sobreabierto | Los pétalos se separan y se pierde la forma de copa | Ya pasó su punto |

- Ningún rasgo decide por sí solo: el criterio sale de leerlos en conjunto.
- El criterio cambia entre variedades. Todo lo que construyamos aplica solo a Freedom.
- La flor sigue abriendo en poscosecha, así que se corta pensando en cómo se verá varios días después.

## Glosario
- **Punto de corte**: estado de apertura en el que se debe cortar la flor.
- **Caracol**: espiral que forman los pétalos internos vistos desde arriba.
- **Poscosecha**: hidratación, clasificación, empaque y transporte de la flor después del corte.
- **Zona gris**: caso en el que ni el modelo ni los expertos coinciden. Es una salida válida del sistema.

## Dataset
En el proyecto, el dataset está en `data/raw/images/` con el nombre `rosa_XX.jpeg`. El número es el ID original y hay una copia por imagen única. Las etiquetas originales están en `data/raw/labels_imagen.csv`. Todo `data/raw/` es de solo lectura. Las anotaciones por flor van en `data/annotations/`.

Anotación por flor (hecha con Label Studio local, config en `tools/annotation/label_config.xml`): `data/annotations/flowers.csv` tiene 178 flores en las 56 fotos (inmaduro 128, óptimo 41, sobreabierto 9; dudosas 0; no anotables 0). Una sola cuenta de anotación (`user1`; el equipo ayudó, sin registro por persona), sin experto y sin acuerdo entre anotadores medido. La pre-anotación con OWLv2 se probó solo en 5 fotos, sin medir; la anotación final es a mano. Sobreabierto (9) es poco concluyente. Propuesto, sin confirmar: DINOv2 como extractor del clasificador y el color desde un sensor aparte.

Distribución original (carpeta `SabanaHack2026/`):
| Carpeta | Archivos |
|---|---|
| `01_Inmaduro_No_Cortar` | 37 |
| `02_Punto_Optimo_Corte` | 18 |
| `03_Pasado_Sobreabierto` | 2 |
| `04_Casos_Dificiles_Ruido` | 8 |
| **Total** | **65 archivos / 56 imágenes únicas (por md5)** |

- Todas las imágenes son JPEG de 1200×1600 en vertical, numeradas del 1 al 64 con huecos.
- Cada carpeta tiene un PDF que es solo la impresión de sus imágenes y no aporta información nueva.

### Hallazgo clave: la etiqueta es de la escena, no de la flor
- Son fotos de la cama tomadas desde abajo, a contraluz con el techo del invernadero de fondo. Cada foto tiene **varias rosas en distintos puntos**, pequeñas dentro del cuadro y mezcladas con follaje.
- Hay 8 imágenes repetidas entre clases:
  - Inmaduro y Óptimo: 8, 16, 25, 28 y 47.
  - Óptimo y Difícil: 45.
  - Inmaduro y Difícil: 63.
  - **En las tres clases: 26**, que muestra un pasillo con muchas flores.
- Interpretación: la misma foto se usó para mostrar rosas de distintos puntos. No se trata de error humano, sino de que la etiqueta apunta a una flor dentro de la escena.
- Implicaciones:
  - Había que **re-anotar por flor**, con cajas de detección y su etapa (ya hecho, ver arriba), antes de entrenar.
  - El split entre entrenamiento y prueba se hace **por imagen única** (md5), para no filtrar las duplicadas.
  - La clase sobreabierto tiene 2 imágenes originales (9 flores tras anotar): no alcanza para entrenar. Se trata con reglas o se deja como clase de baja confianza.
  - Condiciones difíciles: contraluz, oclusión por hojas, flores pequeñas y fondo con varias flores.

### Videos de apoyo (`Videos de apoyo/`). Descritos por su nombre; todavía no se revisó su contenido.
- `Corte con carro.mp4`: la labor de corte con el carro de recolección.
- `Punto de corte baja.mp4`: referencia del punto de corte. Es el video más largo, de unos 73 MB.
- `Video 1 vista a un lado.mp4` y `Video 2 vista al camino.mp4`: cómo se ve la cama desde el pasillo.
- Excluidos como fuente de datos (ni videos ni fotogramas). Solo sirven como referencia de la perspectiva real del cortador.

## Pendiente
- Agregar lo que salió de la sesión de preguntas con los expertos del reto: cómo se capacita hoy, cuánta rotación hay, qué errores son frecuentes y cómo será la prueba en vivo.
