def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_predict_is_stateless(client, valid_patient):
    r = client.post("/predict", json=valid_patient)
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["score"] <= 1
    assert body["level"] in {"bajo", "medio", "alto"}
    assert client.get("/patients").json() == []


def test_predict_rejects_missing_and_invalid_fields(client, valid_patient):
    missing = {k: v for k, v in valid_patient.items() if k != "age"}
    assert client.post("/predict", json=missing).status_code == 422
    assert client.post("/predict", json={**valid_patient, "age": -5}).status_code == 422
    assert client.post("/predict", json={**valid_patient, "gender": "x"}).status_code == 422
    inverted = {**valid_patient, "systolic_bp": 80, "diastolic_bp": 90}
    assert client.post("/predict", json=inverted).status_code == 422


def test_unknown_fields_do_not_break_creation(client, valid_patient):
    r = client.post("/patients", json={**valid_patient, "hacker": "x"})
    assert r.status_code == 201
    assert "hacker" not in r.json()


def test_patient_lifecycle_and_history(client, valid_patient):
    created = client.post("/patients", json=valid_patient)
    assert created.status_code == 201
    pid = created.json()["id"]

    p1 = client.post(f"/patients/{pid}/predictions").json()
    worse = {**valid_patient, "systolic_bp": 170, "diastolic_bp": 105, "cholesterol": 280}
    assert client.put(f"/patients/{pid}", json=worse).status_code == 200
    p2 = client.post(f"/patients/{pid}/predictions").json()
    assert p2["score"] > p1["score"]

    history = client.get(f"/patients/{pid}/predictions").json()
    assert [h["id"] for h in history] == [p1["id"], p2["id"]]

    assert client.delete(f"/patients/{pid}").status_code == 204
    assert client.get(f"/patients/{pid}").status_code == 404


def test_not_found(client):
    assert client.get("/patients/999").status_code == 404
    assert client.post("/patients/999/predictions").status_code == 404
    assert client.get("/patients/999/predictions").status_code == 404


def test_simulation_compares_without_saving(client, valid_patient):
    pid = client.post("/patients", json=valid_patient).json()["id"]
    better = client.post(
        f"/patients/{pid}/simulate",
        json={"systolic_bp_delta": -15, "diastolic_bp_delta": -8, "cholesterol_delta": -40},
    )
    assert better.status_code == 200
    body = better.json()
    assert body["scenario"]["score"] < body["baseline"]["score"]
    assert body["score_change"] < 0

    worse = client.post(f"/patients/{pid}/simulate", json={"cholesterol_delta": 100}).json()
    assert worse["score_change"] > 0

    # Sin cambios: el escenario coincide con la base. Y no se guardó ninguna predicción.
    same = client.post(f"/patients/{pid}/simulate", json={}).json()
    assert same["score_change"] == 0
    assert client.get(f"/patients/{pid}/predictions").json() == []
    assert client.get(f"/patients/{pid}").json()["cholesterol"] == valid_patient["cholesterol"]


def test_simulation_rejects_invalid_scenarios(client, valid_patient):
    pid = client.post("/patients", json=valid_patient).json()["id"]
    # sistólica 130 - 60 = 70 queda por debajo de la diastólica (85)
    r = client.post(f"/patients/{pid}/simulate", json={"systolic_bp_delta": -60})
    assert r.status_code == 422
    assert client.post(f"/patients/{pid}/simulate", json={"cholesterol_delta": 9999}).status_code == 422
    assert client.post("/patients/999/simulate", json={}).status_code == 404
