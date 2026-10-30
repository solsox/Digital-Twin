"""MOTOR SIMULADO — NO CLÍNICO. Solo para desarrollo, pruebas e integración.

El valor se deriva de la estenosis visual más un ruido determinista. No representa ninguna
fisiología real y no debe usarse jamás para decidir conductas.
"""
from __future__ import annotations

import hashlib

from app.engines.base import Engine, EngineInput, EngineResult


class MockEngine(Engine):
    name = "mock-NON-CLINICAL"
    version = "0.1"

    def compute(self, data: EngineInput) -> EngineResult:
        base = 1.0 - (data.visual_stenosis_pct / 100) ** 2 * 0.45
        h = hashlib.sha256(f"{data.study_uid}|{data.lesion_label}".encode()).digest()
        noise = (h[0] / 255 - 0.5) * 0.08          # ±0.04
        value = round(max(0.3, min(1.0, base + noise)), 2)
        return EngineResult(True, value, self.name, self.version, "Valor simulado; no clínico")
