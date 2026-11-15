import pandas as pd

from sqlalchemy import select

from app.database import SessionLocal
from app.models import TelemetryData


def parse_bool(value):
    """
    Converter um valor de CSV para booleano.

    Valores como "false", "0" ou "no" são falsos; qualquer outro
    valor não vazio é verdadeiro. Sem o parser, bool("false")
    devolveria True, pois a cadeia não está vazia.
    """

    if pd.isna(value):
        return False

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {"1", "true", "sim", "yes", "on"}


def load_telemetry_csv(file_path):
    df = pd.read_csv(file_path)

    required = [
        "experiment_id",
        "time_s",
        "flame_temperature_k",
        "burning_rate_mm_s",
        "soot_emission"
    ]

    missing = [
        column for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Colunas obrigatórias em falta: {missing}"
        )

    inserted = 0
    skipped = 0

    with SessionLocal() as session:
        try:
            for _, row in df.iterrows():
                if pd.isna(row["experiment_id"]) or pd.isna(row["time_s"]):
                    skipped += 1
                    continue

                experiment_id = int(row["experiment_id"])
                time_s = float(row["time_s"])

                existing = session.scalar(
                    select(TelemetryData).where(
                        TelemetryData.experiment_id == experiment_id,
                        TelemetryData.time_s == time_s
                    )
                )

                if existing:
                    skipped += 1
                    continue

                record = TelemetryData(
                    experiment_id=experiment_id,
                    time_s=time_s,
                    flame_temperature_k=(
                        None if pd.isna(row["flame_temperature_k"])
                        else float(row["flame_temperature_k"])
                    ),
                    burning_rate_mm_s=(
                        None if pd.isna(row["burning_rate_mm_s"])
                        else float(row["burning_rate_mm_s"])
                    ),
                    soot_emission=(
                        None if pd.isna(row["soot_emission"])
                        else float(row["soot_emission"])
                    ),
                    is_synthetic=(
                        parse_bool(row["is_synthetic"])
                        if "is_synthetic" in df.columns
                        else False
                    )
                )

                session.add(record)
                inserted += 1

            session.commit()

        except Exception:
            session.rollback()
            raise

    return {
        "inserted": inserted,
        "skipped": skipped
    }