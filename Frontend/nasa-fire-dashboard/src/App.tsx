import { useEffect, useState } from "react";
import {
  FileText,
  FlaskConical,
  LayoutGrid,
  ListChecks,
  MessageSquare,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Sun,
} from "lucide-react";

import { api, modoDemo } from "./api/client";
import { useAsync } from "./api/useAsync";
import { PainelFonte } from "./components/Citacoes";
import PainelExperiencia from "./components/PainelExperiencia";
import { Gaveta } from "./components/ui";
import { useFiltros } from "./hooks/useFiltros";
import { usePreferencia } from "./hooks/usePreferencia";
import { construirExperiencias } from "./lib/experiencias";
import type { Experiencia } from "./lib/experiencias";
import Assistente from "./pages/Assistente";
import Conclusoes from "./pages/Conclusoes";
import Experiencias from "./pages/Experiencias";
import Resumos from "./pages/Resumos";
import VisaoGeral from "./pages/VisaoGeral";
import type { Fonte } from "./types/api";

const PAGINAS = [
  { id: "visao-geral", rotulo: "Visão Geral", curto: "Visão", icone: LayoutGrid },
  { id: "experiencias", rotulo: "Experiências", curto: "Experiências", icone: FlaskConical },
  { id: "conclusoes", rotulo: "Conclusões", curto: "Conclusões", icone: ListChecks },
  { id: "resumos", rotulo: "Resumos", curto: "Resumos", icone: FileText },
  { id: "assistente", rotulo: "Assistente", curto: "Assistente", icone: MessageSquare },
] as const;

type PaginaId = (typeof PAGINAS)[number]["id"];

function lerPagina(): PaginaId {
  const id = window.location.hash.replace(/^#\/?/, "");
  return PAGINAS.find((p) => p.id === id)?.id ?? "visao-geral";
}

const SEM_EXPERIENCIAS: Experiencia[] = [];

const TEMAS = ["escuro", "claro"] as const;
const ESTADOS_MENU = ["aberto", "recolhido"] as const;

const temaDoSistema = () =>
  window.matchMedia("(prefers-color-scheme: light)").matches ? "claro" : "escuro";

/** Marca do produto: a chama esférica azul com a brasa âmbar ao centro. */
function Marca() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true" className="shrink-0">
      <circle cx="11" cy="11" r="8.5" fill="none" stroke="var(--color-chama)" strokeWidth="2" />
      <circle cx="11" cy="11" r="2.5" fill="var(--color-ambar)" />
    </svg>
  );
}

