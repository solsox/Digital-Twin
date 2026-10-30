"""Reglas de apoyo a la decisión. La recomendación NO es una orden: decide el médico."""
from __future__ import annotations

from dataclasses import dataclass

from app.schemas import CaseCreate, ClinicalContext, Recommendation

MIN_VISUAL_STENOSIS = 40
MAX_VISUAL_STENOSIS = 90
ALLOWED_CONTEXTS = {ClinicalContext.chronic, ClinicalContext.acs_stabilized}


@dataclass(frozen=True)
class Thresholds:
    defer_above: float = 0.85
    favor_below: float = 0.75

    def __post_init__(self) -> None:
        if not (0.0 < self.favor_below < self.defer_above <= 1.0):
            raise ValueError("Se requiere 0 < favor_below < defer_above <= 1")


def recommend(value: float, t: Thresholds) -> Recommendation:
    """> defer_above → diferir; < favor_below → favorece ICP; en medio → zona gris."""
    if value > t.defer_above:
        return Recommendation.defer_pci
    if value < t.favor_below:
        return Recommendation.favors_pci
    return Recommendation.gray_zone_confirm


def check_eligibility(case: CaseCreate) -> list[str]:
    """Devuelve la lista de motivos de inelegibilidad (vacía = elegible)."""
    reasons: list[str] = []
    if case.clinical_context not in ALLOWED_CONTEXTS:
        reasons.append("Contexto clínico fuera de alcance")
    if not (MIN_VISUAL_STENOSIS <= case.visual_stenosis_pct <= MAX_VISUAL_STENOSIS):
        reasons.append(f"Estenosis visual fuera de {MIN_VISUAL_STENOSIS}-{MAX_VISUAL_STENOSIS}%")
    reasons += [f"Criterio de exclusión: {x.value}" for x in case.exclusions]
    return reasons


def result_visible(mode: str, role: str) -> bool:
    """En modo sombra solo el rol investigador ve el resultado; en guiado, todos."""
    return role == "researcher" or mode == "guided"
