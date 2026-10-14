from sqlalchemy.orm import Session

from ml.model import RiskResult, predict_risk
from models.patient import Patient
from models.prediction import Prediction

_FIELDS = ("age", "gender", "weight", "height_cm", "systolic_bp", "diastolic_bp", "cholesterol")


def patient_to_dict(patient: Patient) -> dict:
    return {f: getattr(patient, f) for f in _FIELDS}


def run_prediction(patient_data: dict) -> RiskResult:
    """Calcula el riesgo sin tocar la base de datos."""
    return predict_risk(patient_data)


def predict_and_store(db: Session, patient: Patient) -> Prediction:
    """Calcula el riesgo de un paciente guardado y registra el resultado en su historial."""
    result = predict_risk(patient_to_dict(patient))
    prediction = Prediction(
        patient_id=patient.id,
        risk_score=result.score,
        risk_level=result.level,
        factors=result.factors,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction
