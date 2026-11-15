import { ExternalLink } from "lucide-react";

import { api } from "../api/client";
import { useAsync } from "../api/useAsync";
import type { Experiencia } from "../lib/experiencias";
import { comUnidade, SEM_VALOR } from "../lib/formato";
import type { CampoExtraido, Fonte, NomeCampo } from "../types/api";
import { AvisoVerificacao, TextoCitado } from "./Citacoes";
import { Assincrono, MarcaResultado, Selo } from "./ui";

const ROTULO_CAMPO: Record<NomeCampo, string> = {
  combustivel: "Combustível",
  ambiente: "Ambiente",
  concentracao_o2: "Concentração de O2",
  pressao: "Pressão",
  velocidade_escoamento: "Velocidade do escoamento",
  resultado_principal: "Resultado principal",
  resultado: "Resultado (categoria)",
};

function Bloco({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <section className="border-b border-linha px-4 py-3 last:border-b-0">
      <h3 className="mb-2 text-sm font-semibold text-texto">{titulo}</h3>
      {children}
    </section>
  );
}

/** Valor convertido e, se a unidade da fonte for outra, o valor original. */
function Grandeza({
  valor,
  unidade,
  campo,
}: {
  valor: number | null;
  unidade: string;
  campo?: CampoExtraido;
}) {
  const original = campo?.valor;
  const mostrarOriginal =
    valor !== null && original && campo?.unidade && campo.unidade !== unidade && campo.unidade !== "%";
  return (
    <>
      <span className="num text-texto">{comUnidade(valor, unidade)}</span>
      {mostrarOriginal && (
        <span className="ml-2 text-xs text-texto-3">
          na fonte: <span className="num">{original}</span>
        </span>
      )}
      {valor === null && campo?.motivo && (
        <span className="ml-2 text-xs text-texto-3">{campo.motivo}</span>
      )}
    </>
  );
}

/** Detalhe de uma experiência: condições, resultado, resumo da IA e fontes. */
export default function PainelExperiencia({
  experiencia: e,
  onAbrirFonte,
}: {
  experiencia: Experiencia;
  onAbrirFonte: (fonte: Fonte) => void;
}) {
  const resumo = useAsync(() => api.resumir(e.id), [e.id]);

  const fontes = (Object.keys(ROTULO_CAMPO) as NomeCampo[]).flatMap((nome) => {
    const c = e.campos[nome];
    return c?.valor && c.pagina !== null ? [{ nome, campo: c }] : [];
  });

  return (
    <div>
      <Bloco titulo="Condições experimentais">
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
          <dt className="text-texto-2">Combustível</dt>
          <dd className="text-texto">{e.combustivel ?? SEM_VALOR}</dd>
          <dt className="text-texto-2">Ambiente</dt>
          <dd className="text-texto">{e.ambiente ?? SEM_VALOR}</dd>
          <dt className="text-texto-2">Categoria</dt>
          <dd className="text-texto">{e.categoria}</dd>
          <dt className="text-texto-2">Concentração de O2</dt>
          <dd>
            <Grandeza valor={e.o2} unidade="% O2" campo={e.campos.concentracao_o2} />
          </dd>
          <dt className="text-texto-2">Pressão</dt>
          <dd>
            <Grandeza valor={e.pressao} unidade="kPa" campo={e.campos.pressao} />
          </dd>
          <dt className="text-texto-2">Escoamento</dt>
          <dd>
            <Grandeza valor={e.velocidade} unidade="cm/s" campo={e.campos.velocidade_escoamento} />
          </dd>
          <dt className="text-texto-2">Ano</dt>
          <dd className="num text-texto">{e.ano ?? SEM_VALOR}</dd>
        </dl>
      </Bloco>

      <Bloco titulo="Resultado">
        <MarcaResultado resultado={e.resultado} />
        <p className="mt-1 text-sm text-texto-2">
          {e.resultadoTexto ??
            e.campos.resultado_principal?.motivo ??
            "O documento não indica o resultado."}
        </p>
      </Bloco>

      <Bloco titulo="Resumo da IA">
        <Assincrono estado={resumo} esqueleto={<ResumoACarregar />}>
          {(r) =>
            r.fontes.length === 0 ? (
              <p className="text-sm text-texto-2">{r.resposta}</p>
            ) : (
              <div className="space-y-2">
                <Selo verificado={r.verificacao.fiavel} />
                <AvisoVerificacao verificacao={r.verificacao} />
                <TextoCitado resposta={r} onAbrirFonte={onAbrirFonte} />
              </div>
            )
          }
        </Assincrono>
      </Bloco>

      <Bloco titulo="Fontes">
        {fontes.length === 0 ? (
          <p className="text-sm text-texto-2">
            Nenhum campo desta experiência tem uma fonte com página.
          </p>
        ) : (
          <ul className="space-y-2">
            {fontes.map(({ nome, campo }) => (
              <li key={nome} className="border-l-2 border-linha-forte pl-3 text-sm">
                <p className="text-texto">
                  {ROTULO_CAMPO[nome]}
                  <span className="text-texto-2">
                    {" "}
                    · {e.titulo} · <span className="num">p. {campo.pagina}</span>
                  </span>
                </p>
                {campo.trecho && (
                  <p className="mt-0.5 text-xs leading-5 text-texto-2">{campo.trecho}</p>
                )}
              </li>
            ))}
          </ul>
        )}
        {e.url && (
          <a
            href={e.url}
            target="_blank"
            rel="noreferrer"
            className="mt-3 inline-flex items-center gap-1 text-sm text-chama underline underline-offset-2"
          >
            Abrir o documento
            <ExternalLink size={12} aria-hidden="true" />
          </a>
        )}
      </Bloco>
    </div>
  );
}

function ResumoACarregar() {
  return (
    <div className="space-y-2" role="status">
      <span className="sr-only">A carregar o resumo…</span>
      <div aria-hidden="true" className="h-4 w-full animate-pulse rounded-sm bg-superficie-2" />
      <div aria-hidden="true" className="h-4 w-5/6 animate-pulse rounded-sm bg-superficie-2" />
      <div aria-hidden="true" className="h-4 w-2/3 animate-pulse rounded-sm bg-superficie-2" />
    </div>
  );
}
