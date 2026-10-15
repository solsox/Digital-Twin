from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import Base, engine
from ml.model import model_info
from models import patient, prediction  # noqa: F401  (registra las tablas en Base)
from routes import patient as patient_routes
from routes import predict as predict_routes


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Digital Twin Health", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patient_routes.router)
app.include_router(predict_routes.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


@app.get("/model", tags=["meta"])
def model():
    """Qué modelo está activo (ejemplo o entrenado) y sus métricas de validación."""
    return model_info()
