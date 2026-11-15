"""Colector do NTRS (trabalho do Dev 1): procura relatórios de combustão em microgravidade,
descarrega os documentos e grava os metadados ao lado de cada um.

    python -m app.collect                 # até 40 documentos
    python -m app.collect --max 80
    python -m app.collect --so-metadados  # só lista, sem descarregar

Saída em data/docs/:
    <id>.pdf (ou <id>.txt)   documento
    <id>.json                metadados (titulo, ano, autores, combustivel, ambiente, url...)
e em data/: experiencias.json e experiencias.csv com a lista completa.

API pública do NTRS, sem chave. Limite: 500 pedidos por 15 minutos.
Crédito: Data provided by NASA Scientific and Technical Information Program.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
from pathlib import Path

import requests

from .config import get_settings
from .ingest import extrair_paginas, limpar_texto
from .rag import classificar_por_palavras

API = "https://ntrs.nasa.gov/api"
SITE = "https://ntrs.nasa.gov"
HEADERS = {"User-Agent": "chama-em-queda-livre/0.1 (projecto academico)"}

# (pesquisa, tema). O tema serve para equilibrar a recolha entre categorias quando
# o título e o resumo não chegam para o determinar.
QUERIES = [
    ("microgravity combustion", None),
    ("spacecraft fire safety", "Segurança contra incêndios em naves"),
    ("droplet combustion microgravity", "Gotas (droplets)"),
    ("flame spread microgravity solid fuel", "Combustíveis sólidos"),
    ("microgravity flammability materials", "Segurança contra incêndios em naves"),
    ("Burning and Suppression of Solids BASS", "Combustíveis sólidos"),
    ("Advanced Combustion via Microgravity Experiments ACME", "Chamas gasosas"),
    ("Flame Extinguishment Experiment FLEX", "Gotas (droplets)"),
    ("Saffire spacecraft fire experiment", "Segurança contra incêndios em naves"),
    ("smoldering combustion microgravity", "Combustíveis sólidos"),
    ("gas jet diffusion flame microgravity", "Chamas gasosas"),
    ("laminar soot processes microgravity flame", "Chamas gasosas"),
    ("premixed flame microgravity", "Chamas gasosas"),
    ("spherical diffusion flame microgravity", "Chamas gasosas"),
    ("supercritical water oxidation microgravity", "Fluidos reactivos supercríticos"),
    ("supercritical water mixture experiment space station", "Fluidos reactivos supercríticos"),
    ("supercritical fluid combustion microgravity", "Fluidos reactivos supercríticos"),
]

FIRE_WORDS = ["combustion", "flame", "fire", "flammab", "burning", "ignition", "smolder", "soot", "oxidation"]
SPACE_WORDS = [
    "microgravity", "low gravity", "low-gravity", "reduced gravity", "reduced-gravity", "zero gravity",
    "zero-g", "weightless", "space station", "spacecraft", "drop tower", "space shuttle",
]

# Etiquetas por palavras-chave no título e no resumo. São pistas para filtros,
# não substituem a extracção feita a partir do texto completo.
FUELS = {
    "heptano": ["heptane"], "decano": ["decane"], "dodecano": ["dodecane"], "metanol": ["methanol"],
    "etanol": ["ethanol"], "metano": ["methane"], "etileno": ["ethylene"], "propano": ["propane"],
    "hidrogénio": ["hydrogen"], "PMMA (acrílico)": ["pmma", "acrylic", "polymethyl"],
    "celulose / papel / algodão": ["cellulos", "paper", "cotton"], "polietileno": ["polyethylene"],
    "espuma de poliuretano": ["polyurethane"], "querosene / jet fuel": ["kerosene", "jet fuel", "jp-8"],
}
ENVIRONMENTS = {
    "ISS": ["international space station", " iss "],
    "Space Shuttle": ["space shuttle", "spacelab", "sts-"],
    "Torre de queda": ["drop tower", "drop-tower", "zero gravity facility", "drop facility"],
    "Voo parabólico": ["parabolic", "kc-135", "reduced-gravity aircraft", "low-gravity aircraft"],
    "Foguete de sondagem": ["sounding rocket"],
    "Cygnus (Saffire)": ["cygnus", "saffire"],
}


def _get(url: str, **kwargs) -> requests.Response:
    time.sleep(2.0)  # bem abaixo do limite de 500 pedidos / 15 min
    return requests.get(url, headers=HEADERS, timeout=120, **kwargs)


def search(query: str, size: int = 100) -> list[dict]:
    """Uma página de resultados com documento disponível."""
    params = {"q": query, "page.size": size, "disseminated": "DOCUMENT_AND_METADATA"}
    response = _get(f"{API}/citations/search", params=params)
    if response.status_code != 200:  # a documentação também descreve a pesquisa por POST
        time.sleep(2.0)
        response = requests.post(
            f"{API}/citations/search",
            headers=HEADERS,
            json={"q": query, "page": {"size": size, "from": 0}, "disseminated": "DOCUMENT_AND_METADATA"},
            timeout=120,
        )
    response.raise_for_status()
    return response.json().get("results", [])


def is_relevant(record: dict) -> bool:
    text = f" {record.get('title', '')} {record.get('abstract', '')} ".lower()
    return any(w in text for w in FIRE_WORDS) and any(w in text for w in SPACE_WORDS)


# ------------------------------------------------------------------ pontuação

# Experiências concretas: (sigla, sensível a maiúsculas; nome por extenso, insensível).
EXPERIMENTS = {
    "BASS": (r"\bBASS\b", r"burning and suppression of solids"),
    "ACME": (r"\bACME\b", r"advanced combustion via microgravity experiments"),
    "FLEX": (r"\bFLEX\b", r"flame extinguishment experiment"),
    "Saffire": (r"\b(Saffire|SAFFIRE)\b", r"spacecraft fire experiment"),
    "CIR": (r"\bCIR\b", r"combustion integrated rack"),
    "MSG": (r"\bMSG\b", r"microgravity science glovebox"),
    "DCE": (r"\bDCE\b", r"droplet combustion experiment"),
    "SIBAL": (r"\bSIBAL\b", r"solid inflammability boundary at low.speed"),
    "SoFIE": (r"\b(SoFIE|SOFIE)\b", r"solid fuel ignition and extinction"),
    "Flammability": (r"(?i:\bflammability\b)", None),
    # chamas gasosas
    "CLD Flame": (r"\bCLD Flame\b", r"coflow laminar diffusion flame"),
    "Flame Design": (r"\bFlame Design\b", None),
    "s-Flame": (r"\bs-Flame\b", r"spherical diffusion flames?"),
    "E-FIELD Flames": (r"\bE-FIELD\b", r"electric.field effects on laminar diffusion flames"),
    "BRE": (r"\bBRE\b", r"burning rate emulator"),
    "SLICE": (r"\bSLICE\b", r"structure and liftoff in combustion experiment"),
    "SPICE": (r"\bSPICE\b", r"smoke point in co.?flow experiment"),
    "LSP": (r"\bLSP\b", r"laminar soot processes"),
    "ELF": (r"\bELF\b", r"enclosed laminar flames?"),
    # fluidos supercríticos
    "SCWO": (r"\bSCWO\b", r"supercritical water oxidation"),
    "SCWM": (r"\bSCWM\b", r"supercritical water mixture"),
    "DECLIC": (r"\bDECLIC\b", None),
}
RESULT_TERMS = ["flame spread rate", "extinction", "burning rate", "oxygen concentration", "limiting oxygen"]
# Títulos de documentos de programa/estratégia (não são experiências).
TITLE_PENALTIES = {
    "overview": r"\boverviews?\b", "program": r"\bprogram(s|me|mes)?\b", "strategy": r"\bstrateg(y|ies|ic)\b",
    "plan": r"\bplan(s|ning)?\b", "workshop": r"\bworkshops?\b", "proceedings": r"\bproceedings\b",
    "bibliography": r"\bbibliograph(y|ies)\b", "annual report": r"\bannual report\b",
}
MIN_SCORE = 2.0      # abaixo disto o registo é excluído
YEAR_PREFERRED = 2000
MIN_CHARS = 1500     # caracteres úteis (letras e algarismos) no documento inteiro
MIN_WORD_RATIO = 0.5  # fracção mínima de "palavras" reais para o texto contar como legível


def _mentions(patterns: tuple[str, str | None], text: str) -> bool:
    acronym, name = patterns
    return bool(re.search(acronym, text) or (name and re.search(name, text, re.I)))


def score(record: dict) -> tuple[float, list[str]]:
    """Pontuação de um registo e os motivos (para o resumo final).

    +3 por experiência concreta no título, +2 se só no resumo (máx. 6);
    +2 por termo de resultados (máx. 6); -4 por termo de programa/estratégia no título;
    +1 se for de 2000 em diante, -1 se for anterior (os antigos só passam se forem
    claramente experiências).
    """
    title = record.get("title") or ""
    abstract = record.get("abstract") or ""
    reasons: list[str] = []

    experiments = 0.0
    for name, patterns in EXPERIMENTS.items():
        if _mentions(patterns, title):
            experiments += 3
            reasons.append(f"+3 {name} (título)")
        elif _mentions(patterns, abstract):
            experiments += 2
            reasons.append(f"+2 {name} (resumo)")
    results = 0.0
    text = f"{title} {abstract}".lower()
    for term in RESULT_TERMS:
        if term in text:
            results += 2
            reasons.append(f"+2 {term}")
    total = min(experiments, 6) + min(results, 6)

    for name, pattern in TITLE_PENALTIES.items():
        if re.search(pattern, title, re.I):
            total -= 4
            reasons.append(f"-4 título: {name}")

    year = _year(record)
    if year is not None:
        if year >= YEAR_PREFERRED:
            total += 1
            reasons.append(f"+1 ano {year}")
        else:
            total -= 1
            reasons.append(f"-1 ano {year}")
    return total, reasons


def exclusion_reason(reasons: list[str]) -> str:
    """Motivo resumido para um registo abaixo do limiar."""
    penalties = [r.split(": ", 1)[1] for r in reasons if r.startswith("-4")]
    if penalties:
        return f"título de programa/estratégia ({', '.join(penalties)})"
    if not any(r.startswith(("+3", "+2")) for r in reasons):
        return "sem menção a experiências concretas nem a termos de resultados"
    return f"sinais insuficientes para um documento anterior a {YEAR_PREFERRED}"


def _title_key(record: dict) -> str:
    """Título normalizado, para detectar o mesmo trabalho com ids diferentes."""
    return re.sub(r"[^a-z0-9]+", " ", (record.get("title") or "").lower()).strip()


def topic(record: dict, query_topic: str | None = None) -> str:
    """Tema provável: palavras-chave do título e do resumo; senão, o tema da pesquisa."""
    guess = classificar_por_palavras(f"{record.get('title', '')} {record.get('abstract', '')}")
    return guess if guess != "Outro" else (query_topic or "Outro")


def balanced_order(candidates: list[tuple]) -> list[tuple]:
    """Ordena por rondas: em cada ronda entra o melhor candidato de cada tema, e dentro
    da ronda vale a pontuação. Assim nenhum tema ocupa a recolha toda. Os candidatos
    sem tema ("Outro") só entram depois de esgotados os restantes."""
    queues: dict[str, list[tuple]] = {}
    for candidate in candidates:  # já vêm ordenados por pontuação
        queues.setdefault(candidate[-1], []).append(candidate)
    others = queues.pop("Outro", [])
    ordered: list[tuple] = []
    while any(queues.values()):
        heads = [queue.pop(0) for queue in queues.values() if queue]
        ordered += sorted(heads, key=lambda c: (-c[0], -c[1], c[2]))
    return ordered + others


# ------------------------------------------------------------------ qualidade do texto

def text_quality(path: Path) -> dict:
    """Extrai o texto e mede-o: páginas, caracteres úteis e se é legível."""
    try:
        pages = extrair_paginas(path)
        text = " ".join(limpar_texto(t) for _, t in pages)
    except Exception as exc:  # PDF corrompido ou cifrado
        return {"paginas": None, "caracteres_texto": 0, "legivel": False, "motivo": f"erro a ler: {exc.__class__.__name__}"}
    useful = sum(c.isalnum() for c in text)
    tokens = text.split()
    words = sum(1 for t in tokens if re.fullmatch(r"[^\W\d_]{2,25}", t.strip(".,;:()[]\"'-")))
    ratio = words / len(tokens) if tokens else 0.0
    info = {"paginas": len(pages) if path.suffix.lower() == ".pdf" else None,
            "caracteres_texto": useful, "legivel": True, "motivo": None}
    if useful < MIN_CHARS:
        info.update(legivel=False, motivo=f"só {useful} caracteres úteis (mínimo {MIN_CHARS})")
    elif ratio < MIN_WORD_RATIO:
        info.update(legivel=False, motivo=f"texto ilegível ({ratio:.0%} de palavras reais)")
    return info


def _tags(text: str, table: dict[str, list[str]]) -> list[str]:
    text = f" {text.lower()} "
    return [label for label, words in table.items() if any(word in text for word in words)]


def _authors(record: dict) -> list[str]:
    names = []
    for item in record.get("authorAffiliations") or []:
        author = (item.get("meta") or {}).get("author") or item.get("author") or {}
        if author.get("name"):
            names.append(author["name"])
    return names


def _year(record: dict) -> int | None:
    candidates = [p.get("publicationDate") for p in record.get("publications") or []]
    candidates += [record.get("distributionDate"), record.get("created")]
    for value in candidates:
        match = re.match(r"(19|20)\d{2}", str(value or ""))
        if match:
            return int(match.group(0))
    return None


def _links(record: dict) -> dict:
    for item in record.get("downloads") or []:
        links = item.get("links") or {}
        if links.get("pdf") or links.get("fulltext") or links.get("original"):
            return links
    return {}


def to_metadata(record: dict) -> dict:
    text = f"{record.get('title', '')} {record.get('abstract', '')}"
    record_id = str(record.get("id"))
    return {
        "id": record_id,
        "titulo": (record.get("title") or "").strip(),
        "ano": _year(record),
        "autores": _authors(record),
        "centro": (record.get("center") or {}).get("name"),
        "tipo": record.get("stiType"),
        "resumo": (record.get("abstract") or "").strip(),
        "combustivel": _tags(text, FUELS),
        "ambiente": _tags(text, ENVIRONMENTS),
        "url": f"{SITE}/citations/{record_id}",
        "fonte": "NASA Technical Reports Server (NTRS)",
    }


def _fetch(url: str, max_mb: float) -> bytes | None:
    try:
        response = _get(url, stream=True)
        if response.status_code != 200:
            return None
        data = bytearray()
        for block in response.iter_content(1 << 16):
            data += block
            if len(data) > max_mb * 1024 * 1024:
                return None
        return bytes(data)
    except requests.RequestException:
        return None


def download(record: dict, folder: Path, max_mb: float) -> tuple[Path | None, dict]:
    """Prefere o PDF (permite citar a página). Se o PDF não tiver texto suficiente ou
    legível, tenta a versão fulltext .txt. Devolve (caminho, qualidade) ou (None, {"motivo"})."""
    links = _links(record)
    record_id = str(record.get("id"))
    problems: list[str] = []
    for key, suffix in (("pdf", ".pdf"), ("fulltext", ".txt")):
        link = links.get(key)
        if not link:
            continue
        data = _fetch(link if link.startswith("http") else SITE + link, max_mb)
        if not data or (suffix == ".pdf" and not data.startswith(b"%PDF")):
            problems.append(f"{suffix[1:]}: download falhou ou acima de {max_mb:g} MB")
            continue
        path = folder / f"{record_id}{suffix}"
        path.write_bytes(data)
        quality = text_quality(path)
        if quality["legivel"]:
            return path, quality
        path.unlink()
        problems.append(f"{suffix[1:]}: {quality['motivo']}")
    return None, {"motivo": "; ".join(problems) or "sem ligação pdf/fulltext"}


CSV_COLUMNS = ["id", "titulo", "ano", "tipo", "centro", "combustivel", "ambiente", "url", "ficheiro",
               "pontuacao", "paginas", "caracteres_texto", "tema"]


def collect(max_docs: int = 40, max_mb: float = 25, only_metadata: bool = False, folder: Path | None = None) -> list[dict]:
    folder = Path(folder or get_settings().docs_dir)
    folder.mkdir(parents=True, exist_ok=True)

    found: dict[str, dict] = {}
    query_topics: dict[str, str] = {}
    for query, query_topic in QUERIES:
        try:
            results = search(query)
        except requests.RequestException as exc:
            print(f"[aviso] pesquisa '{query}' falhou: {exc}")
            continue
        for record in results:
            found.setdefault(str(record["id"]), record)
            if query_topic:
                query_topics.setdefault(str(record["id"]), query_topic)
        print(f"{query}: {len(results)} resultados")

    # Filtra e pontua. `excluded` guarda (id, título, motivo) para o resumo final.
    excluded: list[tuple[str, str, str]] = []
    candidates: list[tuple] = []  # (pontuação, ano, id, registo, tema)
    for record_id, record in found.items():
        title = (record.get("title") or "").strip()
        if not is_relevant(record):
            excluded.append((record_id, title, "fora do tema (sem termos de fogo e de espaço/microgravidade)"))
        elif not _links(record):
            excluded.append((record_id, title, "sem documento descarregável"))
        else:
            points, reasons = score(record)
            if points < MIN_SCORE:
                excluded.append((record_id, title, f"pontuação abaixo de {MIN_SCORE:g}: {exclusion_reason(reasons)}"))
            else:
                candidates.append((points, _year(record) or 0, record_id, record,
                                   topic(record, query_topics.get(record_id))))
    # pontuação; em empate, artigos antes de apresentações, depois os mais recentes
    candidates.sort(key=lambda c: (-c[0], c[3].get("stiType") == "PRESENTATION", -c[1], c[2]))

    # O NTRS tem por vezes dois registos do mesmo trabalho (artigo e apresentação): fica o primeiro.
    by_title: dict[str, str] = {}
    unique: list[tuple] = []
    for candidate in candidates:
        key = _title_key(candidate[3])
        if key in by_title:
            excluded.append((candidate[2], (candidate[3].get("title") or "").strip(),
                             "duplicado (mesmo título que outro registo)"))
        else:
            by_title[key] = candidate[2]
            unique.append(candidate)
    candidates = balanced_order(unique)
    print(f"\n{len(found)} registos únicos, {len(candidates)} acima do limiar ({MIN_SCORE:g}) e sem duplicados")

    rows: list[dict] = []
    for points, _, record_id, record, record_topic in candidates:
        if len(rows) >= max_docs:
            break
        meta = to_metadata(record)
        meta["pontuacao"] = points
        meta["tema"] = record_topic
        existing = [p for p in (folder / f"{record_id}.pdf", folder / f"{record_id}.txt") if p.exists()]
        if only_metadata:
            meta.update(ficheiro=None, paginas=None, caracteres_texto=None)
        else:
            if existing:
                path, quality = existing[0], text_quality(existing[0])
                if not quality["legivel"]:
                    path = None
            else:
                path, quality = download(record, folder, max_mb)
            if path is None:
                excluded.append((record_id, meta["titulo"], f"texto rejeitado ou download falhou: {quality['motivo']}"))
                print(f"[aviso] {record_id}: {quality['motivo']}")
                continue
            meta.update(ficheiro=path.name, paginas=quality["paginas"], caracteres_texto=quality["caracteres_texto"])
            print(f"ok {path.name}  [{points:g}]  {meta['titulo'][:70]}")
            (folder / f"{record_id}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        rows.append(meta)

    base = folder.parent
    (base / "experiencias.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(base / "experiencias.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_COLUMNS)
        for m in rows:
            writer.writerow(["; ".join(m[c]) if isinstance(m[c], list) else m[c] for c in CSV_COLUMNS])

    print(f"\n{len(rows)} documentos em {folder} | lista em {base / 'experiencias.csv'}")
    not_reached = len(candidates) - len(rows) - sum(1 for e in excluded if e[2].startswith("texto rejeitado"))
    if not_reached > 0:
        print(f"{not_reached} candidatos acima do limiar ficaram de fora por causa do --max {max_docs}")
    themes: dict[str, int] = {}
    for m in rows:
        themes[m["tema"]] = themes.get(m["tema"], 0) + 1
    print("Por tema: " + "; ".join(f"{name}: {n}" for name, n in sorted(themes.items(), key=lambda i: -i[1])))
    print(f"Excluídos: {len(excluded)}")
    counts: dict[str, int] = {}
    for _, _, reason in excluded:
        key = reason.split(":")[0] if reason.startswith("texto rejeitado") else reason
        counts[key] = counts.get(key, 0) + 1
    for reason, n in sorted(counts.items(), key=lambda item: -item[1]):
        print(f"  {n:>4}  {reason}")
    for record_id, title, reason in excluded:
        if reason.startswith("texto rejeitado"):
            print(f"        {record_id}  {title[:60]}  → {reason.split(': ', 1)[1]}")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Colector de documentos do NTRS")
    parser.add_argument("--max", type=int, default=40, help="número máximo de documentos")
    parser.add_argument("--max-mb", type=float, default=25, help="tamanho máximo por ficheiro")
    parser.add_argument("--so-metadados", action="store_true", help="não descarrega os documentos")
    args = parser.parse_args()
    collect(args.max, args.max_mb, args.so_metadados)
