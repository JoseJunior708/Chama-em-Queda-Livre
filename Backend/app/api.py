"""API HTTP (FastAPI) do módulo de IA. Arranque: uvicorn app.api:app --reload --port 8000"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import CATEGORIAS
from .llm import LLMError
from .rag import Motor

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Chama em Queda Livre — Módulo de IA",
              description="Busca, resumos, comparações e perguntas com fontes verificadas sobre "
                          "experiências da NASA de combustão em microgravidade.",
              version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_motor: Motor | None = None


def motor() -> Motor:
    global _motor
    if _motor is None:
        _motor = Motor()
    return _motor


def definir_motor(m: Motor | None) -> None:
    """Permite injectar um motor (usado nos testes)."""
    global _motor
    _motor = m


def _executar(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except KeyError as e:
        raise HTTPException(404, str(e).strip("'\""))
    except ValueError as e:
        raise HTTPException(409 if "Índice vazio" in str(e) else 400, str(e))
    except LLMError as e:
        raise HTTPException(503, f"Serviço de IA indisponível: {e}")


# ------------------------------------------------------------------ modelos

class PedidoPergunta(BaseModel):
    pergunta: str = Field(min_length=2)
    categoria: Optional[str] = None
    doc_id: Optional[str] = None


class PedidoResumo(BaseModel):
    doc_id: str


class PedidoComparacao(BaseModel):
    doc_ids: list[str] = Field(min_length=2)


class Fonte(BaseModel):
    tag: str
    doc_id: str
    titulo: str
    pagina: int
    text: str
    url: Optional[str] = None


class Frase(BaseModel):
    i: int
    frase: str
    fontes: list[str]
    estado: str
    motivo: str


class Verificacao(BaseModel):
    fiavel: bool
    frases: list[Frase]


class Resposta(BaseModel):
    resposta: str
    fontes: list[Fonte]
    verificacao: Verificacao


class Conclusao(Resposta):
    id: str
    titulo: str
    pergunta: str


# ------------------------------------------------------------------ rotas

@app.get("/health")
def health():
    m = motor()
    return {"estado": "ok", "documentos": len(m.indice.documentos), "chunks": len(m.indice.chunks),
            "embeddings": m.indice.vetores is not None, "llm": m.llm is not None,
            "modelo": m.s.gemini_model if m.llm else None}


@app.get("/documents")
def documents():
    return motor().documentos()


@app.get("/categories")
def categories():
    return {"categorias": CATEGORIAS, "contagem": motor().categorias()}


@app.get("/search")
def search(q: str = Query(..., min_length=1), k: int = Query(8, ge=1, le=50),
           categoria: Optional[str] = None, doc_id: Optional[str] = None):
    res = _executar(motor().pesquisar, q, k=k, doc_id=doc_id, categoria=categoria)
    return {"q": q, "resultados": res}


@app.post("/ask", response_model=Resposta)
def ask(p: PedidoPergunta):
    return _executar(motor().perguntar, p.pergunta, categoria=p.categoria, doc_id=p.doc_id)


@app.post("/summarize", response_model=Resposta)
def summarize(p: PedidoResumo):
    return _executar(motor().resumir, p.doc_id)


@app.post("/compare", response_model=Resposta)
def compare(p: PedidoComparacao):
    return _executar(motor().comparar, p.doc_ids)


@app.get("/extract/{doc_id}")
def extract(doc_id: str, forcar: bool = False):
    """Dados estruturados de um documento (para os gráficos). Fica em cache após a 1.ª chamada."""
    return _executar(motor().extrair, doc_id, forcar=forcar)


@app.get("/extractions")
def extractions():
    """Todas as extracções já calculadas (não chama o LLM)."""
    return motor().extracoes_em_cache()


@app.get("/conclusions", response_model=list[Conclusao])
def conclusions():
    """Conclusões já geradas para o índice actual (não chama o LLM)."""
    return motor().conclusoes_em_cache()


@app.post("/conclusions", response_model=list[Conclusao])
def gerar_conclusions():
    """Gera as conclusões (uma pergunta por tema) e guarda as que têm fonte."""
    return _executar(motor().gerar_conclusoes)


@app.post("/reindex")
def reindex():
    return _executar(motor().indexar)
