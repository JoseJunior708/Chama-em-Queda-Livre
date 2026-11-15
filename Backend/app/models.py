
from datetime import date

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# Relação muitos-para-muitos entre experiências e combustíveis.
experiment_fuels = Table(
    "experiment_fuels",
    Base.metadata,

    Column(
        "experiment_id",
        ForeignKey("experiments.id", ondelete="CASCADE"),
        primary_key=True,
    ),

    Column(
        "fuel_id",
        ForeignKey("fuels.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    mission_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    experiment_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    gravity_level: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    source_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    data_status: Mapped[str] = mapped_column(
        String(20),
        default="demo",
        nullable=False,
    )

    # Uma experiência pode utilizar vários combustíveis.
    fuels: Mapped[list["Fuel"]] = relationship(
        secondary=experiment_fuels,
        back_populates="experiments",
    )

    # Uma experiência pode ter várias condições ambientais.
    environments: Mapped[list["Environment"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
    )

    # Uma experiência pode ter várias medições.
    telemetry: Mapped[list["TelemetryData"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
    )

    measurements: Mapped[list["ScientificMeasurement"]] = relationship(
    back_populates="experiment",
    cascade="all, delete-orphan",
)


class Fuel(Base):
    __tablename__ = "fuels"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    fuel_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    chemical_composition: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    physical_state: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    experiments: Mapped[list["Experiment"]] = relationship(
        secondary=experiment_fuels,
        back_populates="fuels",
    )

    __table_args__ = (
        UniqueConstraint(
            "fuel_type",
            "chemical_composition",
            "physical_state",
            name="uq_fuel_definition",
        ),
    )


class Environment(Base):
    __tablename__ = "environments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    pressure_kpa: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    oxygen_level_pct: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    diluent_gas: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    initial_temperature_k: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    experiment: Mapped["Experiment"] = relationship(
        back_populates="environments",
    )


class TelemetryData(Base):
    __tablename__ = "telemetry_data"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    environment_id: Mapped[int | None] = mapped_column(
        ForeignKey("environments.id", ondelete="SET NULL"),
        nullable=True,
    )

    time_s: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    flame_temperature_k: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    burning_rate_mm_s: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    soot_emission: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    is_synthetic: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    experiment: Mapped["Experiment"] = relationship(
        back_populates="telemetry",
    )

    environment: Mapped["Environment | None"] = relationship()


class ScientificMeasurement(Base):
    __tablename__ = "scientific_measurements"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sensor: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    time_s: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    variable_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    value: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    unit: Mapped[str] = mapped_column(
        String(30), nullable=False
    )

    source_file: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    is_synthetic: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    experiment: Mapped["Experiment"] = relationship(
        back_populates="measurements"
    )

    __table_args__ = (
        UniqueConstraint(
            "experiment_id",
            "sensor",
            "time_s",
            "variable_name",
            name="uq_scientific_measurement",
        ),
    )
