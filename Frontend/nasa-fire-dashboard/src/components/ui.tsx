import { useEffect, useRef } from "react";
import type { ReactNode } from "react";
import { ArrowLeft, CircleAlert, CircleCheck, TriangleAlert, X } from "lucide-react";

import type { AsyncComRepetir } from "../api/useAsync";
import { ROTULO_RESULTADO } from "../lib/experiencias";
import type { Resultado } from "../lib/experiencias";
import { BOTAO } from "../lib/formato";

// ------------------------------------------------------------------ estados

export function Esqueleto({ className = "" }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded-sm bg-superficie-2 ${className}`}
    />
  );
}

export function EsqueletoLinhas({ linhas = 4 }: { linhas?: number }) {
  return (
    <div className="space-y-2 p-4" role="status">
      <span className="sr-only">A carregar…</span>
      {Array.from({ length: linhas }, (_, i) => (
        <Esqueleto key={i} className={`h-4 ${i % 3 === 2 ? "w-2/3" : "w-full"}`} />
      ))}
    </div>
  );
}

export function EstadoVazio({
  titulo,
  children,
}: {
  titulo: string;
  children?: ReactNode;
}) {
  return (
    <div className="px-4 py-10 text-center">
      <p className="text-sm font-medium text-texto">{titulo}</p>
      {children && (
        <div className="mx-auto mt-1 max-w-md text-sm text-texto-2">{children}</div>
      )}
    </div>
  );
}

export function EstadoErro({
  mensagem,
  repetir,
}: {
  mensagem: string;
  repetir?: () => void;
}) {
  return (
    <div
      role="alert"
      className="flex flex-wrap items-center gap-3 border-l-2 border-ambar bg-ambar-fundo px-4 py-3 text-sm"
    >
      <TriangleAlert size={16} className="shrink-0 text-ambar" aria-hidden="true" />
      <p className="min-w-0 flex-1 text-texto">
        <span className="font-medium">Erro.</span> {mensagem}
      </p>
      {repetir && (
        <button type="button" onClick={repetir} className={BOTAO}>
          Tentar de novo
        </button>
      )}
    </div>
  );
}

/** Mostra esqueleto, erro ou o conteúdo, conforme a fase do pedido. */
export function Assincrono<T>({
  estado,
  esqueleto,
  children,
}: {
  estado: AsyncComRepetir<T>;
  esqueleto?: ReactNode;
  children: (dados: T) => ReactNode;
}) {
  if (estado.fase === "carregar") return <>{esqueleto ?? <EsqueletoLinhas />}</>;
  if (estado.fase === "erro") {
    return <EstadoErro mensagem={estado.erro} repetir={estado.repetir} />;
  }
  return <>{children(estado.dados)}</>;
}

// ------------------------------------------------------------------ painel

export function Seccao({
  titulo,
  nota,
  accoes,
  children,
  className = "",
}: {
  titulo: string;
  nota?: ReactNode;
  accoes?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-lg border border-linha bg-superficie ${className}`}>
      <header className="flex min-h-10 flex-wrap items-center justify-between gap-x-3 gap-y-1 border-b border-linha px-4 py-1.5">
        <div className="flex min-w-0 flex-wrap items-baseline gap-x-2">
          <h2 className="text-sm font-semibold text-texto">{titulo}</h2>
          {nota && <span className="text-xs text-texto-3">{nota}</span>}
        </div>
        {accoes}
      </header>
      {children}
    </section>
  );
}

// ---------------------------------------------------------------- resultado

/** Marca do resultado, centrada em (x, y). A forma muda com o resultado,
    para o significado não depender da cor. */
export function FormaResultado({
  resultado,
  x,
  y,
}: {
  resultado: Resultado;
  x: number;
  y: number;
}) {
  if (resultado === "propagou") {
    return (
      <circle
        cx={x}
        cy={y}
        r={5}
        fill="var(--color-chama)"
        stroke="var(--color-superficie)"
        strokeWidth={2}
      />
    );
  }
  if (resultado === "extinguiu") {
    return (
      <rect
        x={x - 4}
        y={y - 4}
        width={8}
        height={8}
        fill="var(--color-superficie)"
        stroke="var(--color-texto)"
        strokeWidth={2}
      />
    );
  }
  return (
    <path
      d={`M${x - 4} ${y - 4}L${x + 4} ${y + 4}M${x + 4} ${y - 4}L${x - 4} ${y + 4}`}
      stroke="var(--color-texto-3)"
      strokeWidth={2}
      strokeLinecap="round"
    />
  );
}

