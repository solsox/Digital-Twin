"""Puerta de calidad angiográfica.

Los umbrales finales los define el fabricante del motor; aquí son configurables.
Un análisis que no pasa la puerta NO se envía al motor.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations
from typing import Any, Optional


@dataclass(frozen=True)
class Projection:
    primary_angle: float      # LAO(+)/RAO(-) en grados
    secondary_angle: float    # CRA(+)/CAU(-) en grados
    frame_rate: Optional[float] = None
    frames: Optional[int] = None


@dataclass(frozen=True)
class QualityReport:
    ok: bool
    reasons: list[str]
    best_separation_deg: Optional[float] = None


def extract_projection(ds: Any) -> Projection:
    """Lee metadatos DICOM de angiografía (acepta pydicom.Dataset o similar)."""
    primary = getattr(ds, "PositionerPrimaryAngle", None)
    secondary = getattr(ds, "PositionerSecondaryAngle", None)
    if primary is None or secondary is None:
        raise ValueError("DICOM sin ángulos del posicionador")
    fps = getattr(ds, "CineRate", None)
    if fps is None:
        frame_time_ms = getattr(ds, "FrameTime", None)
        fps = 1000.0 / float(frame_time_ms) if frame_time_ms else None
    frames = getattr(ds, "NumberOfFrames", None)
    return Projection(
        float(primary),
        float(secondary),
        float(fps) if fps else None,
        int(frames) if frames else None,
    )


def _direction(primary_deg: float, secondary_deg: float) -> tuple[float, float, float]:
    a, b = math.radians(primary_deg), math.radians(secondary_deg)
    return (math.cos(b) * math.sin(a), math.sin(b), math.cos(b) * math.cos(a))


def angular_separation(p: Projection, q: Projection) -> float:
    u, v = _direction(p.primary_angle, p.secondary_angle), _direction(q.primary_angle, q.secondary_angle)
    dot = max(-1.0, min(1.0, sum(x * y for x, y in zip(u, v))))
    return math.degrees(math.acos(dot))


def assess_quality(
    projections: list[Projection],
    *,
    nitroglycerin_given: bool,
    no_vessel_overlap: bool,
    min_angle_deg: float,
    min_fps: float,
) -> QualityReport:
    reasons: list[str] = []
    if not nitroglycerin_given:
        reasons.append("Sin nitroglicerina intracoronaria documentada")
    if not no_vessel_overlap:
        reasons.append("Superposición de vasos en el segmento de interés")

    usable = [p for p in projections if p.frame_rate is not None and p.frame_rate >= min_fps]
    if len(usable) < len(projections):
        reasons.append(f"Proyecciones con tasa de cuadros desconocida o menor a {min_fps} fps")

    best: Optional[float] = None
    if len(usable) < 2:
        reasons.append("Se requieren al menos 2 proyecciones utilizables")
    else:
        best = max(angular_separation(p, q) for p, q in combinations(usable, 2))
        if best < min_angle_deg:
            reasons.append(f"Separación angular {best:.1f}° menor a {min_angle_deg}°")

    return QualityReport(ok=not reasons, reasons=reasons, best_separation_deg=best)
