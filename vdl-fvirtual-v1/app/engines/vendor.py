"""Adaptador del motor del proveedor (POR IMPLEMENTAR).

Requisitos antes de implementarlo (ver plan maestro):
  * Registro sanitario / marco regulatorio confirmado con Asuntos Regulatorios.
  * Contrato de datos: dónde se procesa, qué se envía (idealmente DICOM desidentificado), retención.
  * Versión del algoritmo devuelta en cada resultado (reproducibilidad).
  * Tiempos de espera y reintentos definidos; un fallo debe devolver analyzable=False,
    nunca bloquear la sala.
"""
from __future__ import annotations

from app.engines.base import Engine, EngineInput, EngineResult


class VendorEngine(Engine):
    name = "vendor"
    version = "unset"

    def compute(self, data: EngineInput) -> EngineResult:
        raise NotImplementedError("Integrar el SDK o servicio del proveedor aquí")
