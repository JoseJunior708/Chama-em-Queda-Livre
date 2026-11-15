# Módulo de IA: Chama em Queda Livre

Serviço Python que indexa documentos científicos da NASA (NTRS, PSI) sobre combustão em
microgravidade e segurança contra incêndios no espaço. Com ele é possível:

- pesquisar nos documentos;
- classificar cada documento por tipo de experiência;
- resumir um documento e comparar experiências;
- responder a perguntas;
- extrair dados estruturados para os gráficos.

**Regra central: nenhuma afirmação sem fonte.** O LLM só vê os trechos recuperados. Cada frase
da resposta tem de citar um trecho, e a resposta é verificada frase a frase antes de ser devolvida.

## Instalação

Requer Python 3.11 ou superior.

```bash
cd Backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # e preenche GEMINI_API_KEY
```

| Variável | Valor por omissão | Descrição |
|---|---|---|
| `GEMINI_API_KEY` | — | Chave do Google AI Studio. **Nunca a escrevas no código nem a envies para o Git.** O `.env` está no `.gitignore`. |
| `GEMINI_MODEL` | `gemini-3.6-flash` | Modelo de geração. |
| `GEMINI_EMBED_MODEL` | `gemini-embedding-2` | Modelo de embeddings, multilingue: aceita perguntas em PT sobre documentos em EN. |
| `GEMINI_EMBED_DIM` | `768` | Dimensão dos vectores. |
| `TOP_K` | `8` | Número de trechos enviados ao LLM. |
| `PESO_VETORIAL` | `0.65` | Peso dos embeddings na busca híbrida (o resto vai para o BM25). |
| `VERIFY_JUDGE` | `true` | Activa o LLM-juiz na verificação. |

Sem chave, o serviço continua a funcionar em modo reduzido: a busca usa só BM25 e a
classificação usa palavras-chave. As rotas `/ask`, `/summarize`, `/compare` e `/extract`
devolvem 503.

## Documentos

O colector (`app/collect.py`) pesquisa a API pública do NTRS, descarrega os PDFs para
`data/docs/` e grava um `<id>.json` de metadados ao lado de cada um:

```bash
python -m app.collect --so-metadados --max 5   # só lista, sem descarregar
python -m app.collect --max 40                 # descarrega até 40 documentos
python -m app.cli index                        # reindexa
```

O colector escolhe os documentos assim:

- **Pontuação:** cada registo recebe pontos e os mais pontuados são descarregados primeiro.
  - +3 por experiência concreta no título (BASS, ACME, FLEX, Saffire, CIR, MSG, DCE, SIBAL, SoFIE,
    Flammability), +2 se só aparecer no resumo (máximo 6).
  - +2 por termo de resultados: flame spread rate, extinction, burning rate, oxygen concentration,
    limiting oxygen (máximo 6).
  - −4 por cada termo de programa no título: overview, program, strategy, plan, workshop,
    proceedings, bibliography, annual report.
  - +1 se for de 2000 em diante, −1 se for anterior.
- **Limiar:** registos com menos de 2 pontos são excluídos. Um documento anterior a 2000 só passa
  se tiver sinais claros de experiência.
- **Qualidade do texto:** depois de descarregar o PDF, o texto é extraído. Se tiver menos de 1500
  caracteres úteis ou for maioritariamente ilegível, o PDF é rejeitado e tenta-se a versão `.txt`.
- **Duplicados:** o NTRS tem por vezes dois registos do mesmo trabalho (artigo e apresentação).
  Fica só um por título, com preferência pelo artigo.
- **Equilíbrio por tema:** cada candidato recebe um tema (pelas palavras-chave do título e do
  resumo ou, na falta delas, pela pesquisa que o encontrou). A selecção faz-se por rondas, com o
  melhor candidato de cada tema em cada ronda, para que nenhum tema ocupe a recolha toda.
- **Resumo final:** o colector mostra quantos documentos ficaram por tema e quantos registos
  foram excluídos e porquê.
