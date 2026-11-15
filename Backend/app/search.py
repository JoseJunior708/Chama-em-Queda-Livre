"""Busca híbrida: embeddings (cosseno) + BM25, com filtros, índice e cache de embeddings em disco."""
from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterable, Protocol

import numpy as np

log = logging.getLogger(__name__)


PESO_REFERENCIAS = 0.4  # factor aplicado à pontuação de chunks de bibliografia


class Embedder(Protocol):
    def embed(self, textos: list[str], tipo: str = "documento",
              titulos: list[str] | None = None) -> np.ndarray: ...


# ------------------------------------------------------------- texto / BM25

_STOP = set("""
a an and are as at be by for from has have in is it its of on or that the this to was were with
which these those than then there their been also into can using used under over between such
o a os as um uma uns umas de do da dos das em no na nos nas por para com sem que qual quais
e ou se ao aos à às pelo pela pelos pelas como mais menos foi foram ser é são sobre entre
""".split())

# Glossário PT->EN para a parte lexical (os embeddings já são multilingues).
GLOSSARIO = {
    "chama": "flame", "chamas": "flame flames", "gota": "droplet", "gotas": "droplet droplets",
    "combustivel": "fuel", "combustiveis": "fuel fuels", "combustao": "combustion",
    "oxigenio": "oxygen", "pressao": "pressure", "microgravidade": "microgravity",
    "gravidade": "gravity", "incendio": "fire", "incendios": "fire fires", "fogo": "fire",
    "seguranca": "safety", "nave": "spacecraft", "naves": "spacecraft", "fuligem": "soot",
    "propagacao": "spread propagation", "velocidade": "velocity speed", "escoamento": "flow",
    "taxa": "rate", "queima": "burning burn", "extincao": "extinction", "ignicao": "ignition",
    "solido": "solid", "solidos": "solid solids", "gasosa": "gas gaseous", "gasosas": "gas gaseous",
    "temperatura": "temperature", "diametro": "diameter", "torre": "tower", "queda": "drop",
    "estacao": "station", "espacial": "space", "experiencia": "experiment", "experiencias": "experiments",
    "resultado": "result", "resultados": "results", "concentracao": "concentration",
    "supercritico": "supercritical", "supercriticos": "supercritical", "agua": "water",
    "inflamabilidade": "flammability", "materiais": "materials", "material": "material",
    "fumo": "smoke", "deteccao": "detection", "supressao": "suppression", "radiacao": "radiation",
    "difusao": "diffusion", "prémistura": "premixed", "pre-misturada": "premixed",
    "chama fria": "cool flame", "frias": "cool", "fria": "cool", "metano": "methane",
    "heptano": "heptane", "etileno": "ethylene", "algodao": "cotton", "tecido": "fabric",
}


def sem_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def tokenizar(texto: str) -> list[str]:
    toks = re.findall(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", sem_acentos(texto.lower()))
    saida = []
    for t in toks:
        if t in _STOP or len(t) < 2:
            continue
        if len(t) > 4 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]  # plural simples
        saida.append(t)
    return saida


def expandir_consulta(consulta: str) -> list[str]:
    """Tokens da consulta + traduções do glossário (melhora o BM25 com perguntas em PT)."""
    base = sem_acentos(consulta.lower())
    extra = []
    for pt, en in GLOSSARIO.items():
        if re.search(rf"\b{re.escape(sem_acentos(pt))}\b", base):
            extra.append(en)
    return tokenizar(consulta + " " + " ".join(extra))


