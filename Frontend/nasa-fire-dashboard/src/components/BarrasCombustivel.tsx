import { useMemo } from "react";

import type { Experiencia } from "../lib/experiencias";
import { EstadoVazio, Seccao } from "./ui";

/** Experiências por combustível. Clicar numa barra filtra por esse combustível. */
export default function BarrasCombustivel({
  experiencias,
  seleccionado,
  onSeleccionar,
}: {
  experiencias: Experiencia[];
  seleccionado: string;
  onSeleccionar: (combustivel: string) => void;
}) {
  const linhas = useMemo(() => {
    const contagem = new Map<string, number>();
    for (const e of experiencias) {
      const k = e.combustivel ?? "";
      contagem.set(k, (contagem.get(k) ?? 0) + 1);
    }
    return [...contagem.entries()].sort((a, b) => b[1] - a[1]);
  }, [experiencias]);

  const maximo = Math.max(1, ...linhas.map((l) => l[1]));

  return (
    <Seccao titulo="Experiências por combustível">
      {linhas.length === 0 ? (
        <EstadoVazio titulo="Sem experiências" />
      ) : (
        <ul className="space-y-px p-2">
          {linhas.map(([combustivel, n]) => {
            const activo = Boolean(combustivel) && combustivel === seleccionado;
            return (
              <li key={combustivel || "sem-dado"}>
                <button
                  type="button"
                  disabled={!combustivel}
                  aria-pressed={activo}
                  onClick={() => onSeleccionar(activo ? "" : combustivel)}
                  title={
                    combustivel
                      ? activo
                        ? "Remover o filtro"
                        : `Filtrar por ${combustivel}`
                      : undefined
                  }
                  className={`grid w-full grid-cols-[minmax(0,9rem)_1fr_2rem] items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm enabled:hover:bg-superficie-2 ${
                    activo ? "bg-superficie-2" : ""
                  }`}
                >
                  <span className={`truncate ${activo ? "font-medium text-texto" : "text-texto-2"}`}>
                    {combustivel || "Sem dado"}
                  </span>
                  <span className="h-2" aria-hidden="true">
                    <span
                      className={`block h-full rounded-r-sm ${activo ? "bg-chama" : "bg-texto-3"}`}
                      style={{ width: `${(n / maximo) * 100}%` }}
                    />
                  </span>
                  <span className="num text-right text-texto">{n}</span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </Seccao>
  );
}
