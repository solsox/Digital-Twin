from sqlalchemy import Column, Integer, Float, String
from database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    age = Column(Integer)
    gender = Column(String)
    weight = Column(Float)
    systolic_bp = Column(Float)
    diastolic_bp = Column(Float)
    cholesterol = Column(Float)