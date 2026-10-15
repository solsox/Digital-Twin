# Datos de entrenamiento: fuentes, licencias y límites

Los datos **no se suben al repositorio** (carpeta `data/` ignorada); solo los modelos resultantes
(JSON con coeficientes) en `backend/ml/artifacts/`. Todos los modelos son experimentales y
**ninguno está validado clínicamente**.

| Análisis | Fuente (alojada en GitHub) | Tamaño | Resultado | Licencia / uso |
|---|---|---|---|---|
| Riesgo cardiovascular | [plaguedoc000/framingham-heart-study-dataset](https://github.com/plaguedoc000/framingham-heart-study-dataset) (copia del Framingham Heart Study) | 4.240 pacientes, 15,2 % con evento a 10 años | AUC 0,69 (test) | Los datos originales son del NHLBI/BioLINCC; la copia no declara licencia. Se publican solo los coeficientes. |
| ECG (5 clases de latidos) | [dhiah-dev/Dataset-Compiled-ECG-MIT-BIH-Arrhythmia](https://github.com/dhiah-dev/Dataset-Compiled-ECG-MIT-BIH-Arrhythmia), derivado de [MIT-BIH](https://physionet.org/content/mitdb/1.0.0/) | 500 segmentos de 10 s a 360 Hz (100 por clase) | exactitud 0,87 en validación cruzada (optimista, sin separar pacientes) | MIT-BIH: Open Data Commons Attribution 1.0. Cita: Moody & Mark (2001); Goldberger et al. (2000). |
| Retina (retinopatía diabética sí/no) | [SRahimDR/DR-image-dataset](https://github.com/SRahimDR/DR-image-dataset) | 600 imágenes (324 con RD) | AUC 0,66 (validación por paciente): **débil** | "Uso académico con atribución"; no es una licencia formal, evita uso comercial. |
| Radiografía de tórax | — | — | **Sin modelo** | Ver abajo. |

## Radiografía de tórax: por qué no hay modelo

Desde el entorno donde se construyó el proyecto solo eran accesibles GitHub y PyPI (PhysioNet, Kaggle,
Hugging Face, Zenodo, NIH y Stanford estaban bloqueados). El único conjunto de radiografías
descargable, [ieee8023/covid-chestxray-dataset](https://github.com/ieee8023/covid-chestxray-dataset),
es de neumonía/COVID (950 filas, solo 22 "No Finding") y con licencias mixtas (CC BY-NC-SA, CC BY 3.0…),
así que no sirve para un modelo cardíaco ni para un modelo general fiable.

La interfaz y la API están listas. Para activarlo cuando tengas datos:

```bash
# Conjuntos abiertos recomendados (requieren descarga manual):
#   NIH ChestX-ray14 (cardiomegalia), CheXpert, MIMIC-CXR, Chest X-ray Pneumonia (Kermany)
cd backend
python -m ml.train_images --task cxr --data ruta/chest_xray --negative NORMAL --source "nombre del dataset"
```

Cada subcarpeta de `--data` es una clase; las de `--negative` cuentan como "sin hallazgo". Se genera
`ml/artifacts/cxr_model.json` y el análisis se activa sin cambiar código.

## Mejoras con mejores datos

- **ECG:** PTB-XL (21.000 ECG de 12 derivaciones, PhysioNet) permitiría diagnóstico por patologías.
- **Retina:** EyePACS / APTOS / Messidor para retinopatía diabética (decenas de miles de imágenes),
  y una red preentrenada (transferencia) en lugar de descriptores clásicos.
- **Riesgo:** añadir fumador, diabetes y medicación (están en Framingham) mejoraría el AUC.
