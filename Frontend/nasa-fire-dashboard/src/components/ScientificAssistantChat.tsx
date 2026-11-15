import { useEffect, useRef, useState } from "react";
import {
  Bot,
  User,
  Send,
  Sparkles,
  LoaderCircle,
  Database,
  FlaskConical,
} from "lucide-react";

export interface ScientificSource {
  id: string;
  label: string;
}

export interface AssistantReply {
  content: string;
  sources?: ScientificSource[];
}

interface ChatMessage {
  id: string;
  role: "researcher" | "assistant";
  content: string;
  sources?: ScientificSource[];
}

interface ScientificAssistantChatProps {
  onAsk: (question: string) => Promise<AssistantReply>;
  onSourceClick?: (source: ScientificSource) => void;
  language?: "pt" | "en";
}

const suggestions = {
  pt: [
    "Quais experimentos tiveram maior anomalia térmica?",
    "Como o oxigénio influencia a combustão em microgravidade?",
    "Quais materiais apresentaram maior duração da chama?",
  ],
  en: [
    "Which experiments showed the highest thermal anomaly?",
    "How does oxygen affect combustion in microgravity?",
    "Which materials had the longest flame duration?",
  ],
};

const translations = {
  pt: {
    title: "Assistente Científico",
    subtitle: "NASA FIRE Research Assistant",
    welcome:
      "Olá! Sou o assistente científico do NASA FIRE. Posso ajudar-te a explorar experimentos, comparar resultados e compreender os dados de combustão em microgravidade.",
    suggestions: "SUGESTÕES DE PERGUNTAS",
    placeholder: "Pergunta algo sobre os experimentos...",
    send: "Enviar",
    analyzing: "Analisando dados...",
    sources: "Fontes / Experimentos citados",
    researcher: "Pesquisador",
    assistant: "Assistente IA",
    empty: "Escreve uma pergunta para começar a explorar os dados científicos.",
    error:
      "Não foi possível obter uma resposta neste momento. Verifica a ligação ao serviço de IA e tenta novamente.",
    footer: "As respostas devem ser verificadas nas fontes científicas originais.",
  },
  en: {
    title: "Scientific Assistant",
    subtitle: "NASA FIRE Research Assistant",
    welcome:
      "Hello! I am the NASA FIRE scientific assistant. I can help you explore experiments, compare results and understand combustion data in microgravity.",
    suggestions: "SUGGESTED QUESTIONS",
    placeholder: "Ask something about the experiments...",
    send: "Send",
    analyzing: "Analyzing data...",
    sources: "Sources / Cited Experiments",
    researcher: "Researcher",
    assistant: "AI Assistant",
    empty: "Write a question to start exploring the scientific data.",
    error:
      "Unable to get a response right now. Check the AI service connection and try again.",
    footer: "Answers should be verified against the original scientific sources.",
  },
};

// Renderização simples e segura de Markdown básico:
// **negrito**, listas com - ou * e parágrafos.
function FormattedMessage({ content }: { content: string }) {
  const lines = content.split("\n");

  function renderInline(text: string) {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);

    return parts.map((part, index) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={index} className="font-semibold text-white">
            {part.slice(2, -2)}
          </strong>
        );
      }

      return <span key={index}>{part}</span>;
    });
  }

  return (
    <div className="space-y-2 text-sm leading-7 text-slate-300">
      {lines.map((line, index) => {
        const trimmed = line.trim();

        if (!trimmed) {
          return <div key={index} className="h-1" />;
        }

        if (/^[-*]\s+/.test(trimmed)) {
          return (
            <div key={index} className="flex gap-2 pl-1">
              <span className="mt-0.5 text-cyan-400">•</span>
              <p>{renderInline(trimmed.replace(/^[-*]\s+/, ""))}</p>
            </div>
          );
        }

        if (/^\d+\.\s+/.test(trimmed)) {
          const match = trimmed.match(/^(\d+)\.\s+(.*)$/);

          return (
            <div key={index} className="flex gap-2 pl-1">
              <span className="text-cyan-400">{match?.[1]}.</span>
              <p>{renderInline(match?.[2] ?? trimmed)}</p>
            </div>
          );
        }

        return <p key={index}>{renderInline(line)}</p>;
      })}
    </div>
  );
}

