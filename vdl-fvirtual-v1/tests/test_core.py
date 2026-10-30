import pytest
from pydicom import Dataset
from types import SimpleNamespace

from app.audit import GENESIS, canonical, compute_hash, verify_chain
from app.decision import Thresholds, check_eligibility, recommend, result_visible
from app.metrics import concordance, wilson_ci
from app.privacy import pseudonymize, strip_dicom_identifiers
from app.quality import Projection, angular_separation, assess_quality, extract_projection
from app.schemas import CaseCreate, Recommendation

T = Thresholds()


@pytest.mark.parametrize("v,exp", [
    (0.90, Recommendation.defer_pci), (0.851, Recommendation.defer_pci),
    (0.85, Recommendation.gray_zone_confirm), (0.80, Recommendation.gray_zone_confirm),
    (0.75, Recommendation.gray_zone_confirm), (0.749, Recommendation.favors_pci),
    (0.50, Recommendation.favors_pci),
])
def test_recommend_boundaries(v, exp):
    assert recommend(v, T) == exp


def test_thresholds_validation():
    with pytest.raises(ValueError):
        Thresholds(defer_above=0.7, favor_below=0.8)
    with pytest.raises(ValueError):
        Thresholds(defer_above=1.2, favor_below=0.5)


def _case(**kw):
    base = dict(patient_ref="x", study_uid="u", lesion_label="l", visual_stenosis_pct=60,
                clinical_context="chronic_coronary_syndrome", consent_id="c")
    return CaseCreate(**{**base, **kw})


def test_eligibility():
    assert check_eligibility(_case()) == []
    assert check_eligibility(_case(visual_stenosis_pct=39))
    assert check_eligibility(_case(visual_stenosis_pct=91))
    assert check_eligibility(_case(clinical_context="other"))
    assert len(check_eligibility(_case(exclusions=["stemi_culprit", "bypass_graft"]))) == 2


def test_visibility_rules():
    assert not result_visible("shadow", "operator")
    assert not result_visible("shadow", "technician")
    assert result_visible("shadow", "researcher")
    assert result_visible("guided", "operator")


def test_angular_separation():
    a, b = Projection(0, 0, 15), Projection(30, 0, 15)
    assert angular_separation(a, b) == pytest.approx(30, abs=1e-6)
    assert angular_separation(a, a) == pytest.approx(0, abs=1e-6)


def q(projs, **kw):
    d = dict(nitroglycerin_given=True, no_vessel_overlap=True, min_angle_deg=25, min_fps=12.5)
    return assess_quality(projs, **{**d, **kw})


def test_quality_gate():
    good = [Projection(30, 20, 15), Projection(-30, -10, 15)]
    assert q(good).ok
    assert not q(good[:1]).ok
    assert not q([Projection(0, 0, 15), Projection(10, 0, 15)]).ok
    assert not q([Projection(30, 0, 7.5), Projection(-30, 0, 7.5)]).ok
    assert not q([Projection(30, 0, None), Projection(-30, 0, 15)]).ok
    assert not q(good, nitroglycerin_given=False).ok
    assert not q(good, no_vessel_overlap=False).ok


def test_extract_projection():
    ds = SimpleNamespace(PositionerPrimaryAngle="30", PositionerSecondaryAngle="-20", FrameTime="66.67")
    p = extract_projection(ds)
    assert p.primary_angle == 30 and p.secondary_angle == -20
    assert p.frame_rate == pytest.approx(15.0, abs=0.01)
    with pytest.raises(ValueError):
        extract_projection(SimpleNamespace())


KEY = "k" * 40


def test_pseudonym():
    a = pseudonymize("HC-1", KEY)
    assert a == pseudonymize(" HC-1 ", KEY) and a.startswith("P-")
    assert a != pseudonymize("HC-2", KEY)
    assert a != pseudonymize("HC-1", "z" * 40)
    with pytest.raises(ValueError):
        pseudonymize("HC-1", "corta")


def test_strip_dicom():
    ds = Dataset()
    ds.PatientName = "Perez^Juan"
    ds.PatientID = "123"
    ds.Modality = "XA"
    strip_dicom_identifiers(ds)
    assert "PatientName" not in ds and "PatientID" not in ds and ds.Modality == "XA"


class Row(SimpleNamespace):
    pass


def _chain(n=3):
    rows, prev = [], GENESIS
    for i in range(n):
        ts, body = f"t{i}", canonical({"i": i})
        h = compute_hash(prev, ts, "a", "r", "e", body)
        rows.append(Row(ts=ts, actor="a", role="r", event_type="e", payload=body, prev_hash=prev, hash=h))
        prev = h
    return rows


def test_audit_chain():
    rows = _chain()
    assert verify_chain(rows) == (True, None)
    rows[1].payload = canonical({"i": 99})
    assert verify_chain(rows) == (False, 1)
    rows = _chain()
    del rows[1]
    assert verify_chain(rows)[0] is False


def test_concordance_known():
    pairs = [(0.70, 0.70), (0.75, 0.78), (0.90, 0.88), (0.85, 0.90), (0.78, 0.85), (0.90, 0.75)]
    c = concordance(pairs)
    assert (c.tp, c.fp, c.tn, c.fn) == (2, 1, 2, 1)
    assert c.accuracy == pytest.approx(4 / 6)
    assert c.sensitivity == pytest.approx(2 / 3) and c.specificity == pytest.approx(2 / 3)
    lo, hi = c.accuracy_ci95
    assert 0 <= lo < c.accuracy < hi <= 1
    assert concordance([]).accuracy is None


def test_wilson_150():
    lo, hi = wilson_ci(135, 150)
    assert 0.84 < lo < 0.86 and 0.93 < hi < 0.95
