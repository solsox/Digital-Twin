"""Entrena un clasificador binario de imágenes a partir de carpetas por clase.

Uso (retina, retinopatía diabética sí/no):
    python -m ml.train_images --task retina \
        --data "ruta/DR and maculopathy 10 classes" --negative "1 - No DR"
Uso (radiografía, cuando consigas un conjunto con carpetas NORMAL / otras):
    python -m ml.train_images --task cxr --data ruta/chest_xray --negative NORMAL

Cada subcarpeta es una clase. Las de `--negative` cuentan como "sin hallazgo" y el resto como
"con hallazgo". Los nombres de archivo tipo PatientNNN_L/R se usan para agrupar ojos del mismo
paciente en el mismo pliegue (evita fuga de datos entre entrenamiento y validación).
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ml.image_features import FEATURE_NAMES, ImageError, extract, load_image

EXTS = {".jpg", ".jpeg", ".png"}


def collect(root: Path, negatives: set[str]):
    X, y, groups, classes = [], [], [], {}
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() not in EXTS:
                continue
            try:
                feats = extract(load_image(f.read_bytes()))
            except (ImageError, OSError):
                continue
            X.append(feats)
            y.append(0 if folder.name in negatives else 1)
            m = re.match(r"(Patient\d+)", f.stem)
            groups.append(m.group(1) if m else f.stem)
            classes[folder.name] = classes.get(folder.name, 0) + 1
    return np.vstack(X), np.array(y), np.array(groups), classes


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--task", required=True, choices=["retina", "cxr"])
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--negative", nargs="+", required=True, help="carpetas que significan 'sin hallazgo'")
    ap.add_argument("--source", default="")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    X, y, groups, classes = collect(args.data, set(args.negative))
    if len(set(y)) < 2:
        raise SystemExit("Hacen falta imágenes de ambos grupos (con y sin hallazgo).")

    pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1, class_weight="balanced"))
    proba = cross_val_predict(pipe, X, y, cv=GroupKFold(5), groups=groups, method="predict_proba")[:, 1]
    auc = float(roc_auc_score(y, proba))
    bacc = float(balanced_accuracy_score(y, proba >= 0.5))

    pipe.fit(X, y)
    scaler, clf = pipe[0], pipe[-1]
    artifact = {
        "kind": f"logistic-image-features-{args.task}",
        "features": FEATURE_NAMES,
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "coefficients": clf.coef_[0].tolist(),
        "intercept": float(clf.intercept_[0]),
        "negative_classes": sorted(args.negative),
        "metrics": {"cv_auc": round(auc, 4), "cv_balanced_accuracy": round(bacc, 4),
                    "n": int(len(y)), "n_positive": int(y.sum()), "classes": classes,
                    "validation": "GroupKFold(5) por paciente"},
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": args.source or str(args.data.name),
    }
    out = args.out or Path(__file__).parent / "artifacts" / f"{args.task}_model.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2))
    print(f"Guardado en {out}\nAUC={auc:.3f}  exactitud balanceada={bacc:.3f}  n={len(y)} (positivos {int(y.sum())})")


if __name__ == "__main__":
    main()
