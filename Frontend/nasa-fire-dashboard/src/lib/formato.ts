const formatador = new Intl.NumberFormat("pt-PT", {
  maximumFractionDigits: 1,
  useGrouping: false,
});

export const SEM_VALOR = "—";

/** Número com uma casa decimal no máximo; travessão quando não há valor. */
export function num(valor: number | null | undefined): string {
  return valor === null || valor === undefined ? SEM_VALOR : formatador.format(valor);
}

/** Número seguido da unidade, por exemplo "101,3 kPa". */
export function comUnidade(valor: number | null | undefined, unidade: string): string {
  return valor === null || valor === undefined ? SEM_VALOR : `${num(valor)} ${unidade}`;
}

// Classes partilhadas pelos controlos.
export const BOTAO =
  "inline-flex h-8 shrink-0 items-center gap-1.5 rounded-md border border-linha-forte px-3 text-sm text-texto hover:bg-superficie-2 disabled:cursor-not-allowed disabled:opacity-50";

export const BOTAO_PRIMARIO =
  "inline-flex h-8 shrink-0 items-center gap-1.5 rounded-md bg-chama px-3 text-sm font-medium text-sobre-chama hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50";

export const CAMPO =
  "h-8 rounded-md border border-linha-forte bg-fundo px-2 text-sm text-texto placeholder:text-texto-3";
