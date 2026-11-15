
import { useState } from "react";

import {
  Activity,
  Atom,
  BrainCircuit,
  Database,
  FlaskConical,
  FileText,
  LayoutDashboard,
  ChevronRight,
  Languages,
  Sparkles,
} from "lucide-react";

import FilterBar from "./components/FilterBar";
import ExperimentComparisonChart from "./components/ExperimentComparisonChart";
import AiSummaryViewer from "./components/AiSummaryViewer";
import ScientificAssistantChat from "./components/ScientificAssistantChat";

import type { AiSummary } from "./components/AiSummaryViewer";
import type { AssistantReply } from "./components/ScientificAssistantChat";

import { useExperimentFilter } from "./hooks/useExperimentFilter";

import { comparisonDemo } from "./data/comparisonDemo";
import { mockNasaData } from "./data/mockNasa";

type Language = "pt" | "en";

type PageKey =
  | "overview"
  | "experiments"
  | "summaries"
  | "assistant";

// ======================================================
// DEMONSTRATION SUMMARY
// Replace this with summaries returned by the AI backend.
// ======================================================

const demoSummary: AiSummary = {
  id: "FIRE-001",

  title:
    "Influência da concentração de oxigénio na propagação da chama",

  confidence: 94,

  executiveSummary:
    "Esta análise demonstrativa explora a relação entre a concentração de oxigénio, a temperatura e o comportamento da chama em condições de microgravidade. Os resultados apresentados ilustram como o sistema poderá organizar e interpretar informação científica. Não representam uma conclusão oficial da NASA.",

  keyFindings: [
    "A concentração de oxigénio é uma variável importante na análise da combustão.",
    "As condições de microgravidade devem ser consideradas na comparação dos experimentos.",
    "A duração da chama pode ajudar a identificar diferenças entre condições experimentais.",
    "São necessários dados experimentais validados para sustentar conclusões científicas.",
  ],

  rawTechnicalDetails: `{
  "experiment_id": "FIRE-001",
  "environment": "Microgravity",
  "oxygen_concentration": "21%",
  "temperature_unit": "Kelvin",
  "analysis_method": "Comparative analysis",
  "validation": "Pending",
  "data_type": "Demonstration"
}`,

  source: "NASA experimental dataset (demo)",
  generatedAt: "15/11/2026",
};

// ======================================================
// NAVIGATION
// ======================================================

const navigation = [
  {
    id: "overview" as PageKey,
    label: "Visão Geral",
    labelEn: "Overview",
    icon: LayoutDashboard,
  },
  {
    id: "experiments" as PageKey,
    label: "Experimentos",
    labelEn: "Experiments",
    icon: FlaskConical,
  },
  {
    id: "summaries" as PageKey,
    label: "Summaries",
    labelEn: "Summaries",
    icon: FileText,
  },
  {
    id: "assistant" as PageKey,
    label: "Assistente IA",
    labelEn: "AI Assistant",
    icon: BrainCircuit,
  },
];

// ======================================================
// AI API CONNECTION
// ======================================================

async function handleScientificQuestion(
  question: string
): Promise<AssistantReply> {
  const response = await fetch("/api/ai/chat", {
    method: "POST",

    headers: {
      "Content-Type": "application/json",
    },

    body: JSON.stringify({
      question,
    }),
  });

  if (!response.ok) {
    throw new Error(
      `AI API error: ${response.status}`
    );
  }

  const data: AssistantReply = await response.json();

  return data;
}

// ======================================================
// MAIN APP
// ======================================================

