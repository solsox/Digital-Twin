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
