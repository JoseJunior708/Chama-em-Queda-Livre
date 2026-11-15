// DADOS DE DEMONSTRAÇÃO: o único sítio onde vivem.
//
// São sintéticos: servem para desenhar e testar a interface e não representam
// resultados da NASA. Tudo o que é exportado tem a forma exacta das respostas
// do Backend, por isso a troca pela API real faz-se em src/api/client.ts
// (variável VITE_API_URL) sem mexer nos componentes.

import type {
  CampoExtraido,
  Conclusao,
  Documento,
  EstadoFrase,
  Extraccao,
  Fonte,
  Resposta,
} from "../types/api";

export const NAO_ENCONTREI = "Não encontrei essa informação nos documentos.";

// ------------------------------------------------------------ experiências

type Linha = [
  doc_id: string,
  titulo: string,
  ano: number,
  categoria: string,
  combustivel: string,
  ambiente: string,
  o2: number | null,
  pressao: [valor: number, unidade: string] | null,
  velocidade: number | null,
  resultado: string | null,
];

const PROPAGOU = "A chama propagou-se ao longo de toda a amostra.";
const EXTINGUIU = "A chama extinguiu-se antes de percorrer a amostra.";

const LINHAS: Linha[] = [
  ["demo-001", "Propagação de chama em placas de PMMA com escoamento oposto", 2016, "Combustíveis sólidos", "PMMA", "Estação Espacial Internacional", 21, [101.3, "kPa"], 10, PROPAGOU],
  ["demo-002", "Limite de extinção de PMMA a baixa concentração de oxigénio", 2016, "Combustíveis sólidos", "PMMA", "Estação Espacial Internacional", 17, [101.3, "kPa"], 5, EXTINGUIU],
  ["demo-003", "PMMA em escoamento concorrente moderado", 2017, "Combustíveis sólidos", "PMMA", "Estação Espacial Internacional", 18, [1, "atm"], 20, PROPAGOU],
  ["demo-004", "Tecido de algodão e fibra de vidro em escoamento concorrente", 2018, "Segurança contra incêndios em naves", "Algodão e fibra de vidro", "Veículo de carga não tripulado", 20, [101.3, "kPa"], 20, PROPAGOU],
  ["demo-005", "Tecido de algodão e fibra de vidro perto do limite de escoamento", 2018, "Segurança contra incêndios em naves", "Algodão e fibra de vidro", "Veículo de carga não tripulado", 16, [101.3, "kPa"], 2, EXTINGUIU],
  ["demo-006", "Tecido de algodão e fibra de vidro a pressão reduzida", 2019, "Segurança contra incêndios em naves", "Algodão e fibra de vidro", "Veículo de carga não tripulado", 18, [70, "kPa"], 10, PROPAGOU],
  ["demo-007", "Extinção radiativa de gotas de heptano", 2012, "Gotas (droplets)", "Heptano", "Estação Espacial Internacional", 18, [1, "atm"], null, "A gota extinguiu-se por perdas radiativas antes de ser totalmente consumida."],
  ["demo-008", "Combustão de gotas de heptano em atmosfera enriquecida", 2013, "Gotas (droplets)", "Heptano", "Estação Espacial Internacional", 30, [101.3, "kPa"], null, "A gota queimou até ao fim."],
  ["demo-009", "Chama de difusão de metano em escoamento co-axial", 2020, "Chamas gasosas", "Metano", "Estação Espacial Internacional", 21, [96, "kPa"], 30, "A chama manteve-se estável e sustentada durante todo o ensaio."],
  ["demo-010", "Chama esférica de etileno a pressão reduzida", 2021, "Chamas gasosas", "Etileno", "Estação Espacial Internacional", 21, [50, "kPa"], 15, "A chama manteve-se sustentada até ao fim do ensaio."],
  ["demo-011", "Isolamento de fio em polietileno com escoamento oposto", 2015, "Combustíveis sólidos", "Polietileno", "Torre de queda livre", 22, [14.7, "psia"], 8, PROPAGOU],
  ["demo-012", "Isolamento de fio em polietileno a baixa concentração de oxigénio", 2015, "Combustíveis sólidos", "Polietileno", "Torre de queda livre", 15, [101.3, "kPa"], 5, EXTINGUIU],
  ["demo-013", "Tecido aramida em atmosfera de exploração", 2022, "Segurança contra incêndios em naves", "Aramida", "Voo parabólico", 30, [70, "kPa"], 10, null],
  ["demo-014", "Gotas de n-decano: ensaios preliminares", 2014, "Gotas (droplets)", "n-Decano", "Estação Espacial Internacional", 24, [1, "atm"], null, null],
  ["demo-015", "Esfera de PMMA em atmosfera de exploração", 2023, "Combustíveis sólidos", "PMMA", "Estação Espacial Internacional", 34, [56.5, "kPa"], 12, PROPAGOU],
  ["demo-016", "Tecido de algodão e fibra de vidro: extinção por sopro", 2019, "Segurança contra incêndios em naves", "Algodão e fibra de vidro", "Veículo de carga não tripulado", 14.5, [101.3, "kPa"], 30, "A chama extinguiu-se por sopro (blow-off)."],
];

