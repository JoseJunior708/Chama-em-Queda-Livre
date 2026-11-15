from pathlib import Path

from app.ingest import criar_chunks, dividir_frases, ingerir_pasta, limpar_texto
from tests.conftest import criar_pdf


def test_limpeza_hifenizacao_e_quebras():
    bruto = "The combus-\ntion of hep-\n  tane\ndroplets   in\nmicrogravity."
    assert limpar_texto(bruto) == "The combustion of heptane droplets in microgravity."


def test_frases_nao_partem_decimais_nem_abreviaturas():
    texto = "The rate was 0.65 mm2/s as shown in Fig. 3 by Smith et al. in 2012. Next sentence here."
    frases = dividir_frases(texto)
    assert len(frases) == 2
    assert frases[0].endswith("in 2012.")


def test_chunks_respeitam_tamanho_sobreposicao_e_frases():
    frases = [f"Sentence number {i} describes a flame at {i}.5 cm/s." for i in range(120)]
    texto = " ".join(frases)
    chunks = criar_chunks(texto, tamanho=300, sobreposicao=80)
    assert len(chunks) > 5
    for c in chunks:
        assert len(c) <= 300
        assert c.endswith("cm/s.")          # termina numa frase inteira
        assert c.startswith("Sentence")     # começa numa frase inteira
    # sobreposição: a última frase de um chunk reaparece no seguinte
    ultima = chunks[0].split(". ")[-1]
    assert ultima.rstrip(".") in chunks[1]


def test_ingestao_pasta_com_metadados_e_pdf(pasta_docs: Path):
    r = ingerir_pasta(pasta_docs)
    ids = {d.doc_id for d in r.documentos}
    assert ids == {"flex_gotas", "saffire", "jato_gasoso"}
    flex = next(d for d in r.documentos if d.doc_id == "flex_gotas")
    assert flex.titulo == "FLEX: combustão de gotas na ISS"
    # formato do colector do NTRS: listas e url
    assert flex.metadados["ambiente"] == ["ISS"]
    assert flex.metadados["combustivel"] == ["heptano", "metanol"]
    assert flex.metadados["ano"] == 2012 and flex.metadados["autores"] == ["Dietrich, D. L."]
    assert flex.metadados["url"].startswith("https://ntrs.nasa.gov/")
    pdf_chunks = [c for c in r.chunks if c.doc_id == "jato_gasoso"]
    assert pdf_chunks and pdf_chunks[0].pagina == 1
    assert "drop tower" in pdf_chunks[0].text
    assert all(c.text and c.pagina >= 1 for c in r.chunks)


def test_pdf_sem_texto_e_ignorado_com_aviso(tmp_path: Path):
    criar_pdf(tmp_path / "digitalizado.pdf", [""])
    criar_pdf(tmp_path / "multi.pdf", ["First page about soot formation in flames.",
                                       "Second page about droplet burning rates."])
    r = ingerir_pasta(tmp_path)
    assert [d.doc_id for d in r.documentos] == ["multi"]
    assert any("digitalizado.pdf" in a for a in r.avisos)
    assert sorted({c.pagina for c in r.chunks}) == [1, 2]
