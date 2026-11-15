import { Search, X } from "lucide-react";

import type { EstadoFiltros } from "../hooks/useFiltros";
import { RESULTADOS, ROTULO_RESULTADO } from "../lib/experiencias";
import { CAMPO } from "../lib/formato";

/** Filtros numa linha compacta, com chips dos activos e botão para limpar. */
export default function Filtros({
  filtros,
  total,
}: {
  filtros: EstadoFiltros;
  total: number;
}) {
  const { f, definir, limpar, opcoes, filtradas, activos } = filtros;

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-40 flex-1 sm:max-w-xs">
          <Search
            size={14}
            aria-hidden="true"
            className="pointer-events-none absolute left-2 top-1/2 -translate-y-1/2 text-texto-3"
          />
          <input
            type="search"
            value={f.pesquisa}
            onChange={(e) => definir("pesquisa", e.target.value)}
            placeholder="Pesquisar código, título ou combustível"
            aria-label="Pesquisar experiências"
            className={`${CAMPO} w-full pl-7`}
          />
        </div>

        <select
          value={f.combustivel}
          onChange={(e) => definir("combustivel", e.target.value)}
          aria-label="Filtrar por combustível"
          className={`${CAMPO} min-w-0 max-w-full`}
        >
          <option value="">Combustível: todos</option>
          {opcoes.combustiveis.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        <select
          value={f.categoria}
          onChange={(e) => definir("categoria", e.target.value)}
          aria-label="Filtrar por categoria"
          className={`${CAMPO} min-w-0 max-w-full`}
        >
          <option value="">Categoria: todas</option>
          {opcoes.categorias.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        <select
          value={f.resultado}
          onChange={(e) => definir("resultado", e.target.value)}
          aria-label="Filtrar por resultado"
          className={`${CAMPO} min-w-0 max-w-full`}
        >
          <option value="">Resultado: todos</option>
          {RESULTADOS.map((r) => (
            <option key={r} value={r}>
              {ROTULO_RESULTADO[r]}
            </option>
          ))}
        </select>

        <p className="ml-auto text-xs text-texto-2" aria-live="polite">
          <span className="num text-texto">{filtradas.length}</span> de{" "}
          <span className="num">{total}</span> experiências
        </p>
      </div>

      {activos.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5">
          {activos.map((a) => (
            <button
              key={a.chave}
              type="button"
              onClick={() => definir(a.chave, "")}
              aria-label={`Remover o filtro ${a.rotulo}`}
              className="inline-flex h-6 max-w-full items-center gap-1 rounded-sm border border-chama bg-chama-fundo px-1.5 text-xs text-texto hover:bg-superficie-2"
            >
              <span className="truncate">{a.rotulo}</span>
              <X size={12} aria-hidden="true" className="shrink-0" />
            </button>
          ))}
          <button
            type="button"
            onClick={limpar}
            className="h-6 rounded-sm px-1.5 text-xs text-chama underline underline-offset-2"
          >
            Limpar filtros
          </button>
        </div>
      )}
    </div>
  );
}
