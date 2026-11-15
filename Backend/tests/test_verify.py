"""Verificador anti-invenção."""
from app.config import NAO_ENCONTREI
from app.verify import dividir_resposta, extrair_citacoes, numeros_em_falta, verificar
from tests.conftest import FakeLLM

FONTES = [
    {"tag": "S1", "text": "The burning rate constant was 0.65 mm2/s for heptane droplets at 1 atm."},
    {"tag": "S2", "text": "Flame spread rate reached 1.8 cm/s in 21% oxygen with 1,500 samples."},
]


def test_apanha_numero_errado():
    v = verificar("A constante da taxa de queima foi 0.75 mm2/s [S1].", FONTES, FakeLLM())
    f = v["frases"][0]
    assert f["estado"] == "numero_nao_encontrado" and "0.75" in f["motivo"]
    assert v["fiavel"] is False


def test_apanha_frase_sem_citacao():
    v = verificar("A chama propagou-se a 1.8 cm/s [S2]. A ISS é o melhor laboratório do mundo.", FONTES, FakeLLM())
    assert [f["estado"] for f in v["frases"]] == ["apoiada", "sem_citacao"]
    assert v["fiavel"] is False


def test_citacao_inexistente():
    v = verificar("A chama propagou-se a 1.8 cm/s [S7].", FONTES, FakeLLM())
    assert v["frases"][0]["estado"] == "sem_citacao" and "S7" in v["frases"][0]["motivo"]


def test_juiz_rejeita_frase_nao_apoiada():
    v = verificar("A chama propagou-se a 1.8 cm/s devido à radiação [S2].", FONTES, FakeLLM(juiz_apoia=False))
    assert v["frases"][0]["estado"] == "nao_apoiada" and v["fiavel"] is False


def test_juiz_indisponivel_nao_e_fiavel():
    v = verificar("A chama propagou-se a 1.8 cm/s [S2].", FONTES, FakeLLM(falhar=True))
    assert v["frases"][0]["estado"] == "nao_apoiada" and "indisponível" in v["frases"][0]["motivo"]


def test_resposta_totalmente_apoiada():
    texto = ("A constante foi 0.65 mm2/s a 1 atm [S1]. A propagação atingiu 1.8 cm/s com 21% de O2 [S2].\n"
             "- Foram usadas 1.500 amostras [S2].")
    v = verificar(texto, FONTES, FakeLLM())
    assert v["fiavel"] is True and len(v["frases"]) == 3
    assert v["frases"][1]["fontes"] == ["S2"]


def test_nao_encontrei_e_fiavel_sem_frases():
    assert verificar(NAO_ENCONTREI, FONTES) == {"fiavel": True, "frases": []}


def test_divisao_e_citacoes():
    frases = dividir_resposta("Resumo:\nA chama era azul [S1, S2]. A gota ardeu. [S2]\n[S1]")
    assert frases == ["A chama era azul [S1, S2].", "A gota ardeu. [S2] [S1]"]
    assert extrair_citacoes("x [S1][S3; 4]") == ["S1", "S3", "S4"]


def test_numeros_virgula_decimal_e_formulas():
    assert numeros_em_falta("taxa de 0,65 mm2/s [S1]", FONTES[0]["text"]) == []
    assert numeros_em_falta("com CO2 e O2", "no numbers") == []  # fórmulas químicas ignoradas
