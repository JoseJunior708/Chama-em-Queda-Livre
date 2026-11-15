from pathlib import Path

models_path = Path("app/models.py")
source = models_path.read_text(encoding="utf-8")

relationship = '''    measurements: Mapped[list["ScientificMeasurement"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
    )
'''

anchor = '''    telemetry: Mapped[list["TelemetryData"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
    )
'''

if "class ScientificMeasurement(Base):" not in source:
    if anchor not in source:
        raise RuntimeError("Não encontrei a relação telemetry em models.py")

    source = source.replace(anchor, anchor + "\n" + relationship, 1)

    source += '''

class ScientificMeasurement(Base):
    __tablename__ = "scientific_measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sensor: Mapped[str] = mapped_column(String(50), nullable=False)
    time_s: Mapped[float] = mapped_column(Float, nullable=False)
    variable_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)

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
'''

    models_path.write_text(source, encoding="utf-8")
    print("[OK] ScientificMeasurement adicionada a models.py")
else:
    print("[OK] ScientificMeasurement já existe")

# Importar apenas depois de atualizar o modelo.
from sqlalchemy import func, select
from app.database import Base, engine, SessionLocal
from app.models import Experiment, ScientificMeasurement

Base.metadata.create_all(bind=engine)
print("[OK] Estrutura da base de dados verificada")

RAW = Path("data/processed/telemetry/FLEX-007")

CONFIG = {
    "ColorCamData": {
        "flame_diameter_mm": "mm",
        "flame_standoff_mm": "not_specified",
    },
    "DropletData": {
        "droplet_diameter_mm": "mm",
        "droplet_x_mm": "mm",
        "droplet_y_mm": "mm",
    },
    "LLUVData": {
        "flame_diameter_mm": "mm",
        "flame_standoff_mm": "not_specified",
        "droplet_x_mm": "mm",
        "droplet_z_mm": "mm",
    },
}

inserted = 0
skipped = 0
missing = 0

with SessionLocal() as session:
    experiment = session.scalar(
        select(Experiment).where(Experiment.mission_code == "PSI-69")
    )

    if experiment is None:
        raise RuntimeError("Experiência PSI-69 não encontrada")

    experiment_id = experiment.id

    existing = session.scalars(
        select(ScientificMeasurement).where(
            ScientificMeasurement.experiment_id == experiment_id
        )
    ).all()

    keys = {
        (item.sensor, item.time_s, item.variable_name)
        for item in existing
    }

    try:
        for sensor, variables in CONFIG.items():
            file_path = RAW / f"{sensor}.csv"

            if not file_path.exists():
                raise FileNotFoundError(file_path)

            with file_path.open(encoding="utf-8-sig", newline="") as file:
                import csv
                reader = csv.DictReader(file)

                for row in reader:
                    time_s = float(row["time_s"])

                    for variable, unit in variables.items():
                        raw_value = row.get(variable, "").strip()
                        value = float(raw_value) if raw_value else None

                        if value is None:
                            missing += 1

                        key = (sensor, time_s, variable)

                        if key in keys:
                            skipped += 1
                            continue

                        session.add(
                            ScientificMeasurement(
                                experiment_id=experiment_id,
                                sensor=sensor,
                                time_s=time_s,
                                variable_name=variable,
                                value=value,
                                unit=unit,
                                source_file=file_path.name,
                                is_synthetic=False,
                            )
                        )

                        keys.add(key)
                        inserted += 1

        session.commit()

    except Exception:
        session.rollback()
        raise

    total = session.scalar(
        select(ScientificMeasurement)
        .where(ScientificMeasurement.experiment_id == experiment_id)
        .with_only_columns(func.count())
        .select_from(ScientificMeasurement)
    )

    print("\n========== IMPORTAÇÃO FLEX-007 ==========")
    print(f"Experiência: PSI-69 (ID {experiment_id})")
    print(f"Novas medições: {inserted}")
    print(f"Valores ausentes preservados: {missing}")
    print(f"Registos já existentes ignorados: {skipped}")
    print(f"Total na base de dados: {total}")
    print("[OK] Transação concluída")
