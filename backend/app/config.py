"""Configuración global de la aplicación mediante variables de entorno."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuraciones del sistema leídas desde variables de entorno con prefijo BIA_."""

    database_url: str = "sqlite:///./bia_energy.db"

    model_config = {"env_prefix": "BIA_"}


def get_settings() -> Settings:
    """Retorna una instancia de Settings, leyendo variables de entorno con prefijo BIA_ si están definidas."""
    return Settings()