- **Lista:** `data/experiencias.csv` inclui as colunas `pontuacao`, `paginas` e `caracteres_texto`.

Também podes colocar PDFs ou `.txt` à mão em `data/docs/`. Os metadados são opcionais e vão num
ficheiro `<nome>.json` ao lado do documento:

```
data/docs/20110012345.pdf
data/docs/20110012345.json   → {"titulo": "...", "ano": 2014, "autores": ["..."],
                                "combustivel": ["heptano"], "ambiente": ["ISS"],
                                "url": "https://ntrs.nasa.gov/citations/20110012345"}
```

- `combustivel` e `ambiente` são listas de etiquetas tiradas do título e do resumo. Servem para
  filtros; os valores para gráficos vêm de `/extract/{doc_id}`.
- O `url` é usado como link das citações.
- Os PDFs descarregados e as listas `data/experiencias.*` não vão para o Git.

- O `doc_id` é o nome do ficheiro sem extensão, em minúsculas.
- Se o `.json` tiver `"categoria"` com uma categoria válida, ela é usada directamente.
- Os PDFs sem texto extraível (digitalizados) são ignorados, com um aviso.

## Uso

### CLI

```bash
python -m app.cli index                    # (re)indexa data/docs
python -m app.cli docs                     # lista documentos e categorias
python -m app.cli search "fuligem em chamas de difusão" -k 5
python -m app.cli ask "Qual a constante da taxa de queima das gotas de heptano?"
python -m app.cli summarize <doc_id>
python -m app.cli compare <doc_id> <doc_id>
python -m app.cli extract <doc_id>         # JSON para os gráficos
python -m app.cli eval --pausa 5           # 15 perguntas de tests/perguntas.json → % de respostas fiáveis
```

### API

```bash
uvicorn app.api:app --reload --port 8000
# documentação interactiva em http://localhost:8000/docs
```

O CORS está aberto a todas as origens.

| Método | Rota | Corpo / parâmetros |
|---|---|---|
| GET | `/health` | — |
| GET | `/documents` | — |
| GET | `/categories` | — |
| GET | `/search` | `q`, `k` (1–50), `categoria?`, `doc_id?` |
| POST | `/ask` | `{"pergunta": str, "categoria"?: str, "doc_id"?: str}` |
| POST | `/summarize` | `{"doc_id": str}` |
| POST | `/compare` | `{"doc_ids": [str, str, ...]}` |
| GET | `/extract/{doc_id}` | `forcar?=true` para recalcular |
| GET | `/extractions` | todas as extracções já calculadas (não chama o LLM) |
| GET | `/conclusions` | conclusões já geradas para o índice actual (não chama o LLM) |
| POST | `/conclusions` | gera e guarda as conclusões (uma pergunta ao LLM por tema) |
| POST | `/reindex` | — |

**Erros:** 404 (documento desconhecido), 409 (índice vazio: chamar `/reindex`),
400/422 (pedido inválido), 503 (LLM indisponível ou quota esgotada). O corpo é sempre
`{"detail": "mensagem"}`.

## Formato das respostas (para o Dev 3)

As rotas `/ask`, `/summarize` e `/compare` devolvem:

```json
{
  "resposta": "A constante da taxa de queima foi 0.65 mm2/s [S1]. As gotas tinham 2.5 mm de diâmetro inicial [S1].",
  "fontes": [
    {"tag": "S1", "doc_id": "20110012345", "titulo": "FLEX-2 ...", "pagina": 4, "text": "trecho original em inglês...",
     "url": "https://ntrs.nasa.gov/citations/20110012345"}
  ],
  "verificacao": {
    "fiavel": true,
    "frases": [
      {"i": 1, "frase": "A constante da taxa de queima foi 0.65 mm2/s [S1].", "fontes": ["S1"], "estado": "apoiada", "motivo": "..."}
    ]
  }
}
```

- **`fontes`**: todos os trechos enviados ao LLM. As etiquetas `[S1]`, `[S2]`... no texto da
  resposta apontam para o `tag`.
