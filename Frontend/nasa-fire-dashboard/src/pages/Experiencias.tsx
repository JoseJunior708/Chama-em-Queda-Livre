import { useState } from "react";

import type { AsyncComRepetir } from "../api/useAsync";
import Comparacao from "../components/Comparacao";
import Filtros from "../components/Filtros";
import TabelaExperiencias from "../components/TabelaExperiencias";
import { Assincrono, Seccao } from "../components/ui";
import type { EstadoFiltros } from "../hooks/useFiltros";
import { BOTAO, BOTAO_PRIMARIO } from "../lib/formato";
import type { DadosBase } from "./VisaoGeral";

export default function Experiencias({
  dados,
  filtros,
  onAbrir,
}: {
  dados: AsyncComRepetir<DadosBase>;
  filtros: EstadoFiltros;
  onAbrir: (id: string) => void;
}) {
  const [seleccao, setSeleccao] = useState<string[]>([]);
  const [aComparar, setAComparar] = useState(false);

  return (
    <Assincrono estado={dados}>
      {({ experiencias }) => {
        const escolhidas = experiencias.filter((e) => seleccao.includes(e.id));
        const podeComparar = escolhidas.length >= 2;

        return (
          <div className="space-y-4">
            <Filtros filtros={filtros} total={experiencias.length} />

            {aComparar && podeComparar && (
              <Comparacao experiencias={escolhidas} onFechar={() => setAComparar(false)} />
            )}

            <Seccao
              titulo="Experiências"
              nota={
                seleccao.length === 0 ? (
                  "selecciona 2 ou 3 linhas para comparar"
                ) : (
                  <>
                    <span className="num">{seleccao.length}</span> de{" "}
                    <span className="num">3</span> seleccionadas
                  </>
                )
              }
              accoes={
                <div className="flex gap-2">
                  {seleccao.length > 0 && (
                    <button
                      type="button"
                      className={BOTAO}
                      onClick={() => {
                        setSeleccao([]);
                        setAComparar(false);
                      }}
                    >
                      Limpar selecção
                    </button>
                  )}
                  <button
                    type="button"
                    className={BOTAO_PRIMARIO}
                    disabled={!podeComparar}
                    onClick={() => setAComparar(true)}
                  >
                    Comparar
                  </button>
                </div>
              }
            >
              <TabelaExperiencias
                experiencias={filtros.filtradas}
                onAbrir={onAbrir}
                seleccao={seleccao}
                onSeleccao={setSeleccao}
              />
            </Seccao>
          </div>
        );
      }}
    </Assincrono>
  );
}
