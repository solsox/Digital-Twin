"""Modelo de riesgo cardiovascular (ilustrativo).

Es un modelo logístico transparente: cada factor suma o resta en la escala logit y el
resultado se convierte a probabilidad (0-1) con la función sigmoide. Así el score siempre
queda acotado y se puede explicar cuánto aporta cada variable.

IMPORTANTE: los coeficientes son valores de ejemplo para el prototipo, NO provienen de un
estudio clínico. Para uso real hay que reemplazarlos por un modelo entrenado y validado
(p. ej. con scikit-learn sobre datos reales) manteniendo la misma interfaz `predict_risk`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

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


def classify(score: float) -> str:
    if score >= THRESHOLD_HIGH:
        return "alto"
    if score >= THRESHOLD_MEDIUM:
        return "medio"
    return "bajo"


def predict_risk(data: dict) -> RiskResult:
    """Calcula el riesgo a partir de un diccionario con los datos del paciente.

    Claves requeridas: age, gender, systolic_bp, diastolic_bp, cholesterol.
    Opcionales: weight y height_cm (si ambas están, se incluye el IMC).
    """
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
