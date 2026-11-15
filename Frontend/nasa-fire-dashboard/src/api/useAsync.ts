import { useCallback, useEffect, useState } from "react";

export type Async<T> =
  | { fase: "carregar" }
  | { fase: "erro"; erro: string }
  | { fase: "ok"; dados: T };

export type AsyncComRepetir<T> = Async<T> & { repetir: () => void };

/** Corre `fn` quando `deps` mudam e expõe os estados carregar, erro e ok. */
export function useAsync<T>(
  fn: () => Promise<T>,
  deps: unknown[]
): AsyncComRepetir<T> {
  const [estado, setEstado] = useState<Async<T>>({ fase: "carregar" });
  const [tentativa, setTentativa] = useState(0);

  useEffect(() => {
    let activo = true;
    setEstado({ fase: "carregar" });
    fn().then(
      (dados) => activo && setEstado({ fase: "ok", dados }),
      (e: unknown) =>
        activo &&
        setEstado({
          fase: "erro",
          erro: e instanceof Error ? e.message : "Ocorreu um erro inesperado.",
        })
    );
    return () => {
      activo = false;
    };
    // `fn` é recriada a cada render; quem chama controla a repetição por `deps`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tentativa]);

  const repetir = useCallback(() => setTentativa((n) => n + 1), []);

  return { ...estado, repetir };
}
