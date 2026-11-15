"""Cliente HTTP do Gemini: geração (generateContent) e embeddings (batchEmbedContents).

- A chave vai no cabeçalho x-goog-api-key e nunca é registada nos logs.
- Novas tentativas com espera exponencial em 429/500/503/504 (respeita o retryDelay da API).
- Embeddings em lotes; respostas determinísticas (temperature=0) guardadas em cache no disco.
"""
from __future__ import annotations

import hashlib
import json
import logging
import random
import re
import time
from pathlib import Path

import numpy as np
import requests

from .config import Settings, get_settings

log = logging.getLogger(__name__)

URL_BASE = "https://generativelanguage.googleapis.com/v1beta"
CODIGOS_REPETIR = {429, 500, 502, 503, 504}


class LLMError(RuntimeError):
    """Erro ao comunicar com o LLM (depois de esgotadas as tentativas)."""


def parse_json(texto: str):
    """Extrai JSON de uma resposta (tolera blocos ```json ... ```)."""
    texto = texto.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", texto, re.S)
    if m:
        texto = m.group(1).strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        for abre, fecha in (("{", "}"), ("[", "]")):
            i, j = texto.find(abre), texto.rfind(fecha)
            if i != -1 and j > i:
                try:
                    return json.loads(texto[i:j + 1])
                except json.JSONDecodeError:
                    pass
    raise LLMError(f"Resposta do LLM não é JSON válido: {texto[:200]!r}")


def _espera_sugerida(resp: requests.Response) -> float | None:
    """Lê o Retry-After ou o google.rpc.RetryInfo.retryDelay ("30s")."""
    ra = resp.headers.get("Retry-After")
    if ra and ra.replace(".", "", 1).isdigit():
        return float(ra)
    try:
        for d in resp.json().get("error", {}).get("details", []):
            atraso = d.get("retryDelay")
            if atraso:
                return float(str(atraso).rstrip("s"))
    except (ValueError, AttributeError):
        pass
    return None


