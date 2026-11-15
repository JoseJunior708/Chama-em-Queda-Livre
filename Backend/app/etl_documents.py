
import json
import re

from pathlib import Path
from datetime import datetime, timezone

import pdfplumber


SECTION_PATTERNS = {
    "resumo": [
        r"abstract",
        r"resumo",
    ],
    "metodologia": [
        r"materials and methods",
        r"methodology",
        r"methods",
        r"experimental procedure",
        r"metodologia",
        r"materiais e métodos",
    ],
    "resultados": [
        r"results and discussion",
        r"results",
        r"discussion",
        r"resultados",
        r"resultados e discussão",
    ],
}


def clean_text(text):
    """Limpar espaços e caracteres desnecessários."""

    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def identify_section_heading(line):
    """Identificar se uma linha representa um título de secção."""

    normalized = line.strip().lower()

    normalized = re.sub(
        r"^\d+(?:\.\d+)*[\s.)-]+",
        "",
        normalized
    )

    normalized = normalized.strip(" .:-")

    for section, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.fullmatch(pattern, normalized, flags=re.IGNORECASE):
                return section

    return None


def extract_pdf_text(pdf_path):
    """Extrair texto de todas as páginas de um PDF."""

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF não encontrado: {path}"
        )

    pages = []

    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            pages.append({
                "page": page_number,
                "text": text,
            })

    return pages


def split_into_sections(full_text):
    """
    Separar o documento em Resumo, Metodologia e Resultados.

    O reconhecimento depende dos títulos existentes no PDF.
    Quando não forem encontrados, a secção fica vazia.
    """

    sections = {
        "resumo": [],
        "metodologia": [],
        "resultados": [],
    }

    current_section = None

    for line in full_text.splitlines():

        detected = identify_section_heading(line)

        if detected:
            current_section = detected
            continue

        if current_section:
            sections[current_section].append(line)

    return {
        section: clean_text(" ".join(lines))
        for section, lines in sections.items()
    }


def process_scientific_pdf(
    pdf_path,
    output_path=None,
    source_url=None,
    doi=None,
):
    """Extrair, organizar e exportar um relatório científico."""

    path = Path(pdf_path)

    pages = extract_pdf_text(path)

    full_text = "\n".join(
        page["text"] for page in pages
    )

    sections = split_into_sections(full_text)

    document = {
        "document": {
            "filename": path.name,
            "source_url": source_url,
            "doi": doi,
            "processed_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "pages_count": len(pages),
        },

        "sections": sections,

        "full_text": clean_text(full_text),

        "extraction_info": {
            "tool": "pdfplumber",
            "sections_found": [
                name
                for name, content in sections.items()
                if content
            ],
            "requires_manual_review": not any(sections.values()),
        },
    }

    if output_path is None:
        output_path = path.with_suffix(".json")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8") as file:
        json.dump(
            document,
            file,
            ensure_ascii=False,
            indent=4,
        )

    return document


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extrair informação científica de PDFs."
    )

    parser.add_argument("pdf", help="Caminho do PDF")
    parser.add_argument(
        "--output",
        help="Caminho do JSON de saída",
    )
    parser.add_argument(
        "--source-url",
        help="URL da fonte original",
    )
    parser.add_argument(
        "--doi",
        help="DOI do documento",
    )

    args = parser.parse_args()

    result = process_scientific_pdf(
        pdf_path=args.pdf,
        output_path=args.output,
        source_url=args.source_url,
        doi=args.doi,
    )

    print("Documento processado com sucesso!")
    print("Secções encontradas:")

    for section, content in result["sections"].items():
        print(f"- {section}: {'Encontrada' if content else 'Não encontrada'}")
