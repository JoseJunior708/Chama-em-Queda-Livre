import { X } from "lucide-react";

import { ROTULO_RESULTADO } from "../lib/experiencias";
import type { Experiencia } from "../lib/experiencias";
import { BOTAO, comUnidade, SEM_VALOR } from "../lib/formato";
import { Seccao } from "./ui";

const LINHAS: { rotulo: string; valor: (e: Experiencia) => string; numerica?: boolean }[] = [
  { rotulo: "Combustível", valor: (e) => e.combustivel ?? SEM_VALOR },
  { rotulo: "Categoria", valor: (e) => e.categoria },
  { rotulo: "Ambiente", valor: (e) => e.ambiente ?? SEM_VALOR },
  { rotulo: "Concentração de O2", valor: (e) => comUnidade(e.o2, "% O2"), numerica: true },
  { rotulo: "Pressão", valor: (e) => comUnidade(e.pressao, "kPa"), numerica: true },
  { rotulo: "Velocidade do escoamento", valor: (e) => comUnidade(e.velocidade, "cm/s"), numerica: true },
  { rotulo: "Ano", valor: (e) => (e.ano === null ? SEM_VALOR : String(e.ano)), numerica: true },
  { rotulo: "Resultado", valor: (e) => ROTULO_RESULTADO[e.resultado] },
];

/** Tabela lado a lado de 2 ou 3 experiências, com as diferenças destacadas. */
export default function Comparacao({
  experiencias,
  onFechar,
}: {
  experiencias: Experiencia[];
  onFechar: () => void;
}) {
  const linhas = LINHAS.map((l) => {
    const valores = experiencias.map(l.valor);
    return { ...l, valores, difere: new Set(valores).size > 1 };
  });
  const diferencas = linhas.filter((l) => l.difere).length;

  return (
    <Seccao
      titulo="Comparação"
      nota={
        <>
          <span className="num">{diferencas}</span> de{" "}
          <span className="num">{linhas.length}</span> campos diferem
        </>
      }
      accoes={
        <button type="button" onClick={onFechar} className={BOTAO}>
          <X size={14} aria-hidden="true" />
          Fechar
        </button>
      }
    >
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="text-left align-top">
              <th scope="col" className="px-4 py-2 text-[11px] font-medium uppercase tracking-wide text-texto-2">
                Campo
              </th>
              {experiencias.map((e) => (
                <th key={e.id} scope="col" className="min-w-40 px-4 py-2 font-medium">
                  <span className="num block text-xs text-texto-2">{e.id}</span>
                  <span className="block text-texto">{e.titulo}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {linhas.map((l) => (
              <tr key={l.rotulo} className={`border-t border-linha ${l.difere ? "bg-chama-fundo" : ""}`}>
                <th
                  scope="row"
                  className={`whitespace-nowrap border-l-2 px-4 py-1.5 text-left font-normal ${
                    l.difere ? "border-chama text-texto" : "border-transparent text-texto-2"
                  }`}
                >
                  {l.rotulo}
                  {l.difere && (
                    <span className="num ml-2 text-xs text-chama">≠ difere</span>
                  )}
                </th>
                {l.valores.map((v, i) => (
                  <td
                    key={experiencias[i].id}
                    className={`px-4 py-1.5 ${l.numerica ? "num" : ""} ${
                      l.difere ? "font-medium text-texto" : "text-texto-2"
                    }`}
                  >
                    {v}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Seccao>
  );
}
