
from datetime import date

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Experiment, Fuel, Environment, TelemetryData


# Os valores ambientais e de telemetria são ilustrativos.
# Não representam medições oficiais da NASA.

EXPERIMENTS = [
    {
        "mission_code": "PSI-69",
        "title": "Flame Extinguishment Experiment (FLEX)",
        "experiment_date": date(2007, 8, 1),
        "summary": (
            "Estudo da combustão de gotas de combustível líquido "
            "em microgravidade e da eficácia de agentes gasosos "
            "de supressão de incêndios."
        ),
        "gravity_level": "Microgravidade - ISS",
        "source_url": (
            "https://psi.nasa.gov/physci/repo/data/investigations/PSI-69"
        ),
        "fuels": [
            ("n-heptano", "C7H16", "líquido"),
            ("metanol", "CH3OH", "líquido"),
        ],
        "environment": {
            "pressure_kpa": 101.3,
            "oxygen_level_pct": 21.0,
            "diluent_gas": "Nitrogénio",
            "initial_temperature_k": 298.15,
        },
    },
    {
        "mission_code": "CFI",
        "title": "Cool Flames Investigation",
        "experiment_date": None,
        "summary": (
            "Investigação de combustão de baixa temperatura "
            "e chamas frias em gotas de combustíveis."
        ),
        "gravity_level": "Microgravidade - ISS",
        "source_url": "https://gipoc.grc.nasa.gov/wp/fcf-cir/mdca/cfi/",
        "fuels": [
            ("n-heptano", "C7H16", "líquido"),
        ],
        "environment": {
            "pressure_kpa": 101.3,
            "oxygen_level_pct": 21.0,
            "diluent_gas": "Nitrogénio",
            "initial_temperature_k": 298.15,
        },
    },
    {
        "mission_code": "PSI-25",
        "title": "Burning and Suppression of Solids-II (BASS-II)",
        "experiment_date": date(2010, 1, 1),
        "summary": (
            "Estudo da ignição, crescimento, propagação e extinção "
            "de chamas em amostras de combustíveis sólidos."
        ),
        "gravity_level": "Microgravidade - ISS",
        "source_url": (
            "https://psi.nasa.gov/physci/repo/data/investigations/PSI-25"
        ),
        "fuels": [
            ("amostras sólidas variadas", None, "sólido"),
        ],
        "environment": {
            "pressure_kpa": None,
            "oxygen_level_pct": None,
            "diluent_gas": None,
            "initial_temperature_k": None,
        },
    },
    {
        "mission_code": "ACME-CLD",
        "title": "ACME - Coflow Laminar Diffusion Flame",
        "experiment_date": None,
        "summary": (
            "Estudo de chamas gasosas de difusão laminar "
            "em condições de microgravidade."
        ),
        "gravity_level": "Microgravidade - ISS",
        "source_url": (
            "https://science.nasa.gov/biological-physical/investigations/acme/"
        ),
        "fuels": [
            ("combustível gasoso (espécie a confirmar)", None, "gasoso"),
        ],
        "environment": {
            "pressure_kpa": 101.3,
            "oxygen_level_pct": 21.0,
            "diluent_gas": "A confirmar",
            "initial_temperature_k": 298.15,
        },
    },
    {
        "mission_code": "PSI-107",
        "title": "Smoke Point In Co-flow Experiment (SPICE)",
        "experiment_date": None,
        "summary": (
            "Investigação das propriedades do ponto de fumo "
            "em chamas de difusão não flutuantes."
        ),
        "gravity_level": "Microgravidade - ISS",
        "source_url": (
            "https://psi.nasa.gov/physci/repo/data/investigations/PSI-107"
        ),
        "fuels": [
            ("combustível gasoso (espécie a confirmar)", None, "gasoso"),
        ],
        "environment": {
            "pressure_kpa": None,
            "oxygen_level_pct": None,
            "diluent_gas": None,
            "initial_temperature_k": None,
        },
    },
]


def get_or_create_fuel(session, fuel_data):
    fuel_type, composition, physical_state = fuel_data

    statement = select(Fuel).where(
        Fuel.fuel_type == fuel_type,
        Fuel.chemical_composition == composition,
        Fuel.physical_state == physical_state,
    )

    fuel = session.scalar(statement)

    if fuel is None:
        fuel = Fuel(
            fuel_type=fuel_type,
            chemical_composition=composition,
            physical_state=physical_state,
        )
        session.add(fuel)
        session.flush()

    return fuel


def add_demo_telemetry(session, experiment, environment):
    # Dados sintéticos exclusivamente para testes.
    samples = [
        (0.0, 300.0, 0.00, 0.00),
        (1.0, 450.0, 0.12, 0.01),
        (2.0, 520.0, 0.10, 0.02),
    ]

    for time_s, temp_k, burn_rate, soot in samples:
        telemetry = TelemetryData(
            experiment=experiment,
            environment=environment,
            time_s=time_s,
            flame_temperature_k=temp_k,
            burning_rate_mm_s=burn_rate,
            soot_emission=soot,
            is_synthetic=True,
        )

        session.add(telemetry)


def seed_database():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        try:
            for item in EXPERIMENTS:

                # Verificar se a experiência já existe.
                statement = select(Experiment).where(
                    Experiment.mission_code == item["mission_code"]
                )

                experiment = session.scalar(statement)

                if experiment is not None:
                    print(
                        f"[EXISTE] {item['mission_code']} - "
                        "não foi duplicada."
                    )
                    continue

                # Criar experiência.
                experiment = Experiment(
                    mission_code=item["mission_code"],
                    title=item["title"],
                    experiment_date=item["experiment_date"],
                    summary=item["summary"],
                    gravity_level=item["gravity_level"],
                    source_url=item["source_url"],
                    data_status="demo",
                )

                # Primeiro adicionar a experiência à sessão.
                session.add(experiment)
                session.flush()

                # Associar combustíveis depois da experiência
                # estar registada na sessão.
                for fuel_data in item["fuels"]:
                    fuel = get_or_create_fuel(session, fuel_data)
                    experiment.fuels.append(fuel)

                session.flush()

                # Criar condição ambiental.
                environment = Environment(
                    experiment=experiment,
                    pressure_kpa=item["environment"]["pressure_kpa"],
                    oxygen_level_pct=item["environment"]["oxygen_level_pct"],
                    diluent_gas=item["environment"]["diluent_gas"],
                    initial_temperature_k=(
                        item["environment"]["initial_temperature_k"]
                    ),
                    notes="Condição ilustrativa para testes.",
                )

                session.add(environment)
                session.flush()

                # Criar telemetria sintética.
                add_demo_telemetry(
                    session,
                    experiment,
                    environment,
                )

                print(f"[CRIADA] {experiment.title}")

            session.commit()
            print("\nBase de dados inicializada com sucesso!")

        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    seed_database()
