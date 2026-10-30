"""Métricas de concordancia entre el valor virtual y la guía de presión (FFR ≤ 0,80 = isquemia)."""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from statistics import mean, pstdev

ISCHEMIA_CUTOFF = 0.80


@dataclass(frozen=True)
class Concordance:
    n: int
    tp: int
    fp: int
    tn: int
    fn: int
    accuracy: float | None
    accuracy_ci95: tuple[float, float] | None
    sensitivity: float | None
    specificity: float | None
    auc: float | None
    mean_difference: float | None
    sd_difference: float | None

    def as_dict(self) -> dict:
        return asdict(self)


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        raise ValueError("n = 0")
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def _ratio(a: int, b: int) -> float | None:
    return a / b if b else None


def _auc(pairs: list[tuple[float, float]]) -> float | None:
    pos = [-v for v, w in pairs if w <= ISCHEMIA_CUTOFF]   # menor valor = más isquemia
    neg = [-v for v, w in pairs if w > ISCHEMIA_CUTOFF]
    if not pos or not neg:
        return None
    wins = sum(1.0 if p > q else 0.5 if p == q else 0.0 for p in pos for q in neg)
    return wins / (len(pos) * len(neg))


def concordance(pairs: list[tuple[float, float]]) -> Concordance:
    """pairs = [(valor_virtual, valor_guía_de_presión), ...]"""
    tp = sum(1 for v, w in pairs if v <= ISCHEMIA_CUTOFF and w <= ISCHEMIA_CUTOFF)
    fp = sum(1 for v, w in pairs if v <= ISCHEMIA_CUTOFF and w > ISCHEMIA_CUTOFF)
    tn = sum(1 for v, w in pairs if v > ISCHEMIA_CUTOFF and w > ISCHEMIA_CUTOFF)
    fn = sum(1 for v, w in pairs if v > ISCHEMIA_CUTOFF and w <= ISCHEMIA_CUTOFF)
    n = len(pairs)
    diffs = [v - w for v, w in pairs]
    return Concordance(
        n=n, tp=tp, fp=fp, tn=tn, fn=fn,
        accuracy=_ratio(tp + tn, n),
        accuracy_ci95=wilson_ci(tp + tn, n) if n else None,
        sensitivity=_ratio(tp, tp + fn),
        specificity=_ratio(tn, tn + fp),
        auc=_auc(pairs),
        mean_difference=mean(diffs) if diffs else None,
        sd_difference=pstdev(diffs) if len(diffs) > 1 else None,
    )