class BM25:
    def __init__(self, documentos: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.freqs = [Counter(d) for d in documentos]
        self.comp = np.array([len(d) for d in documentos], dtype=np.float32)
        self.media = float(self.comp.mean()) if len(documentos) else 0.0
        df: Counter = Counter()
        for d in documentos:
            df.update(set(d))
        n = len(documentos)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def pontuar(self, consulta: list[str], indices: Iterable[int]) -> np.ndarray:
        indices = list(indices)
        out = np.zeros(len(indices), dtype=np.float32)
        termos = [t for t in set(consulta) if t in self.idf]
        for j, i in enumerate(indices):
            f = self.freqs[i]
            norma = self.k1 * (1 - self.b + self.b * self.comp[i] / (self.media or 1))
            s = 0.0
            for t in termos:
                tf = f.get(t, 0)
                if tf:
                    s += self.idf[t] * tf * (self.k1 + 1) / (tf + norma)
            out[j] = s
        return out


# ------------------------------------------------------------- cache de embeddings

class CacheEmbeddings:
    """Cache em disco: hash(modelo|tipo|texto) -> vector. Evita recalcular (quota do plano gratuito)."""

    def __init__(self, pasta: Path, modelo: str):
        self.pasta = pasta
        self.modelo = modelo
        self.f_chaves = pasta / "embeddings_cache.json"
        self.f_vetores = pasta / "embeddings_cache.npy"
        self.chaves: dict[str, int] = {}
        self.vetores: list[np.ndarray] = []
        if self.f_chaves.exists() and self.f_vetores.exists():
            try:
                self.chaves = json.loads(self.f_chaves.read_text())
                self.vetores = list(np.load(self.f_vetores))
            except Exception as e:
                log.warning("Cache de embeddings corrompida, a ignorar: %s", e)
                self.chaves, self.vetores = {}, []

    def chave(self, texto: str, tipo: str) -> str:
        return hashlib.sha256(f"{self.modelo}|{tipo}|{texto}".encode()).hexdigest()

    def obter(self, chave: str) -> np.ndarray | None:
        i = self.chaves.get(chave)
        return self.vetores[i] if i is not None else None

    def guardar(self, chave: str, vetor: np.ndarray) -> None:
        if chave not in self.chaves:
            self.chaves[chave] = len(self.vetores)
            self.vetores.append(np.asarray(vetor, dtype=np.float32))

    def gravar(self) -> None:
        if not self.vetores:
            return
        self.pasta.mkdir(parents=True, exist_ok=True)
        dims = {v.shape for v in self.vetores}
        if len(dims) > 1:  # mudança de dimensão: recomeça a cache
            log.warning("Dimensões diferentes na cache; a descartar entradas antigas.")
            return
        np.save(self.f_vetores, np.vstack(self.vetores))
        self.f_chaves.write_text(json.dumps(self.chaves))


def embed_com_cache(embedder: Embedder, cache: CacheEmbeddings, textos: list[str],
                    tipo: str = "documento", titulos: list[str] | None = None) -> np.ndarray:
    chaves = [cache.chave(t, tipo) for t in textos]
    em_falta = [i for i, k in enumerate(chaves) if cache.obter(k) is None]
    if em_falta:
        novos = embedder.embed([textos[i] for i in em_falta], tipo=tipo,
                               titulos=[titulos[i] for i in em_falta] if titulos else None)
        for i, v in zip(em_falta, novos):
            cache.guardar(chaves[i], v)
        cache.gravar()
    return np.vstack([cache.obter(k) for k in chaves]).astype(np.float32)


def normalizar(m: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(m, axis=-1, keepdims=True)
    n[n == 0] = 1.0
    return m / n


# ------------------------------------------------------------- índice

class Indice:
    def __init__(self, documentos: dict[str, dict], chunks: list[dict],
                 vetores: np.ndarray | None = None):
        self.documentos = documentos
        self.chunks = chunks
        self.vetores = normalizar(vetores) if vetores is not None and len(vetores) else None
        self.bm25 = BM25([tokenizar(c["text"]) for c in chunks])
        self._por_id = {c["id"]: i for i, c in enumerate(chunks)}

    @property
    def vazio(self) -> bool:
        return not self.chunks

    # ---- persistência
    def salvar(self, pasta: Path) -> None:
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "documentos.json").write_text(json.dumps(self.documentos, ensure_ascii=False, indent=1))
        (pasta / "chunks.json").write_text(json.dumps(self.chunks, ensure_ascii=False))
        f_vet = pasta / "vetores.npy"
        if self.vetores is not None:
            np.save(f_vet, self.vetores)
        elif f_vet.exists():
            f_vet.unlink()

    @classmethod
    def carregar(cls, pasta: Path) -> "Indice":
        f_docs, f_chunks = pasta / "documentos.json", pasta / "chunks.json"
        if not f_docs.exists() or not f_chunks.exists():
            return cls({}, [])
        docs = json.loads(f_docs.read_text())
        chunks = json.loads(f_chunks.read_text())
        f_vet = pasta / "vetores.npy"
        vetores = np.load(f_vet) if f_vet.exists() else None
        if vetores is not None and len(vetores) != len(chunks):
            log.warning("Vectores desalinhados com os chunks; a usar só BM25. Corre 'index'.")
            vetores = None
        return cls(docs, chunks, vetores)

    # ---- filtros
    def _passa_filtros(self, chunk: dict, doc_id, categoria, filtros) -> bool:
        if doc_id:
            ids = {doc_id} if isinstance(doc_id, str) else set(doc_id)
            if chunk["doc_id"] not in ids:
                return False
        doc = self.documentos.get(chunk["doc_id"], {})
        if categoria and (doc.get("categoria") or "").lower() != categoria.lower():
            return False
        if filtros:
            meta = doc.get("metadados", {})
            for chave, valor in filtros.items():
                atual = meta.get(chave)
                if atual is None or str(valor).lower() not in str(atual).lower():
                    return False
        return True

    def chunks_do_documento(self, doc_id: str) -> list[dict]:
        return [c for c in self.chunks if c["doc_id"] == doc_id]

    # ---- pesquisa
    def pesquisar(self, consulta: str, k: int = 8, doc_id=None, categoria: str | None = None,
                  filtros: dict | None = None, embedder: Embedder | None = None,
                  cache: CacheEmbeddings | None = None, peso_vetorial: float = 0.65) -> list[dict]:
        candidatos = [i for i, c in enumerate(self.chunks)
                      if self._passa_filtros(c, doc_id, categoria, filtros)]
        if not candidatos or not consulta.strip():
            return []

        lex = self.bm25.pontuar(expandir_consulta(consulta), candidatos)
        lex_n = lex / lex.max() if lex.max() > 0 else lex

        vec_n = np.zeros(len(candidatos), dtype=np.float32)
        peso = 0.0
        if self.vetores is not None and embedder is not None:
            try:
                if cache is not None:
                    q = embed_com_cache(embedder, cache, [consulta], tipo="consulta")[0]
                else:
                    q = embedder.embed([consulta], tipo="consulta")[0]
                q = q / (np.linalg.norm(q) or 1.0)
                cos = np.clip(self.vetores[candidatos] @ q, 0, None)
                vec_n = cos / cos.max() if cos.max() > 0 else cos
                peso = peso_vetorial
            except Exception as e:  # sem embeddings, continua só com BM25
                log.warning("Embedding da consulta falhou (%s); a usar só BM25.", e)

        final = peso * vec_n + (1 - peso) * lex_n
        # listas de referências repetem os termos do tema mas não trazem resultados
        final = final * np.array([PESO_REFERENCIAS if self.chunks[i].get("referencias") else 1.0
                                  for i in candidatos], dtype=np.float32)
        ordem = np.argsort(-final)[:k]
        resultados = []
        for j in ordem:
            if final[j] <= 0:
                break
            c = self.chunks[candidatos[j]]
            resultados.append({**c, "score": round(float(final[j]), 4),
                               "score_vetorial": round(float(vec_n[j]), 4),
                               "score_bm25": round(float(lex_n[j]), 4)})
        return resultados
