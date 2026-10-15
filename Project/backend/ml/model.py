"""Modelo de riesgo cardiovascular (ilustrativo).

Es un modelo logístico transparente: cada factor suma o resta en la escala logit y el
resultado se convierte a probabilidad (0-1) con la función sigmoide. Así el score siempre
queda acotado y se puede explicar cuánto aporta cada variable.

IMPORTANTE: los coeficientes son valores de ejemplo para el prototipo, NO provienen de un
estudio clínico. Para uso real hay que reemplazarlos por un modelo entrenado y validado
(p. ej. con scikit-learn sobre datos reales) manteniendo la misma interfaz `predict_risk`.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

# Valores de referencia (persona "sana" de comparación) y coeficientes en escala logit.
INTERCEPT = -3.0
REF_AGE = 40
REF_SYSTOLIC = 120.0
REF_DIASTOLIC = 80.0
REF_CHOLESTEROL = 180.0
REF_BMI = 25.0

COEF_AGE = 0.06  # por año de diferencia con REF_AGE
COEF_SYSTOLIC = 0.020  # por mmHg por encima de la referencia
COEF_DIASTOLIC = 0.015
COEF_CHOLESTEROL = 0.008  # por mg/dL por encima de la referencia
COEF_BMI = 0.04  # por punto de IMC por encima de la referencia
COEF_MALE = 0.4

# Umbrales de clasificación sobre la probabilidad.
THRESHOLD_MEDIUM = 0.15
THRESHOLD_HIGH = 0.35


# Si existe este archivo (lo genera ml/train.py) se usa el modelo entrenado en lugar de la fórmula de ejemplo.
ARTIFACT_PATH = Path(__file__).parent / "artifacts" / "risk_model.json"

_TRAINED_LABELS = {
    "age": "edad", "male": "sexo", "sysBP": "presion_sistolica",
    "diaBP": "presion_diastolica", "totChol": "colesterol", "BMI": "imc",
}


@dataclass
class RiskResult:
    score: float
    level: str
    factors: dict[str, float] = field(default_factory=dict)


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def bmi(weight_kg: float, height_cm: float | None) -> float | None:
    if not height_cm:
        return None
    meters = height_cm / 100
    return weight_kg / (meters * meters)


def classify(score: float, medium: float = THRESHOLD_MEDIUM, high: float = THRESHOLD_HIGH) -> str:
    if score >= high:
        return "alto"
    if score >= medium:
        return "medio"
    return "bajo"


@lru_cache(maxsize=1)
def _load_trained(path: Path = ARTIFACT_PATH) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def reload_model() -> None:
    """Vuelve a leer el artefacto (útil tras reentrenar sin reiniciar el servidor)."""
    _load_trained.cache_clear()


def model_info() -> dict:
    trained = _load_trained()
    if trained is None:
        return {"kind": "logistic-ejemplo", "clinically_validated": False, "metrics": None}
    return {
        "kind": trained["kind"],
        "clinically_validated": False,
        "metrics": trained["metrics"],
        "trained_at": trained["trained_at"],
        "source": trained["source"],
    }


def _predict_trained(m: dict, data: dict) -> RiskResult:
    """Regresión logística entrenada: cada factor aporta coef * (valor - media) / desviación."""
    height = data.get("height_cm")
    imc = bmi(data["weight"], height) if data.get("weight") and height else None
    raw = {
        "age": data["age"],
        "male": 1.0 if data["gender"] == "male" else 0.0,
        "sysBP": data["systolic_bp"],
        "diaBP": data["diastolic_bp"],
        "totChol": data["cholesterol"],
        # Sin estatura no hay IMC: se usa la mediana del entrenamiento (aporte ~0).
        "BMI": imc if imc is not None else m["medians"]["BMI"],
    }
    contributions = {
        f: m["coefficients"][f] * (raw[f] - m["mean"][f]) / m["scale"][f] for f in m["features"]
    }
    if imc is None:
        contributions.pop("BMI")
    score = _sigmoid(m["intercept"] + sum(contributions.values()) + (
        m["coefficients"]["BMI"] * (m["medians"]["BMI"] - m["mean"]["BMI"]) / m["scale"]["BMI"]
        if imc is None else 0.0
    ))
    t = m["thresholds"]
    return RiskResult(
        score=round(score, 4),
        level=classify(score, t["medium"], t["high"]),
        factors={_TRAINED_LABELS[f]: round(v, 4) for f, v in contributions.items()},
    )


def predict_risk(data: dict) -> RiskResult:
    """Calcula el riesgo a partir de un diccionario con los datos del paciente.

    Claves requeridas: age, gender, systolic_bp, diastolic_bp, cholesterol.
    Opcionales: weight y height_cm (si ambas están, se incluye el IMC).
    """
    trained = _load_trained()
    if trained is not None:
        return _predict_trained(trained, data)

    factors: dict[str, float] = {
        "edad": COEF_AGE * (data["age"] - REF_AGE),
        # Para presión y colesterol solo penaliza lo que excede la referencia.
        "presion_sistolica": COEF_SYSTOLIC * max(0.0, data["systolic_bp"] - REF_SYSTOLIC),
        "presion_diastolica": COEF_DIASTOLIC * max(0.0, data["diastolic_bp"] - REF_DIASTOLIC),
        "colesterol": COEF_CHOLESTEROL * max(0.0, data["cholesterol"] - REF_CHOLESTEROL),
        "sexo": COEF_MALE if data["gender"] == "male" else 0.0,
    }

    imc = bmi(data["weight"], data.get("height_cm")) if data.get("weight") else None
    if imc is not None:
        factors["imc"] = COEF_BMI * max(0.0, imc - REF_BMI)

    score = _sigmoid(INTERCEPT + sum(factors.values()))
    return RiskResult(
        score=round(score, 4),
        level=classify(score),
        factors={k: round(v, 4) for k, v in factors.items()},
    )
