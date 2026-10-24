# Tasks

## 1. Datos y partición

- [x] 1.1 Generar recortes por caja desde `flowers.csv` en un directorio derivado (sin tocar `data/raw/`). Verificar: un recorte por flor anotable y conteo por etapa (128/41/9).
- [x] 1.2 Dividir train/val/test por md5, con recortes de una foto del mismo lado. Verificar: ningún md5 en dos conjuntos; conteo por clase y por conjunto en el chat.
- [ ] 1.3 Reunir ejemplos de "reencuadrar" desde `04_Casos_Dificiles_Ruido`. Verificar: cantidad y revisión a ojo. **Sin ejemplos reales:** no existe la carpeta `04_Casos_Dificiles_Ruido`; las 8 fotos "dificil" (24 flores) son flores válidas con caja. Propuesta pendiente: negativos sintéticos (fondo, desenfoque, recortes cortados), marcados como proxy.

## 2. Velocidad en CPU

- [x] 2.1 Confirmar la licencia de DINOv2 en el LICENSE de facebookresearch/dinov2. Verificar: licencia anotada con enlace.
- [x] 2.2 Medir ms por recorte de ViT-S/14 y ViT-B/14 en el CPU del portátil de la demo. Verificar: tabla con mediana y p95.

## 3. Candidato A (DINOv2 + clasificador ligero)

- [x] 3.1 Extraer embeddings congelados de train/val/test (Colab o CPU). Verificar: archivo de embeddings por conjunto.
- [x] 3.2 Entrenar kNN y regresión logística, con aumentación solo en train (rot ±30°, zoom, brillo/contraste leves, sin hue fuerte). Verificar: métricas en validación por clase.

## 4. Candidato B (VLM)

- [ ] 4.1 Escribir el prompt con terminología de la ficha y verificar la licencia del VLM. Verificar: prompt y licencia en el chat.
- [ ] 4.2 Correr el VLM en validación/test y medir velocidad en CPU. Verificar: métricas por clase y ms por recorte.

## 5. Abstención y umbrales

- [ ] 5.1 Entrenar/calibrar "reencuadrar" y la zona gris con validación. Verificar: curva o tabla que justifique cada umbral; umbrales registrados. **Parcial:** zona gris con TAU=0,55 (decisión 14, `gray_zone.py`); falta "reencuadrar".
- [ ] 5.2 Marcar sobreabierto como baja confianza y derivarlo a zona gris. Verificar: ejemplo de salida. **Parcial:** regla implementada y ejemplos en `gray_zone_results.json`, pero en test los 3 sobreabiertos se predicen óptimo y nunca llegan a zona gris; no se marca.

## 6. Evaluación y decisión

- [x] 6.1 Evaluar en test: precisión, recall y F1 por clase, matriz de confusión, n por clase, clases <5 no concluyentes. Verificar: tablas en el chat. **Hecha:** `stage_results.json` (test, ViT-S/14 + kNN k=7: acc 0,875, bal_acc 0,730, F1 macro 0,755; n 14/7/3; sobreabierto = 3 < 5, no concluyente) y `pipeline/chain_test.json` (cadena detector + clasificador). Falta confirmar que las tablas se reportaron en el chat.
- [ ] 6.2 Comparar contra el piso (0.625/0.250/0.192; 0.438/0.260/0.260; 0.271/0.454/0.317). Verificar: tabla lado a lado. **Pendiente:** el piso no está en los resultados guardados; falta la tabla comparativa.
- [ ] 6.3 Elegir candidato y tamaño con la evidencia; reportar qué se probó, resultado y límites. Verificar: mensaje con la decisión explícita.
- [ ] 6.4 Actualizar `docs/decisiones-y-riesgos.md` con los pendientes resueltos (umbrales, nombre de "reencuadrar", tamaño del modelo). Verificar: diff del documento.
