from sqlalchemy import Column, Integer, Float, String
from database import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer)
    risk_score = Column(Float)
    risk_level = Column(String)

    