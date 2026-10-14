"""Configuración centralizada. Los valores se leen de variables de entorno o de un archivo .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Sin credenciales por defecto: debe definirse en .env (ver .env.example).
    database_url: str = "sqlite:///./gemelo_dev.db"
    # Orígenes permitidos para CORS, separados por coma.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
