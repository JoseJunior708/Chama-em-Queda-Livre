"""Motor RAG: indexação, classificação, perguntas, resumos, comparações e extracção estruturada.

Regra central: nenhuma afirmação sem fonte. O LLM só vê os trechos recuperados, etiquetados
[S1], [S2]...; cada resposta é verificada frase a frase (ver verify.py).
"""
from __future__ import annotations

import hashlib
import json
import logging
import re

from .config import CATEGORIAS, NAO_ENCONTREI, Settings, get_settings
from .ingest import ingerir_pasta
from .llm import LLMError, criar_cliente
from .search import CacheEmbeddings, Indice, embed_com_cache, sem_acentos, tokenizar
from .verify import numeros_em_falta, verificar

log = logging.getLogger(__name__)

_PADRAO = object()

# ------------------------------------------------------------------ prompts

SISTEMA_RAG = f"""És um assistente científico sobre combustão em microgravidade e segurança contra \
incêndios no espaço, baseado em documentos da NASA.
Regras obrigatórias:
1. Usa APENAS a informação dos trechos fornecidos. Não uses conhecimento externo e não tires \
conclusões, causas ou generalizações que os trechos não afirmem explicitamente.
2. Escreve em português europeu, em frases declarativas curtas, em texto corrido (sem títulos).
3. Cada frase termina com a citação do(s) trecho(s) que a suportam, antes do ponto final, \
no formato [S1] ou [S1, S3]. Exemplo: "A chama extinguiu-se ao fim de 3 s [S2]."
4. Copia números e unidades exactamente como aparecem no trecho: não convertas unidades, \
não arredondes, não calcules valores novos.
5. Não escrevas frases sem citação (nem introduções, nem conclusões genéricas).
6. Se os trechos só respondem a parte do pedido, responde apenas a essa parte.
7. Se os trechos não respondem directamente mas tratam do assunto do pedido, relata o que \
eles dizem sobre esse assunto (observações, condições, explicações dadas pelos autores), \
sempre com citação e sem acrescentar conclusões tuas. Usa apenas os trechos ligados ao assunto \
do pedido: não listes factos soltos de outros temas só porque aparecem nos trechos.
8. Só se nenhum trecho tiver relação com o pedido é que respondes exactamente e apenas: \
"{NAO_ENCONTREI}"""

# ------------------------------------------------------------------ conversa

# Palavras de mensagens que não são perguntas sobre os documentos ("olá", "podes ajudar?").
_CONVERSA = set("""
ola oi oie bom dia boa tarde noite hello hi hey help tudo bem obrigado obrigada valeu
entender perceber compreender explicar explica melhor mais isso isto aquilo
plataforma site projeto projecto aplicacao app pagina ferramenta este esta esse essa
pode podes ajudar ajuda ajudas algo alguma coisa favor preciso quero queria gostava
quem es tu voce me te mim fazer faz sabe sabes consegue consegues funciona funcionas serve serves
isto aqui pergunta perguntas perguntar posso exemplo exemplos tipo assistente sistema
""".split())

SUGESTOES = [
    "A que concentração de oxigénio se extinguem as gotas de metanol?",
    "O que são chamas frias e em que condições foram observadas?",
    "Como varia a propagação da chama em PMMA com a velocidade do escoamento?",
    "Que resultados teve a experiência BASS-II?",
]


# Palavras que remetem para a mensagem anterior ("explica melhor isso", "e a pressão dele?").
_REMISSIVAS = set("""
isso isto aquilo disso disto daquilo nisso nisto ele ela eles elas dele dela deles delas
esse essa esses essas este esta estes estas mesmo mesma anterior acima
""".split())

SISTEMA_REESCREVER = (
    "Reescreves perguntas de seguimento de uma conversa como perguntas autónomas, que se percebam "
    "sem a conversa. Não respondes à pergunta nem acrescentas factos: só substituis as referências "
    "(\"isso\", \"ele\", \"essa experiência\") pelo assunto de que a conversa tratava. Escreve em "
    "português. Responde só com JSON.")


