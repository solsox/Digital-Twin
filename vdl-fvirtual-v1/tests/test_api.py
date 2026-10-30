import pytest
from sqlalchemy import text

from app.config import Settings
from app.main import create_app
from tests.conftest import CASE, GOOD_ANALYSIS, hdr


def new_case(c, **over):
    r = c.post("/cases", json={**CASE, **over}, headers=hdr("technician"))
    assert r.status_code == 201, r.text
    return r.json()["case_id"]


def test_auth(shadow):
    bad = {"X-Api-Key": "x" * 20, "X-Actor": "a", "X-Role": "operator"}
    assert shadow.post("/cases", json=CASE, headers=bad).status_code == 401
    assert shadow.post("/cases", json=CASE).status_code == 422
    assert shadow.post("/cases", json=CASE, headers=hdr("admin")).status_code == 403


def test_patient_ref_not_stored(shadow):
    cid = new_case(shadow)
    with shadow.app.state.sessions() as s:
        dump = " ".join(str(r) for t in ("cases", "audit_events") for r in s.execute(text(f"select * from {t}")).all())
    assert "HC-123456" not in dump and cid == 1


def test_ineligible_case_rejected_and_audited(shadow):
    r = shadow.post("/cases", json={**CASE, "exclusions": ["stemi_culprit"]}, headers=hdr("technician"))
    assert r.status_code == 422
    assert shadow.get("/audit/verify", headers=hdr("researcher")).json()["events"] == 1


def test_shadow_hides_result_from_clinical_roles(shadow):
    cid = new_case(shadow)
    r = shadow.post(f"/cases/{cid}/analysis", json=GOOD_ANALYSIS, headers=hdr("operator")).json()
    assert r["visible"] is False and r["value"] is None and r["recommendation"] is None
    r2 = shadow.get(f"/cases/{cid}/analysis/latest", headers=hdr("technician")).json()
    assert r2["value"] is None
    r3 = shadow.get(f"/cases/{cid}/analysis/latest", headers=hdr("researcher")).json()
    assert r3["visible"] and r3["value"] is not None and r3["recommendation"]


def test_guided_shows_result(guided):
    cid = new_case(guided)
    r = guided.post(f"/cases/{cid}/analysis", json=GOOD_ANALYSIS, headers=hdr("operator")).json()
    assert r["visible"] and 0 < r["value"] <= 1
    assert r["recommendation"] in {"DEFER_PCI", "GRAY_ZONE_CONFIRM", "FAVORS_PCI"}
    assert r["engine_name"].startswith("mock")


def test_bad_quality_not_sent_to_engine(guided):
    cid = new_case(guided)
    bad = {**GOOD_ANALYSIS, "intracoronary_nitroglycerin": False}
    r = guided.post(f"/cases/{cid}/analysis", json=bad, headers=hdr("operator")).json()
    assert r["quality_ok"] is False and r["analyzable"] is False
    assert r["value"] is None and r["recommendation"] == "NOT_ANALYZABLE"


def test_outcome_permissions_and_metrics(shadow):
    for i, pct in enumerate([45, 60, 70, 80, 85]):
        cid = new_case(shadow, study_uid=f"1.2.{i}", visual_stenosis_pct=pct)
        shadow.post(f"/cases/{cid}/analysis", json=GOOD_ANALYSIS, headers=hdr("technician"))
        body = {"operator_decision": "MEDICAL_THERAPY", "wire_value": 0.7 + 0.05 * i, "wire_type": "FFR"}
        assert shadow.post(f"/cases/{cid}/outcome", json=body, headers=hdr("researcher")).status_code == 403
        assert shadow.post(f"/cases/{cid}/outcome", json=body, headers=hdr("operator")).status_code == 201
    m = shadow.get("/metrics/concordance", headers=hdr("researcher")).json()
    assert m["cases_analyzed"] == 5 and m["analyzable_rate"] == 1.0
    assert m["concordance"]["n"] == 5
    assert shadow.get("/metrics/concordance", headers=hdr("operator")).status_code == 403


def test_outcome_wire_fields_must_pair(shadow):
    cid = new_case(shadow)
    r = shadow.post(f"/cases/{cid}/outcome", json={"operator_decision": "PCI", "wire_value": 0.7}, headers=hdr("operator"))
    assert r.status_code == 422


def test_audit_detects_tampering(shadow):
    cid = new_case(shadow)
    shadow.post(f"/cases/{cid}/analysis", json=GOOD_ANALYSIS, headers=hdr("operator"))
    assert shadow.get("/audit/verify", headers=hdr("researcher")).json()["chain_ok"] is True
    with shadow.app.state.sessions.begin() as s:
        s.execute(text("update audit_events set actor='intruso' where id=1"))
    v = shadow.get("/audit/verify", headers=hdr("researcher")).json()
    assert v["chain_ok"] is False and v["first_bad_index"] == 0


def test_mock_engine_blocked_when_not_allowed(tmp_path):
    with pytest.raises(ValueError):
        create_app(Settings(database_url=f"sqlite:///{tmp_path}/x.db", engine="mock",
                            allow_mock_engine=False, api_key="k" * 20, pseudonym_key="p" * 40))