export default function App() {
  const [pagina, setPagina] = useState<PaginaId>(lerPagina);
  const [experienciaId, setExperienciaId] = useState<string | null>(null);
  const [fonte, setFonte] = useState<Fonte | null>(null);
  const [tema, setTema] = usePreferencia("cql-tema", TEMAS, temaDoSistema);
  const [menu, setMenu] = usePreferencia("cql-menu", ESTADOS_MENU, () => "aberto");
  const recolhido = menu === "recolhido";

  useEffect(() => {
    document.documentElement.dataset.tema = tema;
  }, [tema]);

  useEffect(() => {
    const aoMudar = () => setPagina(lerPagina());
    window.addEventListener("hashchange", aoMudar);
    return () => window.removeEventListener("hashchange", aoMudar);
  }, []);

  const dados = useAsync(async () => {
    const [documentos, extraccoes] = await Promise.all([
      api.documentos(),
      api.extraccoes(),
    ]);
    return { documentos, experiencias: construirExperiencias(documentos, extraccoes) };
  }, []);
  const conclusoes = useAsync(api.conclusoes, []);
  const saude = useAsync(api.saude, []);

  const experiencias = dados.fase === "ok" ? dados.dados.experiencias : SEM_EXPERIENCIAS;
  const filtros = useFiltros(experiencias);
  const experiencia = experiencias.find((e) => e.id === experienciaId) ?? null;
  const actual = PAGINAS.find((p) => p.id === pagina)!;

  useEffect(() => {
    document.title = `${actual.rotulo} · Chama em Queda Livre`;
  }, [actual.rotulo]);

  return (
    <div className={`min-h-screen bg-fundo text-texto ${recolhido ? "md:pl-14" : "md:pl-64"}`}>
      {/* Barra lateral: a partir de 768px */}
      <aside
        className={`fixed inset-y-0 left-0 hidden flex-col border-r border-linha bg-superficie md:flex ${
          recolhido ? "w-14" : "w-64"
        }`}
      >
        <div className="border-b border-linha">
          <div
            className={`flex h-12 items-center ${
              recolhido ? "justify-center" : "justify-between gap-2 pl-4 pr-2"
            }`}
          >
            {!recolhido && (
              <p className="flex min-w-0 items-center gap-2 text-sm font-semibold text-texto">
                <Marca />
                <span className="truncate">Chama em Queda Livre</span>
              </p>
            )}
            <button
              type="button"
              onClick={() => setMenu(recolhido ? "aberto" : "recolhido")}
              aria-expanded={!recolhido}
              aria-label={recolhido ? "Expandir o menu" : "Recolher o menu"}
              title={recolhido ? "Expandir o menu" : "Recolher o menu"}
              className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-texto-2 hover:bg-superficie-2 hover:text-texto"
            >
              {recolhido ? (
                <PanelLeftOpen size={16} aria-hidden="true" />
              ) : (
                <PanelLeftClose size={16} aria-hidden="true" />
              )}
            </button>
          </div>
          {recolhido ? (
            <p className="flex justify-center pb-3">
              <Marca />
              <span className="sr-only">Chama em Queda Livre</span>
            </p>
          ) : (
            <p className="px-4 pb-3 text-xs leading-4 text-texto-2">
              Combustão em microgravidade · dados abertos da NASA
            </p>
          )}
        </div>
        <nav aria-label="Principal" className="flex-1 py-2">
          <ul>
            {PAGINAS.map((p) => {
              const activa = p.id === pagina;
              return (
                <li key={p.id}>
                  <a
                    href={`#/${p.id}`}
                    aria-current={activa ? "page" : undefined}
                    title={recolhido ? p.rotulo : undefined}
                    className={`flex items-center gap-2.5 border-l-2 py-2 text-sm -outline-offset-2 ${
                      recolhido ? "justify-center px-0" : "px-4"
                    } ${
                      activa
                        ? "border-chama bg-superficie-2 font-medium text-texto"
                        : "border-transparent text-texto-2 hover:bg-superficie-2 hover:text-texto"
                    }`}
                  >
                    <p.icone size={16} aria-hidden="true" className="shrink-0" />
                    <span className={recolhido ? "sr-only" : ""}>{p.rotulo}</span>
                  </a>
                </li>
              );
            })}
          </ul>
        </nav>
      </aside>

      <header className="sticky top-0 z-10 flex h-12 items-center justify-between gap-3 border-b border-linha bg-fundo px-4">
        <p className="flex min-w-0 items-center gap-2 text-sm font-semibold md:hidden">
          <Marca />
          <span className="truncate">Chama em Queda Livre</span>
        </p>
        <h1 className="hidden text-sm font-semibold md:block">{actual.rotulo}</h1>

        <div className="flex shrink-0 items-center gap-2">
        {modoDemo ? (
          <p className="shrink-0 rounded-sm border border-linha-forte px-1.5 py-0.5 text-xs text-texto-2">
            <span className="sm:hidden">Demonstração</span>
            <span className="hidden sm:inline">Dados de demonstração</span>
          </p>
        ) : (
          saude.fase === "ok" &&
          saude.dados?.estado === "ok" && (
            <p className="flex shrink-0 items-center gap-1.5 text-xs text-texto-2">
              <svg width="8" height="8" viewBox="0 0 8 8" aria-hidden="true">
                <circle cx="4" cy="4" r="4" fill="var(--color-verde)" />
              </svg>
              Serviço ligado
              <span className="hidden sm:inline">
                {" "}
                · <span className="num text-texto">{saude.dados.documentos}</span> documentos
              </span>
            </p>
          )
        )}
          <button
            type="button"
            onClick={() => setTema(tema === "claro" ? "escuro" : "claro")}
            aria-label={tema === "claro" ? "Mudar para o modo escuro" : "Mudar para o modo claro"}
            title={tema === "claro" ? "Modo escuro" : "Modo claro"}
            className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-linha-forte text-texto-2 hover:bg-superficie-2 hover:text-texto"
          >
            {tema === "claro" ? (
              <Moon size={14} aria-hidden="true" />
            ) : (
              <Sun size={14} aria-hidden="true" />
            )}
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-[1400px] px-4 pt-4 pb-24 md:pb-6">
        <div className="mb-3 md:hidden">
          <h1 className="text-base font-semibold">{actual.rotulo}</h1>
          <p className="text-xs text-texto-2">
            Combustão em microgravidade · dados abertos da NASA
          </p>
        </div>

        {pagina === "visao-geral" && (
          <VisaoGeral
            dados={dados}
            conclusoes={conclusoes}
            filtros={filtros}
            onAbrir={setExperienciaId}
          />
        )}
        {pagina === "experiencias" && (
          <Experiencias dados={dados} filtros={filtros} onAbrir={setExperienciaId} />
        )}
        {pagina === "conclusoes" && (
          <Conclusoes conclusoes={conclusoes} onAbrirFonte={setFonte} />
        )}
        {pagina === "resumos" && <Resumos dados={dados} onAbrirFonte={setFonte} />}
        {pagina === "assistente" && <Assistente onAbrirFonte={setFonte} />}

        <footer className="mt-6 border-t border-linha pt-3 text-xs text-texto-3">
          Projecto independente, feito com dados abertos. Não é um produto oficial
          da NASA nem tem o seu aval.
          {modoDemo && " Os dados apresentados são de demonstração e não são resultados reais."}
        </footer>
      </main>

      {/* Barra inferior: abaixo de 768px */}
      <nav
        aria-label="Principal"
        className="fixed inset-x-0 bottom-0 z-20 border-t border-linha bg-superficie md:hidden"
      >
        <ul className="grid grid-cols-5">
          {PAGINAS.map((p) => {
            const activa = p.id === pagina;
            return (
              <li key={p.id}>
                <a
                  href={`#/${p.id}`}
                  aria-current={activa ? "page" : undefined}
                  className={`flex h-14 flex-col items-center justify-center gap-1 border-t-2 text-[10px] -outline-offset-2 ${
                    activa
                      ? "border-chama font-medium text-texto"
                      : "border-transparent text-texto-2"
                  }`}
                >
                  <p.icone size={18} aria-hidden="true" />
                  {p.curto}
                </a>
              </li>
            );
          })}
        </ul>
      </nav>

      {fonte ? (
        <Gaveta
          key={`fonte-${fonte.doc_id}-${fonte.tag}`}
          titulo={`Fonte ${fonte.tag}`}
          subtitulo="Trecho original"
          voltar={experiencia !== null}
          onFechar={() => setFonte(null)}
        >
          <PainelFonte fonte={fonte} />
        </Gaveta>
      ) : (
        experiencia && (
          <Gaveta
            key={`experiencia-${experiencia.id}`}
            titulo={experiencia.titulo}
            subtitulo={<span className="num">{experiencia.id}</span>}
            onFechar={() => setExperienciaId(null)}
          >
            <PainelExperiencia experiencia={experiencia} onAbrirFonte={setFonte} />
          </Gaveta>
        )
      )}
    </div>
  );
}
