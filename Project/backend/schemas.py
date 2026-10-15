from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PatientBase(BaseModel):
    age: int = Field(ge=0, le=120, description="Edad en años")
    gender: Literal["male", "female"]
    weight: float = Field(gt=0, le=400, description="Peso en kg")
    height_cm: float | None = Field(default=None, gt=50, le=260, description="Estatura en cm")
    systolic_bp: float = Field(ge=50, le=300, description="Presión sistólica (mmHg)")
    diastolic_bp: float = Field(ge=30, le=200, description="Presión diastólica (mmHg)")
    cholesterol: float = Field(ge=50, le=600, description="Colesterol total (mg/dL)")

    @model_validator(mode="after")
    def _systolic_above_diastolic(self):
        if self.systolic_bp <= self.diastolic_bp:
            raise ValueError("La presión sistólica debe ser mayor que la diastólica")
        return self


class PatientCreate(PatientBase):
    pass


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    patient_id: int | None = None
    score: float
    level: Literal["bajo", "medio", "alto"]
    factors: dict[str, float]
    created_at: datetime | None = None


class PatientOut(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class PredictionRecord(BaseModel):
    """Fila del historial guardado en base de datos."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    risk_score: float
    risk_level: str
    factors: dict[str, float]
    created_at: datetime


class SimulationIn(BaseModel):
    """Escenario 'what-if': cambios relativos sobre los valores actuales del paciente."""

    systolic_bp_delta: float = Field(default=0, ge=-100, le=100)
    diastolic_bp_delta: float = Field(default=0, ge=-60, le=60)
    cholesterol_delta: float = Field(default=0, ge=-300, le=300)
    weight_delta: float = Field(default=0, ge=-100, le=100)


class SimulationOut(BaseModel):
    baseline: PredictionOut
    scenario: PredictionOut
    score_change: float  # scenario.score - baseline.score (negativo = el riesgo baja)
