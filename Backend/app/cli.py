"""Linha de comandos.

  python -m app.cli index
  python -m app.cli docs
  python -m app.cli search "texto" [-k 5] [--categoria ...] [--doc-id ...]
  python -m app.cli ask "pergunta" [--categoria ...] [--doc-id ...]
  python -m app.cli summarize <doc_id>
  python -m app.cli compare <id> <id> [...]
  python -m app.cli extract <doc_id> [--forcar]
  python -m app.cli eval [--ficheiro tests/perguntas.json] [--pausa 0]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import textwrap
import time
from pathlib import Path

from .config import BASE_DIR, NAO_ENCONTREI
from .llm import LLMError
from .rag import Motor

ICONES = {"apoiada": "✔", "sem_citacao": "✘ sem citação", "numero_nao_encontrado": "✘ número",
          "nao_apoiada": "✘ não apoiada"}


def _imprimir_resposta(r: dict) -> None:
    print("\n" + textwrap.fill(r["resposta"], 100) + "\n")
    v = r["verificacao"]
    print(f"Fiável: {'SIM' if v['fiavel'] else 'NÃO'}")
    for f in v["frases"]:
        print(f"  [{ICONES.get(f['estado'], f['estado'])}] {f['frase'][:90]}")
        if f["estado"] != "apoiada":
            print(f"      motivo: {f['motivo']}")
    if r["fontes"]:
        print("\nFontes:")
        for s in r["fontes"]:
            print(f"  [{s['tag']}] {s['titulo']} — p. {s['pagina']}" + (f"  {s['url']}" if s.get("url") else ""))


def cmd_index(m: Motor, a) -> None:
    r = m.indexar()
    print(f"Indexados {r['documentos']} documentos, {r['chunks']} chunks "
          f"({'com' if r['embeddings'] else 'sem'} embeddings).")
    for aviso in r["avisos"]:
        print(f"  aviso: {aviso}")


def cmd_docs(m: Motor, a) -> None:
    docs = m.documentos()
    if not docs:
        print("Nenhum documento indexado. Corre: python -m app.cli index")
    for d in docs:
        print(f"{d['doc_id']:<30} {d['categoria'] or '-':<38} {d['paginas']:>3} p.  {d['titulo']}")


def cmd_search(m: Motor, a) -> None:
    for r in m.pesquisar(a.consulta, k=a.k, doc_id=a.doc_id, categoria=a.categoria):
        print(f"{r['score']:.3f}  {r['doc_id']} p.{r['pagina']}: {r['text'][:120]}…")


def cmd_ask(m: Motor, a) -> None:
    _imprimir_resposta(m.perguntar(a.pergunta, categoria=a.categoria, doc_id=a.doc_id))


def cmd_summarize(m: Motor, a) -> None:
    _imprimir_resposta(m.resumir(a.doc_id))


def cmd_compare(m: Motor, a) -> None:
    _imprimir_resposta(m.comparar(a.doc_ids))


def cmd_extract(m: Motor, a) -> None:
    print(json.dumps(m.extrair(a.doc_id, forcar=a.forcar), ensure_ascii=False, indent=2))


def cmd_eval(m: Motor, a) -> None:
    perguntas = json.loads(Path(a.ficheiro).read_text(encoding="utf-8"))
    fiaveis = nao_encontradas = erros = 0
    for n, p in enumerate(perguntas, 1):
        try:
            r = m.perguntar(p["pergunta"], categoria=p.get("categoria"), doc_id=p.get("doc_id"))
        except LLMError as e:
            erros += 1
            print(f"{n:>2}. ERRO   {p['pergunta']}\n      {e}")
            continue
        v = r["verificacao"]
        nf = r["resposta"] == NAO_ENCONTREI
        fiaveis += v["fiavel"]
        nao_encontradas += nf
        estado = "N/E" if nf else ("FIÁVEL" if v["fiavel"] else "FALHA")
        print(f"{n:>2}. {estado:<6} {p['pergunta']}")
        for f in v["frases"]:
            if f["estado"] != "apoiada":
                print(f"      ✘ {f['estado']}: {f['frase'][:80]}")
        if a.pausa and n < len(perguntas):
            time.sleep(a.pausa)
    total = len(perguntas)
    print(f"\nRespostas fiáveis: {fiaveis}/{total} ({100 * fiaveis / total:.0f}%)")
    print(f"  das quais 'não encontrei': {nao_encontradas}   erros: {erros}")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    ap = argparse.ArgumentParser(prog="python -m app.cli", description="Módulo de IA — Chama em Queda Livre")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index", help="(re)indexa data/docs")
    sub.add_parser("docs", help="lista os documentos indexados")
    s = sub.add_parser("search", help="busca híbrida")
    s.add_argument("consulta"); s.add_argument("-k", type=int, default=5)
    s.add_argument("--categoria"); s.add_argument("--doc-id")
    s = sub.add_parser("ask", help="pergunta com fontes verificadas")
    s.add_argument("pergunta"); s.add_argument("--categoria"); s.add_argument("--doc-id")
    s = sub.add_parser("summarize", help="resume um documento")
    s.add_argument("doc_id")
    s = sub.add_parser("compare", help="compara documentos")
    s.add_argument("doc_ids", nargs="+")
    s = sub.add_parser("extract", help="extracção estruturada (JSON)")
    s.add_argument("doc_id"); s.add_argument("--forcar", action="store_true")
    s = sub.add_parser("eval", help="avaliação com tests/perguntas.json")
    s.add_argument("--ficheiro", default=str(BASE_DIR / "tests" / "perguntas.json"))
    s.add_argument("--pausa", type=float, default=0.0, help="segundos entre perguntas (limites de quota)")
    a = ap.parse_args(argv)

    comandos = {"index": cmd_index, "docs": cmd_docs, "search": cmd_search, "ask": cmd_ask,
                "summarize": cmd_summarize, "compare": cmd_compare, "extract": cmd_extract,
                "eval": cmd_eval}
    try:
        comandos[a.cmd](Motor(), a)
    except (ValueError, KeyError, LLMError) as e:
        print(f"Erro: {str(e).strip(chr(39))}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