- **`fontes[].url`**: link da citação. É o campo `url` dos metadados do documento (a página do
  documento no NTRS). É `null` se o documento não tiver `url` nos metadados. O mesmo campo `url`
  aparece em `/search`, `/documents` e `/extract/{doc_id}`.
- **`verificacao.frases[].estado`** pode ter um destes valores:
  - `apoiada`: tem citação válida, os números existem no trecho e o juiz confirmou o apoio.
  - `sem_citacao`: a frase não tem citação, ou cita um `[Sn]` que não existe.
  - `numero_nao_encontrado`: há um número na frase que não está no trecho citado.
  - `nao_apoiada`: o juiz considerou que o trecho não apoia a frase (ou o juiz não respondeu).
- **`verificacao.fiavel`** só é `true` quando todas as frases estão `apoiada`. Sugestão: mostrar um
  aviso quando é `false` e destacar as frases com problemas.
- Se as fontes não respondem, a resposta é exactamente
  `"Não encontrei essa informação nos documentos."`, com `frases: []` e `fiavel: true`.

### `/search`

```json
{"q": "...", "resultados": [{"id": "doc:p4:c1", "doc_id": "...", "titulo": "...", "pagina": 4, "text": "...",
                             "score": 0.91, "score_vetorial": 0.95, "score_bm25": 0.83}]}
```

### `/documents`

```json
[{"doc_id": "...", "titulo": "...", "ficheiro": "x.pdf", "paginas": 12, "chunks": 30,
  "categoria": "Gotas (droplets)", "categoria_origem": "llm", "metadados": {...}}]
```

`categoria_origem` indica de onde veio a categoria: `metadados`, `llm` ou `palavras-chave`.

As categorias possíveis são:
- Segurança contra incêndios em naves
- Gotas (droplets)
- Chamas gasosas
- Combustíveis sólidos
- Fluidos reactivos supercríticos
- Outro

### `/conclusions`

```json
[{"id": "C1", "titulo": "Limite de oxigénio para a propagação de chama", "pergunta": "...",
  "resposta": "... [S1].", "fontes": [...], "verificacao": {...}}]
```

- Cada conclusão é a resposta verificada a uma pergunta fixa (`TEMAS_CONCLUSOES` em `app/rag.py`),
  com a mesma forma de `/ask` mais `id`, `titulo` e `pergunta`.
- `fontes` traz só os trechos citados na resposta. Uma resposta sem citações não é guardada.
- `POST /conclusions` gera e guarda (chama o LLM); `GET /conclusions` só lê. As conclusões guardadas
  deixam de ser devolvidas quando o índice muda, até serem geradas de novo.

### `/extract/{doc_id}` (dados para gráficos)

```json
{
  "doc_id": "...", "titulo": "...", "categoria": "Combustíveis sólidos", "hash": "...",
  "campos": {
    "combustivel":           {"valor": "PMMA", "pagina": 3, "fonte": "S2", "trecho": "...", "motivo": null},
    "ambiente":              {"valor": "International Space Station", "pagina": 2, ...},
    "pressao":               {"valor": "1 atm", "valor_numerico": 1.0, "unidade": "atm", "pagina": 5, ...},
    "concentracao_o2":       {"valor": "21%", "valor_numerico": 21.0, "unidade": "%", ...},
    "velocidade_escoamento": {"valor": null, "valor_numerico": null, "unidade": null, "pagina": null,
                              "motivo": "Não consta nos trechos."},
    "resultado_principal":   {"valor": "...", "pagina": 9, ...},
    "resultado":             {"valor": "propagou", "pagina": 9, ...}
  }
}
```

- `resultado` é uma categoria fechada: `"propagou"` ou `"extinguiu"`. Qualquer outro valor é
  descartado (`valor: null`). Extracções em cache anteriores a este campo não o têm; usa
  `forcar=true` para as recalcular.
- `valor` é `null` quando o campo não consta no documento, ou quando o valor proposto pelo LLM não
  tem fonte válida ou o número não aparece na fonte. Nesses casos o `motivo` explica porquê.
