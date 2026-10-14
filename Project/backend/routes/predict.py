from fastapi import APIRouter

from schemas import PatientCreate, PredictionOut
from services.prediction_service import run_prediction

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=PredictionOut)
def predict(data: PatientCreate):
    """Predicción rápida sin guardar nada (útil para simular escenarios)."""
    result = run_prediction(data.model_dump())
    return PredictionOut(score=result.score, level=result.level, factors=result.factors)
