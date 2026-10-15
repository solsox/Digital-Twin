"""Análisis de ECG, retina y radiografía de tórax.

Diseño de privacidad: los archivos se procesan en memoria y NO se guardan ni se registran.
Son modelos de demostración: no sirven para diagnóstico.
"""
import io

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ml import ecg, image_model
from ml.image_features import ImageError
from schemas import AnalysisCatalog, EcgAnalysis, ImageAnalysis

router = APIRouter(prefix="/analysis", tags=["analysis"])

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_SIGNAL_BYTES = 4 * 1024 * 1024
IMAGE_TYPES = {"image/jpeg", "image/png"}

DISCLAIMER = (
    "Resultado orientativo de un modelo de demostración. No es un diagnóstico: "
    "consulta a un profesional de la salud."
)

IMAGE_TASKS = {
    "retina": {
        "title": "Retina (fondo de ojo)",
        "positive": "Posibles signos de retinopatía diabética",
        "negative": "Sin signos claros de retinopatía diabética",
    },
    "xray": {
        "title": "Radiografía de tórax",
        "positive": "Posible hallazgo radiológico",
        "negative": "Sin hallazgo claro",
    },
}
_MODEL_KEY = {"retina": "retina", "xray": "cxr"}  # nombre de la ruta -> nombre del artefacto


async def _read_limited(file: UploadFile, limit: int) -> bytes:
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(413, f"El archivo supera el máximo de {limit // (1024 * 1024)} MB.")
    if not data:
        raise HTTPException(422, "El archivo está vacío.")
    return data


@router.get("", response_model=AnalysisCatalog)
def catalog():
    """Qué análisis están disponibles y con qué calidad de modelo."""
    return AnalysisCatalog(
        ecg={"title": "Electrocardiograma (señal)", **ecg.model_info()},
        retina={"title": IMAGE_TASKS["retina"]["title"], **image_model.model_info("retina")},
        xray={"title": IMAGE_TASKS["xray"]["title"], **image_model.model_info("cxr")},
    )


@router.post("/ecg", response_model=EcgAnalysis)
async def analyze_ecg(file: UploadFile = File(...), fs: float = Form(360, ge=50, le=2000)):
    """Analiza una señal de ECG de un canal (CSV/TXT con una muestra por línea o por columna)."""
    raw = await _read_limited(file, MAX_SIGNAL_BYTES)
    try:
        values = np.genfromtxt(io.BytesIO(raw), delimiter=",", dtype=float, invalid_raise=False)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(422, "No se pudo leer la señal: usa un CSV/TXT numérico.") from exc
    values = np.atleast_2d(values)
    # Dos columnas (tiempo, valor) -> toma la última; una fila larga -> la fila; una columna -> la columna.
    signal = values.ravel() if min(values.shape) == 1 else values[:, -1]
    signal = signal[np.isfinite(signal)]
    if signal.size < 100:
        raise HTTPException(422, "No se encontraron suficientes muestras numéricas en el archivo.")
    if not ecg.is_available():
        raise HTTPException(503, "El modelo de ECG no está entrenado en este servidor.")
    try:
        result = ecg.classify_signal(signal, fs=fs)
    except ecg.EcgError as exc:
        raise HTTPException(422, str(exc)) from exc
    return EcgAnalysis(**result, disclaimer=DISCLAIMER)


@router.post("/{kind}", response_model=ImageAnalysis)
async def analyze_image(kind: str, file: UploadFile = File(...)):
    """Analiza una imagen de retina (`retina`) o radiografía de tórax (`xray`)."""
    task = IMAGE_TASKS.get(kind)
    if task is None:
        raise HTTPException(404, "Tipo de análisis desconocido. Usa: ecg, retina o xray.")
    if file.content_type not in IMAGE_TYPES:
        raise HTTPException(415, "Formato no admitido: usa JPG o PNG.")
    data = await _read_limited(file, MAX_IMAGE_BYTES)
    model = _MODEL_KEY[kind]
    if not image_model.is_available(model):
        raise HTTPException(
            503,
            f"No hay un modelo entrenado para '{task['title']}'. "
            "Entrénalo con ml/train_images.py (ver README) cuando tengas datos.",
        )
    try:
        out = image_model.predict(model, data)
    except ImageError as exc:
        raise HTTPException(422, str(exc)) from exc
    metrics = image_model.model_info(model)["metrics"]
    return ImageAnalysis(
        kind=kind,
        finding=task["positive"] if out["positive"] else task["negative"],
        probability=out["probability"],
        image_size=out["image_size"],
        model_auc=metrics["cv_auc"],
        disclaimer=DISCLAIMER,
    )
