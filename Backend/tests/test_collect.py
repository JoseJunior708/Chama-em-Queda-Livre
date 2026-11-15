"""Testa o colector com respostas simuladas no formato descrito na documentação do NTRS."""
import csv
import json

from app import collect
from tests.conftest import criar_pdf

RELEVANT = {
    "id": 20160000593,
    "title": "Combustion of Solids in Microgravity: Results from the BASS-II Experiment",
    "abstract": "Tests on the International Space Station burned acrylic slabs in a small wind tunnel.",
    "stiType": "PRESENTATION",
    "center": {"code": "GRC", "name": "Glenn Research Center"},
    "publications": [{"publicationDate": "2015-11-11T00:00:00.0000000+00:00"}],
    "authorAffiliations": [{"meta": {"author": {"name": "Ferkul, Paul V."}}}],
    "downloads": [{"links": {"pdf": "/api/citations/20160000593/downloads/20160000593.pdf",
                             "fulltext": "/api/citations/20160000593/downloads/20160000593.txt"}}],
}
OFF_TOPIC = {"id": 1, "title": "Wing aerodynamics", "abstract": "Wind tunnel tests of a wing.",
             "downloads": [{"links": {"pdf": "/x.pdf"}}]}
NO_FILE = {"id": 2, "title": "Microgravity combustion overview", "abstract": "flame", "downloads": []}


class FakeResponse:
    def __init__(self, status=200, payload=None, content=b""):
        self.status_code, self._payload, self._content = status, payload, content

    def json(self):
        return self._payload

    def raise_for_status(self):
        assert self.status_code == 200

    def iter_content(self, size):
        yield self._content


PROGRAM = {"id": 3, "title": "NASA Microgravity Combustion Program Overview",
           "abstract": "Overview of flame spread rate and extinction research on the space station.",
           "publications": [{"publicationDate": "2015-01-01"}], "downloads": [{"links": {"pdf": "/3.pdf"}}]}
GENERIC = {"id": 4, "title": "Combustion in microgravity", "abstract": "General remarks on flames.",
           "publications": [{"publicationDate": "2010-01-01"}], "downloads": [{"links": {"pdf": "/4.pdf"}}]}
OLD_EXPERIMENT = {"id": 5, "title": "Droplet Combustion Experiment drop tower tests",
                  "abstract": "Burning rate of heptane droplets in microgravity.",
                  "publications": [{"publicationDate": "1994-01-01"}],
                  "downloads": [{"links": {"pdf": "/5.pdf", "fulltext": "/5.txt"}}]}
OLD_VAGUE = {"id": 6, "title": "Microgravity flames", "abstract": "Notes on extinction of a flame.",
             "publications": [{"publicationDate": "1990-01-01"}], "downloads": [{"links": {"pdf": "/6.pdf"}}]}

LINHA = "The flame spread rate over the acrylic slab was measured in the wind tunnel at several flow speeds."
TEXTO_BOM = "\n".join([LINHA] * 30)


def pdf_bytes(tmp_path, paginas):
    criar_pdf(tmp_path / "_modelo.pdf", paginas)
    return (tmp_path / "_modelo.pdf").read_bytes()


def make_fake_get(results, files):
    """`files` mapeia o fim do URL -> bytes; o resto devolve 404."""
    def fake_get(url, **kwargs):
        if url.endswith("/citations/search"):
            return FakeResponse(payload={"results": results})
        for ending, content in files.items():
            if url.endswith(ending):
                return FakeResponse(content=content)
        return FakeResponse(status=404)
    return fake_get


def test_metadata_fields():
    meta = collect.to_metadata(RELEVANT)
    assert meta["ano"] == 2015
    assert meta["autores"] == ["Ferkul, Paul V."]
    assert meta["combustivel"] == ["PMMA (acrílico)"]
    assert meta["ambiente"] == ["ISS"]
    assert meta["url"] == "https://ntrs.nasa.gov/citations/20160000593"


def test_relevance_filter():
    assert collect.is_relevant(RELEVANT)
    assert not collect.is_relevant(OFF_TOPIC)


def test_score_ranks_experiments_above_program_documents():
    experiment, _ = collect.score(RELEVANT)          # BASS no título (+3), 2015 (+1)
    program, reasons = collect.score(PROGRAM)        # 2 termos de resultados, mas "program" e "overview" no título
    assert experiment == 4
    assert program < collect.MIN_SCORE <= experiment
    assert "programa/estratégia" in collect.exclusion_reason(reasons)
    assert collect.score(GENERIC)[0] < collect.MIN_SCORE


def test_old_documents_kept_only_when_clearly_experiments():
    assert collect.score(OLD_EXPERIMENT)[0] >= collect.MIN_SCORE   # DCE no título + burning rate - 1
    assert collect.score(OLD_VAGUE)[0] < collect.MIN_SCORE         # um só termo de resultados - 1
    newer = dict(OLD_EXPERIMENT, publications=[{"publicationDate": "2005-01-01"}])
    assert collect.score(newer)[0] == collect.score(OLD_EXPERIMENT)[0] + 2