- Os campos `pressao`, `concentracao_o2` e `velocidade_escoamento` trazem também `valor_numerico`
  e `unidade`, prontos para os gráficos. As unidades vêm tal como na fonte (não são convertidas).
- A extracção fica em cache e só é recalculada se o PDF mudar.

## Como funciona

1. **Ingestão** (`app/ingest.py`):
   - extrai o texto página a página com `pypdf`;
   - corrige a hifenização e as quebras de linha;
   - corta em chunks de cerca de 1200 caracteres, sem partir frases, com 200 caracteres de
     sobreposição (feita por frases inteiras);
   - cada chunk guarda `doc_id`, página e texto.
2. **Busca** (`app/search.py`):
   - combina o cosseno sobre embeddings do Gemini (guardados em `data/index/vetores.npy`) com o BM25;
   - o BM25 usa um glossário PT→EN para que perguntas em português também encontrem termos em inglês;
   - aceita filtros por `doc_id`, categoria e metadados;
   - os embeddings ficam numa cache em disco e nunca são recalculados para o mesmo texto.
3. **LLM** (`app/llm.py`):
   - usa HTTP directo para os endpoints `generateContent` e `batchEmbedContents`, com a chave no
     cabeçalho `x-goog-api-key`;
   - os embeddings são pedidos em lotes;
   - em 429/5xx, repete o pedido com espera exponencial, respeitando o `retryDelay` da API;
   - as respostas com `temperature=0` ficam em cache.
4. **Classificação** (`app/rag.py`): pede ao LLM uma saída JSON com uma das 6 categorias. Se o LLM
   falhar ou devolver uma categoria inválida, usa palavras-chave com pesos.
5. **RAG** (`app/rag.py`): o prompt contém apenas os trechos `[S1]..[Sn]` e regras estritas:
   - citar no fim de cada frase;
   - copiar números e unidades tal como estão;
   - não usar conhecimento externo;
   - quando não há resposta, usar a frase fixa.
6. **Verificação** (`app/verify.py`): para cada frase confirma (a) a citação, (b) os números
   (aceita vírgula ou ponto decimal e ignora fórmulas como O2 e CO2) e (c) o apoio, com o LLM-juiz.
   Para poupar quota, o juiz avalia todas as frases de uma resposta numa única chamada.

**Custo por pergunta:** 1 embedding (que fica em cache), 1 geração e 1 chamada ao juiz. Se a quota
do plano gratuito esgotar, usa `eval --pausa 5`.

## Testes

```bash
pytest -q
```

Os testes correm sem internet e sem chave, porque o LLM e os embeddings são simulados
(`tests/conftest.py`). Cobrem:

- a ingestão (incluindo um PDF sem texto);
- a busca com filtros;
- a cache de embeddings;
- as novas tentativas em 429/503;
- a classificação por palavras-chave;
- o verificador (número errado, frase sem citação, citação inexistente, juiz);
- a API e a CLI.

A avaliação real, com a API e documentos verdadeiros, faz-se com `python -m app.cli eval`.

## Estrutura

```
Backend/
├── app/
│   ├── config.py   # configuração (.env), categorias, frase "não encontrei"
│   ├── collect.py  # colector do NTRS: descarrega PDFs e metadados para data/docs
│   ├── ingest.py   # PDFs/.txt → chunks com página
│   ├── search.py   # BM25 + embeddings, filtros, índice e cache em disco
│   ├── llm.py      # cliente HTTP do Gemini (geração + embeddings, novas tentativas, cache)
│   ├── rag.py      # Motor: indexar, classificar, perguntar, resumir, comparar, extrair
│   ├── verify.py   # verificação anti-invenção por frase
│   ├── api.py      # FastAPI
│   └── cli.py      # linha de comandos
├── data/docs/      # documentos (o índice é gerado em data/index/, fora do Git)
├── tests/          # pytest + perguntas.json
├── requirements.txt
└── .env.example
```
