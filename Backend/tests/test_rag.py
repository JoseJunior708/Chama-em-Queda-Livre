"""RAG, classificação e extracção com LLM e embeddings simulados."""
import pytest

from app.config import NAO_ENCONTREI
from app.rag import Motor, classificar_documento, classificar_por_palavras
from tests.conftest import TEXTO_GASOSO, TEXTO_GOTAS, TEXTO_SOLIDOS, FakeLLM


def test_classificacao_por_palavras_chave():
    assert classificar_por_palavras(TEXTO_GOTAS) == "Gotas (droplets)"
    assert classificar_por_palavras(TEXTO_SOLIDOS) == "Combustíveis sólidos"
    assert classificar_por_palavras(TEXTO_GASOSO) == "Chamas gasosas"
    assert classificar_por_palavras("Supercritical water oxidation near the critical point.") \
        == "Fluidos reactivos supercríticos"
    assert classificar_por_palavras("Spacecraft fire safety and fire detection in the cabin.") \
        == "Segurança contra incêndios em naves"
    assert classificar_por_palavras("Budget report for the year.") == "Outro"


def test_classificacao_llm_com_recurso_a_palavras_chave():
    doc = {"doc_id": "d", "titulo": "t", "metadados": {}}
    chunks = [{"text": TEXTO_GOTAS}]
    assert classificar_documento(doc, chunks, FakeLLM({"Categorias possíveis": {"categoria": "Chamas gasosas"}})) \
        == ("Chamas gasosas", "llm")
    # LLM devolve categoria inválida -> palavras-chave
    assert classificar_documento(doc, chunks, FakeLLM({"Categorias possíveis": {"categoria": "Plasma"}})) \
        == ("Gotas (droplets)", "palavras-chave")
    # LLM falha -> palavras-chave
    assert classificar_documento(doc, chunks, FakeLLM(falhar=True)) == ("Gotas (droplets)", "palavras-chave")
    # categoria nos metadados tem prioridade
    doc_meta = {"doc_id": "d", "titulo": "t", "metadados": {"categoria": "outro"}}
    assert classificar_documento(doc_meta, chunks, None) == ("Outro", "metadados")


@pytest.fixture
def motor(ambiente):
    llm = FakeLLM({
        "Responde à pergunta: Qual a taxa de queima":
            "A constante da taxa de queima foi 0.65 mm2/s [S1]. As gotas tinham 2.5 mm de diâmetro inicial [S1].",
        "Responde à pergunta: Qual o diâmetro":
            "As gotas tinham 3.0 mm de diâmetro [S1]. Isto prova que a ISS é segura.",
        "Responde à pergunta: Quanto custou": NAO_ENCONTREI,
        "Extrai do documento": {
            "combustivel": {"valor": "Heptane", "fonte": "S1"},
            "ambiente": {"valor": "International Space Station", "fonte": "S1"},
            "pressao": {"valor": "1 atm", "fonte": "S1"},
            "concentracao_o2": {"valor": "21%", "fonte": "S1"},
            "velocidade_escoamento": {"valor": "5 cm/s", "fonte": "S1"},  # inventado
            "resultado_principal": {"valor": None, "fonte": None},
            "resultado": {"valor": "Extinguiu-se", "fonte": "S1"},
        },
    })
    m = Motor(ambiente, llm=llm)
    m.indexar()
    return m


def test_indexacao_classifica_e_persiste(motor, ambiente):
    docs = {d["doc_id"]: d for d in motor.documentos()}
    assert docs["flex_gotas"]["categoria"] == "Gotas (droplets)"
    assert docs["saffire"]["categoria_origem"] == "palavras-chave"  # FakeLLM devolve {} na classificação
    assert Motor(ambiente, llm=None).indice.documentos.keys() == docs.keys()


def test_perguntar_resposta_fiavel_com_fontes(motor):
    r = motor.perguntar("Qual a taxa de queima das gotas de heptano?")
    assert r["fontes"][0]["doc_id"] == "flex_gotas"
    assert set(r["fontes"][0]) == {"tag", "doc_id", "titulo", "pagina", "text", "url"}
    assert r["fontes"][0]["url"] == "https://ntrs.nasa.gov/citations/20120000001"
    assert r["verificacao"]["fiavel"] is True
    assert [f["estado"] for f in r["verificacao"]["frases"]] == ["apoiada", "apoiada"]
    # o prompt só contém trechos etiquetados
    prompt_rag = next(p for p in motor.llm.prompts if "Responde à pergunta" in p)
    assert prompt_rag.startswith("TRECHOS:\n\n[S1] (documento:")


