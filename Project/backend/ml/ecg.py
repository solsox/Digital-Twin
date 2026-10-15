"""Análisis de ECG: extracción de características y clasificador (inferencia sin scikit-learn).

Entrada: señal de un solo canal (1-D). El modelo se entrena con segmentos de 10 s a 360 Hz del
MIT-BIH Arrhythmia Database (versión compilada), por eso `fs` por defecto es 360.

Clases (convención AAMI): N normal/bloqueos, S supraventricular ectópico, V ventricular ectópico,
F fusión, Q desconocido/marcapasos.

NO es un diagnóstico: es un clasificador básico de demostración.
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy import signal as sp
from scipy import stats

ARTIFACT_PATH = Path(__file__).parent / "artifacts" / "ecg_model.json"
TRAIN_FS = 360
SEGMENT_SECONDS = 10

CLASS_LABELS = {
    "N": "Ritmo normal (o bloqueo de rama)",
    "S": "Latidos supraventriculares ectópicos",
    "V": "Latidos ventriculares ectópicos",
    "F": "Latidos de fusión",
    "Q": "Latidos no clasificables / marcapasos",
}

FEATURE_NAMES = [
    "n_peaks", "mean_hr", "std_rr", "cv_rr", "rmssd", "max_min_rr", "frac_rr_irregular",
    "mean_width", "mean_amp", "cv_amp", "skew", "kurtosis", "p_low", "p_qrs", "p_high",
]


class EcgError(ValueError):
    """La señal no se puede analizar (demasiado corta, plana, etc.)."""


def _clean(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    x = x - np.median(x)
    mad = np.median(np.abs(x)) * 1.4826
    return x / (mad if mad > 1e-9 else (x.std() or 1.0))


def extract_features(x: np.ndarray, fs: float = TRAIN_FS) -> np.ndarray:
    """Devuelve el vector de características (en el orden de FEATURE_NAMES)."""
    if len(x) < 2 * fs:
        raise EcgError("La señal debe durar al menos 2 segundos.")
    z = _clean(x)
    if np.ptp(z) < 1e-6:
        raise EcgError("La señal es plana.")

    # Pasa-banda 5-15 Hz realza el complejo QRS; el pico se busca sobre la energía filtrada.
    nyq = fs / 2
    b, a = sp.butter(2, [5 / nyq, min(15 / nyq, 0.99)], btype="band")
    env = sp.filtfilt(b, a, z) ** 2
    peaks, props = sp.find_peaks(env, distance=int(0.25 * fs), height=0.3 * np.percentile(env, 99.5),
                                 prominence=0.1 * np.percentile(env, 99.5))
    rr = np.diff(peaks) / fs if len(peaks) > 1 else np.array([])

    if len(rr) >= 2:
        mean_rr = rr.mean()
        drr = np.abs(np.diff(rr))
        std_rr, cv_rr = rr.std(), rr.std() / mean_rr
        rmssd = math.sqrt(np.mean(np.diff(rr) ** 2))
        max_min = rr.max() / rr.min()
        irregular = float(np.mean(drr > 0.12 * mean_rr))
        mean_hr = 60.0 / mean_rr
    else:
        std_rr = cv_rr = rmssd = irregular = 0.0
        max_min, mean_hr = 1.0, 0.0

    if len(peaks) >= 1:
        widths = sp.peak_widths(env, peaks, rel_height=0.5)[0] / fs
        amps = z[peaks]
        mean_width, mean_amp = float(widths.mean()), float(np.abs(amps).mean())
        cv_amp = float(np.abs(amps).std() / (np.abs(amps).mean() + 1e-9))
    else:
        mean_width = mean_amp = cv_amp = 0.0

    f, pxx = sp.welch(z, fs=fs, nperseg=min(len(z), 1024))
    total = pxx.sum() + 1e-12
    band = lambda lo, hi: float(pxx[(f >= lo) & (f < hi)].sum() / total)  # noqa: E731

    return np.array([
        len(peaks), mean_hr, std_rr, cv_rr, rmssd, max_min, irregular,
        mean_width, mean_amp, cv_amp, float(stats.skew(z)), float(stats.kurtosis(z)),
        band(0.5, 5), band(5, 15), band(15, 40),
    ], dtype=float)


@lru_cache(maxsize=1)
def _load(path: Path = ARTIFACT_PATH) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def is_available() -> bool:
    return _load() is not None


def model_info() -> dict:
    m = _load()
    return {"available": m is not None, "metrics": m["metrics"] if m else None,
            "source": m["source"] if m else None}


def classify_signal(x: np.ndarray, fs: float = TRAIN_FS) -> dict:
    """Clasifica un segmento. Si la señal es más larga que 10 s, analiza ventanas y agrega."""
    m = _load()
    if m is None:
        raise FileNotFoundError("Modelo de ECG no entrenado (ver ml/train_ecg.py).")

    if fs != TRAIN_FS:  # remuestrea a la frecuencia de entrenamiento
        n = int(round(len(x) * TRAIN_FS / fs))
        x = sp.resample(np.asarray(x, dtype=float), n)

    win = SEGMENT_SECONDS * TRAIN_FS
    segments = [x[i:i + win] for i in range(0, max(len(x) - win // 2, 1), win)] or [x]
    segments = [s for s in segments if len(s) >= 2 * TRAIN_FS]
    if not segments:
        raise EcgError("La señal debe durar al menos 2 segundos.")

    mean, scale = np.array(m["mean"]), np.array(m["scale"])
    W, b = np.array(m["coefficients"]), np.array(m["intercepts"])
    probs = []
    for seg in segments:
        feats = (extract_features(seg, TRAIN_FS) - mean) / scale
        logits = W @ feats + b
        e = np.exp(logits - logits.max())
        probs.append(e / e.sum())
    p = np.mean(probs, axis=0)

    ranked = sorted(zip(m["classes"], p), key=lambda t: -t[1])
    hr = extract_features(segments[0], TRAIN_FS)[1]
    return {
        "label": ranked[0][0],
        "description": CLASS_LABELS[ranked[0][0]],
        "confidence": round(float(ranked[0][1]), 4),
        "probabilities": {c: round(float(v), 4) for c, v in ranked},
        "heart_rate_bpm": round(float(hr), 1) if hr > 0 else None,
        "segments_analyzed": len(segments),
    }