def test_collect_writes_files(tmp_path, monkeypatch, capsys):
    pdf = pdf_bytes(tmp_path, [TEXTO_BOM])
    monkeypatch.setattr(collect, "_get", make_fake_get(
        [RELEVANT, OFF_TOPIC, NO_FILE, PROGRAM, GENERIC], {"20160000593.pdf": pdf}))
    docs = tmp_path / "docs"
    rows = collect.collect(max_docs=5, folder=docs)
    assert [r["id"] for r in rows] == ["20160000593"]
    assert (docs / "20160000593.pdf").read_bytes().startswith(b"%PDF")
    meta = json.loads((docs / "20160000593.json").read_text(encoding="utf-8"))
    assert meta["titulo"].startswith("Combustion")
    assert meta["pontuacao"] == 4 and meta["paginas"] == 1 and meta["caracteres_texto"] >= 1500
    with open(tmp_path / "experiencias.csv", encoding="utf-8") as handle:
        linhas = list(csv.DictReader(handle))
    assert linhas[0]["pontuacao"] == "4.0" and linhas[0]["paginas"] == "1"
    assert int(linhas[0]["caracteres_texto"]) >= 1500
    saida = capsys.readouterr().out
    assert "Excluídos: 4" in saida and "programa/estratégia" in saida and "fora do tema" in saida


def test_orders_by_score_and_respects_max(tmp_path, monkeypatch):
    pdf = pdf_bytes(tmp_path, [TEXTO_BOM])
    monkeypatch.setattr(collect, "_get", make_fake_get(
        [OLD_EXPERIMENT, RELEVANT], {"5.pdf": pdf, "20160000593.pdf": pdf}))
    rows = collect.collect(max_docs=1, folder=tmp_path / "docs")
    assert [r["id"] for r in rows] == ["20160000593"]   # 4 pontos, 2015 — à frente do de 1994 (também 4)


def test_pdf_without_text_falls_back_to_fulltext(tmp_path, monkeypatch):
    curto = pdf_bytes(tmp_path, ["Only a title page."])
    monkeypatch.setattr(collect, "_get", make_fake_get(
        [OLD_EXPERIMENT], {"5.pdf": curto, "5.txt": TEXTO_BOM.encode()}))
    docs = tmp_path / "docs"
    rows = collect.collect(max_docs=5, folder=docs)
    assert rows[0]["ficheiro"] == "5.txt" and rows[0]["paginas"] is None
    assert not (docs / "5.pdf").exists()


def test_rejects_unreadable_text(tmp_path, monkeypatch, capsys):
    lixo = ("#@ 12 %& 0x 3.4 ~~ ^^ 99 || " * 400).encode()
    curto = pdf_bytes(tmp_path, [""])
    monkeypatch.setattr(collect, "_get", make_fake_get([OLD_EXPERIMENT], {"5.pdf": curto, "5.txt": lixo}))
    docs = tmp_path / "docs"
    assert collect.collect(max_docs=5, folder=docs) == []
    assert not list(docs.glob("5.*"))
    saida = capsys.readouterr().out
    assert "ilegível" in saida and "caracteres úteis" in saida


def test_removes_duplicate_titles_keeping_the_paper(tmp_path, monkeypatch, capsys):
    pdf = pdf_bytes(tmp_path, [TEXTO_BOM])
    slides = dict(RELEVANT, id=777)                      # mesma obra, registo de apresentação
    paper = dict(RELEVANT, id=888, stiType="CONFERENCE_PAPER",
                 downloads=[{"links": {"pdf": "/888.pdf"}}])
    monkeypatch.setattr(collect, "_get", make_fake_get([slides, paper], {"888.pdf": pdf, "777.pdf": pdf}))
    rows = collect.collect(max_docs=5, folder=tmp_path / "docs")
    assert [r["id"] for r in rows] == ["888"]
    assert "duplicado" in capsys.readouterr().out


def test_balanced_order_alternates_topics():
    c = lambda pts, rid, tema: (pts, 2010, rid, {}, tema)
    ordered = collect.balanced_order([c(9, "s1", "Sólidos"), c(8, "s2", "Sólidos"), c(7, "s3", "Sólidos"),
                                      c(6, "o1", "Outro"), c(5, "g1", "Gasosas"), c(3, "x1", "Supercríticos")])
    assert [x[2] for x in ordered] == ["s1", "g1", "x1", "s2", "s3", "o1"]


def test_topic_from_keywords_or_query():
    droplets = {"title": "Droplet combustion in microgravity", "abstract": ""}
    vague = {"title": "Flames in microgravity", "abstract": ""}
    assert collect.topic(droplets, "Chamas gasosas") == "Gotas (droplets)"
    assert collect.topic(vague, "Chamas gasosas") == "Chamas gasosas"
    assert collect.topic(vague) == "Outro"
