import { useMemo, useState } from "react";

import { ROTULO_RESULTADO } from "../lib/experiencias";
import type { Experiencia, Resultado } from "../lib/experiencias";

export interface Filtros {
  pesquisa: string;
  combustivel: string;
  categoria: string;
  resultado: string;
}

const INICIAL: Filtros = {
  pesquisa: "",
  combustivel: "",
  categoria: "",
  resultado: "",
};

const normalizar = (valor: string) =>
  valor
    .toLocaleLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .trim();

const unicos = (valores: (string | null)[]) =>
  [...new Set(valores.filter((v): v is string => Boolean(v)))].sort((a, b) =>
    a.localeCompare(b, "pt")
  );

/** Estado dos filtros, partilhado pelo mapa, pelo gráfico e pela tabela. */
export function useFiltros(experiencias: Experiencia[]) {
  const [f, setF] = useState<Filtros>(INICIAL);

  const opcoes = useMemo(
    () => ({
      combustiveis: unicos(experiencias.map((e) => e.combustivel)),
      categorias: unicos(experiencias.map((e) => e.categoria)),
    }),
    [experiencias]
  );

  const filtradas = useMemo(() => {
    const termo = normalizar(f.pesquisa);
    return experiencias.filter(
      (e) =>
        (!termo ||
          normalizar(
            [e.id, e.titulo, e.combustivel, e.ambiente, e.categoria].join(" ")
          ).includes(termo)) &&
        (!f.combustivel || e.combustivel === f.combustivel) &&
        (!f.categoria || e.categoria === f.categoria) &&
        (!f.resultado || e.resultado === f.resultado)
    );
  }, [experiencias, f]);

  const definir = (chave: keyof Filtros, valor: string) =>
    setF((actual) => ({ ...actual, [chave]: valor }));

  const activos = [
    f.pesquisa.trim() && { chave: "pesquisa" as const, rotulo: `“${f.pesquisa.trim()}”` },
    f.combustivel && { chave: "combustivel" as const, rotulo: `Combustível: ${f.combustivel}` },
    f.categoria && { chave: "categoria" as const, rotulo: `Categoria: ${f.categoria}` },
    f.resultado && {
      chave: "resultado" as const,
      rotulo: `Resultado: ${ROTULO_RESULTADO[f.resultado as Resultado]}`,
    },
  ].filter((x): x is { chave: keyof Filtros; rotulo: string } => Boolean(x));

  return {
    f,
    definir,
    limpar: () => setF(INICIAL),
    opcoes,
    filtradas,
    activos,
  };
}

export type EstadoFiltros = ReturnType<typeof useFiltros>;
