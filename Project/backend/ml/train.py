"""Entrena el modelo de riesgo con el conjunto de datos de Framingham y lo exporta a JSON.

Uso (desde Project/backend):
    pip install -r requirements-train.txt
    python -m ml.train --data ruta/a/framingham.csv

Columnas esperadas (nombres del CSV público de Framingham en Kaggle):
    male, age, sysBP, diaBP, totChol, BMI, TenYearCHD

El resultado (ml/artifacts/risk_model.json) contiene solo números: coeficientes, medias y
desviaciones. La API lo lee sin necesitar scikit-learn y sin cargar pickles.

AVISO: Framingham describe una cohorte de EE. UU. de mediados del siglo XX. Es un buen
ejercicio académico, pero el modelo resultante NO está validado para uso clínico.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

# Orden fijo: la API construye el vector de entrada en este mismo orden.
FEATURES = ["age", "male", "sysBP", "diaBP", "totChol", "BMI"]
TARGET = "TenYearCHD"
DEFAULT_OUT = Path(__file__).parent / "artifacts" / "risk_model.json"
# diaBP está muy correlacionada con sysBP; al entrenar con Framingham su coeficiente sale
# negativo (bajar la diastólica "subiría" el riesgo), lo cual es un artefacto estadístico.
DEFAULT_EXCLUDE = ("diaBP",)


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
    if missing:
        raise SystemExit(f"Faltan columnas en el CSV: {missing}")
    df = df[FEATURES + [TARGET]].dropna(subset=[TARGET])
    return df


def train(df: pd.DataFrame, seed: int = 42, exclude: tuple[str, ...] = DEFAULT_EXCLUDE) -> dict:
    features = [f for f in FEATURES if f not in exclude]
    medians = df[FEATURES].median()  # se usan para imputar valores ausentes (también en la API)
    X = df[features].fillna(medians[features])
    y = df[TARGET].astype(int)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, stratify=y, random_state=seed)

    mean = X_tr.mean()
    scale = X_tr.std(ddof=0).replace(0, 1.0)
    clf = LogisticRegression(max_iter=1000, class_weight=None)
    clf.fit(((X_tr - mean) / scale).to_numpy(), y_tr)

    proba = clf.predict_proba(((X_te - mean) / scale).to_numpy())[:, 1]
    base_rate = float(y.mean())

    return {
        "kind": "logistic-framingham",
        "features": features,
        "excluded": list(exclude),
        "intercept": float(clf.intercept_[0]),
        "coefficients": {f: float(c) for f, c in zip(features, clf.coef_[0])},
        "mean": {f: float(mean[f]) for f in features},
        "scale": {f: float(scale[f]) for f in features},
        "medians": {f: float(medians[f]) for f in FEATURES},
        # Umbrales relativos a la tasa base del conjunto de datos.
        "thresholds": {"medium": round(base_rate * 0.75, 4), "high": round(base_rate * 1.75, 4)},
        "metrics": {
            "auc_test": round(float(roc_auc_score(y_te, proba)), 4),
            "brier_test": round(float(brier_score_loss(y_te, proba)), 4),
            "base_rate": round(base_rate, 4),
            "n_train": int(len(X_tr)),
            "n_test": int(len(X_te)),
        },
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Framingham Heart Study (CSV público)",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--data", required=True, type=Path, help="CSV de Framingham")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--exclude", nargs="*", default=list(DEFAULT_EXCLUDE),
                        help="variables a omitir (por defecto diaBP, por colinealidad)")
    args = parser.parse_args()

    artifact = train(load_data(args.data), seed=args.seed, exclude=tuple(args.exclude))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2, ensure_ascii=False))
    m = artifact["metrics"]
    print(f"Modelo guardado en {args.out}")
    print(f"AUC (test): {m['auc_test']}  Brier: {m['brier_test']}  tasa base: {m['base_rate']}")


if __name__ == "__main__":
    main()
