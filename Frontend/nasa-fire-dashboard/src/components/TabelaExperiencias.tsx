import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";

import type { Experiencia } from "../lib/experiencias";
import { comUnidade, num, SEM_VALOR } from "../lib/formato";
import { EstadoVazio, MarcaResultado } from "./ui";

type Chave = "id" | "titulo" | "combustivel" | "o2" | "pressao" | "velocidade" | "ano" | "resultado";

interface Coluna {
  chave: Chave;
  rotulo: string;
  unidade?: string;
  numerica?: boolean;
  /** Classes que escondem a coluna quando a tabela tem pouco espaço. */
  visivel?: string;
  celula: (e: Experiencia) => ReactNode;
}

const COLUNAS: Coluna[] = [
  { chave: "id", rotulo: "Código", celula: (e) => <span className="num text-texto-2">{e.id}</span> },
  { chave: "titulo", rotulo: "Experiência", celula: (e) => e.titulo },
  {
    chave: "combustivel",
    rotulo: "Combustível",
    celula: (e) => (
      <span className="block max-w-40 truncate" title={e.combustivel ?? undefined}>
        {e.combustivel ?? SEM_VALOR}
      </span>
    ),
  },
  { chave: "o2", rotulo: "Oxigénio", unidade: "% O2", numerica: true, celula: (e) => num(e.o2) },
  { chave: "pressao", rotulo: "Pressão", unidade: "kPa", numerica: true, celula: (e) => num(e.pressao) },
  { chave: "velocidade", rotulo: "Escoamento", unidade: "cm/s", numerica: true, celula: (e) => num(e.velocidade) },
  { chave: "ano", rotulo: "Ano", numerica: true, visivel: "hidden @6xl:table-cell", celula: (e) => e.ano ?? SEM_VALOR },
  { chave: "resultado", rotulo: "Resultado", celula: (e) => <MarcaResultado resultado={e.resultado} /> },
];

const MAX_SELECCAO = 3;

/** Tabela densa e ordenável. Com pouco espaço esconde o ano e, abaixo disso,
    passa a lista de cartões. Mede o espaço do contentor, não o do ecrã, para
    se adaptar também ao menu lateral aberto ou recolhido. */
