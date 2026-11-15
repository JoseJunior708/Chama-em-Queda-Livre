// Sistema de tradução: inglês padrão, português opcional.
// Sem dependências. As chaves são estáveis; os textos mudam com o idioma.

export type Idioma = "en" | "pt";

const IDIOMAS: Idioma[] = ["en", "pt"];

const DETECTADO = (): Idioma => {
  try {
    const guardado = window.localStorage.getItem("cql-idioma") as Idioma | null;
    if (guardado && IDIOMAS.includes(guardado)) return guardado;
  } catch { /* sem armazenamento */ }
  // Inglês é o idioma principal (padrão). O português só é usado
  // quando o utilizador o escolhe explicitamente e fica guardado no localStorage.
  return "en";
};

/** Estado do idioma: lê do localStorage (ou navigator) e guarda. */
export function idiomaInicial(): Idioma {
  return DETECTADO();
}

export function guardarIdioma(idioma: Idioma): void {
  try {
    window.localStorage.setItem("cql-idioma", idioma);
  } catch { /* sem armazenamento */ }
}

export { default as en } from "./en";
export { default as pt } from "./pt";