export default function ScientificAssistantChat({
  onAsk,
  onSourceClick,
  language = "pt",
}: ScientificAssistantChatProps) {
  const t = translations[language];

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: t.welcome,
      sources: [],
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, loading]);

  async function sendMessage(question: string) {
    const cleanQuestion = question.trim();

    if (!cleanQuestion || loading) return;

    const researcherMessage: ChatMessage = {
      id: `researcher-${Date.now()}`,
      role: "researcher",
      content: cleanQuestion,
    };

    setMessages((previous) => [...previous, researcherMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await onAsk(cleanQuestion);

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.content,
        sources: response.sources ?? [],
      };

      setMessages((previous) => [...previous, assistantMessage]);
    } catch {
      setMessages((previous) => [
        ...previous,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: t.error,
        },
      ]);
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  }

  function handleKeyDown(
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendMessage(input);
    }
  }

  return (
    <section className="flex h-[680px] min-h-[500px] flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#0c1424] shadow-2xl">

      {/* HEADER */}
      <header className="flex items-center justify-between border-b border-white/10 px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400">
            <BrainIcon />
          </div>

          <div>
            <h2 className="text-sm font-semibold text-white">
              {t.title}
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              {t.subtitle}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          <span className="text-xs text-emerald-400">Online</span>
        </div>
      </header>

      {/* SUGGESTED QUESTIONS */}
      <div className="border-b border-white/10 px-5 py-4">
        <div className="mb-3 flex items-center gap-2">
          <Sparkles size={14} className="text-cyan-400" />
          <span className="text-[10px] font-bold tracking-[0.15em] text-slate-500">
            {t.suggestions}
          </span>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-1">
          {suggestions[language].map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              disabled={loading}
              onClick={() => void sendMessage(suggestion)}
              className="min-w-[210px] max-w-[260px] rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-left text-xs leading-5 text-slate-400 transition hover:border-cyan-500/40 hover:bg-cyan-500/5 hover:text-cyan-300 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      {/* MESSAGES */}
      <div
        className="flex-1 space-y-6 overflow-y-auto px-5 py-6"
        aria-live="polite"
      >
        {messages.map((message) => {
          const isResearcher = message.role === "researcher";

          return (
            <div
              key={message.id}
              className={`flex gap-3 ${
                isResearcher ? "flex-row-reverse" : "flex-row"
              }`}
            >
              <div
                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${
                  isResearcher
                    ? "bg-indigo-500/10 text-indigo-400"
                    : "bg-cyan-500/10 text-cyan-400"
                }`}
              >
                {isResearcher ? <User size={18} /> : <Bot size={18} />}
              </div>

              <div
                className={`max-w-[85%] ${
                  isResearcher ? "items-end" : "items-start"
                } flex flex-col`}
              >
                <span className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                  {isResearcher ? t.researcher : t.assistant}
                </span>

                <div
                  className={`rounded-2xl px-4 py-3 ${
                    isResearcher
                      ? "rounded-tr-sm border border-indigo-500/20 bg-indigo-500/10"
                      : "rounded-tl-sm border border-white/10 bg-[#142034]"
                  }`}
                >
                  {isResearcher ? (
                    <p className="whitespace-pre-wrap text-sm leading-6 text-slate-200">
                      {message.content}
                    </p>
                  ) : (
                    <FormattedMessage content={message.content} />
                  )}
                </div>

                {!isResearcher &&
                  (message.sources?.length ?? 0) > 0 && (
                    <div className="mt-3 w-full">
                      <p className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                        <Database size={13} />
                        {t.sources}
                      </p>

                      <div className="flex flex-wrap gap-2">
                        {message.sources?.map((source) => (
                          <button
                            key={source.id}
                            type="button"
                            onClick={() => onSourceClick?.(source)}
                            className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-500/20 bg-cyan-500/5 px-2.5 py-1.5 text-xs text-cyan-300 transition hover:border-cyan-400/50 hover:bg-cyan-500/10"
                          >
                            <FlaskConical size={12} />
                            {source.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
              </div>
            </div>
          );
        })}

        {/* LOADING INDICATOR */}
        {loading && (
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400">
              <Bot size={18} />
            </div>

            <div className="rounded-2xl rounded-tl-sm border border-white/10 bg-[#142034] px-4 py-3">
              <div className="flex items-center gap-2 text-xs text-cyan-300">
                <LoaderCircle size={15} className="animate-spin" />
                {t.analyzing}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* INPUT AREA */}
      <footer className="border-t border-white/10 bg-[#0a1220] p-4">
        {messages.length === 1 && (
          <p className="mb-3 text-center text-xs text-slate-600">
            {t.empty}
          </p>
        )}

        <div className="flex items-end gap-3 rounded-xl border border-white/10 bg-[#101a2b] p-2 transition focus-within:border-cyan-500/40">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t.placeholder}
            rows={1}
            disabled={loading}
            className="max-h-28 min-h-10 flex-1 resize-y bg-transparent px-3 py-2.5 text-sm text-white outline-none placeholder:text-slate-600 disabled:opacity-50"
          />

          <button
            type="button"
            onClick={() => void sendMessage(input)}
            disabled={!input.trim() || loading}
            aria-label={t.send}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-cyan-500 text-[#06111d] transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-30"
          >
            {loading ? (
              <LoaderCircle size={18} className="animate-spin" />
            ) : (
              <Send size={18} />
            )}
          </button>
        </div>

        <p className="mt-3 text-center text-[10px] text-slate-600">
          {t.footer}
        </p>
      </footer>
    </section>
  );
}

function BrainIcon() {
  return <Bot size={22} />;
}
