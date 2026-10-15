"""Pruebas del pipeline de entrenamiento con datos SINTÉTICOS (solo para probar el código)."""
import json

import numpy as np
import pandas as pd
import pytest

from ml import model as risk_model
from ml.train import FEATURES, TARGET, load_data, train


@pytest.fixture()
def synthetic_csv(tmp_path):
    rng = np.random.default_rng(0)
    n = 1500
    df = pd.DataFrame({
        "age": rng.integers(35, 70, n),
        "male": rng.integers(0, 2, n),
        "sysBP": rng.normal(132, 20, n),
        "diaBP": rng.normal(83, 11, n),
        "totChol": rng.normal(236, 40, n),
        "BMI": rng.normal(26, 4, n),
    })
    logit = -4.0 + 0.05 * (df.age - 50) + 0.4 * df.male + 0.02 * (df.sysBP - 130) + 0.005 * (df.totChol - 230)
    df[TARGET] = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    df.loc[::25, "BMI"] = np.nan  # valores ausentes, como en los datos reales
    path = tmp_path / "synthetic.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture()
def trained_artifact(synthetic_csv, monkeypatch):
    artifact = train(load_data(synthetic_csv))
    monkeypatch.setattr(risk_model, "_load_trained", lambda: artifact)
    return artifact


def test_training_produces_sane_artifact(synthetic_csv):
    artifact = train(load_data(synthetic_csv))
    assert artifact["features"] == FEATURES
    assert 0.6 < artifact["metrics"]["auc_test"] < 1.0
    assert artifact["coefficients"]["age"] > 0 and artifact["coefficients"]["sysBP"] > 0
    json.dumps(artifact)  # debe ser serializable


def test_trained_model_is_used_and_monotonic(trained_artifact):
    base = {"age": 45, "gender": "male", "weight": 80, "height_cm": 178,
            "systolic_bp": 125, "diastolic_bp": 80, "cholesterol": 190}
    low = risk_model.predict_risk(base)
    high = risk_model.predict_risk({**base, "age": 65, "systolic_bp": 165, "cholesterol": 270})
    assert 0 <= low.score < high.score <= 1
    assert set(low.factors) == {"edad", "sexo", "presion_sistolica", "presion_diastolica", "colesterol", "imc"}
    assert risk_model.model_info()["kind"] == "logistic-framingham"


def test_trained_model_without_height_skips_bmi(trained_artifact):
    data = {"age": 50, "gender": "female", "weight": 70,
            "systolic_bp": 130, "diastolic_bp": 85, "cholesterol": 210}
    result = risk_model.predict_risk(data)
    assert "imc" not in result.factors and 0 <= result.score <= 1


def test_model_endpoint_reports_example_model_without_artifact(client):
    risk_model.reload_model()
    info = client.get("/model").json()
    assert info["clinically_validated"] is False
    assert info["kind"] in {"logistic-ejemplo", "logistic-framingham"}
