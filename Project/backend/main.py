from fastapi import FastAPI
from database import engine, Base

from models import patient, prediction

app = FastAPI()

Base.metadata.create_all(bind=engine)

from routes import patient

app.include_router(patient.router)

from routes import predict

app.include_router(predict.router)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)