// Documentos de contexto, sem dados experimentais extraídos.
const SO_DOCUMENTOS: [string, string, number][] = [
  ["demo-101", "Visão geral de um programa de combustão em microgravidade", 2015],
  ["demo-102", "Actas de um encontro sobre combustão em microgravidade", 1997],
  ["demo-103", "Revisão: inflamabilidade de materiais em naves espaciais", 2020],
];

const titulo = (doc_id: string) =>
  [...LINHAS, ...SO_DOCUMENTOS].find((l) => l[0] === doc_id)?.[1] ?? doc_id;

const campo = (
  valor: string,
  pagina: number,
  fonte: string,
  trecho: string,
  extra: Partial<CampoExtraido> = {}
): CampoExtraido => ({
  valor,
  pagina,
  fonte,
  trecho: `[Demo excerpt] ${trecho}`,
  motivo: null,
  ...extra,
});

const semValor = (numerico = false): CampoExtraido => ({
  valor: null,
  pagina: null,
  fonte: null,
  trecho: null,
  motivo: "Não consta nos trechos.",
  ...(numerico ? { valor_numerico: null, unidade: null } : {}),
});

export const documentos: Documento[] = [
  ...LINHAS.map(
    ([doc_id, tit, ano, categoria, combustivel, ambiente]): Documento => ({
      doc_id,
      titulo: tit,
      ficheiro: `${doc_id}.pdf`,
      paginas: 12,
      chunks: 30,
      categoria,
      categoria_origem: "metadados",
      url: null,
      metadados: { ano, combustivel: [combustivel], ambiente: [ambiente] },
    })
  ),
  ...SO_DOCUMENTOS.map(
    ([doc_id, tit, ano]): Documento => ({
      doc_id,
      titulo: tit,
      ficheiro: `${doc_id}.pdf`,
      paginas: 40,
      chunks: 110,
      categoria: "Outro",
      categoria_origem: "palavras-chave",
      url: null,
      metadados: { ano },
    })
  ),
];

export const extraccoes: Extraccao[] = LINHAS.map(
  ([doc_id, tit, , categoria, combustivel, ambiente, o2, pressao, vel, resultado]) => ({
    doc_id,
    titulo: tit,
    categoria,
    hash: `demo-${doc_id}`,
    url: null,
    campos: {
      combustivel: campo(combustivel, 2, "S1", `The fuel sample was ${combustivel}.`),
      ambiente: campo(ambiente, 2, "S1", `Tests were conducted in: ${ambiente}.`),
      concentracao_o2:
        o2 === null
          ? semValor(true)
          : campo(`${o2}%`, 4, "S2", `The ambient oxygen concentration was ${o2}% by volume.`, {
              valor_numerico: o2,
              unidade: "%",
            }),
      pressao:
        pressao === null
          ? semValor(true)
          : campo(`${pressao[0]} ${pressao[1]}`, 4, "S2", `Chamber pressure was held at ${pressao[0]} ${pressao[1]}.`, {
              valor_numerico: pressao[0],
              unidade: pressao[1],
            }),
      velocidade_escoamento:
        vel === null
          ? semValor(true)
          : campo(`${vel} cm/s`, 5, "S3", `The imposed flow velocity was ${vel} cm/s.`, {
              valor_numerico: vel,
              unidade: "cm/s",
            }),
      resultado_principal:
        resultado === null
          ? semValor()
          : campo(
              resultado,
              9,
              "S4",
              /extingu/.test(resultado)
                ? "The flame extinguished before the fuel was consumed."
                : "The flame was sustained for the full duration of the test."
            ),
      resultado:
        resultado === null
          ? semValor()
          : campo(
              /extingu/.test(resultado) ? "extinguiu" : "propagou",
              9,
              "S4",
              /extingu/.test(resultado)
                ? "The flame extinguished before the fuel was consumed."
                : "The flame was sustained for the full duration of the test."
            ),
    },
  })
);

// --------------------------------------------------- respostas com fontes

type F = [frase: string, tags: string[], estado?: EstadoFrase, motivo?: string];

function resp(frases: F[], fontes: Fonte[]): Resposta {
  const fr = frases.map(([frase, tags, estado = "apoiada", motivo = ""], i) => ({
    i: i + 1,
    frase,
    fontes: tags,
    estado,
    motivo,
  }));
  return {
    resposta: fr.map((x) => x.frase).join(" "),
    fontes,
    verificacao: { fiavel: fr.every((x) => x.estado === "apoiada"), frases: fr },
  };
}

const fonte = (tag: string, doc_id: string, pagina: number, text: string): Fonte => ({
  tag,
  doc_id,
  titulo: titulo(doc_id),
  pagina,
  text: `[Demo excerpt] ${text}`,
  url: null,
});

const semResposta: Resposta = {
  resposta: NAO_ENCONTREI,
  fontes: [],
  verificacao: { fiavel: true, frases: [] },
};

