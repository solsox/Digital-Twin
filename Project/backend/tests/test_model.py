from ml.model import classify, predict_risk

BASE = {
    "age": 30,
    "gender": "female",
    "weight": 60,
    "height_cm": 165,
    "systolic_bp": 115,
    "diastolic_bp": 75,
    "cholesterol": 170,
}


def test_score_is_always_a_probability():
    extreme = {**BASE, "age": 120, "systolic_bp": 300, "diastolic_bp": 200, "cholesterol": 600}
    for data in (BASE, extreme):
        assert 0.0 <= predict_risk(data).score <= 1.0


def test_healthy_profile_is_low():
    assert predict_risk(BASE).level == "bajo"


def test_risky_profile_is_high():
    risky = {**BASE, "gender": "male", "age": 65, "systolic_bp": 170,
             "diastolic_bp": 100, "cholesterol": 280, "weight": 105}
    assert predict_risk(risky).level == "alto"


def test_risk_increases_with_each_factor():
    base = predict_risk(BASE).score
    for field, value in [("age", 55), ("systolic_bp", 160), ("cholesterol", 260)]:
        assert predict_risk({**BASE, field: value}).score > base


def test_factors_explain_the_result():
    result = predict_risk({**BASE, "cholesterol": 300})
    assert result.factors["colesterol"] > 0
    assert "imc" in result.factors


def test_works_without_height():
    data = {k: v for k, v in BASE.items() if k != "height_cm"}
    assert "imc" not in predict_risk(data).factors


def test_classify_thresholds():
    assert classify(0.05) == "bajo"
    assert classify(0.2) == "medio"
    assert classify(0.6) == "alto"