def test_perguntar_detecta_invencao(motor):
    r = motor.perguntar("Qual o diâmetro das gotas?")
    estados = [f["estado"] for f in r["verificacao"]["frases"]]
    assert estados == ["numero_nao_encontrado", "sem_citacao"]
    assert r["verificacao"]["fiavel"] is False


def test_nao_encontrei(motor):
    r = motor.perguntar("Quanto custou a missão?")
    assert r["resposta"] == NAO_ENCONTREI
    assert r["verificacao"] == {"fiavel": True, "frases": []}


def test_filtro_categoria_sem_resultados(motor):
    r = motor.perguntar("taxa de queima", categoria="Fluidos reactivos supercríticos")
    assert r["resposta"] == NAO_ENCONTREI and r["fontes"] == []


def test_resumir_e_comparar(motor):
    r = motor.resumir("saffire")
    assert {f["doc_id"] for f in r["fontes"]} == {"saffire"}
    c = motor.comparar(["saffire", "flex_gotas"])
    assert {f["doc_id"] for f in c["fontes"]} == {"saffire", "flex_gotas"}
    with pytest.raises(ValueError):
        motor.comparar(["saffire"])
    with pytest.raises(KeyError):
        motor.resumir("nao-existe")


def test_extracao_estruturada_descarta_valores_sem_fonte(motor):
    e = motor.extrair("flex_gotas")
    c = e["campos"]
    assert c["combustivel"]["valor"] == "Heptane" and c["combustivel"]["pagina"] == 1
    assert c["pressao"]["valor_numerico"] == 1.0 and c["pressao"]["unidade"] == "atm"
    assert c["concentracao_o2"]["valor_numerico"] == 21.0
    assert c["velocidade_escoamento"]["valor"] is None  # 5 cm/s não está na fonte
    assert "descartado" in c["velocidade_escoamento"]["motivo"]
    assert c["resultado_principal"]["valor"] is None
    assert c["resultado"]["valor"] == "extinguiu" and c["resultado"]["fonte"] == "S1"
    assert motor.extracoes_em_cache()[0]["doc_id"] == "flex_gotas"


def test_resultado_fora_das_categorias_e_descartado(ambiente):
    from app.rag import normalizar_resultado

    assert normalizar_resultado(" Propagou-se ") == "propagou"
    assert normalizar_resultado("Extinção por sopro") == "extinguiu"
    assert normalizar_resultado("inconclusivo") is None

    m = Motor(ambiente, llm=FakeLLM({"Extrai do documento": {"resultado": {"valor": "inconclusivo", "fonte": "S1"}}}))
    m.indexar()
    r = m.extrair("flex_gotas")["campos"]["resultado"]
    assert r["valor"] is None and "Categoria inválida" in r["motivo"]


def test_conclusoes_so_com_fonte_e_invalidadas_pelo_indice(motor):
    from app.rag import TEMAS_CONCLUSOES

    assert motor.conclusoes_em_cache() == []
    # O LLM simulado responde "Não encontrei" a todas as perguntas dos temas: nada é guardado.
    assert motor.gerar_conclusoes() == []

    motor.llm.respostas["Responde à pergunta: Porque é que as chamas de gotas"] = \
        "A constante da taxa de queima foi 0.65 mm2/s [S1]."
    geradas = motor.gerar_conclusoes()
    assert [c["id"] for c in geradas] == ["C4"]
    assert geradas[0]["titulo"] == dict((i, t) for i, t, _ in TEMAS_CONCLUSOES)["C4"]
    assert [f["tag"] for f in geradas[0]["fontes"]] == ["S1"]  # só as fontes citadas
    assert motor.conclusoes_em_cache() == geradas

    # Um documento alterado invalida as conclusões guardadas.
    motor.indice.documentos["flex_gotas"]["hash"] = "outro"
    assert motor.conclusoes_em_cache() == []
