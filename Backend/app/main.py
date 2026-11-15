
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import models
from app.models import Experiment, TelemetryData, ScientificMeasurement
from app.schemas import serialize_model


# Criar as tabelas caso ainda nÃ£o existam
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NASA Fire Experiments API",
    description="API para consulta de experiÃªncias de combustÃ£o em microgravidade.",
    version="1.0.0"
)

# Permitir comunicaÃ§Ã£o com o frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "NASA Fire Experiments API",
        "status": "online",
        "documentation": "/docs"
    }


@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=f"Database unavailable: {str(error)}"
        )


@app.get("/api/experiments")
def list_experiments(db: Session = Depends(get_db)):
    statement = select(Experiment).order_by(Experiment.id)
    experiments = db.scalars(statement).all()

    return [
        serialize_model(experiment, include_relationships=True)
        for experiment in experiments
    ]


@app.get("/api/experiments/{experiment_id}")
def get_experiment(
    experiment_id: int,
    db: Session = Depends(get_db)
):
    experiment = db.get(Experiment, experiment_id)

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found"
        )

    return serialize_model(
        experiment,
        include_relationships=True
    )


@app.get("/api/telemetry")
def list_telemetry(
    experiment_id: int | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db)
):
    statement = select(TelemetryData)

    if experiment_id is not None:
        statement = statement.where(
            TelemetryData.experiment_id == experiment_id
        )

    statement = statement.order_by(
        TelemetryData.experiment_id,
        TelemetryData.time_s
    ).limit(limit)

    records = db.scalars(statement).all()

    return [
        serialize_model(record)
        for record in records
    ]


@app.get("/api/documents")
def list_documents():
    documents_dir = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "processed"
        / "documents"
    )

    if not documents_dir.exists():
        return []

    documents = []

    for file_path in documents_dir.glob("*.json"):
        documents.append({
            "filename": file_path.name,
            "path": str(file_path),
            "size_bytes": file_path.stat().st_size
        })

    return documents


@app.get("/api/experiments/{experiment_id}/measurements")
def list_scientific_measurements(
    experiment_id: int,
    sensor: str | None = None,
    variable: str | None = None,
    limit: int = Query(default=5000, ge=1, le=20000),
    db: Session = Depends(get_db),
):
    experiment = db.get(Experiment, experiment_id)

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found"
        )

    statement = select(ScientificMeasurement).where(
        ScientificMeasurement.experiment_id == experiment_id
    )

    if sensor:
        statement = statement.where(
            ScientificMeasurement.sensor == sensor
        )

    if variable:
        statement = statement.where(
            ScientificMeasurement.variable_name == variable
        )

    statement = statement.order_by(
        ScientificMeasurement.time_s,
        ScientificMeasurement.sensor,
        ScientificMeasurement.variable_name,
    ).limit(limit)

    records = db.scalars(statement).all()

    return {
        "experiment_id": experiment_id,
        "mission_code": experiment.mission_code,
        "count": len(records),
        "measurements": [
            {
                "id": item.id,
                "sensor": item.sensor,
                "time_s": item.time_s,
                "variable": item.variable_name,
                "value": item.value,
                "unit": item.unit,
                "source_file": item.source_file,
                "is_synthetic": item.is_synthetic,
            }
            for item in records
        ],
    }
