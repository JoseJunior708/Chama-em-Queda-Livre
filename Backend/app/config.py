"""Configuração do módulo de IA, lida do ambiente e do ficheiro .env."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Categorias fixas de experiência (a ordem é a apresentada ao utilizador).
CATEGORIAS: list[str] = [
    "Segurança contra incêndios em naves",
    "Gotas (droplets)",
    "Chamas gasosas",
    "Combustíveis sólidos",
    "Fluidos reactivos supercríticos",
    "Outro",
]

# Resposta obrigatória quando as fontes não respondem à pergunta.
NAO_ENCONTREI = "Não encontrei essa informação nos documentos."


def _caminho(valor: str) -> Path:
    p = Path(valor)
    return p if p.is_absolute() else BASE_DIR / p


def _bool(valor: str) -> bool:
    return valor.strip().lower() in {"1", "true", "sim", "yes", "on"}


@dataclass
class Settings:
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    embed_model: str = "gemini-embedding-2"
    embed_dim: int = 768
    docs_dir: Path = field(default_factory=lambda: BASE_DIR / "data" / "docs")
    index_dir: Path = field(default_factory=lambda: BASE_DIR / "data" / "index")
    chunk_size: int = 1200
    chunk_overlap: int = 200
    embed_batch: int = 50
    max_retries: int = 6
    top_k: int = 8
    peso_vetorial: float = 0.65
    verify_judge: bool = True
    timeout: float = 60.0


def get_settings() -> Settings:
    """Lê a configuração do ambiente em cada chamada (facilita os testes)."""
    env = os.environ.get
    return Settings(
        gemini_api_key=env("GEMINI_API_KEY", "").strip(),
        gemini_model=env("GEMINI_MODEL", "gemini-3.6-flash").strip(),
        embed_model=env("GEMINI_EMBED_MODEL", "gemini-embedding-2").strip(),
        embed_dim=int(env("GEMINI_EMBED_DIM", "768")),
        docs_dir=_caminho(env("DOCS_DIR", "data/docs")),
        index_dir=_caminho(env("INDEX_DIR", "data/index")),
        chunk_size=int(env("CHUNK_SIZE", "1200")),
        chunk_overlap=int(env("CHUNK_OVERLAP", "200")),
        embed_batch=min(100, int(env("EMBED_BATCH", "50"))),
        max_retries=int(env("MAX_RETRIES", "6")),
        top_k=int(env("TOP_K", "8")),
        peso_vetorial=float(env("PESO_VETORIAL", "0.65")),
        verify_judge=_bool(env("VERIFY_JUDGE", "true")),
        timeout=float(env("GEMINI_TIMEOUT", "60")),
    )