export function MarcaResultado({ resultado }: { resultado: Resultado }) {
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap text-sm text-texto">
      <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
        <FormaResultado resultado={resultado} x={7} y={7} />
      </svg>
      {ROTULO_RESULTADO[resultado]}
    </span>
  );
}

// --------------------------------------------------------------------- selo

export function Selo({ verificado }: { verificado: boolean }) {
  return verificado ? (
    <span className="inline-flex shrink-0 items-center gap-1 rounded-sm border border-verde bg-verde-fundo px-1.5 py-0.5 text-xs font-medium text-verde">
      <CircleCheck size={12} aria-hidden="true" />
      Verificado
    </span>
  ) : (
    <span className="inline-flex shrink-0 items-center gap-1 rounded-sm border border-ambar bg-ambar-fundo px-1.5 py-0.5 text-xs font-medium text-ambar">
      <CircleAlert size={12} aria-hidden="true" />
      Por verificar
    </span>
  );
}

// ------------------------------------------------------------------- gaveta

/** Painel lateral modal: fecha com Escape, prende e devolve o foco. */
export function Gaveta({
  titulo,
  subtitulo,
  onFechar,
  voltar = false,
  children,
}: {
  titulo: ReactNode;
  subtitulo?: ReactNode;
  onFechar: () => void;
  /** O painel abriu por cima de outro: o botão passa a "Voltar". */
  voltar?: boolean;
  children: ReactNode;
}) {
  const painel = useRef<HTMLDivElement>(null);
  const fechar = useRef(onFechar);

  useEffect(() => {
    fechar.current = onFechar;
  });

  useEffect(() => {
    const anterior = document.activeElement as HTMLElement | null;
    painel.current?.querySelector<HTMLElement>("button")?.focus();

    function tecla(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.stopPropagation();
        fechar.current();
        return;
      }
      if (e.key !== "Tab" || !painel.current) return;
      const focaveis = painel.current.querySelectorAll<HTMLElement>(
        'button, a[href], input, select, textarea, summary, [tabindex="0"]'
      );
      if (focaveis.length === 0) return;
      const primeiro = focaveis[0];
      const ultimo = focaveis[focaveis.length - 1];
      if (e.shiftKey && document.activeElement === primeiro) {
        e.preventDefault();
        ultimo.focus();
      } else if (!e.shiftKey && document.activeElement === ultimo) {
        e.preventDefault();
        primeiro.focus();
      }
    }

    document.addEventListener("keydown", tecla);
    return () => {
      document.removeEventListener("keydown", tecla);
      if (anterior?.isConnected) anterior.focus();
    };
  }, []);

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <div
        className="absolute inset-0 bg-fundo/70"
        onClick={onFechar}
        aria-hidden="true"
      />
      <div
        ref={painel}
        role="dialog"
        aria-modal="true"
        aria-label={typeof titulo === "string" ? titulo : "Detalhe"}
        className="relative flex h-full w-full max-w-md flex-col border-l border-linha bg-superficie"
      >
        <header className="flex items-start gap-3 border-b border-linha px-4 py-3">
          <button
            type="button"
            onClick={onFechar}
            className="mt-0.5 inline-flex h-7 shrink-0 items-center gap-1 rounded-md border border-linha-forte px-2 text-xs text-texto hover:bg-superficie-2"
          >
            {voltar ? (
              <ArrowLeft size={14} aria-hidden="true" />
            ) : (
              <X size={14} aria-hidden="true" />
            )}
            {voltar ? "Voltar" : "Fechar"}
          </button>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-texto">{titulo}</p>
            {subtitulo && <p className="text-xs text-texto-2">{subtitulo}</p>}
          </div>
        </header>
        <div className="flex-1 overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
