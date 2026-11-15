"""Ingestão: leitura de PDFs/.txt, limpeza do texto e divisão em chunks com página de origem."""
from __future__ import annotations

import hashlib
import json
import logging
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)
# O pypdf emite centenas de avisos por PDF (fontes, codificações); só interessam os erros.
logging.getLogger("pypdf").setLevel(logging.ERROR)

EXTENSOES = {".pdf", ".txt"}

# Abreviaturas comuns em artigos científicos que não terminam frase.
_ABREVIATURAS = {
    "fig", "figs", "eq", "eqs", "ref", "refs", "al", "e.g", "i.e", "vs", "approx",
    "no", "vol", "pp", "ca", "cf", "dr", "mr", "ms", "sec", "tab", "ch", "st", "inc",
    "etc", "resp", "max", "min", "avg",
}


@dataclass
class Chunk:
    id: str
    doc_id: str
    pagina: int
    text: str


@dataclass
class Documento:
    doc_id: str
    titulo: str
    ficheiro: str
    paginas: int
    hash: str
    metadados: dict = field(default_factory=dict)
    categoria: str | None = None
    categoria_origem: str | None = None  # "metadados", "llm" ou "palavras-chave"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ResultadoIngestao:
    documentos: list[Documento]
    chunks: list[Chunk]
    avisos: list[str]


# ---------------------------------------------------------------- limpeza

def limpar_texto(texto: str) -> str:
    """Corrige hifenização no fim de linha, junta linhas e normaliza espaços."""
    texto = unicodedata.normalize("NFKC", texto)
    texto = texto.replace("­", "")  # hífen condicional
    # "combus-\ntion" -> "combustion" (só entre letras minúsculas, para não estragar "O2-\nN2")
    texto = re.sub(r"([a-zà-ÿ])-\s*\n\s*([a-zà-ÿ])", r"\1\2", texto)
    texto = re.sub(r"[ \t]*\n[ \t]*", " ", texto)
    texto = re.sub(r"[^\S\r\n]+", " ", texto)
    return texto.strip()


def dividir_frases(texto: str) -> list[str]:
    """Divide em frases sem partir números decimais nem abreviaturas comuns."""
    frases: list[str] = []
    inicio = 0
    for m in re.finditer(r"[.!?]+[\"')\]]*\s+(?=[A-Z0-9\"'(\[])", texto):
        fim = m.end()
        candidato = texto[inicio:fim].strip()
        ultima = re.search(r"([A-Za-z.]+)[.!?]+[\"')\]]*\s*$", candidato)
        if ultima and ultima.group(1).lower().rstrip(".") in _ABREVIATURAS:
            continue
        if ultima and len(ultima.group(1)) == 1 and ultima.group(1).isupper():
            continue  # iniciais: "J. Smith"
        frases.append(candidato)
        inicio = fim
    resto = texto[inicio:].strip()
    if resto:
        frases.append(resto)
    return frases


def _partir_frase_longa(frase: str, tamanho: int) -> list[str]:
    partes, atual = [], ""
    for palavra in frase.split(" "):
        if atual and len(atual) + 1 + len(palavra) > tamanho:
            partes.append(atual)
            atual = palavra
        else:
            atual = f"{atual} {palavra}".strip()
    if atual:
        partes.append(atual)
    return partes


def criar_chunks(texto: str, tamanho: int = 1200, sobreposicao: int = 200) -> list[str]:
    """Agrupa frases inteiras em blocos de ~`tamanho` caracteres.

    A sobreposição é feita repetindo as últimas frases do bloco anterior
    (até `sobreposicao` caracteres), para nunca partir frases a meio.
    """
    frases: list[str] = []
    for f in dividir_frases(texto):
        frases.extend(_partir_frase_longa(f, tamanho) if len(f) > tamanho else [f])

    chunks: list[str] = []
    atual: list[str] = []
    comprimento = 0
    novas = 0  # frases novas no bloco actual (não contam as de sobreposição)
    for frase in frases:
        if atual and comprimento + 1 + len(frase) > tamanho:
            chunks.append(" ".join(atual))
            cauda: list[str] = []
            total = 0
            for f in reversed(atual):
                if total + len(f) + 1 > sobreposicao:
                    break
                cauda.insert(0, f)
                total += len(f) + 1
            # garante que a cauda + a frase seguinte cabem no tamanho
            while cauda and total + len(frase) > tamanho:
                total -= len(cauda.pop(0)) + 1
            atual, comprimento, novas = cauda, total, 0
        atual.append(frase)
        comprimento += len(frase) + 1
        novas += 1
    if atual and novas:
        chunks.append(" ".join(atual))
    return chunks