def depende_do_historico(texto: str) -> bool:
    """Verdadeiro se a pergunta só se percebe com a mensagem anterior."""
    palavras = set(re.findall(r"[a-z]+", sem_acentos(texto.lower())))
    conteudo = [t for t in tokenizar(texto) if t not in _CONVERSA]
    return bool(palavras & _REMISSIVAS) or len(conteudo) <= 2


_NOME_PLATAFORMA = re.compile(r"chama\s+(?:em|de|da|na)\s+queda\s+livre")


def e_sobre_a_plataforma(texto: str) -> bool:
    """Verdadeiro se a pergunta é sobre a própria plataforma e não sobre os documentos."""
    base = sem_acentos(texto.lower())
    nomeada = bool(_NOME_PLATAFORMA.search(base)) or bool(
        re.search(r"\b(plataforma|site|projec?to|aplicacao|app|ferramenta)\b", base))
    return nomeada and e_conversa(_NOME_PLATAFORMA.sub(" ", base))


def e_conversa(texto: str) -> bool:
    """Verdadeiro para saudações e pedidos de ajuda genéricos, sem conteúdo para pesquisar."""
    return not [t for t in tokenizar(texto) if t not in _CONVERSA]


def _contexto(fontes: list[dict]) -> str:
    return "\n\n".join(
        f"[{f['tag']}] (documento: {f['titulo']}, página {f['pagina']})\n{f['text']}" for f in fontes)


# ------------------------------------------------------------------ classificação

PALAVRAS_CHAVE: dict[str, dict[str, float]] = {
    "Segurança contra incêndios em naves": {
        "spacecraft fire": 3, "fire safety": 3, "saffire": 3, "flammability": 2, "fire detection": 3,
        "smoke": 1.5, "nasa-std-6001": 3, "cabin": 1.5, "extinguish": 1.5, "fire suppression": 2,
        "crew": 1, "spacecraft": 1.5, "material flammability": 3, "post-fire": 2,
    },
    "Gotas (droplets)": {
        "droplet": 3, "flex": 2, "burning rate constant": 3, "cool flame": 2, "d2 law": 3,
        "d-squared": 3, "fiber-supported": 2, "sphere": 1, "heptane": 1, "evaporation": 1.5,
        "spray": 1.5, "radiative extinction": 1.5,
    },
    "Chamas gasosas": {
        "gas jet": 3, "diffusion flame": 2.5, "premixed": 2.5, "laminar flame": 2, "soot": 2,
        "acme": 2, "coflow": 2.5, "gaseous": 2, "burke-schumann": 3, "flame ball": 3,
        "methane": 1, "ethylene": 1, "lean flame": 1.5, "flame design": 2,
    },
    "Combustíveis sólidos": {
        "solid fuel": 3, "flame spread": 2.5, "pmma": 3, "cotton": 2, "fabric": 1.5, "char": 1.5,
        "smolder": 3, "polymer": 1.5, "cellulose": 2, "burning and suppression of solids": 3,
        "wire insulation": 2.5, "thin fuel": 2, "thick fuel": 2, "opposed flow": 1.5,
    },
    "Fluidos reactivos supercríticos": {
        "supercritical": 3, "transcritical": 3, "scwo": 3, "critical point": 2.5,
        "supercritical water oxidation": 4, "reactive fluid": 2, "near-critical": 2.5,
    },
}


def classificar_por_palavras(texto: str) -> str:
    t = texto.lower()
    pontos = {cat: sum(peso * t.count(chave.lower()) for chave, peso in palavras.items())
              for cat, palavras in PALAVRAS_CHAVE.items()}
    melhor = max(pontos, key=pontos.get)
    return melhor if pontos[melhor] > 0 else "Outro"


def normalizar_categoria(valor) -> str | None:
    if not isinstance(valor, str) or not valor.strip():
        return None
    alvo = sem_acentos(valor.strip().lower())
    for cat in CATEGORIAS:
        c = sem_acentos(cat.lower())
        if alvo == c or c.startswith(alvo) or alvo.startswith(c.split(" (")[0]):
            return cat
    return None


