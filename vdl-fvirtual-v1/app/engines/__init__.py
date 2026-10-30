from app.config import Settings
from app.engines.base import Engine
from app.engines.mock import MockEngine
from app.engines.vendor import VendorEngine


def build_engine(settings: Settings) -> Engine:
    if settings.engine == "mock":
        if not settings.allow_mock_engine:
            raise ValueError("Motor simulado deshabilitado")
        return MockEngine()
    return VendorEngine()
