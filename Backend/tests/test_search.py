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


REFS = ("[11] B.L. Zhang, J.M. Card, and F.A. Williams. Combustion and Flame, 105 (1996) 267-290. "
        "[12] B.L. Zhang and F.A. Williams. Combust. Flame, 112 (1998) 113-120. "
        "[13] V. Nayagam, D.L. Dietrich, P.V. Ferkul, M.C. Hicks, F.A. Williams, Combust. Flame 159 (2012) 3583. "
        "[14] T.I. Farouk, F.L. Dryer, Proc. Combust. Inst. 34 (2013) pp. 1609-1616. "
        "[15] D.L. Dietrich et al., Microgravity Sci. Technol. 26 (2014) 65-76, droplet extinction.")


def test_listas_de_referencias_sao_detectadas_e_penalizadas():
    from app.ingest import e_lista_de_referencias
    from tests.conftest import TEXTO_GOTAS
    assert e_lista_de_referencias(REFS)
    assert not e_lista_de_referencias(TEXTO_GOTAS)
    docs = {"d": {"doc_id": "d", "titulo": "t", "metadados": {}}}
    chunks = [{"id": "d:p9:c0", "doc_id": "d", "pagina": 9, "text": REFS, "referencias": True},
              {"id": "d:p2:c0", "doc_id": "d", "pagina": 2, "referencias": False,
               "text": "Radiative extinction of the droplet flame was observed at low oxygen."}]
    res = Indice(docs, chunks).pesquisar("droplet extinction Williams Combustion Flame", k=2)
    assert res[0]["id"] == "d:p2:c0"  # sem a penalização ganhava a bibliografia
    assert Indice(docs, [dict(c, referencias=False) for c in chunks]).pesquisar(
        "droplet extinction Williams Combustion Flame", k=2)[0]["id"] == "d:p9:c0"
