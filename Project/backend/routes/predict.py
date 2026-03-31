from fastapi import APIRouter
from services.prediction_service import run_prediction

router = APIRouter()

@router.post("/predict")
def predict(data: dict):
    result = run_prediction(data)
    return result