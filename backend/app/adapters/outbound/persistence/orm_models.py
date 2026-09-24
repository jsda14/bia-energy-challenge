"""Modelos ORM de SQLAlchemy para la persistencia en base de datos relacional."""

from datetime import datetime
from sqlalchemy import DateTime, Float, String, UniqueConstraint, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos ORM de la aplicación."""

    pass


class MeterORM(Base):
    """Entidad de base de datos para medidores eléctricos registrados."""

    __tablename__ = "meters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meter_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class ReadingORM(Base):
    """Entidad de base de datos para lecturas horarias de consumo y variables eléctricas."""

    __tablename__ = "readings"
    __table_args__ = (
        UniqueConstraint("meter_id", "timestamp", name="uq_reading_meter_ts"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meter_id: Mapped[str] = mapped_column(String, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    consumption_kwh: Mapped[float] = mapped_column(Float)
    voltage_v: Mapped[float] = mapped_column(Float)
    current_a: Mapped[float] = mapped_column(Float)
    power_factor: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String)


class EventORM(Base):
    """Entidad de base de datos para eventos operativos conocidos asociados a medidores."""

    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint(
            "meter_id",
            "event_timestamp",
            "event_type",
            name="uq_event_meter_ts_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meter_id: Mapped[str] = mapped_column(String, index=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    event_type: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)


class AnomalyORM(Base):
    __tablename__ = "anomalies"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    meter_id: Mapped[str] = mapped_column(String, index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    type: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(String)
    recommended_action: Mapped[str] = mapped_column(String)
    baseline_kwh: Mapped[float] = mapped_column(Float)
    observed_kwh: Mapped[float] = mapped_column(Float)
    variation_pct: Mapped[float] = mapped_column(Float)
    affected_variables: Mapped[str] = mapped_column(String)
    correlated_event: Mapped[str | None] = mapped_column(String, nullable=True)
    window_start: Mapped[datetime] = mapped_column(DateTime)
    window_end: Mapped[datetime] = mapped_column(DateTime)

class AnalysisRunORM(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    requested_meter_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime] = mapped_column(DateTime)
    anomalies_detected_count: Mapped[int] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

