import { useState } from "react";
import { Check, Copy, Download } from "lucide-react";

import { api } from "../api/client";
import { useAsync } from "../api/useAsync";
import type { AsyncComRepetir } from "../api/useAsync";
import { AvisoVerificacao, ChipsFontes, TextoCitado } from "../components/Citacoes";
import { Assincrono, EstadoVazio, Seccao, Selo } from "../components/ui";
import { BOTAO, CAMPO } from "../lib/formato";
import type { Documento, Fonte, Resposta } from "../types/api";
import type { DadosBase } from "./VisaoGeral";

function emMarkdown(doc: Documento, r: Resposta): string {
  const fontes = r.fontes
    .map((f) => `- [${f.tag}] ${f.titulo}, p. ${f.pagina}${f.url ? ` (${f.url})` : ""}`)
    .join("\n");
  return `# ${doc.titulo}\n\nCódigo: ${doc.doc_id}\nVerificação: ${
    r.verificacao.fiavel ? "verificado" : "por verificar"
  }\n\n## Resumo\n\n${r.resposta}\n\n## Fontes\n\n${fontes}\n`;
}

function Resumo({
  doc,
  onAbrirFonte,
}: {
  doc: Documento;
  onAbrirFonte: (fonte: Fonte) => void;
}) {
  const resumo = useAsync(() => api.resumir(doc.doc_id), [doc.doc_id]);
  const [copiado, setCopiado] = useState(false);
  const pronto = resumo.fase === "ok" && resumo.dados.fontes.length > 0;

  async function copiar() {
    if (resumo.fase !== "ok") return;
    try {
      await navigator.clipboard.writeText(emMarkdown(doc, resumo.dados));
      setCopiado(true);
      window.setTimeout(() => setCopiado(false), 2000);
    } catch {
      setCopiado(false);
    }
  }

  function exportar() {
    if (resumo.fase !== "ok") return;
    const url = URL.createObjectURL(
      new Blob([emMarkdown(doc, resumo.dados)], { type: "text/markdown;charset=utf-8" })
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = `resumo-${doc.doc_id}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <Seccao
      titulo={doc.titulo}
      accoes={
        <div className="flex gap-2">
          <button type="button" className={BOTAO} onClick={copiar} disabled={!pronto}>
            {copiado ? <Check size={14} aria-hidden="true" /> : <Copy size={14} aria-hidden="true" />}
            <span aria-live="polite">{copiado ? "Copiado" : "Copiar"}</span>
          </button>
          <button type="button" className={BOTAO} onClick={exportar} disabled={!pronto}>
            <Download size={14} aria-hidden="true" />
            Exportar .md
          </button>
        </div>
      }
    >
      <p className="border-b border-linha px-4 py-2 text-xs text-texto-2">
        <span className="num">{doc.doc_id}</span> · {doc.categoria} ·{" "}
        <span className="num">{doc.paginas}</span> páginas
        {doc.metadados?.ano && (
          <>
            {" "}
            · <span className="num">{doc.metadados.ano}</span>
          </>
        )}
      </p>
      <Assincrono estado={resumo}>
        {(r) =>
          r.fontes.length === 0 ? (
            <EstadoVazio titulo="Sem resumo para este documento">{r.resposta}</EstadoVazio>
          ) : (
            <div className="space-y-3 p-4">
              <Selo verificado={r.verificacao.fiavel} />
              <AvisoVerificacao verificacao={r.verificacao} />
              <TextoCitado resposta={r} onAbrirFonte={onAbrirFonte} />
              <ChipsFontes fontes={r.fontes} onAbrirFonte={onAbrirFonte} />
            </div>
          )
        }
      </Assincrono>
    </Seccao>
  );
}

export default function Resumos({
  dados,
  onAbrirFonte,
}: {
  dados: AsyncComRepetir<DadosBase>;
  onAbrirFonte: (fonte: Fonte) => void;
}) {
  const [escolhido, setEscolhido] = useState<string | null>(null);

  return (
    <Assincrono estado={dados}>
      {({ documentos }) => {
        if (documentos.length === 0) {
          return (
            <div className="rounded-lg border border-linha bg-superficie">
              <EstadoVazio titulo="Ainda não há documentos indexados" />
            </div>
          );
        }
        const doc = documentos.find((d) => d.doc_id === escolhido) ?? documentos[0];

        return (
          <div className="grid items-start gap-4 lg:grid-cols-[18rem_minmax(0,1fr)]">
            {/* Ecrãs pequenos: lista pendente */}
            <label className="block lg:hidden">
              <span className="mb-1 block text-xs text-texto-2">Documento</span>
              <select
                value={doc.doc_id}
                onChange={(e) => setEscolhido(e.target.value)}
                className={`${CAMPO} w-full`}
              >
                {documentos.map((d) => (
                  <option key={d.doc_id} value={d.doc_id}>
                    {d.doc_id} · {d.titulo}
                  </option>
                ))}
              </select>
            </label>

            {/* Ecrãs largos: lista lateral */}
            <nav
              aria-label="Documentos"
              className="hidden max-h-[calc(100vh-7rem)] overflow-y-auto rounded-lg border border-linha bg-superficie lg:block"
            >
              <ul className="divide-y divide-linha">
                {documentos.map((d) => {
                  const activo = d.doc_id === doc.doc_id;
                  return (
                    <li key={d.doc_id}>
                      <button
                        type="button"
                        aria-current={activo ? "true" : undefined}
                        onClick={() => setEscolhido(d.doc_id)}
                        className={`block w-full border-l-2 px-3 py-2 text-left hover:bg-superficie-2 ${
                          activo ? "border-chama bg-superficie-2" : "border-transparent"
                        }`}
                      >
                        <span className="num block text-xs text-texto-2">{d.doc_id}</span>
                        <span className={`block text-sm ${activo ? "font-medium text-texto" : "text-texto-2"}`}>
                          {d.titulo}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </nav>

            <Resumo key={doc.doc_id} doc={doc} onAbrirFonte={onAbrirFonte} />
          </div>
        );
      }}
    </Assincrono>
  );
}
