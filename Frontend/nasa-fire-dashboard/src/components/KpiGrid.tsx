
import { useEffect, useState } from "react";

import {
  FlaskConical,
  ShieldAlert,
  BrainCircuit,
  RadioTower,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";

// ==========================================
// 1. TYPESCRIPT INTERFACES
// ==========================================

type TrendStatus = "positive" | "negative" | "neutral";

interface KpiItem {
  id: string;
  title: string;
  value: string;
  variation: number;
  trend: TrendStatus;
  description: string;
  icon: React.ElementType;
  iconColor: string;
  iconBackground: string;
}

interface KpiGridProps {
  data?: KpiItem[];
  loading?: boolean;
}

// ==========================================
// 2. MOCK DATA
// ==========================================

const mockKpis: KpiItem[] = [
  {
    id: "experiments",
    title: "Experimentos Analisados",
    value: "248",
    variation: 12.5,
    trend: "positive",
    description: "Experimentos processados",
    icon: FlaskConical,
    iconColor: "text-cyan-400",
    iconBackground: "bg-cyan-400/10",
  },
  {
    id: "success",
    title: "Sucesso / Anomalias",
    value: "94.2%",
    variation: 2.1,
    trend: "negative",
    description: "Taxa de sucesso experimental",
    icon: ShieldAlert,
    iconColor: "text-red-400",
    iconBackground: "bg-red-400/10",
  },
  {
    id: "accuracy",
    title: "Precisão do Modelo IA",
    value: "96.8%",
    variation: 1.8,
    trend: "positive",
    description: "Precisão na validação do modelo",
    icon: BrainCircuit,
    iconColor: "text-violet-400",
    iconBackground: "bg-violet-400/10",
  },
  {
    id: "telemetry",
    title: "Última Telemetria",
    value: "14:32:08",
    variation: 0,
    trend: "neutral",
    description: "Último registo recebido",
    icon: RadioTower,
    iconColor: "text-amber-400",
    iconBackground: "bg-amber-400/10",
  },
];

// ==========================================
// 3. SKELETON LOADING
// ==========================================

function KpiSkeleton() {
  return (
    <div className="animate-pulse rounded-2xl border border-slate-800 bg-[#111827] p-5">

      <div className="flex items-center justify-between">
        <div className="h-11 w-11 rounded-xl bg-slate-700/60" />
        <div className="h-5 w-16 rounded bg-slate-700/60" />
      </div>

      <div className="mt-5 h-4 w-36 rounded bg-slate-700/60" />

      <div className="mt-3 h-9 w-28 rounded bg-slate-700/60" />

      <div className="mt-4 h-3 w-40 rounded bg-slate-700/60" />

    </div>
  );
}

// ==========================================
// 4. KPI CARD
// ==========================================

function KpiCard({ item }: { item: KpiItem }) {

  const Icon = item.icon;

  const trendConfig = {
    positive: {
      icon: TrendingUp,
      color: "text-emerald-400",
      label: "+",
    },
    negative: {
      icon: TrendingDown,
      color: "text-red-400",
      label: "-",
    },
    neutral: {
      icon: Minus,
      color: "text-slate-400",
      label: "",
    },
  };

  const trend = trendConfig[item.trend];
  const TrendIcon = trend.icon;

  return (
    <article className="
      group relative overflow-hidden
      rounded-2xl border border-slate-800
      bg-[#111827] p-5
      transition-all duration-300
      hover:-translate-y-1
      hover:border-cyan-500/30
      hover:shadow-lg hover:shadow-cyan-950/20
    ">

      {/* TOP SECTION */}

      <div className="flex items-center justify-between">

        <div className={`rounded-xl p-3 ${item.iconBackground}`}>
          <Icon size={21} className={item.iconColor} />
        </div>

        <div className={`flex items-center gap-1 text-xs font-semibold ${trend.color}`}>

          <TrendIcon size={14} />

          {item.trend === "neutral"
            ? "Estável"
            : `${trend.label}${item.variation}%`}

        </div>

      </div>

      {/* KPI INFORMATION */}

      <div className="mt-5">

        <p className="text-sm font-medium text-slate-400">
          {item.title}
        </p>

        <h3 className="mt-2 text-3xl font-bold tracking-tight text-white">
          {item.value}
        </h3>

        <p className="mt-3 text-xs text-slate-500">
          {item.description}
        </p>

      </div>

      {/* DECORATIVE ELEMENT */}

      <div className="
        absolute -bottom-8 -right-8
        h-24 w-24 rounded-full
        bg-cyan-500/5 blur-2xl
        transition group-hover:bg-cyan-500/10
      " />

    </article>
  );
}

// ==========================================
// 5. MAIN COMPONENT
// ==========================================

export default function KpiGrid({
  data,
  loading,
}: KpiGridProps) {

  const [isLoading, setIsLoading] = useState(
    loading ?? true
  );

  // Simulate asynchronous API request
  useEffect(() => {

    if (loading !== undefined) {
      setIsLoading(loading);
      return;
    }

    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1500);

    return () => clearTimeout(timer);

  }, [loading]);

  const kpis = data ?? mockKpis;

  return (
    <section className="space-y-4">

      {/* SECTION HEADER */}

      <div className="flex items-center justify-between">

        <div>
          <h2 className="text-lg font-semibold text-white">
            Indicadores Científicos
          </h2>

          <p className="mt-1 text-xs text-slate-500">
            Monitorização e análise dos dados da missão
          </p>
        </div>

        <span className="
          rounded-full border border-cyan-500/20
          bg-cyan-500/10 px-3 py-1
          text-[10px] font-semibold uppercase
          tracking-wider text-cyan-400
        ">
          Mission KPIs
        </span>

      </div>

      {/* RESPONSIVE GRID */}

      <div className="
        grid grid-cols-1 gap-4
        sm:grid-cols-2
        xl:grid-cols-4
      ">

        {isLoading
          ? Array.from({ length: 4 }).map((_, index) => (
              <KpiSkeleton key={index} />
            ))
          : kpis.map((item) => (
              <KpiCard key={item.id} item={item} />
            ))
        }

      </div>

    </section>
  );
}