const limitePmma = resp(
  [
    ["Nas experiências com PMMA, a chama propagou-se a 21 % O2 e a 18 % O2 [S1][S2].", ["S1", "S2"]],
    ["A 17 % O2, com um escoamento de 5 cm/s, a chama extinguiu-se antes de percorrer a amostra [S3].", ["S3"]],
  ],
  [
    fonte("S1", "demo-001", 9, "At 21% oxygen the flame spread over the full length of the PMMA sample."),
    fonte("S2", "demo-003", 9, "At 18% oxygen and 20 cm/s the flame was sustained for the full test."),
    fonte("S3", "demo-002", 9, "At 17% oxygen and 5 cm/s the flame extinguished before reaching the end of the sample."),
  ]
);

const escoamentoTecidos = resp(
  [
    ["Em tecido de algodão e fibra de vidro, a chama extinguiu-se a 16 % O2 com um escoamento de 2 cm/s [S1].", ["S1"]],
    ["No extremo oposto, a 14,5 % O2 e 30 cm/s, a extinção deu-se por sopro [S2].", ["S2"]],
    ["A 20 % O2 e 20 cm/s a chama propagou-se por toda a amostra [S3].", ["S3"]],
  ],
  [
    fonte("S1", "demo-005", 9, "At 16% oxygen and a 2 cm/s flow the flame extinguished shortly after ignition."),
    fonte("S2", "demo-016", 9, "At 14.5% oxygen and 30 cm/s the flame was blown off."),
    fonte("S3", "demo-004", 9, "At 20% oxygen and 20 cm/s the flame spread over the full sample."),
  ]
);

const atmosferasExploracao = resp(
  [
    ["A 34 % O2 e 56,5 kPa, a chama propagou-se numa esfera de PMMA [S1].", ["S1"]],
    [
      "A velocidade de propagação foi 40 % superior à observada a 21 % O2 [S1].",
      ["S1"],
      "numero_nao_encontrado",
      "O número 40 não aparece no trecho citado.",
    ],
  ],
  [fonte("S1", "demo-015", 9, "At 34% oxygen and 56.5 kPa the flame was sustained over the PMMA sphere.")]
);

const gotasHeptano = resp(
  [
    ["A 18 % O2, a gota de heptano extinguiu-se por perdas radiativas antes de ser totalmente consumida [S1].", ["S1"]],
    ["A 30 % O2, a gota queimou até ao fim [S2].", ["S2"]],
  ],
  [
    fonte("S1", "demo-007", 9, "At 18% oxygen the droplet flame extinguished radiatively before burnout."),
    fonte("S2", "demo-008", 9, "At 30% oxygen the heptane droplet burned to completion."),
  ]
);

export const conclusoes: Conclusao[] = [
  { id: "C1", titulo: "Limite de oxigénio para a propagação em PMMA", ...limitePmma },
  { id: "C2", titulo: "O escoamento define dois limites de extinção em tecidos", ...escoamentoTecidos },
  { id: "C3", titulo: "Atmosferas de exploração com mais oxigénio", ...atmosferasExploracao },
  { id: "C4", titulo: "Gotas de heptano: extinção radiativa", ...gotasHeptano },
];

/** As 4 perguntas de exemplo do Assistente e as respostas de demonstração. */
export const respostasDemo: Record<string, Resposta> = {
  "Abaixo de que concentração de O2 deixa de haver propagação de chama em PMMA?": limitePmma,
  "Como é que a velocidade do escoamento afecta a extinção de chamas em tecidos?": escoamentoTecidos,
  "As atmosferas de exploração com mais O2 aumentam o risco de incêndio a bordo?": atmosferasExploracao,
  "Porque é que as gotas de heptano se extinguem em microgravidade?": gotasHeptano,
};

export const perguntasExemplo = Object.keys(respostasDemo);

export function perguntarDemo(pergunta: string): Resposta {
  return respostasDemo[pergunta.trim()] ?? semResposta;
}

/** Resumo de demonstração de um documento, construído a partir da extracção. */
export function resumirDemo(doc_id: string): Resposta {
  const c = extraccoes.find((e) => e.doc_id === doc_id)?.campos;
  if (!c) return semResposta;

  const f = (tag: string, cp?: CampoExtraido) =>
    fonte(tag, doc_id, cp?.pagina ?? 1, (cp?.trecho ?? "").replace("[Demo excerpt] ", ""));

  const frases: F[] = [
    [`A experiência usou ${c.combustivel?.valor} como combustível [S1].`, ["S1"]],
  ];
  const fontes = [f("S1", c.combustivel)];

  if (c.concentracao_o2?.valor) {
    frases.push([`A concentração de oxigénio foi de ${c.concentracao_o2.valor_numerico} % O2 [S2].`, ["S2"]]);
    fontes.push(f("S2", c.concentracao_o2));
  }
  if (c.resultado_principal?.valor) {
    frases.push([`${c.resultado_principal.valor.replace(/\.$/, "")} [S3].`, ["S3"]]);
    fontes.push(f("S3", c.resultado_principal));
  }
  return resp(frases, fontes);
}
