"""Entrena el clasificador de ECG con el MIT-BIH compilado (CSV: 500 filas x 3600 muestras + etiqueta).

Uso:  python -m ml.train_ecg --data ruta/Compiled-ECG-MIT-BIH-Arrhytmia.csv
Fuente: https://github.com/dhiah-dev/Dataset-Compiled-ECG-MIT-BIH-Arrhythmia
        (derivado de MIT-BIH / PhysioNet, licencia ODC-By 1.0 en el original).

Los segmentos de un mismo paciente pueden caer en pliegues distintos de la validación cruzada
(el CSV no trae id de paciente), así que las métricas son optimistas.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ml.ecg import FEATURE_NAMES, TRAIN_FS, extract_features, EcgError

DEFAULT_OUT = Path(__file__).parent / "artifacts" / "ecg_model.json"


def build(df: pd.DataFrame):
    labels = df.iloc[:, -1].astype(str).to_numpy()
    X, y = [], []
    for row, label in zip(df.iloc[:, :-1].to_numpy(dtype=float), labels):
        try:
            X.append(extract_features(row, TRAIN_FS))
            y.append(label)
        except EcgError:
            continue
    return np.vstack(X), np.array(y)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    X, y = build(pd.read_csv(args.data))
    pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=1.0))
    cv = StratifiedKFold(5, shuffle=True, random_state=args.seed)
    pred = cross_val_predict(pipe, X, y, cv=cv)
    acc, f1 = accuracy_score(y, pred), f1_score(y, pred, average="macro")

    pipe.fit(X, y)
    scaler, clf = pipe[0], pipe[-1]
    per_class = {str(c): round(float(f1_score(y == c, pred == c)), 4) for c in clf.classes_}
    artifact = {
        "kind": "logistic-ecg-features",
        "features": FEATURE_NAMES,
        "classes": [str(c) for c in clf.classes_],
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "coefficients": clf.coef_.tolist(),
        "intercepts": clf.intercept_.tolist(),
        "metrics": {"cv_accuracy": round(float(acc), 4), "cv_macro_f1": round(float(f1), 4),
                    "f1_per_class": per_class, "n": int(len(y)), "optimistic_no_patient_split": True},
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "MIT-BIH Arrhythmia (compilado, dhiah-dev)",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2))
    print(f"Guardado en {args.out}\nCV accuracy={acc:.3f} macro-F1={f1:.3f}\nF1 por clase: {per_class}")


if __name__ == "__main__":
    main()
