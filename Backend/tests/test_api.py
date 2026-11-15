"""API e CLI com motor simulado."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import api, cli
from app.rag import Motor
from tests.conftest import FakeLLM

RESPOSTA = "A constante da taxa de queima foi 0.65 mm2/s [S1]."


@pytest.fixture
def cliente(ambiente):
    m = Motor(ambiente, llm=FakeLLM({"Responde à pergunta": RESPOSTA}))
    api.definir_motor(m)
    yield TestClient(api.app)
    api.definir_motor(None)


def test_fluxo_completo(cliente):
    assert cliente.get("/search", params={"q": "chama"}).status_code == 409  # índice vazio
    r = cliente.post("/reindex").json()
    assert r["documentos"] == 3
    assert cliente.get("/health").json()["chunks"] > 0
    docs = cliente.get("/documents").json()
    assert {d["doc_id"] for d in docs} == {"flex_gotas", "saffire", "jato_gasoso"}
    cats = cliente.get("/categories").json()
    assert len(cats["categorias"]) == 6

    res = cliente.get("/search", params={"q": "gotas", "k": 2, "doc_id": "flex_gotas"}).json()
    assert res["resultados"] and all(x["doc_id"] == "flex_gotas" for x in res["resultados"])

    ask = cliente.post("/ask", json={"pergunta": "Qual a taxa de queima das gotas?"})
    assert ask.status_code == 200
    corpo = ask.json()
    assert set(corpo) == {"resposta", "fontes", "verificacao"}
    assert corpo["verificacao"]["fiavel"] is True
    assert set(corpo["fontes"][0]) == {"tag", "doc_id", "titulo", "pagina", "text", "url"}
    assert corpo["fontes"][0]["url"].startswith("https://ntrs.nasa.gov/citations/")

    assert cliente.post("/summarize", json={"doc_id": "nao-existe"}).status_code == 404
    assert cliente.post("/compare", json={"doc_ids": ["saffire"]}).status_code == 422
    assert cliente.post("/compare", json={"doc_ids": ["saffire", "flex_gotas"]}).status_code == 200
    assert cliente.get("/extractions").json() == []

    assert cliente.get("/conclusions").json() == []
    geradas = cliente.post("/conclusions").json()
    assert geradas and set(geradas[0]) == {"id", "titulo", "pergunta", "resposta", "fontes", "verificacao"}
    assert cliente.get("/conclusions").json() == geradas


def test_cors_aberto(cliente):
    r = cliente.options("/health", headers={"Origin": "http://localhost:5173",
                                           "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") in ("*", "http://localhost:5173")


def test_sem_llm_devolve_503(ambiente):
    m = Motor(ambiente, llm=None)
    m.indexar()
    api.definir_motor(m)
    try:
        r = TestClient(api.app).post("/ask", json={"pergunta": "taxa de queima das gotas"})
        assert r.status_code == 503
    finally:
        api.definir_motor(None)


def test_cli_eval_mostra_percentagem(ambiente, monkeypatch, capsys, tmp_path: Path):
    llm = FakeLLM({"Responde à pergunta: Qual a taxa": RESPOSTA})
    monkeypatch.setattr(cli, "Motor", lambda: Motor(ambiente, llm=llm))
    assert cli.main(["index"]) == 0
    f = tmp_path / "p.json"
    f.write_text(json.dumps([{"pergunta": "Qual a taxa de queima das gotas?"},
                             {"pergunta": "Quem ganhou o mundial?"}]))
    assert cli.main(["eval", "--ficheiro", str(f)]) == 0
    saida = capsys.readouterr().out
    assert "Respostas fiáveis: 2/2 (100%)" in saida


def test_perguntas_de_avaliacao_existem():
    p = json.loads((Path(__file__).parent / "perguntas.json").read_text(encoding="utf-8"))
    assert len(p) == 15 and all(x["pergunta"] for x in p)
