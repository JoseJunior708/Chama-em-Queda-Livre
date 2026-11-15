import { ExternalLink, TriangleAlert } from "lucide-react";

import type { EstadoFrase, Fonte, Frase, Resposta, Verificacao } from "../types/api";

const ROTULO_ESTADO: Record<EstadoFrase, string> = {
  apoiada: "Apoiada",
  sem_citacao: "Sem citação",
  numero_nao_encontrado: "Número não encontrado na fonte",
  nao_apoiada: "Não apoiada pela fonte",
};

type AoFonte = (fonte: Fonte) => void;

/** Divide o texto em troços, marcando os que correspondem a frases verificadas. */
function segmentar(r: Resposta): { texto: string; frase?: Frase }[] {
  const troços: { texto: string; frase?: Frase }[] = [];
  let cursor = 0;
  for (const frase of r.verificacao.frases) {
    const inicio = r.resposta.indexOf(frase.frase, cursor);
    if (inicio < 0) continue;
    if (inicio > cursor) troços.push({ texto: r.resposta.slice(cursor, inicio) });
    troços.push({ texto: frase.frase, frase });
    cursor = inicio + frase.frase.length;
  }
  if (cursor < r.resposta.length) troços.push({ texto: r.resposta.slice(cursor) });
  return troços;
}

/** Texto de uma resposta com as citações [S1] como chips e as frases não
    apoiadas sublinhadas. */
export function TextoCitado({
  resposta,
  onAbrirFonte,
  onPreverFonte,
}: {
  resposta: Resposta;
  onAbrirFonte: AoFonte;
  onPreverFonte?: AoFonte;
}) {
  const porTag = new Map(resposta.fontes.map((f) => [f.tag, f]));

  const comChips = (texto: string) =>
    texto.split(/(\[S\d+\])/g).map((parte, i) => {
      const tag = /^\[(S\d+)\]$/.exec(parte)?.[1];
      if (!tag) return parte;
      const fonte = porTag.get(tag);
      if (!fonte) return parte;
      return (
        <button
          key={i}
          type="button"
          onClick={() => onAbrirFonte(fonte)}
          onMouseEnter={() => onPreverFonte?.(fonte)}
          onFocus={() => onPreverFonte?.(fonte)}
          aria-label={`Fonte ${tag}: ${fonte.titulo}, página ${fonte.pagina}`}
          className="num mx-0.5 inline-flex h-5 items-center rounded-sm border border-chama bg-chama-fundo px-1 align-baseline text-xs text-chama hover:bg-superficie-2"
        >
          {tag}
        </button>
      );
    });

  return (
    <p className="whitespace-pre-wrap text-sm leading-6 text-texto">
      {segmentar(resposta).map((s, i) =>
        s.frase && s.frase.estado !== "apoiada" ? (
          <span
            key={i}
            title={`${ROTULO_ESTADO[s.frase.estado] ?? s.frase.estado}. ${s.frase.motivo}`}
            className="underline decoration-ambar decoration-wavy decoration-1 underline-offset-4"
          >
            {comChips(s.texto)}
            <span className="sr-only"> (frase não apoiada pelas fontes)</span>
          </span>
        ) : (
          <span key={i}>{comChips(s.texto)}</span>
        )
      )}
    </p>
  );
}

/** Faixa âmbar quando a verificação falha, com o motivo de cada frase. */
export function AvisoVerificacao({ verificacao }: { verificacao: Verificacao }) {
  if (verificacao.fiavel) return null;
  const falhas = verificacao.frases.filter((f) => f.estado !== "apoiada");

  return (
    <div
      role="note"
      className="border-l-2 border-ambar bg-ambar-fundo px-3 py-2 text-sm text-texto"
    >
      <p className="flex items-center gap-2 font-medium">
        <TriangleAlert size={14} className="shrink-0 text-ambar" aria-hidden="true" />
        Verificação falhou:{" "}
        <span>
          <span className="num">{falhas.length}</span> de{" "}
          <span className="num">{verificacao.frases.length}</span> frases sem apoio
          nas fontes. Estão sublinhadas no texto.
        </span>
      </p>
      {falhas.length > 0 && (
        <ul className="mt-1 space-y-0.5 pl-6 text-xs text-texto-2">
          {falhas.map((f) => (
            <li key={f.i}>
              Frase <span className="num">{f.i}</span>:{" "}
              {ROTULO_ESTADO[f.estado] ?? f.estado}
              {f.motivo ? `. ${f.motivo}` : ""}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** Lista de fontes como chips: etiqueta, documento e página. */
export function ChipsFontes({
  fontes,
  onAbrirFonte,
}: {
  fontes: Fonte[];
  onAbrirFonte: AoFonte;
}) {
  return (
    <ul className="flex flex-wrap gap-1.5">
      {fontes.map((f) => (
        <li key={f.tag} className="min-w-0 max-w-full">
          <button
            type="button"
            onClick={() => onAbrirFonte(f)}
            className="flex max-w-full items-center gap-1.5 rounded-sm border border-linha-forte px-1.5 py-0.5 text-xs text-texto-2 hover:bg-superficie-2 hover:text-texto"
          >
            <span className="num text-chama">{f.tag}</span>
            <span className="truncate">{f.titulo}</span>
            <span className="num shrink-0">p. {f.pagina}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}

/** Trecho original de uma fonte. */
export function PainelFonte({ fonte }: { fonte: Fonte }) {
  return (
    <div className="space-y-3 p-4 text-sm">
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
        <dt className="text-texto-2">Documento</dt>
        <dd className="text-texto">{fonte.titulo}</dd>
        <dt className="text-texto-2">Código</dt>
        <dd className="num text-texto">{fonte.doc_id}</dd>
        <dt className="text-texto-2">Página</dt>
        <dd className="num text-texto">{fonte.pagina}</dd>
      </dl>
      <div>
        <p className="mb-1 text-xs text-texto-2">
          Trecho original, tal como consta no documento
        </p>
        <blockquote className="border-l-2 border-linha-forte pl-3 leading-6 text-texto">
          {fonte.text}
        </blockquote>
      </div>
      {fonte.url && (
        <a
          href={fonte.url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-chama underline underline-offset-2"
        >
          Abrir o documento
          <ExternalLink size={12} aria-hidden="true" />
        </a>
      )}
    </div>
  );
}
