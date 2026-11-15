import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { idiomaInicial, guardarIdioma, type Idioma } from "./index";
import en from "./en";
import pt from "./pt";

const TRADUCOES = { en, pt } as const;

type Traducoes = typeof en;

interface ContextoIdioma {
  idioma: Idioma;
  trocarIdioma: (i: Idioma) => void;
  t: Traducoes;
}

const Contexto = createContext<ContextoIdioma | null>(null);

export function ProvedorIdioma({ children }: { children: ReactNode }) {
  const [idioma, setIdioma] = useState<Idioma>(idiomaInicial);
  const [tradacoes, setTradacoes] = useState<Traducoes>(TRADUCOES[idioma]);

  useEffect(() => {
    setTradacoes(TRADUCOES[idioma]);
    document.documentElement.lang = idioma;
    document.documentElement.dir = "ltr";
  }, [idioma]);

  const trocar = useCallback((novo: Idioma) => {
    setIdioma(novo);
    guardarIdioma(novo);
  }, []);

  return (
    <Contexto.Provider value={{ idioma, trocarIdioma: trocar, t: tradacoes }}>
      {children}
    </Contexto.Provider>
  );
}

export function useIdioma(): ContextoIdioma {
  const ctx = useContext(Contexto);
  if (!ctx) throw new Error("useIdioma deve ser usado dentro de ProvedorIdioma");
  return ctx;
}

export function useT(): Traducoes {
  return useIdioma().t;
}