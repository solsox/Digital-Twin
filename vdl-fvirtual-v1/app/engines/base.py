"""Contrato del motor de cálculo. TODO motor (simulado o de proveedor) implementa esta interfaz."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class EngineInput:
    study_uid: str
    lesion_label: str
    visual_stenosis_pct: int
    dicom_paths: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EngineResult:
    analyzable: bool
    value: Optional[float]          # FFR virtual en [0, 1]; None si no analizable
    engine_name: str
    engine_version: str
    notes: str = ""


class Engine(ABC):
    name: str
    version: str

    @abstractmethod
    def compute(self, data: EngineInput) -> EngineResult:
        """Debe ser determinista para la misma entrada y versión, y no lanzar excepciones
        por casos no analizables (devolver analyzable=False)."""
