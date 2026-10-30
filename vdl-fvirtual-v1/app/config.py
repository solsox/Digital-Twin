"""Configuración. Todo sale del entorno; nada sensible vive en el código."""
from __future__ import annotations

import os
from dataclasses import dataclass

VALID_MODES = ("shadow", "guided")
VALID_ENGINES = ("mock", "vendor")


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./vdl.db"
    mode: str = "shadow"
    engine: str = "mock"
    allow_mock_engine: bool = False
    api_key: str = ""
    pseudonym_key: str = ""
    defer_above: float = 0.85
    favor_below: float = 0.75
    min_angle_deg: float = 25.0
    min_fps: float = 12.5

    @classmethod
    def from_env(cls) -> "Settings":
        e = os.environ
        return cls(
            database_url=e.get("DATABASE_URL", cls.database_url),
            mode=e.get("MODE", cls.mode),
            engine=e.get("ENGINE", cls.engine),
            allow_mock_engine=e.get("ALLOW_MOCK_ENGINE", "false").lower() == "true",
            api_key=e.get("API_KEY", ""),
            pseudonym_key=e.get("PSEUDONYM_KEY", ""),
            defer_above=float(e.get("DEFER_ABOVE", cls.defer_above)),
            favor_below=float(e.get("FAVOR_BELOW", cls.favor_below)),
            min_angle_deg=float(e.get("MIN_ANGLE_DEG", cls.min_angle_deg)),
            min_fps=float(e.get("MIN_FPS", cls.min_fps)),
        )

    def validate(self) -> None:
        if self.mode not in VALID_MODES:
            raise ValueError(f"MODE debe ser uno de {VALID_MODES}")
        if self.engine not in VALID_ENGINES:
            raise ValueError(f"ENGINE debe ser uno de {VALID_ENGINES}")
        if len(self.api_key) < 16:
            raise ValueError("API_KEY debe tener al menos 16 caracteres")
        if len(self.pseudonym_key) < 32:
            raise ValueError("PSEUDONYM_KEY debe tener al menos 32 caracteres")
        if self.engine == "mock" and not self.allow_mock_engine:
            raise ValueError("El motor simulado está deshabilitado (ALLOW_MOCK_ENGINE=false)")
