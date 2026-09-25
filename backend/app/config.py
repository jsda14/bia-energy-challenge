"""Configuración global de la aplicación mediante variables de entorno."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuraciones del sistema leídas desde variables de entorno con prefijo BIA_."""

    database_url: str = "sqlite:///./bia_energy.db"
    anthropic_api_key: str | None = None
    claude_model: str = "claude-sonnet-4-6"

    model_config = {"env_prefix": "BIA_", "env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    """Retorna una instancia de Settings, leyendo variables de entorno con prefijo BIA_ si están definidas."""
    return Settings()
