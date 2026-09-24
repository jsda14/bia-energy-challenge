"""Funciones para inicialización de motor de base de datos, creación de tablas y gestión de sesiones."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.adapters.outbound.persistence.orm_models import Base


def create_db_engine(database_url: str) -> Engine:
    """Crea el engine de SQLAlchemy para la URL de conexión dada.

    Args:
        database_url: Cadena de conexión (ej. 'sqlite:///./bia_energy.db').

    Returns:
        Instancia de SQLAlchemy Engine configurada.
    """
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(database_url, connect_args=connect_args)


def create_all_tables(engine: Engine) -> None:
    """Crea todas las tablas definidas en Base.metadata si no existen ya.

    Es idempotente: si las tablas ya existen, no modifica ni elimina datos existentes (CB-05).

    Args:
        engine: Instancia de SQLAlchemy Engine conectada a la base de datos.
    """
    Base.metadata.create_all(bind=engine)


def get_session(engine: Engine) -> Session:
    """Retorna una nueva sesión de SQLAlchemy vinculada al engine dado.

    Args:
        engine: Instancia de SQLAlchemy Engine.

    Returns:
        Nueva sesión de SQLAlchemy con expire_on_commit=False.
    """
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    return session_factory()
