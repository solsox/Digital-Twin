import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

KEY = "k" * 20
PSEUDO = "p" * 40


def make_client(tmp_path, mode: str) -> TestClient:
    s = Settings(
        database_url=f"sqlite:///{tmp_path}/t.db", mode=mode, engine="mock",
        allow_mock_engine=True, api_key=KEY, pseudonym_key=PSEUDO,
    )
    return TestClient(create_app(s))


def hdr(role: str, actor: str = "dr.test") -> dict:
    return {"X-Api-Key": KEY, "X-Actor": actor, "X-Role": role}


@pytest.fixture
def shadow(tmp_path):
    return make_client(tmp_path, "shadow")


@pytest.fixture
def guided(tmp_path):
    return make_client(tmp_path, "guided")


CASE = {
    "patient_ref": "HC-123456", "study_uid": "1.2.3.4", "lesion_label": "DA proximal",
    "visual_stenosis_pct": 65, "clinical_context": "chronic_coronary_syndrome",
    "consent_id": "CI-001", "exclusions": [],
}
GOOD_ANALYSIS = {
    "projections": [
        {"primary_angle": 30, "secondary_angle": 20, "frame_rate": 15},
        {"primary_angle": -30, "secondary_angle": -10, "frame_rate": 15},
    ],
    "intracoronary_nitroglycerin": True, "no_vessel_overlap": True,
}
