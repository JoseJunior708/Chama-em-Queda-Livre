import { useEffect, useState } from "react";

function ler<T extends string>(chave: string, validos: readonly T[], omissao: T): T {
  try {
    const valor = window.localStorage.getItem(chave);
    return validos.includes(valor as T) ? (valor as T) : omissao;
  } catch {
    // Armazenamento bloqueado (janela privada, por exemplo): usa a omissão.
    return omissao;
  }
}

/** Preferência do utilizador guardada no browser; funciona sem armazenamento. */
export function usePreferencia<T extends string>(
  chave: string,
  validos: readonly T[],
  omissao: () => T
) {
  const [valor, setValor] = useState<T>(() => ler(chave, validos, omissao()));

  useEffect(() => {
    try {
      window.localStorage.setItem(chave, valor);
    } catch {
      // Sem armazenamento, a preferência vale só para esta sessão.
    }
  }, [chave, valor]);

  return [valor, setValor] as const;
}