# ---------------------------------------------------------------- leitura

def extrair_paginas(caminho: Path) -> list[tuple[int, str]]:
    """Devolve [(número_da_página, texto_bruto)] (páginas a começar em 1)."""
    if caminho.suffix.lower() == ".txt":
        bruto = caminho.read_text(encoding="utf-8", errors="replace")
        # Form feed (\f) separa páginas, se existir.
        return [(i + 1, p) for i, p in enumerate(bruto.split("\f"))]

    from pypdf import PdfReader

    leitor = PdfReader(str(caminho))
    paginas = []
    for i, pagina in enumerate(leitor.pages):
        try:
            paginas.append((i + 1, pagina.extract_text() or ""))
        except Exception as e:  # páginas corrompidas não devem travar a ingestão
            log.warning("Falha a extrair a página %d de %s: %s", i + 1, caminho.name, e)
            paginas.append((i + 1, ""))
    return paginas


def gerar_doc_id(caminho: Path) -> str:
    base = unicodedata.normalize("NFKD", caminho.stem).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", base).strip("-").lower() or "doc"


def carregar_metadados(caminho: Path) -> dict:
    """Carrega <nome>.json ao lado do documento, se existir."""
    meta = caminho.with_suffix(".json")
    if not meta.exists():
        return {}
    try:
        dados = json.loads(meta.read_text(encoding="utf-8"))
        return dados if isinstance(dados, dict) else {}
    except json.JSONDecodeError as e:
        log.warning("Metadados inválidos em %s: %s", meta.name, e)
        return {}


def _hash_ficheiro(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()[:16]


def ingerir_documento(caminho: Path, tamanho: int = 1200, sobreposicao: int = 200
                      ) -> tuple[Documento, list[Chunk]] | None:
    paginas = extrair_paginas(caminho)
    doc_id = gerar_doc_id(caminho)
    chunks: list[Chunk] = []
    for num, bruto in paginas:
        limpo = limpar_texto(bruto)
        if len(limpo) < 20:
            continue
        for j, texto in enumerate(criar_chunks(limpo, tamanho, sobreposicao)):
            chunks.append(Chunk(id=f"{doc_id}:p{num}:c{j}", doc_id=doc_id, pagina=num, text=texto))
    if not chunks:
        return None
    meta = carregar_metadados(caminho)
    titulo = str(meta.get("titulo") or meta.get("title") or caminho.stem)
    doc = Documento(doc_id=doc_id, titulo=titulo, ficheiro=caminho.name, paginas=len(paginas),
                    hash=_hash_ficheiro(caminho), metadados=meta)
    return doc, chunks


def ingerir_pasta(pasta: Path, tamanho: int = 1200, sobreposicao: int = 200) -> ResultadoIngestao:
    documentos: list[Documento] = []
    chunks: list[Chunk] = []
    avisos: list[str] = []
    if not pasta.exists():
        return ResultadoIngestao([], [], [f"A pasta {pasta} não existe."])

    vistos: set[str] = set()
    for caminho in sorted(pasta.iterdir()):
        if caminho.suffix.lower() not in EXTENSOES or not caminho.is_file():
            continue
        try:
            resultado = ingerir_documento(caminho, tamanho, sobreposicao)
        except Exception as e:
            aviso = f"Não foi possível ler {caminho.name}: {e}"
            log.warning(aviso)
            avisos.append(aviso)
            continue
        if resultado is None:
            aviso = f"{caminho.name} não tem texto extraível (PDF digitalizado?) — ignorado."
            log.warning(aviso)
            avisos.append(aviso)
            continue
        doc, doc_chunks = resultado
        if doc.doc_id in vistos:
            avisos.append(f"doc_id duplicado '{doc.doc_id}' ({caminho.name}) — ignorado.")
            continue
        vistos.add(doc.doc_id)
        documentos.append(doc)
        chunks.extend(doc_chunks)
    return ResultadoIngestao(documentos, chunks, avisos)