function App() {
  const [activePage, setActivePage] =
    useState<PageKey>("overview");

  const [language, setLanguage] =
    useState<Language>("pt");

  const [collapsed, setCollapsed] =
    useState(false);

  // NASA DATA

  const { experiments, insights } = mockNasaData;

  // EXPERIMENT FILTERS

  const {
    search,
    setSearch,

    category,
    setCategory,

    status,
    setStatus,

    year,
    setYear,

    mission,
    setMission,

    categories,
    years,
    missions,
    statuses,

    filteredExperiments,
    hasActiveFilters,
    clearFilters,
  } = useExperimentFilter(experiments);

  // ====================================================
  // TRANSLATIONS
  // ====================================================

  const text = {
    pt: {
      subtitle:
        "Análise científica de combustão em microgravidade",

      overview: "Visão Geral",
      experiments: "Experimentos",
      summaries: "Summaries",
      assistant: "Assistente IA",

      total: "Total de Experimentos",
      completed: "Concluídos",
      processing: "Em Análise",
      pending: "Pendentes",

      experiment: "Experimento",
      mission: "Missão",
      material: "Material",
      temperature: "Temperatura",
      oxygen: "Oxigénio",
      status: "Estado",

      noResults: "Nenhum experimento encontrado.",

      insights: "Insights Científicos",

      chart: "Comparação de Experimentos",

      summariesDescription:
        "Relatórios, descobertas e interpretações produzidas pelo módulo de Inteligência Artificial.",

      assistantDescription:
        "Explore os dados científicos através de perguntas e respostas.",

      demo:
        "Dados demonstrativos. Não representam resultados oficiais da NASA.",
    },

    en: {
      subtitle:
        "Scientific analysis of combustion in microgravity",

      overview: "Overview",
      experiments: "Experiments",
      summaries: "Summaries",
      assistant: "AI Assistant",

      total: "Total Experiments",
      completed: "Completed",
      processing: "Processing",
      pending: "Pending",

      experiment: "Experiment",
      mission: "Mission",
      material: "Material",
      temperature: "Temperature",
      oxygen: "Oxygen",
      status: "Status",

      noResults: "No experiments found.",

      insights: "Scientific Insights",

      chart: "Experiment Comparison",

      summariesDescription:
        "Reports, findings and interpretations produced by the Artificial Intelligence module.",

      assistantDescription:
        "Explore scientific data through questions and answers.",

      demo:
        "Demonstration data. These are not official NASA findings.",
    },
  }[language];

  // ====================================================
  // KPI METRICS
  // ====================================================

  const totalExperiments = experiments.length;

  const completedExperiments = experiments.filter(
    (item) => item.status === "completed"
  ).length;

  const processingExperiments = experiments.filter(
    (item) => item.status === "processing"
  ).length;

  const pendingExperiments = experiments.filter(
    (item) => item.status === "pending"
  ).length;

  const metrics = [
    {
      label: text.total,
      value: totalExperiments,
      icon: Database,
    },
    {
      label: text.completed,
      value: completedExperiments,
      icon: Activity,
    },
    {
      label: text.processing,
      value: processingExperiments,
      icon: FlaskConical,
    },
    {
      label: text.pending,
      value: pendingExperiments,
      icon: Atom,
    },
  ];

  // ====================================================
  // STATUS LABELS AND COLORS
  // ====================================================

  const statusLabels: Record<string, string> = {
    completed: text.completed,
    processing: text.processing,
    pending: text.pending,
  };

  const statusStyles: Record<string, string> = {
    completed:
      "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",

    processing:
      "bg-amber-500/10 text-amber-400 border-amber-500/20",

    pending:
      "bg-slate-500/10 text-slate-400 border-slate-500/20",
  };

  // ====================================================
  // CURRENT PAGE TITLE
  // ====================================================

  const currentPageTitle =
    navigation.find(
      (item) => item.id === activePage
    )?.[language === "pt" ? "label" : "labelEn"] ??
    text.overview;

  // ====================================================
  // RENDER
  // ====================================================

  return (
    <div className="min-h-screen bg-[#080d18] text-slate-100">

      <div className="flex min-h-screen">

        {/* ============================================
            SIDEBAR
        ============================================ */}

        <aside
          className={`${
            collapsed ? "w-20" : "w-64"
          } hidden md:flex flex-col border-r border-white/10 bg-[#0c1424] transition-all duration-300`}
        >

          {/* BRAND */}

          <div className="flex h-20 items-center gap-3 border-b border-white/10 px-5">

            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400">
              <FlaskConical size={22} />
            </div>

            {!collapsed && (
              <div>
                <h1 className="text-sm font-bold tracking-wide">
                  NASA FIRE
                </h1>

                <p className="text-xs text-slate-500">
                  Research Dashboard
                </p>
              </div>
            )}

          </div>

          {/* NAVIGATION */}

          <nav className="flex-1 space-y-2 p-3">

            {!collapsed && (
              <p className="px-3 pb-2 pt-4 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">
                {language === "pt"
                  ? "Menu Principal"
                  : "Main Menu"}
              </p>
            )}

            {navigation.map((item) => {

              const Icon = item.icon;

              const active =
                activePage === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() =>
                    setActivePage(item.id)
                  }
                  title={
                    collapsed
                      ? language === "pt"
                        ? item.label
                        : item.labelEn
                      : undefined
                  }
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm transition ${
                    active
                      ? "border border-cyan-500/20 bg-cyan-500/10 text-cyan-400"
                      : "text-slate-400 hover:bg-white/5 hover:text-white"
                  }`}
                >

                  <Icon size={19} />

                  {!collapsed && (
                    <span>
                      {language === "pt"
                        ? item.label
                        : item.labelEn}
                    </span>
                  )}

                  {!collapsed && active && (
                    <ChevronRight
                      className="ml-auto"
                      size={16}
                    />
                  )}

                </button>
              );
            })}

          </nav>

          {/* COLLAPSE SIDEBAR */}

          <div className="border-t border-white/10 p-3">

            <button
              onClick={() =>
                setCollapsed(!collapsed)
              }
              className="w-full rounded-xl px-3 py-3 text-left text-xs text-slate-500 hover:bg-white/5 hover:text-white"
            >
              {collapsed
                ? "→"
                : language === "pt"
                  ? "← Recolher menu"
                  : "← Collapse menu"}
            </button>

          </div>

        </aside>

        {/* ============================================
            MAIN CONTENT
        ============================================ */}

        <main className="min-w-0 flex-1">

          {/* HEADER */}

          <header className="flex min-h-20 flex-wrap items-center justify-between gap-4 border-b border-white/10 bg-[#0c1424]/80 px-5 py-4 md:px-8">

            <div>
              <h2 className="text-xl font-bold">
                {currentPageTitle}
              </h2>

              <p className="mt-1 text-xs text-slate-500">
                {text.subtitle}
              </p>
            </div>

            <div className="flex items-center gap-3">

              {/* LANGUAGE */}

              <button
                onClick={() =>
                  setLanguage(
                    language === "pt" ? "en" : "pt"
                  )
                }
                className="flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-xs text-slate-300 hover:bg-white/5"
              >
                <Languages size={16} />

                {language === "pt" ? "PT" : "EN"}
              </button>

              {/* SYSTEM STATUS */}

              <div className="hidden items-center gap-2 rounded-xl border border-white/10 px-3 py-2 sm:flex">

                <span className="h-2 w-2 rounded-full bg-emerald-400" />

                <span className="text-xs text-slate-400">
                  {language === "pt"
                    ? "Sistema Online"
                    : "System Online"}
                </span>

              </div>

            </div>

          </header>

          {/* ==========================================
              PAGE CONTENT
          ========================================== */}

          <div className="space-y-8 p-5 md:p-8">

            {/* ========================================
                OVERVIEW
            ======================================== */}

            {activePage === "overview" && (

              <section className="space-y-8">

                {/* KPI CARDS */}

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

                  {metrics.map((metric) => {

                    const Icon = metric.icon;

                    return (
                      <div
                        key={metric.label}
                        className="rounded-2xl border border-white/10 bg-[#101a2b] p-5"
                      >

                        <div className="flex items-center justify-between">

                          <p className="text-sm text-slate-400">
                            {metric.label}
                          </p>

                          <Icon
                            className="text-cyan-400"
                            size={20}
                          />

                        </div>

                        <p className="mt-4 text-3xl font-bold">
                          {metric.value}
                        </p>

                      </div>
                    );
                  })}

                </div>

                {/* EXPERIMENT TABLE */}

                <div className="space-y-4">

                  <div>
                    <h3 className="text-lg font-semibold">
                      {text.experiments}
                    </h3>

                    <p className="mt-1 text-sm text-slate-500">
                      {language === "pt"
                        ? "Pesquisa e filtragem dos dados experimentais."
                        : "Search and filter experimental data."}
                    </p>
                  </div>

                  {/* FILTER BAR */}

                  <FilterBar
                    language={language}
                    search={search}
                    setSearch={setSearch}
                    category={category}
                    setCategory={setCategory}
                    status={status}
                    setStatus={setStatus}
                    year={year}
                    setYear={setYear}
                    mission={mission}
                    setMission={setMission}
                    categories={categories}
                    years={years}
                    missions={missions}
                    statuses={statuses}
                    hasActiveFilters={hasActiveFilters}
                    clearFilters={clearFilters}
                  />

                  {/* TABLE */}

                  <div className="overflow-x-auto rounded-2xl border border-white/10 bg-[#101a2b]">

                    <table className="w-full min-w-[850px] text-left text-sm">

                      <thead className="border-b border-white/10 bg-white/[0.02] text-xs uppercase text-slate-500">

                        <tr>
                          <th className="px-5 py-4">
                            {text.experiment}
                          </th>

                          <th className="px-5 py-4">
                            {text.mission}
                          </th>

                          <th className="px-5 py-4">
                            {text.material}
                          </th>

                          <th className="px-5 py-4">
                            {text.temperature}
                          </th>

                          <th className="px-5 py-4">
                            {text.oxygen}
                          </th>

                          <th className="px-5 py-4">
                            {text.status}
                          </th>
                        </tr>

                      </thead>

                      <tbody className="divide-y divide-white/5">

                        {filteredExperiments.map(
                          (experiment) => (

                            <tr
                              key={experiment.id}
                              className="hover:bg-white/[0.02]"
                            >

                              <td className="px-5 py-4 font-medium text-white">

                                {experiment.title}

                                <p className="mt-1 text-xs text-slate-500">
                                  {experiment.id}
                                </p>

                              </td>

                              <td className="px-5 py-4 text-slate-400">
                                {experiment.mission}
                              </td>

                              <td className="px-5 py-4 text-slate-400">
                                {experiment.material}
                              </td>

                              <td className="px-5 py-4 text-slate-300">
                                {experiment.temperature} K
                              </td>

                              <td className="px-5 py-4 text-slate-300">
                                {experiment.oxygenConcentration}%
                              </td>

                              <td className="px-5 py-4">

                                <span
                                  className={`rounded-full border px-3 py-1 text-xs ${
                                    statusStyles[
                                      experiment.status
                                    ] ?? statusStyles.pending
                                  }`}
                                >
                                  {statusLabels[
                                    experiment.status
                                  ] ?? experiment.status}
                                </span>

                              </td>

                            </tr>

                          )
                        )}

                        {filteredExperiments.length === 0 && (

                          <tr>
                            <td
                              colSpan={6}
                              className="px-5 py-10 text-center text-slate-500"
                            >
                              {text.noResults}
                            </td>
                          </tr>

                        )}

                      </tbody>

                    </table>

                  </div>

                </div>

                {/* SCIENTIFIC INSIGHTS */}

                <div>

                  <h3 className="mb-4 text-lg font-semibold">
                    {text.insights}
                  </h3>

                  <div className="grid gap-4 md:grid-cols-2">

                    {insights.map((insight, index) => (

                      <div
                        key={index}
                        className="rounded-2xl border border-white/10 bg-[#101a2b] p-5"
                      >

                        <div className="mb-3 flex items-center gap-2 text-cyan-400">

                          <Sparkles size={18} />

                          <span className="text-xs font-semibold uppercase tracking-wider">
                            Insight
                          </span>

                        </div>

                        <p className="font-medium text-slate-200">
                          {insight.title}
                        </p>

                        <p className="mt-2 text-sm leading-6 text-slate-400">
                          {insight.description}
                        </p>

                      </div>

                    ))}

                  </div>

                </div>

              </section>

            )}

            {/* ========================================
                EXPERIMENTS
            ======================================== */}

            {activePage === "experiments" && (

              <section className="space-y-6">

                <div>
                  <h3 className="text-lg font-semibold">
                    {text.chart}
                  </h3>

                  <p className="mt-1 text-sm text-slate-500">
                    {language === "pt"
                      ? "Compare as variáveis dos experimentos científicos."
                      : "Compare scientific experiment variables."}
                  </p>
                </div>

                <ExperimentComparisonChart
                  experiments={comparisonDemo}
                  language={language}
                />

              </section>

            )}

            {/* ========================================
                SUMMARIES
            ======================================== */}

            {activePage === "summaries" && (

              <section className="space-y-6">

                <div className="flex items-center gap-3">

                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400">
                    <BrainCircuit size={24} />
                  </div>

                  <div>

                    <h3 className="text-lg font-semibold">
                      {language === "pt"
                        ? "Relatórios e Descobertas Científicas"
                        : "Scientific Reports and Discoveries"}
                    </h3>

                    <p className="mt-1 text-sm text-slate-500">
                      {text.summariesDescription}
                    </p>

                  </div>

                </div>

                <AiSummaryViewer
                  summary={demoSummary}
                  language={language}
                />

              </section>

            )}

            {/* ========================================
                SCIENTIFIC AI ASSISTANT
            ======================================== */}

            {activePage === "assistant" && (

              <section className="space-y-6">

                <div>

                  <h3 className="text-lg font-semibold">
                    {language === "pt"
                      ? "Assistente Científico IA"
                      : "AI Scientific Assistant"}
                  </h3>

                  <p className="mt-1 text-sm text-slate-500">
                    {text.assistantDescription}
                  </p>

                </div>

                <ScientificAssistantChat
                  language={language}
                  onAsk={handleScientificQuestion}
                  onSourceClick={(source) => {

                    setSearch(source.id);

                    setActivePage("overview");

                  }}
                />

              </section>

            )}

            {/* ========================================
                FOOTER
            ======================================== */}

            <footer className="border-t border-white/10 pt-5">

              <p className="text-center text-xs text-slate-600">
                NASA FIRE Dashboard · {text.demo}
              </p>

            </footer>

          </div>

        </main>

      </div>

    </div>
  );
}

export default App;
