from fastapi import APIRouter
from sqlalchemy.orm import Session
from database import SessionLocal
from models.patient import Patient

router = APIRouter()

@router.post("/patients")
def create_patient(data: dict):
    db: Session = SessionLocal()

    new_patient = Patient(**data)
    db.add(new_patient)
    db.commit()

    return {"message": "Paciente creado"}