"""Verificação anti-invenção, frase a frase.

Para cada frase da resposta:
  (a) tem citação [Sn] válida?                  -> senão: sem_citacao
  (b) todos os números existem no trecho citado? -> senão: numero_nao_encontrado
  (c) o LLM-juiz confirma que o trecho apoia a frase? -> senão: nao_apoiada
Se passar tudo: apoiada. "fiavel" só é verdadeiro se todas as frases estiverem apoiadas.
"""
from __future__ import annotations

import logging
import re

from .config import NAO_ENCONTREI

log = logging.getLogger(__name__)

APOIADA, SEM_CITACAO, NUMERO_NAO_ENCONTRADO, NAO_APOIADA = (
    "apoiada", "sem_citacao", "numero_nao_encontrado", "nao_apoiada")

_CITACAO = re.compile(r"\[\s*(S\d+(?:\s*[,;]\s*S?\d+)*)\s*\]", re.I)
_MAIUSC = "A-ZÁÉÍÓÚÂÊÔÃÕÀÇ\"“(«"
_DIVISOR = re.compile(rf"(?<=[.!?])\s+(?=[{_MAIUSC}])|(?<=\])\s+(?=[{_MAIUSC}])")
# Números "soltos" na frase (ignora os colados a letras, ex.: O2, CO2, S1, mm2).
_NUM_FRASE = re.compile(r"(?<![A-Za-z\d.,])\d+(?:[.,]\d+)*")
_NUM_FONTE = re.compile(r"\d+(?:[.,]\d+)*")

SISTEMA_JUIZ = (
    "És um verificador de factos rigoroso. Recebes frases em português e trechos de artigos "
    "científicos (em inglês). Para cada frase decide se o(s) trecho(s) citado(s) afirmam "
    "EXPLICITAMENTE o que a frase diz. Uma tradução fiel conta como apoiada. Considera NÃO "
    "apoiada se a frase acrescenta conclusões, causas, generalizações, comparações ou valores "
    "que o trecho não contém, ou se contradiz o trecho. Responde só com JSON."
)


def extrair_citacoes(frase: str) -> list[str]:
    tags: list[str] = []
    for m in _CITACAO.finditer(frase):
        for parte in re.split(r"[,;]", m.group(1)):
            n = re.sub(r"\D", "", parte)
            if n and f"S{n}" not in tags:
                tags.append(f"S{n}")
    return tags


def _e_titulo(linha: str) -> bool:
    if _CITACAO.search(linha):
        return False
    return linha.endswith(":") or (len(linha.split()) <= 6 and not re.search(r"[.!?]$", linha))


def dividir_resposta(texto: str) -> list[str]:
    """Divide a resposta em frases; ignora títulos e marcadores de lista."""
    frases: list[str] = []
    for linha in texto.splitlines():
        linha = re.sub(r"^\s*(?:#+\s*|[-*•]\s+|\d+[.)]\s+)", "", linha)
        linha = linha.replace("**", "").strip()
        if not linha or _e_titulo(linha):
            continue
        for parte in _DIVISOR.split(linha):
            parte = parte.strip()
            if not parte:
                continue
            # citação órfã (ex.: "[S2]" numa linha à parte) junta-se à frase anterior
            if frases and not re.search(r"[A-Za-zÀ-ÿ]", _CITACAO.sub("", parte)):
                frases[-1] = f"{frases[-1]} {parte}"
            else:
                frases.append(parte)
    return frases


def _variantes(num: str) -> set[str]:
    v = {num, num.replace(",", ".")}
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", num):  # separador de milhares
        v.add(re.sub(r"[.,]", "", num))
    return v


def numeros_da_frase(frase: str) -> list[str]:
    return _NUM_FRASE.findall(_CITACAO.sub("", frase))


def numeros_em_falta(frase: str, texto_fonte: str) -> list[str]:
    na_fonte: set[str] = set()
    for n in _NUM_FONTE.findall(texto_fonte):
        na_fonte |= _variantes(n)
    return [n for n in numeros_da_frase(frase) if not (_variantes(n) & na_fonte)]


def _prompt_juiz(pendentes: list[dict], fontes: dict[str, dict]) -> str:
    blocos = ["FRASES A AVALIAR"]
    for f in pendentes:
        trechos = "\n".join(f"[{t}] {fontes[t]['text']}" for t in f["fontes"])
        blocos.append(f"### Frase {f['i']}\n{f['frase']}\nTrechos citados:\n{trechos}")
    blocos.append(
        'Responde com uma lista JSON, um objecto por frase: '
        '[{"i": <número da frase>, "apoiada": true|false, "motivo": "<explicação curta em português>"}]')
    return "\n\n".join(blocos)


def verificar(resposta: str, fontes: list[dict], llm=None, usar_juiz: bool = True) -> dict:
    """Devolve {"fiavel": bool, "frases": [{"i","frase","fontes","estado","motivo"}]}."""
    if resposta.strip() == NAO_ENCONTREI:
        return {"fiavel": True, "frases": []}

    por_tag = {f["tag"]: f for f in fontes}
    frases: list[dict] = []
    pendentes: list[dict] = []
    for i, texto in enumerate(dividir_resposta(resposta), start=1):
        tags = extrair_citacoes(texto)
        item = {"i": i, "frase": texto, "fontes": tags, "estado": APOIADA, "motivo": ""}
        invalidas = [t for t in tags if t not in por_tag]
        if not tags:
            item.update(estado=SEM_CITACAO, motivo="A frase não tem citação.")
        elif invalidas:
            item.update(estado=SEM_CITACAO, motivo=f"Citação inexistente: {', '.join(invalidas)}.")
        else:
            texto_fontes = " ".join(por_tag[t]["text"] for t in tags)
            falta = numeros_em_falta(texto, texto_fontes)
            if falta:
                item.update(estado=NUMERO_NAO_ENCONTRADO,
                            motivo=f"Número(s) ausente(s) do trecho citado: {', '.join(falta)}.")
            else:
                pendentes.append(item)
        frases.append(item)

    if pendentes:
        if usar_juiz and llm is not None:
            try:
                veredictos = llm.generate_json(_prompt_juiz(pendentes, por_tag), system=SISTEMA_JUIZ)
                if isinstance(veredictos, dict):
                    veredictos = veredictos.get("frases") or veredictos.get("resultados") or [veredictos]
                mapa = {int(v.get("i")): v for v in veredictos if isinstance(v, dict) and "i" in v}
                for item in pendentes:
                    v = mapa.get(item["i"])
                    if v is None:
                        item.update(estado=NAO_APOIADA, motivo="O juiz não avaliou esta frase.")
                    elif v.get("apoiada") is True:
                        item.update(motivo=str(v.get("motivo") or "Confirmada pelo juiz."))
                    else:
                        item.update(estado=NAO_APOIADA,
                                    motivo=str(v.get("motivo") or "O trecho não apoia a frase."))
            except Exception as e:  # sem confirmação, não se pode afirmar que é fiável
                log.warning("Juiz LLM falhou: %s", e)
                for item in pendentes:
                    item.update(estado=NAO_APOIADA,
                                motivo="Juiz indisponível: não foi possível confirmar o apoio.")
        else:
            for item in pendentes:
                item["motivo"] = "Citação e números conferidos (juiz LLM desactivado)."

    fiavel = bool(frases) and all(f["estado"] == APOIADA for f in frases)
    return {"fiavel": fiavel, "frases": frases}
