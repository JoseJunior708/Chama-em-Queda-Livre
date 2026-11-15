"""Utilitários de teste: PDFs sintéticos, embeddings e LLM simulados (sem internet nem chave)."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def criar_pdf(caminho: Path, paginas: list[str]) -> None:
    """Escreve um PDF mínimo e válido com uma linha de texto por página (lista vazia de texto = página em branco)."""
    objetos: list[bytes] = []
    n = len(paginas)
    # 1: catálogo, 2: páginas, 3: fonte, depois (página, conteúdo) por cada página
    kids = " ".join(f"{4 + 2 * i} 0 R" for i in range(n))
    objetos.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objetos.append(f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode())
    objetos.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for i, texto in enumerate(paginas):
        linhas = [l for l in texto.split("\n")] if texto else []
        ops = ["BT /F1 10 Tf 40 800 Td 12 TL"]
        for l in linhas:
            esc = l.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            ops.append(f"({esc}) Tj T*")
        ops.append("ET")
        stream = "\n".join(ops).encode("latin-1") if linhas else b""
        objetos.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {5 + 2 * i} 0 R >>".encode())
        objetos.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
    saida = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objetos):
        offsets.append(len(saida))
        saida += f"{i + 1} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(saida)
    saida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        saida += f"{off:010d} 00000 n \n".encode()
    saida += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    caminho.write_bytes(bytes(saida))


# Sinónimos PT->EN para que o embedder falso imite um modelo multilingue.
_SINONIMOS = {
    "gota": "droplet", "gotas": "droplet", "chama": "flame", "chamas": "flame",
    "combustivel": "fuel", "combustível": "fuel", "oxigenio": "oxygen", "oxigénio": "oxygen",
    "pressao": "pressure", "pressão": "pressure", "fuligem": "soot", "propagacao": "spread",
    "propagação": "spread", "incendio": "fire", "incêndio": "fire", "nave": "spacecraft",
    "taxa": "rate", "queima": "burning", "extincao": "extinction", "extinção": "extinction",
}


def _tokens(texto: str) -> list[str]:
    toks = re.findall(r"[a-zà-ÿ0-9]+", texto.lower())
    return [_SINONIMOS.get(t, t) for t in toks if len(t) > 2]


class FakeEmbedder:
    """Embeddings determinísticos de saco de palavras (hashing), normalizados."""

    dim = 64

    def __init__(self):
        self.chamadas = 0

    def _vetor(self, texto: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        for t in _tokens(texto):
            h = int(hashlib.md5(t.encode()).hexdigest(), 16)
            v[h % self.dim] += 1.0
        n = np.linalg.norm(v)
        return v / n if n else v

    def embed(self, textos: list[str], tipo: str = "documento", titulos=None) -> np.ndarray:
        self.chamadas += 1
        return np.vstack([self._vetor(t) for t in textos]) if textos else np.zeros((0, self.dim))


class FakeLLM(FakeEmbedder):
    """LLM simulado. `respostas` mapeia um fragmento do prompt -> resposta (str ou dict)."""

    def __init__(self, respostas: dict | None = None, juiz_apoia: bool = True, falhar: bool = False):
        super().__init__()
        self.respostas = respostas or {}
        self.juiz_apoia = juiz_apoia
        self.falhar = falhar
        self.prompts: list[str] = []

    def generate(self, prompt: str, system: str | None = None, json_mode: bool = False,
                 temperature: float = 0.0, max_tokens: int | None = None) -> str:
        from app.llm import LLMError

        self.prompts.append(prompt)
        if self.falhar:
            raise LLMError("falha simulada")
        if "FRASES A AVALIAR" in prompt:  # chamada do juiz
            idx = [int(i) for i in re.findall(r"^### Frase (\d+)", prompt, re.M)]
            return json.dumps([{"i": i, "apoiada": self.juiz_apoia, "motivo": "simulado"} for i in idx])
        for fragmento, resposta in self.respostas.items():
            if fragmento in prompt:
                return json.dumps(resposta) if isinstance(resposta, (dict, list)) else resposta
        return "{}" if json_mode else "Não encontrei essa informação nos documentos."

    def generate_json(self, prompt: str, system: str | None = None, **kw):
        from app.llm import parse_json
        return parse_json(self.generate(prompt, system=system, json_mode=True, **kw))


# ------------------------------------------------------------- corpus de teste

TEXTO_GOTAS = (
    "Droplet combustion experiments were performed aboard the International Space Station "
    "in the FLEX apparatus. Heptane droplets with initial diameters of 2.5 mm burned in "
    "an atmosphere with 21% oxygen at 1 atm. The burning rate constant was 0.65 mm2/s. "
    "Cool flame burning was observed after radiative extinction of the hot flame."
)
TEXTO_SOLIDOS = (
    "Flame spread over thin solid fuels such as cotton fabric and PMMA was studied in the "
    "Saffire experiment. The flame spread rate reached 1.8 cm/s at an opposed flow velocity "
    "of 20 cm/s. Char formation and smoldering were recorded for the cellulose samples."
)
TEXTO_GASOSO = (
    "Laminar gas jet diffusion flames of methane were studied in a 2.2 second drop tower. "
    "Soot formation decreased at lower pressure. The coflow diffusion flame was longer in "
    "microgravity than in normal gravity."
)


@pytest.fixture
def pasta_docs(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "flex_gotas.txt").write_text(TEXTO_GOTAS, encoding="utf-8")
    (docs / "flex_gotas.json").write_text(json.dumps(
        {"titulo": "FLEX: combustão de gotas na ISS", "ano": 2012, "autores": ["Dietrich, D. L."],
         "combustivel": ["heptano", "metanol"], "ambiente": ["ISS"],
         "url": "https://ntrs.nasa.gov/citations/20120000001"}), encoding="utf-8")
    (docs / "saffire.txt").write_text(TEXTO_SOLIDOS, encoding="utf-8")
    (docs / "saffire.json").write_text(json.dumps(
        {"titulo": "Saffire: propagação em sólidos", "combustivel": "algodão", "ambiente": "Cygnus"}),
        encoding="utf-8")
    criar_pdf(docs / "jato_gasoso.pdf", [TEXTO_GASOSO])
    return docs


@pytest.fixture
def ambiente(tmp_path: Path, pasta_docs: Path, monkeypatch):
    """Configuração isolada: sem chave, índice numa pasta temporária."""
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("DOCS_DIR", str(pasta_docs))
    monkeypatch.setenv("INDEX_DIR", str(tmp_path / "index"))
    from app.config import get_settings
    return get_settings()