export default function TabelaExperiencias({
  experiencias,
  onAbrir,
  seleccao,
  onSeleccao,
}: {
  experiencias: Experiencia[];
  onAbrir: (id: string) => void;
  /** Com `seleccao`, cada linha ganha uma caixa para comparar (até 3). */
  seleccao?: string[];
  onSeleccao?: (ids: string[]) => void;
}) {
  const [ordem, setOrdem] = useState<{ chave: Chave; desc: boolean }>({
    chave: "id",
    desc: false,
  });

  const linhas = useMemo(() => {
    const { chave, desc } = ordem;
    return [...experiencias].sort((a, b) => {
      const x = a[chave];
      const y = b[chave];
      // Sem valor fica sempre no fim, em qualquer sentido.
      if (x === null || y === null) return x === y ? 0 : x === null ? 1 : -1;
      const r =
        typeof x === "number" && typeof y === "number"
          ? x - y
          : String(x).localeCompare(String(y), "pt", { numeric: true });
      return desc ? -r : r;
    });
  }, [experiencias, ordem]);

  if (experiencias.length === 0) {
    return (
      <EstadoVazio titulo="Nenhuma experiência corresponde aos filtros">
        Remove um filtro ou altera a pesquisa para ver mais resultados.
      </EstadoVazio>
    );
  }

  const alternar = (id: string) => {
    if (!seleccao || !onSeleccao) return;
    onSeleccao(
      seleccao.includes(id) ? seleccao.filter((s) => s !== id) : [...seleccao, id]
    );
  };

  const caixa = (e: Experiencia) =>
    seleccao && (
      <input
        type="checkbox"
        checked={seleccao.includes(e.id)}
        disabled={!seleccao.includes(e.id) && seleccao.length >= MAX_SELECCAO}
        onChange={() => alternar(e.id)}
        aria-label={`Seleccionar ${e.id} para comparar`}
        className="h-4 w-4 accent-chama"
      />
    );

  return (
    <div className="@container">
      {/* Tabela: quando o contentor tem pelo menos 56rem */}
      <div className="hidden overflow-x-auto @4xl:block">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="text-left">
              {seleccao && (
                <th scope="col" className="w-8 px-3 py-2">
                  <span className="sr-only">Comparar</span>
                </th>
              )}
              {COLUNAS.map((c) => {
                const activa = ordem.chave === c.chave;
                const Icone = !activa ? ChevronsUpDown : ordem.desc ? ArrowDown : ArrowUp;
                return (
                  <th
                    key={c.chave}
                    scope="col"
                    aria-sort={activa ? (ordem.desc ? "descending" : "ascending") : "none"}
                    className={`px-3 py-2 align-bottom font-medium ${c.numerica ? "text-right" : ""} ${c.visivel ?? ""}`}
                  >
                    <button
                      type="button"
                      onClick={() =>
                        setOrdem({ chave: c.chave, desc: activa ? !ordem.desc : false })
                      }
                      className={`inline-flex items-end gap-1 whitespace-nowrap text-[11px] uppercase leading-4 tracking-wide hover:text-texto ${
                        activa ? "text-texto" : "text-texto-2"
                      } ${c.numerica ? "text-right" : "text-left"}`}
                    >
                      <span>
                        {c.rotulo}
                        {c.unidade && (
                          <span className="num block normal-case tracking-normal text-texto-3">
                            {c.unidade}
                          </span>
                        )}
                      </span>
                      <Icone size={12} aria-hidden="true" className="mb-0.5 shrink-0" />
                    </button>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {linhas.map((e) => (
              <tr
                key={e.id}
                onClick={() => onAbrir(e.id)}
                className={`cursor-pointer border-t border-linha hover:bg-superficie-2 ${
                  seleccao?.includes(e.id) ? "bg-chama-fundo" : ""
                }`}
              >
                {seleccao && (
                  <td className="px-3 py-1.5" onClick={(ev) => ev.stopPropagation()}>
                    {caixa(e)}
                  </td>
                )}
                {COLUNAS.map((c) => (
                  <td
                    key={c.chave}
                    className={`px-3 py-1.5 ${
                      c.numerica ? "num text-right text-texto" : "text-texto"
                    } ${c.chave === "titulo" ? "w-full max-w-0" : "whitespace-nowrap"} ${c.visivel ?? ""}`}
                  >
                    {c.chave === "titulo" ? (
                      <button
                        type="button"
                        onClick={(ev) => {
                          ev.stopPropagation();
                          onAbrir(e.id);
                        }}
                        title={e.titulo}
                        className="block max-w-full truncate text-left hover:underline"
                      >
                        {e.titulo}
                      </button>
                    ) : (
                      c.celula(e)
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Lista de cartões: contentor abaixo de 56rem; duas colunas se couberem */}
      <ul className="grid gap-px bg-linha @2xl:grid-cols-2 @4xl:hidden">
        {linhas.map((e) => (
          <li key={e.id} className="flex items-start gap-3 bg-superficie px-4 py-3">
            {seleccao && <div className="pt-0.5">{caixa(e)}</div>}
            <button
              type="button"
              onClick={() => onAbrir(e.id)}
              className="min-w-0 flex-1 text-left"
            >
              <span className="flex items-center justify-between gap-2">
                <span className="num text-xs text-texto-2">{e.id}</span>
                <MarcaResultado resultado={e.resultado} />
              </span>
              <span className="mt-0.5 block text-sm font-medium text-texto">{e.titulo}</span>
              <span className="mt-0.5 block text-xs text-texto-2">
                {e.combustivel ?? "Combustível sem dado"}
              </span>
              <span className="num mt-1 flex flex-wrap gap-x-3 text-xs text-texto">
                <span>{comUnidade(e.o2, "% O2")}</span>
                <span>{comUnidade(e.pressao, "kPa")}</span>
                <span>{comUnidade(e.velocidade, "cm/s")}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
