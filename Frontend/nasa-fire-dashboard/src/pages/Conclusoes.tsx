import { useState } from "react";
import { RefreshCw } from "lucide-react";

import { api, modoDemo } from "../api/client";
import type { AsyncComRepetir } from "../api/useAsync";
import { AvisoVerificacao, ChipsFontes, TextoCitado } from "../components/Citacoes";
import { Assincrono, EstadoErro, EstadoVazio, Selo } from "../components/ui";
import { BOTAO, BOTAO_PRIMARIO } from "../lib/formato";
import type { Conclusao, Fonte } from "../types/api";

/** Pede ao Backend para gerar as conclusões de novo. Só existe com a API real. */
function useGerar(aoTerminar: () => void) {
  const [aGerar, setAGerar] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function gerar() {
    setAGerar(true);
    setErro(null);
    try {
      await api.gerarConclusoes();
      aoTerminar();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Ocorreu um erro inesperado.");
    } finally {
      setAGerar(false);
    }
  }

  return { aGerar, erro, gerar };
}

export default function Conclusoes({
  conclusoes,
  onAbrirFonte,
}: {
  conclusoes: AsyncComRepetir<Conclusao[]>;
  onAbrirFonte: (fonte: Fonte) => void;
}) {
  const { aGerar, erro, gerar } = useGerar(conclusoes.repetir);

  const botaoGerar = (classe: string, rotulo: string) =>
    !modoDemo && (
      <button type="button" className={classe} onClick={() => void gerar()} disabled={aGerar}>
        <RefreshCw size={14} aria-hidden="true" className={aGerar ? "animate-spin" : ""} />
        <span aria-live="polite">{aGerar ? "A gerar…" : rotulo}</span>
      </button>
    );

  return (
    <div className="space-y-3">
      {erro && <EstadoErro mensagem={erro} repetir={() => void gerar()} />}

      <Assincrono estado={conclusoes}>
        {(todas) => {
          // Regra central do projecto: nenhuma conclusão sem fonte.
          const comFonte = todas.filter((c) => c.fontes.length > 0);

          if (comFonte.length === 0) {
            return (
              <div className="rounded-lg border border-linha bg-superficie">
                <EstadoVazio titulo="Ainda não há conclusões com fonte">
                  <p>
                    Só aparecem aqui conclusões apoiadas em pelo menos um documento.
                    {!modoDemo &&
                      " Gerar faz uma pergunta ao modelo por tema e pode demorar cerca de um minuto."}
                  </p>
                  <div className="mt-3 flex justify-center">
                    {botaoGerar(BOTAO_PRIMARIO, "Gerar conclusões")}
                  </div>
                </EstadoVazio>
              </div>
            );
          }

          const verificadas = comFonte.filter((c) => c.verificacao.fiavel).length;

          return (
            <>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm text-texto-2">
                  <span className="num text-texto">{verificadas}</span> de{" "}
                  <span className="num text-texto">{comFonte.length}</span> conclusões
                  verificadas frase a frase contra as fontes. Clica numa citação para
                  ler o trecho original.
                </p>
                {botaoGerar(BOTAO, "Gerar de novo")}
              </div>

              <ul className="space-y-3">
                {comFonte.map((c) => (
                  <li key={c.id} className="rounded-lg border border-linha bg-superficie">
                    <article className="space-y-3 p-4">
                      <header className="flex flex-wrap items-start justify-between gap-2">
                        <div className="min-w-0">
                          <h2 className="text-sm font-semibold text-texto">
                            <span className="num mr-2 font-normal text-texto-2">{c.id}</span>
                            {c.titulo}
                          </h2>
                          {c.pergunta && (
                            <p className="mt-0.5 text-xs text-texto-2">{c.pergunta}</p>
                          )}
                        </div>
                        <Selo verificado={c.verificacao.fiavel} />
                      </header>
                      <AvisoVerificacao verificacao={c.verificacao} />
                      <TextoCitado resposta={c} onAbrirFonte={onAbrirFonte} />
                      <ChipsFontes fontes={c.fontes} onAbrirFonte={onAbrirFonte} />
                    </article>
                  </li>
                ))}
              </ul>
            </>
          );
        }}
      </Assincrono>
    </div>
  );
}
