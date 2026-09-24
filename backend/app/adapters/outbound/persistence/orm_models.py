"""Modelos ORM de SQLAlchemy para la persistencia en base de datos relacional."""

from datetime import datetime
from sqlalchemy import DateTime, Float, String, UniqueConstraint
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