SISTEMA_CLASSIFICAR = (
    "Classificas documentos científicos da NASA sobre combustão em microgravidade. "
    "Escolhe exactamente UMA categoria da lista, com base apenas no texto fornecido. Responde só com JSON.")


def classificar_documento(doc: dict, chunks: list[dict], llm=None) -> tuple[str, str]:
    """Devolve (categoria, origem). Origem: metadados | llm | palavras-chave."""
    meta_cat = normalizar_categoria(doc.get("metadados", {}).get("categoria"))
    if meta_cat:
        return meta_cat, "metadados"
    amostra = " ".join(c["text"] for c in chunks[:4])[:4500]
    if llm is not None:
        prompt = (f"Categorias possíveis: {json.dumps(CATEGORIAS, ensure_ascii=False)}\n\n"
                  f"Título: {doc.get('titulo')}\n\nTexto:\n{amostra}\n\n"
                  'Responde com {"categoria": "<uma das categorias, escrita exactamente igual>", '
                  '"justificacao": "<uma frase>"}')
        try:
            dados = llm.generate_json(prompt, system=SISTEMA_CLASSIFICAR)
            cat = normalizar_categoria(dados.get("categoria") if isinstance(dados, dict) else None)
            if cat:
                return cat, "llm"
            log.warning("Categoria inválida do LLM para %s; a usar palavras-chave.", doc["doc_id"])
        except Exception as e:
            log.warning("Classificação por LLM falhou para %s (%s); a usar palavras-chave.", doc["doc_id"], e)
    texto_completo = f"{doc.get('titulo', '')} " + " ".join(c["text"] for c in chunks)
    return classificar_por_palavras(texto_completo), "palavras-chave"


# ------------------------------------------------------------------ extracção estruturada

CAMPOS_EXTRACAO = {
    "combustivel": ("combustível utilizado", "fuel used burned heptane methane ethylene PMMA cotton"),
    "ambiente": ("ambiente/instalação da experiência (ISS, torre de queda, voo parabólico, foguete de sondagem, laboratório em 1 g...)",
                 "experiment conducted aboard International Space Station drop tower parabolic flight sounding rocket facility"),
    "pressao": ("pressão ambiente", "ambient pressure atm kPa psia"),
    "concentracao_o2": ("concentração de oxigénio", "oxygen concentration mole fraction percent O2 atmosphere"),
    "velocidade_escoamento": ("velocidade do escoamento", "flow velocity cm/s opposed forced flow speed"),
    "resultado_principal": ("resultado principal, numa frase curta em português", "main result conclusion we found showed demonstrated"),
    "resultado": ("resultado do ensaio, numa só palavra: \"propagou\" se a chama se propagou ou se manteve, "
                  "\"extinguiu\" se a chama se extinguiu ou não houve ignição",
                  "flame spread sustained burned extinguished extinction blow-off quenched did not ignite"),
}
RESULTADOS = ("propagou", "extinguiu")
CAMPOS_NUMERICOS = {"pressao", "concentracao_o2", "velocidade_escoamento"}

SISTEMA_EXTRAIR = (
    "Extrais dados de artigos científicos. Usa APENAS os trechos fornecidos. Quando um campo não "
    "consta explicitamente nos trechos, usa null. Copia números e unidades exactamente como na fonte. "
    "Responde só com JSON.")


def normalizar_resultado(valor: str) -> str | None:
    """Reduz o valor do LLM a uma das categorias de RESULTADOS (ou None se não for nenhuma)."""
    v = sem_acentos(valor.strip().lower())
    if v.startswith("propag"):
        return "propagou"
    if v.startswith("extin"):
        return "extinguiu"
    return None


# ------------------------------------------------------------------ conclusões

