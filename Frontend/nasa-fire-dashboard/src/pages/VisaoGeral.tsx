import type { AsyncComRepetir } from "../api/useAsync";
import BarrasCombustivel from "../components/BarrasCombustivel";
import Filtros from "../components/Filtros";
import MapaInflamabilidade from "../components/MapaInflamabilidade";
import TabelaExperiencias from "../components/TabelaExperiencias";
import { Esqueleto, EstadoErro, EstadoVazio, Seccao } from "../components/ui";
import type { EstadoFiltros } from "../hooks/useFiltros";
import type { Experiencia } from "../lib/experiencias";
import { num, SEM_VALOR } from "../lib/formato";
import type { Conclusao, Documento } from "../types/api";

export interface DadosBase {
  documentos: Documento[];
  experiencias: Experiencia[];
}

function Indicadores({
  dados,
  conclusoes,
}: {
  dados: DadosBase;
  conclusoes: AsyncComRepetir<Conclusao[]>;
}) {
  const { experiencias, documentos } = dados;
  const o2 = experiencias.flatMap((e) => (e.o2 === null ? [] : [e.o2]));
  const combustiveis = new Set(experiencias.map((e) => e.combustivel).filter(Boolean));

  const frases =
    conclusoes.fase === "ok" ? conclusoes.dados.flatMap((c) => c.verificacao.frases) : [];
  const apoiadas = frases.filter((f) => f.estado === "apoiada").length;

  const itens: { rotulo: string; valor: string; unidade?: string }[] = [
    { rotulo: "Experiências indexadas", valor: num(experiencias.length) },
    { rotulo: "Combustíveis cobertos", valor: num(combustiveis.size) },
    {
      rotulo: "Intervalo de O2 estudado",
      valor: o2.length ? `${num(Math.min(...o2))}–${num(Math.max(...o2))}` : SEM_VALOR,
      unidade: o2.length ? "% O2" : undefined,
    },
    { rotulo: "Documentos-fonte", valor: num(documentos.length) },
    {
      rotulo: "Afirmações verificadas pela IA",
      valor: frases.length ? num((apoiadas / frases.length) * 100) : SEM_VALOR,
      unidade: frases.length ? `% (${apoiadas} de ${frases.length})` : undefined,
    },
  ];

  return (
    <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-linha bg-linha sm:grid-cols-3 lg:grid-cols-5">
      {itens.map((i) => (
        <div key={i.rotulo} className="flex flex-col-reverse bg-superficie px-4 py-3 last:col-span-2 lg:last:col-span-1">
          <dt className="text-xs text-texto-2">{i.rotulo}</dt>
          <dd className="num text-xl font-medium text-texto">
            {i.valor}
            {i.unidade && <span className="ml-1 text-xs font-normal text-texto-2">{i.unidade}</span>}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export default function VisaoGeral({
  dados,
  conclusoes,
  filtros,
  onAbrir,
}: {
  dados: AsyncComRepetir<DadosBase>;
  conclusoes: AsyncComRepetir<Conclusao[]>;
  filtros: EstadoFiltros;
  onAbrir: (id: string) => void;
}) {
  if (dados.fase === "carregar") {
    return (
      <div className="space-y-4" role="status">
        <span className="sr-only">A carregar a visão geral…</span>
        <Esqueleto className="h-[4.5rem] w-full" />
        <Esqueleto className="h-8 w-full" />
        <div className="grid gap-4 lg:grid-cols-[1fr_20rem]">
          <Esqueleto className="h-96" />
          <Esqueleto className="h-96" />
        </div>
        <Esqueleto className="h-64 w-full" />
      </div>
    );
  }

  if (dados.fase === "erro") {
    return <EstadoErro mensagem={dados.erro} repetir={dados.repetir} />;
  }

  const total = dados.dados.experiencias.length;

  if (total === 0) {
    return (
      <div className="rounded-lg border border-linha bg-superficie">
        <EstadoVazio titulo="Ainda não há experiências indexadas">
          Os documentos já indexados aparecem aqui depois de os dados experimentais
          serem extraídos.
        </EstadoVazio>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Indicadores dados={dados.dados} conclusoes={conclusoes} />

      <Filtros filtros={filtros} total={total} />

      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <MapaInflamabilidade experiencias={filtros.filtradas} onAbrir={onAbrir} />
        <BarrasCombustivel
          experiencias={filtros.filtradas}
          seleccionado={filtros.f.combustivel}
          onSeleccionar={(c) => filtros.definir("combustivel", c)}
        />
      </div>

      <Seccao titulo="Experiências" nota="os mesmos filtros do mapa">
        <TabelaExperiencias experiencias={filtros.filtradas} onAbrir={onAbrir} />
      </Seccao>
    </div>
  );
}
