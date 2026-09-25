from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from app.adapters.outbound.persistence.db import get_session
from app.adapters.outbound.persistence.db_state import get_or_create_engine

def get_db_session() -> Generator[Session, None, None]:
    session = get_session(get_or_create_engine())
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Stubs for Dependency Injection.
# These will be overridden in main.py via app.dependency_overrides.

def get_analyze_meter_use_case():
    raise NotImplementedError

def get_dashboard_summary_use_case():
    raise NotImplementedError

def get_list_meters_use_case():
    raise NotImplementedError

def get_meter_detail_use_case():
    raise NotImplementedError

def get_list_anomalies_use_case():
    raise NotImplementedError

def get_anomaly_detail_use_case():
    raise NotImplementedError

def get_regenerate_explanation_use_case():
    raise NotImplementedError
