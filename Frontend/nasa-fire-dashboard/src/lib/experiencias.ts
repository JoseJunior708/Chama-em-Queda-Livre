// Modelo de vista: junta /documents e /extractions numa linha por experiência,
// com as grandezas convertidas para unidades únicas (% O2, kPa, cm/s).

import type { CampoExtraido, Documento, Extraccao } from "../types/api";

export type Resultado = "propagou" | "extinguiu" | "sem_dado";

export const RESULTADOS: Resultado[] = ["propagou", "extinguiu", "sem_dado"];

export const ROTULO_RESULTADO: Record<Resultado, string> = {
  propagou: "Propagou",
  extinguiu: "Extinguiu",
  sem_dado: "Sem dado",
};

export interface Experiencia {
  id: string;
  titulo: string;
  ano: number | null;
  categoria: string;
  combustivel: string | null;
  ambiente: string | null;
  /** % O2 */
  o2: number | null;
  /** kPa */
  pressao: number | null;
  /** cm/s */
  velocidade: number | null;
  resultado: Resultado;
  resultadoTexto: string | null;
  url: string | null;
  campos: Extraccao["campos"];
}

const PARA_KPA: Record<string, number> = {
  kpa: 1,
  pa: 0.001,
  mpa: 1000,
  atm: 101.325,
  bar: 100,
  mbar: 0.1,
  psi: 6.894757,
  psia: 6.894757,
  torr: 0.133322,
  mmhg: 0.133322,
};

const PARA_CM_S: Record<string, number> = {
  "cm/s": 1,
  "m/s": 100,
  "mm/s": 0.1,
};

function converter(
  campo: CampoExtraido | undefined,
  tabela: Record<string, number>
): number | null {
  const v = campo?.valor_numerico;
  if (v === null || v === undefined || !campo?.unidade) return null;
  const factor = tabela[campo.unidade.trim().toLowerCase().replace(/\s+/g, "")];
  // Unidade desconhecida: mais vale "sem dado" do que um valor na escala errada.
  return factor === undefined ? null : v * factor;
}

function o2EmPercentagem(campo: CampoExtraido | undefined): number | null {
  const v = campo?.valor_numerico;
  if (v === null || v === undefined) return null;
  // Fracção molar (0 a 1) sem unidade passa a percentagem.
  return !campo?.unidade && v <= 1 ? v * 100 : v;
}

/** Recurso para extracções antigas, sem o campo categórico `resultado`:
    infere a categoria a partir do texto livre. */
export function classificarResultado(texto: string | null | undefined): Resultado {
  if (!texto) return "sem_dado";
  const t = texto.toLowerCase();
  if (/extin|apag|quench|blow-?off|did not (ignite|spread)|não (se )?propag/.test(t)) {
    return "extinguiu";
  }
  if (/propag|sustent|queimou|spread|sustain|burned/.test(t)) return "propagou";
  return "sem_dado";
}

export function construirExperiencias(
  documentos: Documento[],
  extraccoes: Extraccao[]
): Experiencia[] {
  const porId = new Map(documentos.map((d) => [d.doc_id, d]));

  return extraccoes.map((x) => {
    const doc = porId.get(x.doc_id);
    const c = x.campos;
    return {
      id: x.doc_id,
      titulo: x.titulo,
      ano: doc?.metadados?.ano ?? null,
      categoria: x.categoria,
      combustivel: c.combustivel?.valor ?? null,
      ambiente: c.ambiente?.valor ?? null,
      o2: o2EmPercentagem(c.concentracao_o2),
      pressao: converter(c.pressao, PARA_KPA),
      velocidade: converter(c.velocidade_escoamento, PARA_CM_S),
      resultado:
        c.resultado?.valor === "propagou" || c.resultado?.valor === "extinguiu"
          ? c.resultado.valor
          : c.resultado
            ? "sem_dado"
            : classificarResultado(c.resultado_principal?.valor),
      resultadoTexto: c.resultado_principal?.valor ?? null,
      url: x.url ?? doc?.url ?? null,
      campos: c,
    };
  });
}
