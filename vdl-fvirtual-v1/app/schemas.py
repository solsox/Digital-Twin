"""Contratos de datos de la API."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ClinicalContext(str, Enum):
    chronic = "chronic_coronary_syndrome"
    acs_stabilized = "acs_stabilized"
    other = "other"


class Exclusion(str, Enum):
    stemi_culprit = "stemi_culprit"
    cardiogenic_shock = "cardiogenic_shock"
    unprotected_left_main = "unprotected_left_main"
    bypass_graft = "bypass_graft"
    chronic_total_occlusion = "chronic_total_occlusion"
    severe_calcification_or_ostial = "severe_calcification_or_ostial"


class Recommendation(str, Enum):
    defer_pci = "DEFER_PCI"
    gray_zone_confirm = "GRAY_ZONE_CONFIRM"
    favors_pci = "FAVORS_PCI"
    not_analyzable = "NOT_ANALYZABLE"


class OperatorDecision(str, Enum):
    pci = "PCI"
    medical = "MEDICAL_THERAPY"
    cabg = "CABG"
    other = "OTHER"


class WireType(str, Enum):
    ffr = "FFR"
    ifr = "iFR"


class CaseCreate(BaseModel):
    patient_ref: str = Field(min_length=1, description="Identificador interno (p. ej. historia). NO se almacena.")
    study_uid: str = Field(min_length=1)
    lesion_label: str = Field(min_length=1, description="Ej.: 'DA proximal'")
    visual_stenosis_pct: int = Field(ge=0, le=100)
    clinical_context: ClinicalContext
    consent_id: str = Field(min_length=1)
    exclusions: list[Exclusion] = Field(default_factory=list)


class ProjectionIn(BaseModel):
    primary_angle: float
    secondary_angle: float
    frame_rate: Optional[float] = None


class AnalysisRequest(BaseModel):
    projections: list[ProjectionIn]
    intracoronary_nitroglycerin: bool
    no_vessel_overlap: bool


class AnalysisOut(BaseModel):
    case_id: int
    mode: str
    visible: bool
    message: Optional[str] = None
    analyzable: bool
    quality_ok: bool
    quality_reasons: list[str] = []
    value: Optional[float] = None
    recommendation: Optional[Recommendation] = None
    engine_name: Optional[str] = None
    engine_version: Optional[str] = None


class OutcomeIn(BaseModel):
    operator_decision: OperatorDecision
    wire_value: Optional[float] = Field(default=None, ge=0, le=1.2)
    wire_type: Optional[WireType] = None
