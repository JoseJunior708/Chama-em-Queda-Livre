
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Carrega as variáveis do ficheiro .env, caso exista.
load_dotenv()

# SQLite é a base de dados padrão durante o desenvolvimento.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./nasa_fire.db"
)

engine_options = {}

if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {
        "check_same_thread": False
    }

# Criar a ligação à base de dados.
engine = create_engine(
    DATABASE_URL,
    echo=False,
    **engine_options
)


# Activar chaves estrangeiras no SQLite.
if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Classe base de todos os modelos.
class Base(DeclarativeBase):
    pass


# Fábrica de sessões.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)


def create_database():
    """Criar todas as tabelas registadas nos modelos."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Disponibilizar uma sessão para a futura API."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
