// Formas das respostas do Backend (ver Backend/README.md e Backend/app/api.py).

export interface Fonte {
  tag: string;
  doc_id: string;
  titulo: string;
  pagina: number;
  /** Trecho original do documento. */
  text: string;
  url: string | null;
}

export type EstadoFrase =
  | "apoiada"
  | "sem_citacao"
  | "numero_nao_encontrado"
  | "nao_apoiada";

export interface Frase {
  i: number;
  frase: string;
  fontes: string[];
  estado: EstadoFrase;
  motivo: string;
}

export interface Verificacao {
  fiavel: boolean;
  frases: Frase[];
}

/** Devolvida por /ask, /summarize e /compare. */
export interface Resposta {
  resposta: string;
  fontes: Fonte[];
  verificacao: Verificacao;
}

/** Uma conclusão é uma resposta com identificador e título. */
export interface Conclusao extends Resposta {
  id: string;
  titulo: string;
  /** Pergunta que deu origem à conclusão (só na API real). */
  pergunta?: string;
}

/** Elemento de /documents. */
export interface Documento {
  doc_id: string;
  titulo: string;
  ficheiro: string | null;
  paginas: number;
  chunks: number;
  categoria: string;
  categoria_origem: string;
  url: string | null;
  metadados: {
    ano?: number;
    autores?: string[];
    combustivel?: string[];
    ambiente?: string[];
    url?: string;
  } | null;
}

export interface CampoExtraido {
  valor: string | null;
  valor_numerico?: number | null;
  unidade?: string | null;
  pagina: number | null;
  fonte?: string | null;
  trecho?: string | null;
  motivo?: string | null;
}

export type NomeCampo =
  | "combustivel"
  | "ambiente"
  | "pressao"
  | "concentracao_o2"
  | "velocidade_escoamento"
  | "resultado_principal"
  /** Categoria fechada: "propagou" ou "extinguiu". */
  | "resultado";

/** Elemento de /extractions e resposta de /extract/{doc_id}. */
export interface Extraccao {
  doc_id: string;
  titulo: string;
  categoria: string;
  hash?: string;
  url?: string | null;
  campos: Partial<Record<NomeCampo, CampoExtraido>>;
}

/** Resposta de /health. */
export interface Saude {
  estado: string;
  documentos: number;
  chunks: number;
  embeddings: boolean;
  llm: boolean;
  modelo: string | null;
}
