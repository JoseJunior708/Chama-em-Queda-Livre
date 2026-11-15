
import { useState } from "react";

import {
  Sparkles,
  Copy,
  Download,
  ChevronDown,
  ChevronUp,
  Check,
  BrainCircuit,
  FileText,
  Lightbulb,
} from "lucide-react";

export interface AiSummary {
  id: string;
  title: string;
  confidence: number;
  executiveSummary: string;
  keyFindings: string[];
  rawTechnicalDetails: string;
  source?: string;
  generatedAt?: string;
}

interface AiSummaryViewerProps {
  summary: AiSummary;
  language?: "pt" | "en";
}

export default function AiSummaryViewer({
  summary,
  language = "pt",
}: AiSummaryViewerProps) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const isPortuguese = language === "pt";

  // Impede que a barra ultrapasse os limites de 0 a 100%.
  const confidence = Math.min(
    100,
    Math.max(0, summary.confidence)
  );

  // Constrói o relatório em Markdown.
  const generateMarkdown = () => {
    return `# ${summary.title}

## ${isPortuguese ? "Confiança da IA" : "AI Confidence"}

${confidence}%

## ${isPortuguese ? "Resumo Executivo" : "Executive Summary"}

${summary.executiveSummary}

## ${isPortuguese ? "Principais Descobertas" : "Key Findings"}

${summary.keyFindings.map((finding) => `- ${finding}`).join("\n")}

## ${isPortuguese ? "Detalhes Técnicos" : "Technical Details"}

${summary.rawTechnicalDetails}

${summary.source ? `\n## Source\n${summary.source}` : ""}

${summary.generatedAt ? `\n${isPortuguese ? "Gerado em" : "Generated on"}: ${summary.generatedAt}` : ""}
`;
  };

  // Copiar o relatório.
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(generateMarkdown());
      setCopied(true);

      window.setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch (error) {
      console.error("Erro ao copiar o relatório:", error);
    }
  };

  // Exportar o relatório como ficheiro .md.
  const handleExport = () => {
    const markdown = generateMarkdown();

    const blob = new Blob([markdown], {
      type: "text/markdown;charset=utf-8",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = `nasa-ai-report-${summary.id}.md`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  return (
    <article className="group relative overflow-hidden rounded-2xl border border-cyan-500/20 bg-[#111827] shadow-[0_0_35px_rgba(6,182,212,0.04)] transition duration-300 hover:border-cyan-500/40">

      {/* DECORATIVE GLOW */}
      <div className="pointer-events-none absolute -right-20 -top-20 h-48 w-48 rounded-full bg-cyan-500/5 blur-3xl" />

      {/* HEADER */}
      <div className="relative flex flex-col justify-between gap-4 border-b border-slate-800 p-5 sm:flex-row sm:items-center">

        <div className="flex items-center gap-3">
          <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/10 p-3">
            <Sparkles className="h-5 w-5 text-cyan-400" />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
                NASA AI INSIGHTS
              </span>

              <span className="rounded-full border border-cyan-500/20 bg-cyan-500/10 px-2 py-0.5 text-[9px] font-semibold text-cyan-400">
                AI GENERATED
              </span>
            </div>

            <p className="mt-1 text-xs text-slate-500">
              {isPortuguese
                ? "Relatório de análise científica"
                : "Scientific analysis report"}
            </p>
          </div>
        </div>

        {/* QUICK ACTIONS */}
        <div className="flex flex-wrap items-center gap-2">

          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-2 rounded-lg border border-slate-700 bg-[#0B0F19] px-3 py-2 text-xs text-slate-300 transition hover:border-cyan-500/40 hover:text-cyan-400"
          >
            {copied ? (
              <Check size={14} className="text-emerald-400" />
            ) : (
              <Copy size={14} />
            )}

            {copied
              ? isPortuguese
                ? "Copiado!"
                : "Copied!"
              : isPortuguese
                ? "Copiar Resumo"
                : "Copy Summary"}
          </button>

          <button
            type="button"
            onClick={handleExport}
            className="flex items-center gap-2 rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3 py-2 text-xs text-cyan-400 transition hover:bg-cyan-500/20"
          >
            <Download size={14} />

            {isPortuguese
              ? "Exportar .md"
              : "Export .md"}
          </button>

          <button
            type="button"
            onClick={() => setExpanded((current) => !current)}
            aria-expanded={expanded}
            className="flex items-center gap-2 rounded-lg border border-slate-700 bg-[#0B0F19] px-3 py-2 text-xs text-slate-300 transition hover:border-cyan-500/40 hover:text-cyan-400"
          >
            {expanded ? (
              <ChevronUp size={14} />
            ) : (
              <ChevronDown size={14} />
            )}

            {isPortuguese
              ? expanded
                ? "Recolher detalhes"
                : "Detalhes técnicos"
              : expanded
                ? "Hide details"
                : "Technical details"}
          </button>
        </div>
      </div>

      {/* CONTENT */}
      <div className="relative space-y-6 p-5 sm:p-6">

        {/* TITLE */}
        <div>
          <div className="mb-2 flex items-center gap-2 text-xs text-slate-500">
            <BrainCircuit size={14} className="text-cyan-400" />

            {isPortuguese
              ? "Título do Insight"
              : "Insight Title"}
          </div>

          <h2 className="text-xl font-bold leading-relaxed text-white sm:text-2xl">
            {summary.title}
          </h2>
        </div>

        {/* CONFIDENCE */}
        <section className="rounded-xl border border-slate-800 bg-[#0B0F19]/70 p-4">

          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-medium text-slate-400">
                {isPortuguese
                  ? "Nível de Confiança da IA"
                  : "AI Confidence Level"}
              </p>

              <p className="mt-1 text-[10px] text-slate-600">
                {isPortuguese
                  ? "Confiança estimada pelo modelo"
                  : "Model-estimated confidence"}
              </p>
            </div>

            <span className="text-2xl font-bold tabular-nums text-cyan-400">
              {confidence}%
            </span>
          </div>

          <div
            className="h-2 overflow-hidden rounded-full bg-slate-800"
            role="progressbar"
            aria-label={
              isPortuguese
                ? "Confiança da IA"
                : "AI confidence"
            }
            aria-valuenow={confidence}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className="h-full rounded-full bg-gradient-to-r from-cyan-600 to-cyan-300 transition-all duration-700"
              style={{ width: `${confidence}%` }}
            />
          </div>
        </section>

        {/* EXECUTIVE SUMMARY */}
        <section>
          <div className="mb-3 flex items-center gap-2">
            <FileText size={16} className="text-cyan-400" />

            <h3 className="text-sm font-semibold text-white">
              {isPortuguese
                ? "Resumo Executivo"
                : "Executive Summary"}
            </h3>
          </div>

          <p className="text-sm leading-7 text-slate-400">
            {summary.executiveSummary}
          </p>
        </section>

        {/* KEY FINDINGS */}
        <section>
          <div className="mb-3 flex items-center gap-2">
            <Lightbulb size={16} className="text-cyan-400" />

            <h3 className="text-sm font-semibold text-white">
              {isPortuguese
                ? "Principais Descobertas"
                : "Key Findings"}
            </h3>
          </div>

          <ul className="space-y-3">
            {summary.keyFindings.map((finding, index) => (
              <li
                key={`${summary.id}-finding-${index}`}
                className="flex items-start gap-3 rounded-xl border border-slate-800/80 bg-[#0B0F19]/50 p-3"
              >
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10 text-xs font-semibold text-cyan-400">
                  {index + 1}
                </span>

                <p className="text-sm leading-6 text-slate-300">
                  {finding}
                </p>
              </li>
            ))}
          </ul>
        </section>

        {/* RAW TECHNICAL DETAILS */}
        {expanded && (
          <section className="animate-in fade-in slide-in-from-top-2 duration-300 rounded-xl border border-cyan-500/20 bg-[#080D17] p-4">

            <div className="mb-4 flex items-center gap-2">
              <DatabaseIcon />

              <h3 className="text-sm font-semibold text-cyan-400">
                {isPortuguese
                  ? "Dados Técnicos Brutos"
                  : "Raw Technical Data"}
              </h3>
            </div>

            <pre className="max-h-[400px] overflow-auto whitespace-pre-wrap break-words font-mono text-xs leading-6 text-slate-400">
              {summary.rawTechnicalDetails}
            </pre>
          </section>
        )}

        {/* FOOTER */}
        <div className="flex flex-col justify-between gap-2 border-t border-slate-800 pt-4 text-[10px] text-slate-600 sm:flex-row">
          <span>
            {summary.source
              ? `Source: ${summary.source}`
              : "MICROGRAVITY FIRE ANALYSIS"}
          </span>

          {summary.generatedAt && (
            <span>
              {isPortuguese ? "Gerado em" : "Generated on"}:{" "}
              {summary.generatedAt}
            </span>
          )}
        </div>
      </div>
    </article>
  );
}

function DatabaseIcon() {
  return <BrainCircuit size={16} className="text-cyan-400" />;
}
