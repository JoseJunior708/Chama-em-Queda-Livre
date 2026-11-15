import { useMemo, useState } from "react";
import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { RESULTADOS, ROTULO_RESULTADO } from "../lib/experiencias";
import type { Experiencia } from "../lib/experiencias";
import { comUnidade, num } from "../lib/formato";
import { EstadoVazio, FormaResultado, MarcaResultado, Seccao } from "./ui";

type EixoY = "velocidade" | "pressao";

const EIXOS: Record<EixoY, { rotulo: string; unidade: string }> = {
  velocidade: { rotulo: "Velocidade do escoamento", unidade: "cm/s" },
  pressao: { rotulo: "Pressão", unidade: "kPa" },
};

interface Ponto {
  o2: number;
  y: number;
  e: Experiencia;
}

const TICK = {
  fill: "var(--color-texto-2)",
  fontSize: 11,
  fontFamily: "var(--font-mono)",
};

function Marca({
  cx = 0,
  cy = 0,
  payload,
  eixo,
  onAbrir,
}: {
  cx?: number;
  cy?: number;
  payload?: Ponto;
  eixo: EixoY;
  onAbrir: (id: string) => void;
}) {
  if (!payload) return null;
  const { e, o2, y } = payload;
  return (
    <g
      className="ponto"
      tabIndex={0}
      role="button"
      aria-label={`${e.id}, ${e.titulo}: ${comUnidade(o2, "% O2")}, ${comUnidade(
        y,
        EIXOS[eixo].unidade
      )}, ${ROTULO_RESULTADO[e.resultado]}. Abrir experiência.`}
      onClick={() => onAbrir(e.id)}
      onKeyDown={(ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          onAbrir(e.id);
        }
      }}
    >
      <circle className="ponto-alvo" cx={cx} cy={cy} r={12} />
      <FormaResultado resultado={e.resultado} x={cx} y={cy} />
    </g>
  );
}

function Dica({
  active,
  payload,
  eixo,
}: {
  active?: boolean;
  payload?: { payload: Ponto }[];
  eixo: EixoY;
}) {
  const p = payload?.[0]?.payload;
  if (!active || !p) return null;
  return (
    <div className="max-w-64 rounded-md border border-linha-forte bg-superficie-2 p-2 text-xs">
      <p className="num text-texto-2">{p.e.id}</p>
      <p className="mb-1 font-medium text-texto">{p.e.titulo}</p>
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 text-texto-2">
        <dt>O2</dt>
        <dd className="num text-right text-texto">{comUnidade(p.o2, "% O2")}</dd>
        <dt>{EIXOS[eixo].rotulo}</dt>
        <dd className="num text-right text-texto">
          {comUnidade(p.y, EIXOS[eixo].unidade)}
        </dd>
      </dl>
      <div className="mt-1">
        <MarcaResultado resultado={p.e.resultado} />
      </div>
    </div>
  );
}

/** Dispersão de O2 contra pressão ou velocidade, um ponto por experiência. */
export default function MapaInflamabilidade({
  experiencias,
  onAbrir,
}: {
  experiencias: Experiencia[];
  onAbrir: (id: string) => void;
}) {
  const [eixo, setEixo] = useState<EixoY>("velocidade");

  const pontos = useMemo(
    () =>
      experiencias.flatMap((e): Ponto[] => {
        const y = e[eixo];
        return e.o2 === null || y === null ? [] : [{ o2: e.o2, y, e }];
      }),
    [experiencias, eixo]
  );

  const fora = experiencias.length - pontos.length;
  const { rotulo, unidade } = EIXOS[eixo];

  return (
    <Seccao
      titulo="Mapa de inflamabilidade"
      nota="um ponto por experiência"
      accoes={
        <div
          role="group"
          aria-label="Grandeza do eixo vertical"
          className="flex rounded-md border border-linha-forte p-px text-xs"
        >
          {(Object.keys(EIXOS) as EixoY[]).map((k) => (
            <button
              key={k}
              type="button"
              aria-pressed={eixo === k}
              onClick={() => setEixo(k)}
              className={`h-6 rounded-sm px-2 ${
                eixo === k
                  ? "bg-chama font-medium text-sobre-chama"
                  : "text-texto-2 hover:text-texto"
              }`}
            >
              {k === "velocidade" ? "Velocidade" : "Pressão"}
            </button>
          ))}
        </div>
      }
    >
      <ul className="flex flex-wrap gap-x-4 gap-y-1 px-4 pt-3" aria-label="Legenda">
        {RESULTADOS.map((r) => (
          <li key={r}>
            <MarcaResultado resultado={r} />
          </li>
        ))}
      </ul>

      {pontos.length === 0 ? (
        <EstadoVazio titulo="Nenhuma experiência para mostrar no mapa">
          Nenhuma das experiências filtradas tem concentração de O2 e{" "}
          {rotulo.toLowerCase()} em simultâneo.
        </EstadoVazio>
      ) : (
        <div className="h-80 w-full px-2 pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart
              accessibilityLayer={false}
              margin={{ top: 8, right: 16, bottom: 24, left: 12 }}
            >
              <CartesianGrid stroke="var(--color-linha)" />
              <XAxis
                type="number"
                dataKey="o2"
                domain={[
                  (min: number) => Math.floor((min - 1) / 5) * 5,
                  (max: number) => Math.ceil((max + 1) / 5) * 5,
                ]}
                tickCount={6}
                tick={TICK}
                tickLine={false}
                axisLine={{ stroke: "var(--color-linha-forte)" }}
                label={{
                  value: "Concentração de O2 (% O2)",
                  position: "insideBottom",
                  offset: -14,
                  fill: "var(--color-texto-2)",
                  fontSize: 12,
                }}
              />
              <YAxis
                type="number"
                dataKey="y"
                domain={[0, (max: number) => Math.ceil((max * 1.1) / 20) * 20]}
                tickCount={5}
                width={48}
                tick={TICK}
                tickLine={false}
                axisLine={{ stroke: "var(--color-linha-forte)" }}
                label={{
                  value: `${rotulo} (${unidade})`,
                  angle: -90,
                  position: "insideLeft",
                  style: { textAnchor: "middle" },
                  fill: "var(--color-texto-2)",
                  fontSize: 12,
                }}
              />
              <Tooltip
                cursor={false}
                isAnimationActive={false}
                content={<Dica eixo={eixo} />}
              />
              <Scatter
                data={pontos}
                isAnimationActive={false}
                shape={(p: unknown) => (
                  <Marca
                    {...(p as { cx?: number; cy?: number; payload?: Ponto })}
                    eixo={eixo}
                    onAbrir={onAbrir}
                  />
                )}
              />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      )}

      <p className="border-t border-linha px-4 py-2 text-xs text-texto-2">
        <span className="num text-texto">{num(pontos.length)}</span> de{" "}
        <span className="num">{num(experiencias.length)}</span> experiências no mapa.
        {fora > 0 && (
          <>
            {" "}
            <span className="num">{num(fora)}</span> sem O2 ou sem{" "}
            {rotulo.toLowerCase()} ficam só na tabela.
          </>
        )}{" "}
        Clica num ponto para abrir a experiência.
      </p>
    </Seccao>
  );
}
