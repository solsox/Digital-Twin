import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Permite importar los módulos del backend (main, database, ...) desde las pruebas.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture(autouse=True)
def example_model(monkeypatch):
    """Por defecto las pruebas usan el modelo de ejemplo, no el artefacto entrenado del disco."""
    from ml import model as risk_model

    monkeypatch.setattr(risk_model, "_load_trained", lambda: None)


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def valid_patient():
    return {
        "age": 45,
        "gender": "male",
        "weight": 82,
        "height_cm": 175,
        "systolic_bp": 130,
        "diastolic_bp": 85,
        "cholesterol": 200,
    }
