from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models.patient import Patient
from models.prediction import Prediction
from schemas import (
    PatientBase,
    PatientCreate,
    PatientOut,
    PredictionOut,
    PredictionRecord,
    SimulationIn,
    SimulationOut,
)
from services.prediction_service import patient_to_dict, predict_and_store, run_prediction

router = APIRouter(prefix="/patients", tags=["patients"])


def _get_patient_or_404(db: Session, patient_id: int) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado")
    return patient


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(data: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(**data.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("", response_model=list[PatientOut])
def list_patients(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    limit = min(max(limit, 1), 200)
    return db.scalars(select(Patient).order_by(Patient.id).offset(skip).limit(limit)).all()


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    return _get_patient_or_404(db, patient_id)


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int, data: PatientCreate, db: Session = Depends(get_db)):
    """Actualiza los signos vitales: el gemelo digital evoluciona con el paciente."""
    patient = _get_patient_or_404(db, patient_id)
    for key, value in data.model_dump().items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    db.delete(_get_patient_or_404(db, patient_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{patient_id}/predictions",
    response_model=PredictionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_prediction(patient_id: int, db: Session = Depends(get_db)):
    """Calcula y guarda una nueva predicción con los datos actuales del paciente."""
    patient = _get_patient_or_404(db, patient_id)
    prediction = predict_and_store(db, patient)
    return PredictionOut(
        id=prediction.id,
        patient_id=prediction.patient_id,
        score=prediction.risk_score,
        level=prediction.risk_level,
        factors=prediction.factors,
        created_at=prediction.created_at,
    )


@router.get("/{patient_id}/predictions", response_model=list[PredictionRecord])
def list_predictions(patient_id: int, db: Session = Depends(get_db)):
    _get_patient_or_404(db, patient_id)
    return db.scalars(
        select(Prediction).where(Prediction.patient_id == patient_id).order_by(Prediction.id)
    ).all()


@router.post("/{patient_id}/simulate", response_model=SimulationOut)
def simulate(patient_id: int, scenario: SimulationIn, db: Session = Depends(get_db)):
    """Escenario 'what-if': ¿cómo cambiaría el riesgo si se modifican ciertas variables?

    No guarda nada: compara el riesgo actual del paciente con el del escenario.
    """
    base = patient_to_dict(_get_patient_or_404(db, patient_id))
    changed = {
        **base,
        "systolic_bp": base["systolic_bp"] + scenario.systolic_bp_delta,
        "diastolic_bp": base["diastolic_bp"] + scenario.diastolic_bp_delta,
        "cholesterol": base["cholesterol"] + scenario.cholesterol_delta,
        "weight": base["weight"] + scenario.weight_delta,
    }
    try:
        PatientBase(**changed)  # el escenario debe seguir siendo un paciente válido
    except ValidationError as exc:
        msg = "; ".join(e["msg"] for e in exc.errors())
        raise HTTPException(422, f"Escenario no válido: {msg}")

    before, after = run_prediction(base), run_prediction(changed)
    return SimulationOut(
        baseline=PredictionOut(score=before.score, level=before.level, factors=before.factors),
        scenario=PredictionOut(score=after.score, level=after.level, factors=after.factors),
        score_change=round(after.score - before.score, 4),
    )