class GeminiClient:
    def __init__(self, settings: Settings | None = None, sessao: requests.Session | None = None):
        self.s = settings or get_settings()
        if not self.s.gemini_api_key:
            raise LLMError("GEMINI_API_KEY não definida (ver .env.example).")
        self.sessao = sessao or requests.Session()
        self.pasta_cache = self.s.index_dir / "cache_llm"
        self.dim = self.s.embed_dim

    @property
    def id_embeddings(self) -> str:
        return f"{self.s.embed_model}@{self.s.embed_dim}"

    # ---------------------------------------------------------------- HTTP
    def _post(self, url: str, corpo: dict) -> dict:
        cabecalhos = {"Content-Type": "application/json", "x-goog-api-key": self.s.gemini_api_key}
        ultimo_erro = ""
        for tentativa in range(self.s.max_retries + 1):
            try:
                resp = self.sessao.post(url, headers=cabecalhos, json=corpo, timeout=self.s.timeout)
            except requests.RequestException as e:
                resp, ultimo_erro = None, f"erro de rede: {e.__class__.__name__}"
            if resp is not None:
                if resp.status_code == 200:
                    return resp.json()
                ultimo_erro = f"HTTP {resp.status_code}: {resp.text[:300]}"
                if resp.status_code not in CODIGOS_REPETIR:
                    raise LLMError(ultimo_erro)
            if tentativa == self.s.max_retries:
                break
            espera = (_espera_sugerida(resp) if resp is not None else None) \
                or min(60.0, 2.0 ** tentativa) + random.uniform(0, 1)
            log.warning("Gemini indisponível (%s). Nova tentativa %d/%d dentro de %.1fs.",
                        ultimo_erro[:80], tentativa + 1, self.s.max_retries, espera)
            time.sleep(espera)
        raise LLMError(f"Falha após {self.s.max_retries + 1} tentativas — {ultimo_erro}")

    # ---------------------------------------------------------------- geração
    def _cache_get(self, chave: str) -> str | None:
        f = self.pasta_cache / f"{chave}.json"
        if f.exists():
            try:
                return json.loads(f.read_text(encoding="utf-8"))["texto"]
            except (ValueError, KeyError):
                return None
        return None

    def _cache_set(self, chave: str, texto: str) -> None:
        self.pasta_cache.mkdir(parents=True, exist_ok=True)
        (self.pasta_cache / f"{chave}.json").write_text(
            json.dumps({"texto": texto}, ensure_ascii=False),
            encoding="utf-8",
        )

    def generate(self, prompt: str, system: str | None = None, json_mode: bool = False,
                 temperature: float = 0.0, max_tokens: int | None = None) -> str:
        chave = hashlib.sha256(json.dumps(
            [self.s.gemini_model, system, prompt, json_mode, temperature, max_tokens]).encode()).hexdigest()
        if temperature == 0:
            em_cache = self._cache_get(chave)
            if em_cache is not None:
                return em_cache

        config: dict = {"temperature": temperature}
        if json_mode:
            config["responseMimeType"] = "application/json"
        if max_tokens:
            config["maxOutputTokens"] = max_tokens
        corpo: dict = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                       "generationConfig": config}
        if system:
            corpo["systemInstruction"] = {"parts": [{"text": system}]}

        dados = self._post(f"{URL_BASE}/models/{self.s.gemini_model}:generateContent", corpo)
        candidatos = dados.get("candidates") or []
        if not candidatos:
            motivo = dados.get("promptFeedback", {}).get("blockReason", "sem candidatos")
            raise LLMError(f"O modelo não devolveu resposta ({motivo}).")
        partes = candidatos[0].get("content", {}).get("parts", [])
        texto = "".join(p.get("text", "") for p in partes if not p.get("thought")).strip()
        if not texto:
            raise LLMError(f"Resposta vazia (finishReason={candidatos[0].get('finishReason')}).")
        if temperature == 0:
            self._cache_set(chave, texto)
        return texto

    def generate_json(self, prompt: str, system: str | None = None, **kw):
        return parse_json(self.generate(prompt, system=system, json_mode=True, **kw))

    # ---------------------------------------------------------------- embeddings
    def _formatar(self, texto: str, tipo: str, titulo: str | None) -> dict:
        """gemini-embedding-2 usa prefixos de tarefa; o 001 usa taskType."""
        pedido: dict = {"model": f"models/{self.s.embed_model}",
                        "output_dimensionality": self.s.embed_dim}
        texto = texto[:8000]
        if self.s.embed_model.endswith("-001"):
            pedido["taskType"] = "RETRIEVAL_QUERY" if tipo == "consulta" else "RETRIEVAL_DOCUMENT"
            if tipo != "consulta" and titulo:
                pedido["title"] = titulo
        elif tipo == "consulta":
            texto = f"task: search result | query: {texto}"
        else:
            texto = f"title: {titulo or 'none'} | text: {texto}"
        pedido["content"] = {"parts": [{"text": texto}]}
        return pedido

    def embed(self, textos: list[str], tipo: str = "documento",
              titulos: list[str] | None = None) -> np.ndarray:
        if not textos:
            return np.zeros((0, self.s.embed_dim), dtype=np.float32)
        url = f"{URL_BASE}/models/{self.s.embed_model}:batchEmbedContents"
        vetores: list[list[float]] = []
        for ini in range(0, len(textos), self.s.embed_batch):
            lote = textos[ini:ini + self.s.embed_batch]
            tits = titulos[ini:ini + self.s.embed_batch] if titulos else [None] * len(lote)
            dados = self._post(url, {"requests": [self._formatar(t, tipo, ti) for t, ti in zip(lote, tits)]})
            embs = dados.get("embeddings") or []
            if len(embs) != len(lote):
                raise LLMError("Número de embeddings devolvidos não corresponde ao pedido.")
            vetores.extend(e["values"] for e in embs)
            if len(textos) > self.s.embed_batch:
                log.info("Embeddings: %d/%d", min(ini + self.s.embed_batch, len(textos)), len(textos))
        m = np.asarray(vetores, dtype=np.float32)
        n = np.linalg.norm(m, axis=1, keepdims=True)
        n[n == 0] = 1.0
        return m / n


def criar_cliente(settings: Settings | None = None) -> GeminiClient | None:
    """Devolve o cliente, ou None se não houver chave (modo só-BM25/sem LLM)."""
    try:
        return GeminiClient(settings)
    except LLMError as e:
        log.warning("%s O LLM fica desactivado.", e)
        return None
