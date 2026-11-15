import { useEffect, useRef, useState } from "react";

import { api, NAO_ENCONTREI, perguntasExemplo } from "../api/client";
import { AvisoVerificacao, PainelFonte, TextoCitado } from "../components/Citacoes";
import { Esqueleto, EstadoErro, Selo } from "../components/ui";
import { BOTAO_PRIMARIO } from "../lib/formato";
import type { Fonte, Resposta } from "../types/api";

interface Troca {
  id: number;
  pergunta: string;
  estado:
    | { fase: "carregar" }
    | { fase: "erro"; erro: string }
    | { fase: "ok"; resposta: Resposta };
}

const ecraLargo = () => window.matchMedia("(min-width: 1024px)").matches;

export default function Assistente({
  onAbrirFonte,
}: {
  /** Abre a fonte na gaveta, usada quando não há espaço para a coluna lateral. */
  onAbrirFonte: (fonte: Fonte) => void;
}) {
  const [trocas, setTrocas] = useState<Troca[]>([]);
  const [texto, setTexto] = useState("");
  const [fonte, setFonte] = useState<Fonte | null>(null);
  const fim = useRef<HTMLDivElement>(null);
  const proximoId = useRef(1);

  const ocupado = trocas.some((t) => t.estado.fase === "carregar");

  useEffect(() => {
    fim.current?.scrollIntoView({ block: "nearest" });
  }, [trocas]);

  async function perguntar(pergunta: string) {
    const limpa = pergunta.trim();
    if (limpa.length < 2 || ocupado) return;

    const id = proximoId.current++;
    const definir = (estado: Troca["estado"]) =>
      setTrocas((ts) => ts.map((t) => (t.id === id ? { ...t, estado } : t)));

    setTrocas((ts) => [...ts, { id, pergunta: limpa, estado: { fase: "carregar" } }]);
    setTexto("");
    try {
      definir({ fase: "ok", resposta: await api.perguntar(limpa) });
    } catch (e) {
      definir({
        fase: "erro",
        erro: e instanceof Error ? e.message : "Ocorreu um erro inesperado.",
      });
    }
  }

  const abrir = (f: Fonte) => {
    setFonte(f);
    if (!ecraLargo()) onAbrirFonte(f);
  };

  return (
    <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
      <div className="flex min-h-[60vh] flex-col rounded-lg border border-linha bg-superficie">
        <div className="flex-1 space-y-5 p-4" aria-live="polite">
          {trocas.length === 0 && (
            <div className="mx-auto max-w-2xl py-6">
              <h2 className="text-sm font-semibold text-texto">
                Pergunta sobre segurança contra incêndios no espaço
              </h2>
              <p className="mt-1 text-sm text-texto-2">
                As respostas vêm só dos documentos indexados. Cada frase cita a
                fonte e é verificada antes de ser mostrada.
              </p>
              <ul className="mt-4 grid gap-2 sm:grid-cols-2">
                {perguntasExemplo.map((p) => (
                  <li key={p}>
                    <button
                      type="button"
                      onClick={() => void perguntar(p)}
                      className="h-full w-full rounded-md border border-linha-forte px-3 py-2 text-left text-sm text-texto hover:border-chama hover:bg-superficie-2"
                    >
                      {p}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {trocas.map((t) => (
            <article key={t.id} className="space-y-2">
              <h2 className="border-l-2 border-chama pl-3 text-sm font-medium text-texto">
                <span className="sr-only">Pergunta: </span>
                {t.pergunta}
              </h2>

              <div className="pl-3.5">
                {t.estado.fase === "carregar" && (
                  <div className="space-y-2" role="status">
                    <span className="sr-only">A procurar nos documentos…</span>
                    <Esqueleto className="h-4 w-full" />
                    <Esqueleto className="h-4 w-5/6" />
                    <Esqueleto className="h-4 w-1/2" />
                  </div>
                )}

                {t.estado.fase === "erro" && (
                  <EstadoErro
                    mensagem={t.estado.erro}
                    repetir={() => void perguntar(t.pergunta)}
                  />
                )}

                {t.estado.fase === "ok" &&
                  (t.estado.resposta.resposta.trim() === NAO_ENCONTREI ? (
                    <p className="text-sm text-texto-2">
                      {NAO_ENCONTREI} Tenta reformular a pergunta ou usar termos
                      que apareçam nos documentos.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      <AvisoVerificacao verificacao={t.estado.resposta.verificacao} />
                      <TextoCitado
                        resposta={t.estado.resposta}
                        onAbrirFonte={abrir}
                        onPreverFonte={setFonte}
                      />
                      <Selo verificado={t.estado.resposta.verificacao.fiavel} />
                    </div>
                  ))}
              </div>
            </article>
          ))}
          <div ref={fim} />
        </div>

        <form
          className="flex items-end gap-2 border-t border-linha p-3"
          onSubmit={(e) => {
            e.preventDefault();
            void perguntar(texto);
          }}
        >
          <label className="min-w-0 flex-1">
            <span className="sr-only">Pergunta</span>
            <textarea
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void perguntar(texto);
                }
              }}
              rows={2}
              placeholder="Escreve uma pergunta sobre os documentos"
              className="block w-full resize-y rounded-md border border-linha-forte bg-fundo px-2 py-1.5 text-sm text-texto placeholder:text-texto-3"
            />
          </label>
          <button
            type="submit"
            className={BOTAO_PRIMARIO}
            disabled={texto.trim().length < 2 || ocupado}
          >
            Perguntar
          </button>
        </form>
      </div>

      {/* Coluna da fonte: só em ecrãs largos; nos outros abre a gaveta. */}
      <aside
        aria-label="Trecho da fonte"
        className="sticky top-16 hidden rounded-lg border border-linha bg-superficie lg:block"
      >
        <h2 className="border-b border-linha px-4 py-2.5 text-sm font-semibold text-texto">
          Fonte{fonte && <span className="num ml-2 text-chama">{fonte.tag}</span>}
        </h2>
        {fonte ? (
          <PainelFonte fonte={fonte} />
        ) : (
          <p className="p-4 text-sm text-texto-2">
            Passa o cursor ou clica numa citação, por exemplo{" "}
            <span className="num text-texto">S1</span>, para ler aqui o trecho
            original da fonte.
          </p>
        )}
      </aside>
    </div>
  );
}
