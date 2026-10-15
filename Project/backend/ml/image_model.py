"""Inferencia de los clasificadores binarios de imagen (retina / radiografía)."""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np

from ml.image_features import FEATURE_NAMES, extract, load_image

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
TASKS = ("retina", "cxr")


@lru_cache(maxsize=4)
def _load(task: str) -> dict | None:
    try:
        m = json.loads((ARTIFACT_DIR / f"{task}_model.json").read_text())
    except (OSError, ValueError):
        return None
    return m if m.get("features") == FEATURE_NAMES else None  # artefacto de otra versión: se ignora


def is_available(task: str) -> bool:
    return _load(task) is not None


def model_info(task: str) -> dict:
    m = _load(task)
    return {"available": m is not None, "metrics": m["metrics"] if m else None,
            "source": m["source"] if m else None}


def predict(task: str, data: bytes) -> dict:
    """Devuelve la probabilidad de 'hallazgo' para una imagen. Lanza ImageError si no es válida."""
    m = _load(task)
    if m is None:
        raise FileNotFoundError(f"Modelo '{task}' no entrenado.")
    img = load_image(data)
    z = (extract(img) - np.array(m["mean"])) / np.array(m["scale"])
    p = 1.0 / (1.0 + math.exp(-(float(np.dot(m["coefficients"], z)) + m["intercept"])))
    return {"probability": round(p, 4), "positive": p >= 0.5, "image_size": list(img.size)}
