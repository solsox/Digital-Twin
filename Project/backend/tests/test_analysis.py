import io

import numpy as np
import pytest
from PIL import Image

from ml import ecg, image_model


def synthetic_ecg(bpm=75, seconds=10, fs=360):
    """Señal tipo ECG artificial (picos gaussianos + ruido), solo para probar el flujo."""
    t = np.arange(seconds * fs) / fs
    sig = np.zeros_like(t)
    for c in np.arange(0.4, seconds, 60 / bpm):
        sig += np.exp(-((t - c) ** 2) / (2 * 0.012**2))
        sig += 0.2 * np.exp(-((t - c - 0.25) ** 2) / (2 * 0.04**2))
    return sig + np.random.default_rng(1).normal(0, 0.02, t.size)


def csv_bytes(values):
    return "\n".join(f"{v:.5f}" for v in values).encode()


def png_bytes(size=(300, 300), color=(120, 60, 40)):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    return buf.getvalue()


def post_file(client, url, content, name="f.png", ctype="image/png", **data):
    return client.post(url, files={"file": (name, content, ctype)}, data=data)


def test_catalog_lists_all_three(client):
    body = client.get("/analysis").json()
    assert set(body) == {"ecg", "retina", "xray"}
    assert body["xray"]["available"] is False  # sin datos con hallazgos cardíacos/torácicos


@pytest.mark.skipif(not ecg.is_available(), reason="sin artefacto de ECG")
def test_ecg_analysis(client):
    r = post_file(client, "/analysis/ecg", csv_bytes(synthetic_ecg()), "ecg.csv", "text/csv", fs="360")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["label"] in {"N", "S", "V", "F", "Q"}
    assert abs(sum(body["probabilities"].values()) - 1) < 0.01
    assert 65 < body["heart_rate_bpm"] < 85  # señal sintética a 75 lpm
    assert "diagnóstico" in body["disclaimer"]


def test_ecg_rejects_bad_input(client):
    assert post_file(client, "/analysis/ecg", b"", "e.csv", "text/csv").status_code == 422
    assert post_file(client, "/analysis/ecg", b"hola,mundo\nabc", "e.csv", "text/csv").status_code == 422
    flat = csv_bytes(np.ones(3600))
    if ecg.is_available():
        assert post_file(client, "/analysis/ecg", flat, "e.csv", "text/csv").status_code == 422
    short = csv_bytes(synthetic_ecg(seconds=1))
    assert post_file(client, "/analysis/ecg", short, "e.csv", "text/csv").status_code == 422


def test_ecg_unavailable_model_returns_503(client, monkeypatch):
    monkeypatch.setattr(ecg, "is_available", lambda: False)
    r = post_file(client, "/analysis/ecg", csv_bytes(synthetic_ecg()), "e.csv", "text/csv")
    assert r.status_code == 503


@pytest.mark.skipif(not image_model.is_available("retina"), reason="sin artefacto de retina")
def test_retina_analysis(client):
    r = post_file(client, "/analysis/retina", png_bytes())
    assert r.status_code == 200, r.text
    body = r.json()
    assert 0 <= body["probability"] <= 1 and body["image_size"] == [300, 300]
    assert body["model_auc"] < 0.8  # la respuesta debe advertir lo débil que es el modelo


def test_image_validation(client, monkeypatch):
    monkeypatch.setattr(image_model, "is_available", lambda task: True)
    assert post_file(client, "/analysis/retina", b"%PDF-1.4", "x.pdf", "application/pdf").status_code == 415
    assert post_file(client, "/analysis/retina", b"no soy una imagen").status_code == 422
    assert post_file(client, "/analysis/retina", png_bytes((20, 20))).status_code == 422
    assert post_file(client, "/analysis/retina", b"").status_code == 422
    big = b"\x89PNG" + b"0" * (8 * 1024 * 1024 + 10)
    assert post_file(client, "/analysis/retina", big).status_code == 413
    assert post_file(client, "/analysis/otro", png_bytes()).status_code == 404


def test_xray_without_model_is_503_with_instructions(client):
    r = post_file(client, "/analysis/xray", png_bytes())
    assert r.status_code == 503
    assert "train_images" in r.json()["detail"]
