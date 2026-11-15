"""Testes do cliente Gemini com HTTP simulado (sem rede)."""
import pytest

from app import llm
from app.config import Settings
from app.llm import GeminiClient, LLMError, parse_json


class Resp:
    def __init__(self, status, dados=None, headers=None):
        self.status_code = status
        self._dados = dados or {}
        self.headers = headers or {}
        self.text = str(self._dados)

    def json(self):
        return self._dados


class SessaoFalsa:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.pedidos = []

    def post(self, url, headers=None, json=None, timeout=None):
        self.pedidos.append({"url": url, "headers": headers, "json": json})
        return self.respostas.pop(0)


@pytest.fixture
def settings(tmp_path):
    return Settings(gemini_api_key="chave-teste", gemini_model="modelo-flash",
                    embed_model="gemini-embedding-2", embed_dim=4, index_dir=tmp_path,
                    embed_batch=2, max_retries=3)


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)


def _ok(texto):
    return Resp(200, {"candidates": [{"content": {"parts": [{"text": texto}]}}]})


def test_repete_em_429_e_503_e_usa_cabecalho(settings):
    sessao = SessaoFalsa([
        Resp(429, {"error": {"details": [{"retryDelay": "2s"}]}}),
        Resp(503),
        _ok("olá"),
    ])
    c = GeminiClient(settings, sessao)
    assert c.generate("pergunta") == "olá"
    assert len(sessao.pedidos) == 3
    assert sessao.pedidos[0]["headers"]["x-goog-api-key"] == "chave-teste"
    assert "key=" not in sessao.pedidos[0]["url"]  # a chave nunca vai no URL


def test_erro_400_nao_repete(settings):
    sessao = SessaoFalsa([Resp(400, {"error": "mau pedido"})])
    with pytest.raises(LLMError):
        GeminiClient(settings, sessao).generate("x")
    assert len(sessao.pedidos) == 1


def test_esgota_tentativas(settings):
    sessao = SessaoFalsa([Resp(503)] * 4)
    with pytest.raises(LLMError, match="4 tentativas"):
        GeminiClient(settings, sessao).generate("x")


def test_cache_de_respostas(settings):
    sessao = SessaoFalsa([_ok("resposta")])
    c = GeminiClient(settings, sessao)
    assert c.generate("igual") == "resposta"
    assert c.generate("igual") == "resposta"
    assert len(sessao.pedidos) == 1


def test_embeddings_em_lotes_com_prefixos(settings):
    v = {"values": [1.0, 0.0, 0.0, 0.0]}
    sessao = SessaoFalsa([Resp(200, {"embeddings": [v, v]}), Resp(200, {"embeddings": [v]})])
    m = GeminiClient(settings, sessao).embed(["a", "b", "c"], tipo="documento", titulos=["T", None, None])
    assert m.shape == (3, 4)
    assert len(sessao.pedidos) == 2  # lote de 2 + lote de 1
    pedido = sessao.pedidos[0]["json"]["requests"][0]
    assert pedido["content"]["parts"][0]["text"] == "title: T | text: a"
    assert pedido["output_dimensionality"] == 4


def test_sem_chave_da_erro(tmp_path):
    with pytest.raises(LLMError):
        GeminiClient(Settings(gemini_api_key="", index_dir=tmp_path))


def test_parse_json_tolerante():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json('Aqui está: {"a": [1,2]} fim') == {"a": [1, 2]}
