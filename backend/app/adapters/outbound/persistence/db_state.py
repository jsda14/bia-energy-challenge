from sqlalchemy import Engine
from app.adapters.outbound.persistence.db import create_db_engine
from app.config import get_settings

_engine: Engine | None = None

def get_or_create_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_db_engine(get_settings().database_url)
    return _engine