# Perguntas fixas que alimentam a página de conclusões. Cada conclusão é a resposta verificada
# a uma destas perguntas; só fica guardada se citar pelo menos uma fonte.
TEMAS_CONCLUSOES = [
    ("C1", "Limite de oxigénio para a propagação de chama",
     "Abaixo de que concentração de oxigénio deixa de haver propagação de chama em microgravidade?"),
    ("C2", "Efeito da velocidade do escoamento",
     "Como é que a velocidade do escoamento afecta a propagação e a extinção da chama em microgravidade?"),
    ("C3", "Efeito da pressão ambiente",
     "Como é que a pressão ambiente afecta a inflamabilidade dos materiais em microgravidade?"),
    ("C4", "Extinção de gotas de combustível",
     "Porque é que as chamas de gotas de combustível se extinguem em microgravidade?"),
    ("C5", "Microgravidade em comparação com a gravidade normal",
     "Que diferenças há entre a combustão em microgravidade e em gravidade normal?"),
    ("C6", "Detecção e supressão de incêndios em naves",
     "Que conclusões há sobre a detecção e a supressão de incêndios em naves espaciais?"),
]


def _numero_e_unidade(valor: str) -> tuple[float | None, str | None]:
    m = re.search(r"(-?\d+(?:[.,]\d+)?)\s*([^\d\s,;()][^,;()]{0,15})?", valor)
    if not m:
        return None, None
    try:
        num = float(m.group(1).replace(",", "."))
    except ValueError:
        return None, None
    unidade = (m.group(2) or "").strip() or None
    return num, unidade


# ------------------------------------------------------------------ motor

