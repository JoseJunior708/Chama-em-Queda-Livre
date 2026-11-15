// Camada de acesso a dados. Com VITE_API_URL definido fala com o Backend;
// sem ele devolve os dados de demonstração, com a mesma forma.

import * as demo from "../data/demo";
import type {
  Conclusao,
  Documento,
  Extraccao,
  Resposta,
  Saude,
} from "../types/api";

const BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "");

export const modoDemo = !BASE;

async function pedir<T>(caminho: string, corpo?: unknown): Promise<T> {
  let r: Response;
  try {
    r = await fetch(`${BASE}${caminho}`, {
      method: corpo ? "POST" : "GET",
      headers: corpo ? { "Content-Type": "application/json" } : undefined,
      body: corpo ? JSON.stringify(corpo) : undefined,
    });
  } catch {
    throw new Error("Não foi possível contactar o serviço. Verifica a ligação e tenta de novo.");
  }
  if (!r.ok) {
    // O Backend responde sempre {"detail": "mensagem"} em caso de erro.
    const detalhe = await r
      .json()
      .then((j: { detail?: unknown }) => (typeof j.detail === "string" ? j.detail : null))
      .catch(() => null);
    throw new Error(detalhe ?? `O serviço respondeu com o erro ${r.status}.`);
  }
  return r.json() as Promise<T>;
}

// Pequeno atraso para os estados de carregamento serem visíveis na demonstração.
const ATRASO_MS = Number(import.meta.env.VITE_DEMO_ATRASO_MS ?? 250);
const simular = <T>(valor: T) =>
  new Promise<T>((resolver) => setTimeout(() => resolver(valor), ATRASO_MS));

export const api = {
  /** null em modo de demonstração: não há serviço para reportar. */
  saude: (): Promise<Saude | null> =>
    modoDemo ? Promise.resolve(null) : pedir<Saude>("/health"),

  documentos: (): Promise<Documento[]> =>
    modoDemo ? simular(demo.documentos) : pedir("/documents"),

  extraccoes: (): Promise<Extraccao[]> =>
    modoDemo ? simular(demo.extraccoes) : pedir("/extractions"),

  /** Conclusões já geradas; não chama o LLM. */
  conclusoes: (): Promise<Conclusao[]> =>
    modoDemo ? simular(demo.conclusoes) : pedir("/conclusions"),

  /** Gera as conclusões de novo (uma pergunta ao LLM por tema). */
  gerarConclusoes: (): Promise<Conclusao[]> =>
    modoDemo ? simular(demo.conclusoes) : pedir("/conclusions", {}),

  resumir: (doc_id: string): Promise<Resposta> =>
    modoDemo ? simular(demo.resumirDemo(doc_id)) : pedir("/summarize", { doc_id }),

  perguntar: (pergunta: string): Promise<Resposta> =>
    modoDemo ? simular(demo.perguntarDemo(pergunta)) : pedir("/ask", { pergunta }),
};

export const perguntasExemplo = demo.perguntasExemplo;
export const NAO_ENCONTREI = demo.NAO_ENCONTREI;
