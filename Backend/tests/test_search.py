import numpy as np

from app.ingest import ingerir_pasta
from app.search import CacheEmbeddings, Indice, embed_com_cache, expandir_consulta
from tests.conftest import FakeEmbedder


def _indice(pasta_docs, embedder=None, categorias=None):
    r = ingerir_pasta(pasta_docs)
    docs = {d.doc_id: d.to_dict() for d in r.documentos}
    for doc_id, cat in (categorias or {}).items():
        docs[doc_id]["categoria"] = cat
    chunks = [c.__dict__ for c in r.chunks]
    vet = embedder.embed([c["text"] for c in chunks]) if embedder else None
    return Indice(docs, chunks, vet)


def test_busca_hibrida_pergunta_em_portugues(pasta_docs):
    emb = FakeEmbedder()
    idx = _indice(pasta_docs, emb)
    res = idx.pesquisar("Qual a taxa de queima das gotas de heptano?", k=3, embedder=emb)
    assert res[0]["doc_id"] == "flex_gotas"
    assert res[0]["score_vetorial"] > 0 and res[0]["score_bm25"] > 0


def test_busca_so_bm25_sem_embeddings(pasta_docs):
    idx = _indice(pasta_docs)
    res = idx.pesquisar("propagação da chama em algodão", k=2)
    assert res[0]["doc_id"] == "saffire"


def test_filtros_doc_id_categoria_metadados(pasta_docs):
    emb = FakeEmbedder()
    idx = _indice(pasta_docs, emb, {"flex_gotas": "Gotas (droplets)", "saffire": "Combustíveis sólidos",
                                    "jato_gasoso": "Chamas gasosas"})
    q = "flame microgravity"
    assert {r["doc_id"] for r in idx.pesquisar(q, doc_id="saffire", embedder=emb)} == {"saffire"}
    assert {r["doc_id"] for r in idx.pesquisar(q, doc_id=["saffire", "jato_gasoso"], embedder=emb)} \
        <= {"saffire", "jato_gasoso"}
    assert {r["doc_id"] for r in idx.pesquisar(q, categoria="chamas gasosas", embedder=emb)} == {"jato_gasoso"}
    assert {r["doc_id"] for r in idx.pesquisar(q, filtros={"ambiente": "iss"}, embedder=emb)} == {"flex_gotas"}
    assert {r["doc_id"] for r in idx.pesquisar(q, filtros={"combustivel": "metanol"}, embedder=emb)} == {"flex_gotas"}
    assert idx.pesquisar(q, filtros={"ambiente": "Marte"}, embedder=emb) == []


def test_persistencia_do_indice(pasta_docs, tmp_path):
    emb = FakeEmbedder()
    idx = _indice(pasta_docs, emb)
    idx.salvar(tmp_path / "idx")
    novo = Indice.carregar(tmp_path / "idx")
    assert len(novo.chunks) == len(idx.chunks)
    assert np.allclose(novo.vetores, idx.vetores)


def test_cache_de_embeddings_evita_recalcular(tmp_path):
    emb = FakeEmbedder()
    cache = CacheEmbeddings(tmp_path, "fake")
    a = embed_com_cache(emb, cache, ["texto um", "texto dois"])
    assert emb.chamadas == 1
    cache2 = CacheEmbeddings(tmp_path, "fake")  # recarrega do disco
    b = embed_com_cache(emb, cache2, ["texto um", "texto dois"])
    assert emb.chamadas == 1 and np.allclose(a, b)


def test_glossario_expande_consulta():
    toks = expandir_consulta("pressão e fuligem")
    assert "pressure" in toks and "soot" in toks