class Motor:
    def __init__(self, settings: Settings | None = None, llm=_PADRAO, embedder=_PADRAO):
        self.s = settings or get_settings()
        self.llm = criar_cliente(self.s) if llm is _PADRAO else llm
        self.embedder = self.llm if embedder is _PADRAO else embedder
        id_emb = getattr(self.embedder, "id_embeddings", type(self.embedder).__name__)
        self.cache = CacheEmbeddings(self.s.index_dir, id_emb)
        self.indice = Indice.carregar(self.s.index_dir)
        self._f_extracoes = self.s.index_dir / "extracoes.json"
        self._f_conclusoes = self.s.index_dir / "conclusoes.json"

    # -------------------------------------------------------------- indexação
    def indexar(self) -> dict:
        r = ingerir_pasta(self.s.docs_dir, self.s.chunk_size, self.s.chunk_overlap)
        avisos = list(r.avisos)
        anteriores = self.indice.documentos
        chunks = [c.__dict__.copy() for c in r.chunks]

        vetores = None
        if self.embedder is not None and chunks:
            titulos_doc = {d.doc_id: d.titulo for d in r.documentos}
            try:
                vetores = embed_com_cache(self.embedder, self.cache, [c["text"] for c in chunks],
                                          tipo="documento", titulos=[titulos_doc[c["doc_id"]] for c in chunks])
            except Exception as e:
                avisos.append(f"Embeddings indisponíveis ({e}); índice só com BM25.")
                log.warning(avisos[-1])
        elif chunks:
            avisos.append("Sem embedder (GEMINI_API_KEY em falta): índice só com BM25.")

        documentos: dict[str, dict] = {}
        for doc in r.documentos:
            d = doc.to_dict()
            ant = anteriores.get(doc.doc_id)
            meta_cat = normalizar_categoria(d["metadados"].get("categoria"))
            if ant and ant.get("hash") == doc.hash and ant.get("categoria_origem") == "llm" and not meta_cat:
                d["categoria"], d["categoria_origem"] = ant["categoria"], "llm"  # já classificado
            else:
                d["categoria"], d["categoria_origem"] = classificar_documento(
                    d, [c for c in chunks if c["doc_id"] == doc.doc_id], self.llm)
            documentos[doc.doc_id] = d

        self.indice = Indice(documentos, chunks, vetores)
        self.indice.salvar(self.s.index_dir)
        return {"documentos": len(documentos), "chunks": len(chunks),
                "embeddings": vetores is not None, "avisos": avisos}

    # -------------------------------------------------------------- consulta
    def _exigir_indice(self):
        if self.indice.vazio:
            raise ValueError("Índice vazio: corre 'python -m app.cli index' ou POST /reindex.")

    def _exigir_llm(self):
        if self.llm is None:
            raise LLMError("LLM indisponível: define GEMINI_API_KEY no .env.")

    def _url(self, doc_id: str) -> str | None:
        """Link do documento (campo "url" dos metadados), usado nas citações."""
        url = self.indice.documentos.get(doc_id, {}).get("metadados", {}).get("url")
        return url if isinstance(url, str) and url.startswith(("http://", "https://")) else None

    def documentos(self) -> list[dict]:
        out = []
        for d in self.indice.documentos.values():
            n = sum(1 for c in self.indice.chunks if c["doc_id"] == d["doc_id"])
            out.append({k: d.get(k) for k in ("doc_id", "titulo", "ficheiro", "paginas", "categoria",
                                              "categoria_origem", "metadados")}
                       | {"chunks": n, "url": self._url(d["doc_id"])})
        return out

    def categorias(self) -> list[dict]:
        cont = {c: 0 for c in CATEGORIAS}
        for d in self.indice.documentos.values():
            if d.get("categoria") in cont:
                cont[d["categoria"]] += 1
        return [{"categoria": c, "documentos": n} for c, n in cont.items()]

    def pesquisar(self, consulta: str, k: int | None = None, doc_id=None, categoria: str | None = None,
                  filtros: dict | None = None) -> list[dict]:
        self._exigir_indice()
        res = self.indice.pesquisar(consulta, k or self.s.top_k, doc_id=doc_id, categoria=categoria,
                                    filtros=filtros, embedder=self.embedder, cache=self.cache,
                                    peso_vetorial=self.s.peso_vetorial)
        for r in res:
            r["titulo"] = self.indice.documentos.get(r["doc_id"], {}).get("titulo", r["doc_id"])
            r["url"] = self._url(r["doc_id"])
        return res

    def _fontes(self, resultados: list[dict]) -> list[dict]:
        vistos, fontes = set(), []
        for r in resultados:
            if r["id"] in vistos:
                continue
            vistos.add(r["id"])
            titulo = self.indice.documentos.get(r["doc_id"], {}).get("titulo", r["doc_id"])
            fontes.append({"tag": f"S{len(fontes) + 1}", "doc_id": r["doc_id"], "titulo": titulo,
                           "pagina": r["pagina"], "text": r["text"], "url": self._url(r["doc_id"])})
        return fontes

    def _responder(self, instrucao: str, fontes: list[dict]) -> dict:
        if not fontes:
            return {"resposta": NAO_ENCONTREI, "fontes": [], "verificacao": {"fiavel": True, "frases": []},
                    "tipo": "nao_encontrado", "sugestoes": SUGESTOES}
        self._exigir_llm()
        prompt = f"TRECHOS:\n\n{_contexto(fontes)}\n\nPEDIDO:\n{instrucao}"
        resposta = self.llm.generate(prompt, system=SISTEMA_RAG).strip()
        if sem_acentos(NAO_ENCONTREI.lower().rstrip(".")) in sem_acentos(resposta.lower()) \
                and len(resposta) < len(NAO_ENCONTREI) + 40:
            resposta = NAO_ENCONTREI
        verificacao = verificar(resposta, fontes, llm=self.llm, usar_juiz=self.s.verify_judge)
        verificacao["removidas"] = []
        if self.s.remover_nao_apoiadas:
            resposta = self._retirar_nao_apoiadas(resposta, verificacao)
        encontrou = resposta != NAO_ENCONTREI
        return {"resposta": resposta, "fontes": fontes, "verificacao": verificacao,
                "tipo": "resposta" if encontrou else "nao_encontrado",
                "sugestoes": [] if encontrou else SUGESTOES}

    @staticmethod
    def _retirar_nao_apoiadas(resposta: str, verificacao: dict) -> str:
        """Retira da resposta as frases que falharam a verificação e guarda-as em "removidas".

        A resposta mostrada fica só com frases apoiadas. Se o juiz esteve indisponível não se
        retira nada: nesse caso as frases não foram reprovadas, apenas ficaram por confirmar."""
        frases = verificacao["frases"]
        falhadas = [f for f in frases if f["estado"] != "apoiada"]
        if not falhadas or any("Juiz indisponível" in f["motivo"] for f in falhadas):
            return resposta
        apoiadas = [f for f in frases if f["estado"] == "apoiada"]
        for novo_i, f in enumerate(apoiadas, start=1):
            f["i"] = novo_i
        verificacao.update(frases=apoiadas, removidas=falhadas, fiavel=True)
        return " ".join(f["frase"] for f in apoiadas) if apoiadas else NAO_ENCONTREI

    def _conversa(self, sobre_plataforma: bool = False) -> dict:
        """Resposta fixa a saudações e pedidos de ajuda: não passa pelo LLM nem afirma nada científico."""
        n = len(self.indice.documentos)
        if sobre_plataforma:
            texto = (f"A Chama em Queda Livre é esta plataforma. Reúne {n} documentos públicos da NASA sobre "
                     "experiências de combustão em microgravidade e segurança contra incêndios no espaço, "
                     "organiza-os por tipo de experiência e permite pesquisá-los, resumi-los, compará-los e "
                     "fazer-lhes perguntas. As respostas vêm só desses documentos e cada frase indica o trecho "
                     "de onde vem. É um projecto independente, não é um produto oficial da NASA. "
                     "Experimenta uma destas perguntas ou escreve a tua.")
            return {"resposta": texto, "fontes": [], "verificacao": {"fiavel": True, "frases": []},
                    "tipo": "conversa", "sugestoes": SUGESTOES}
        texto = (f"Posso responder a perguntas sobre os {n} documentos da NASA indexados, que tratam de "
                 "combustão em microgravidade e de segurança contra incêndios no espaço. Só uso o que está "
                 "nesses documentos, e cada frase da resposta indica o trecho de onde vem. "
                 "Experimenta uma destas perguntas ou escreve a tua.")
        return {"resposta": texto, "fontes": [], "verificacao": {"fiavel": True, "frases": []},
                "tipo": "conversa", "sugestoes": SUGESTOES}

    def _reescrever(self, pergunta: str, historico: list[dict]) -> str:
        """Transforma uma pergunta de seguimento numa pergunta autónoma, com base na conversa."""
        conversa = "\n\n".join(
            f"Utilizador: {h.get('pergunta', '')}\nAssistente: {str(h.get('resposta', ''))[:700]}"
            for h in historico[-2:])
        prompt = (f"CONVERSA ANTERIOR:\n{conversa}\n\nPERGUNTA DE SEGUIMENTO:\n{pergunta}\n\n"
                  'Responde com {"pergunta": "<pergunta autónoma>"}')
        try:
            dados = self.llm.generate_json(prompt, system=SISTEMA_REESCREVER)
            nova = str(dados.get("pergunta") or "").strip() if isinstance(dados, dict) else ""
            if len(nova) >= 5:
                return nova
        except Exception as e:
            log.warning("Não foi possível reescrever a pergunta de seguimento: %s", e)
        # sem LLM, junta a pergunta anterior para a busca ter contexto
        return f"{historico[-1].get('pergunta', '')} {pergunta}".strip()

    def perguntar(self, pergunta: str, categoria: str | None = None, doc_id=None,
                  historico: list[dict] | None = None) -> dict:
        """`historico` são as trocas anteriores [{"pergunta", "resposta"}], da mais antiga à mais recente."""
        self._exigir_indice()
        interpretada = None
        if e_sobre_a_plataforma(pergunta):
            return self._conversa(sobre_plataforma=True)
        if historico and self.llm is not None and depende_do_historico(pergunta):
            interpretada = self._reescrever(pergunta, historico)
        elif e_conversa(pergunta):
            return self._conversa()
        final = interpretada or pergunta
        fontes = self._fontes(self.pesquisar(final, doc_id=doc_id, categoria=categoria))
        r = self._responder(
            f"Responde à pergunta: {final}\n"
            "Começa pelo que responde mais directamente e usa no máximo 6 frases.", fontes)
        r["pergunta_interpretada"] = interpretada
        return r

    def _doc(self, doc_id: str) -> dict:
        self._exigir_indice()
        if doc_id not in self.indice.documentos:
            raise KeyError(f"Documento desconhecido: {doc_id}")
        return self.indice.documentos[doc_id]

    def _chunks_representativos(self, doc_id: str, consulta: str, n_inicio: int, k: int) -> list[dict]:
        inicio = self.indice.chunks_do_documento(doc_id)[:n_inicio]
        busca = self.pesquisar(consulta, k=k, doc_id=doc_id)
        juntos = {c["id"]: c for c in inicio + busca}
        return sorted(juntos.values(), key=lambda c: (c["pagina"], c["id"]))

    def resumir(self, doc_id: str) -> dict:
        doc = self._doc(doc_id)
        chunks = self._chunks_representativos(
            doc_id, "objective experimental setup conditions results conclusions", n_inicio=3, k=6)
        instrucao = (f"Resume o documento \"{doc['titulo']}\" em 5 a 8 frases: objectivo, instalação/ambiente "
                     "da experiência, condições (combustível, pressão, oxigénio, escoamento), principais "
                     "resultados e conclusões dos autores. Inclui apenas o que os trechos dizem.")
        return self._responder(instrucao, self._fontes(chunks))

    def comparar(self, doc_ids: list[str]) -> dict:
        if len(doc_ids) < 2:
            raise ValueError("Indica pelo menos dois doc_ids para comparar.")
        docs = [self._doc(d) for d in doc_ids]
        chunks: list[dict] = []
        for d in doc_ids:
            chunks += self._chunks_representativos(
                d, "fuel environment pressure oxygen concentration flow velocity results conclusions",
                n_inicio=1, k=4)
        nomes = "; ".join(f"\"{d['titulo']}\"" for d in docs)
        instrucao = (f"Compara as experiências destes documentos: {nomes}. Compara objectivo, combustível, "
                     "ambiente, condições (pressão, oxigénio, escoamento) e resultados. Cada frase deve "
                     "identificar a que experiência se refere. Se um aspecto só consta num documento, "
                     "menciona-o só para esse documento, sem especular sobre o outro.")
        return self._responder(instrucao, self._fontes(chunks))

    # -------------------------------------------------------------- extracção
    def _ler_extracoes(self) -> dict:
        if self._f_extracoes.exists():
            try:
                return json.loads(self._f_extracoes.read_text(encoding="utf-8"))
            except ValueError:
                return {}
        return {}

    def extracoes_em_cache(self) -> list[dict]:
        cache = self._ler_extracoes()
        return [v for k, v in cache.items()
                if k in self.indice.documentos and v.get("hash") == self.indice.documentos[k].get("hash")]

    def extrair(self, doc_id: str, forcar: bool = False) -> dict:
        doc = self._doc(doc_id)
        cache = self._ler_extracoes()
        if not forcar and cache.get(doc_id, {}).get("hash") == doc.get("hash"):
            return cache[doc_id]
        self._exigir_llm()

        juntos: dict[str, dict] = {}
        for _, consulta in CAMPOS_EXTRACAO.values():
            for c in self.pesquisar(consulta, k=3, doc_id=doc_id):
                juntos.setdefault(c["id"], c)
        fontes = self._fontes(sorted(juntos.values(), key=lambda c: (c["pagina"], c["id"]))[:14])
        por_tag = {f["tag"]: f for f in fontes}

        esquema = {campo: {"valor": f"<{descr}> ou null", "fonte": "<S1, S2...> ou null"}
                   for campo, (descr, _) in CAMPOS_EXTRACAO.items()}
        prompt = (f"TRECHOS:\n\n{_contexto(fontes)}\n\nExtrai do documento \"{doc['titulo']}\" os campos abaixo. "
                  "Em \"fonte\" indica a etiqueta do trecho onde o valor aparece.\n"
                  f"Formato:\n{json.dumps(esquema, ensure_ascii=False, indent=1)}")
        bruto = self.llm.generate_json(prompt, system=SISTEMA_EXTRAIR)
        if not isinstance(bruto, dict):
            raise LLMError("Extracção devolveu um formato inesperado.")

        campos = {}
        for campo in CAMPOS_EXTRACAO:
            item = bruto.get(campo) if isinstance(bruto.get(campo), dict) else {}
            valor = item.get("valor")
            valor = str(valor).strip() if valor not in (None, "", "null") else None
            categoria_invalida = False
            if campo == "resultado" and valor is not None:
                valor = normalizar_resultado(valor)
                categoria_invalida = valor is None
            m = re.search(r"S\s*(\d+)", str(item.get("fonte") or ""), re.I)
            tag = f"S{m.group(1)}" if m else None
            saida = {"valor": None, "pagina": None, "fonte": None, "trecho": None, "motivo": None}
            if categoria_invalida:
                saida["motivo"] = "Categoria inválida — descartado."
            elif valor is None:
                saida["motivo"] = "Não consta nos trechos."
            elif tag not in por_tag:
                saida["motivo"] = "Sem fonte válida — descartado."
            elif numeros_em_falta(valor, por_tag[tag]["text"]):
                saida["motivo"] = "Número não encontrado na fonte — descartado."
            else:
                f = por_tag[tag]
                saida.update(valor=valor, pagina=f["pagina"], fonte=tag, trecho=f["text"])
            if campo in CAMPOS_NUMERICOS:
                num, unid = _numero_e_unidade(saida["valor"]) if saida["valor"] else (None, None)
                saida["valor_numerico"], saida["unidade"] = num, unid
            campos[campo] = saida

        resultado = {"doc_id": doc_id, "titulo": doc["titulo"], "categoria": doc.get("categoria"),
                     "url": self._url(doc_id), "hash": doc.get("hash"), "campos": campos}
        cache[doc_id] = resultado
        self.s.index_dir.mkdir(parents=True, exist_ok=True)
        self._f_extracoes.write_text(
            json.dumps(cache, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        return resultado

    # -------------------------------------------------------------- conclusões
    def _assinatura_indice(self) -> str:
        """Muda sempre que um documento entra, sai ou é alterado."""
        hashes = sorted(f"{k}:{d.get('hash')}" for k, d in self.indice.documentos.items())
        return hashlib.sha256("|".join(hashes).encode()).hexdigest()[:16]

    def conclusoes_em_cache(self) -> list[dict]:
        """Conclusões já geradas para o índice actual (não chama o LLM)."""
        if not self._f_conclusoes.exists():
            return []
        try:
            cache = json.loads(self._f_conclusoes.read_text(encoding="utf-8"))
        except ValueError:
            return []
        if not isinstance(cache, dict) or cache.get("indice") != self._assinatura_indice():
            return []
        return cache.get("conclusoes", [])

    def gerar_conclusoes(self) -> list[dict]:
        """Responde às perguntas de TEMAS_CONCLUSOES e guarda só as respostas com fonte."""
        self._exigir_indice()
        self._exigir_llm()
        conclusoes = []
        for cid, titulo, pergunta in TEMAS_CONCLUSOES:
            r = self.perguntar(pergunta)
            citadas = {t for f in r["verificacao"]["frases"] for t in f["fontes"]}
            fontes = [f for f in r["fontes"] if f["tag"] in citadas]
            if r["resposta"] == NAO_ENCONTREI or not fontes:
                continue  # nenhuma conclusão sem fonte
            conclusoes.append({"id": cid, "titulo": titulo, "pergunta": pergunta, "resposta": r["resposta"],
                               "fontes": fontes, "verificacao": r["verificacao"]})
        self.s.index_dir.mkdir(parents=True, exist_ok=True)
        self._f_conclusoes.write_text(json.dumps(
            {"indice": self._assinatura_indice(), "conclusoes": conclusoes},
            ensure_ascii=False, indent=1), encoding="utf-8")
        return conclusoes
