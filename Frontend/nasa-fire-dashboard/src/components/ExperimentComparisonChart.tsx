
import { useMemo, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";

export type ComparisonMetric =
  | "temperature"
  | "radiation"
  | "biomass";

export type ChartMode = "line" | "bar";
export type DashboardLanguage = "pt" | "en";

export interface TelemetryPoint {
  time: string;
  temperature: number;
  radiation: number;
  biomass: number;
}

export interface ExperimentComparison {
  id: string;
  name: string;

  // Unidades fornecidas pela fonte dos dados.
  units: Record<ComparisonMetric, string>;

  // Valores resumidos para comparação em barras.
  metrics: Record<ComparisonMetric, number>;

  // Valores recolhidos ao longo do tempo.
  telemetry: TelemetryPoint[];
}

interface ExperimentComparisonChartProps {
  experiments: ExperimentComparison[];
  language?: DashboardLanguage;
}

const METRIC_COLORS: Record<ComparisonMetric, string> = {
  temperature: "#22D3EE",
  radiation: "#A78BFA",
  biomass: "#34D399",
};

const METRIC_LABELS = {
  pt: {
    temperature: "Temperatura",
    radiation: "Radiação",
    biomass: "Biomassa",
  },
  en: {
    temperature: "Temperature",
    radiation: "Radiation",
    biomass: "Biomass",
  },
};

const TEXT = {
  pt: {
    title: "Comparação de experiências",
    subtitle: "Analise os resultados de diferentes experiências espaciais.",
    chartType: "Tipo de gráfico",
    line: "Gráfico de linhas",
    bar: "Gráfico de barras",
    metric: "Métrica científica",
    time: "Tempo",
    value: "Valor",
    noData: "Ainda não existem dados suficientes para comparar.",
    needTwo: "Selecione pelo menos duas experiências para comparar.",
    lineDescription: "Evolução temporal da métrica selecionada.",
    barDescription: "Comparação direta das métricas entre experiências.",
  },
  en: {
    title: "Experiment Comparison",
    subtitle: "Analyze the results of different space experiments.",
    chartType: "Chart type",
    line: "Line chart",
    bar: "Bar chart",
    metric: "Scientific metric",
    time: "Time",
    value: "Value",
    noData: "There is not enough data to compare yet.",
    needTwo: "Select at least two experiments to compare.",
    lineDescription: "Time evolution of the selected metric.",
    barDescription: "Direct comparison of metrics across experiments.",
  },
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    dataKey?: string;
    value?: number | string;
    color?: string;
    name?: string;
  }>;
  label?: string | number;
  mode: ChartMode;
  metric: ComparisonMetric;
  experiments: ExperimentComparison[];
  language: DashboardLanguage;
}

function CustomTooltip({
  active,
  payload,
  label,
  mode,
  metric,
  experiments,
  language,
}: CustomTooltipProps) {
  if (!active || !payload?.length) return null;

  const labels = METRIC_LABELS[language];

  return (
    <div className="min-w-48 rounded-xl border border-slate-700 bg-[#111827] p-4 shadow-2xl">
      <p className="mb-3 text-xs font-semibold text-white">
        {label}
      </p>

      <div className="space-y-2">
        {payload.map((item, index) => {
          let experiment: ExperimentComparison | undefined;
          let metricName = labels[metric];

          if (mode === "line") {
            const experimentIndex = Number(
              item.dataKey?.replace("experiment_", "")
            );

            experiment = experiments[experimentIndex];
          } else {
            experiment = experiments.find(
              (entry) => entry.name === label
            );

            const key = item.dataKey as ComparisonMetric;
            metricName = labels[key] ?? key;
          }

          if (!experiment) return null;

          const currentMetric =
            mode === "line"
              ? metric
              : (item.dataKey as ComparisonMetric);

          const unit = experiment.units[currentMetric];

          return (
            <div
              key={`${item.dataKey}-${index}`}
              className="flex items-center justify-between gap-5 text-xs"
            >
              <span className="flex items-center gap-2 text-slate-400">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                {mode === "line"
                  ? experiment.name
                  : metricName}
              </span>

              <span className="font-semibold text-white">
                {Number(item.value).toLocaleString(
                  language === "pt" ? "pt-PT" : "en-US",
                  { maximumFractionDigits: 2 }
                )}{" "}
                <span className="text-slate-400">{unit}</span>
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function ExperimentComparisonChart({
  experiments,
  language = "pt",
}: ExperimentComparisonChartProps) {
  const [mode, setMode] = useState<ChartMode>("line");
  const [metric, setMetric] =
    useState<ComparisonMetric>("temperature");

  const t = TEXT[language];
  const metricLabels = METRIC_LABELS[language];

  const lineData = useMemo(() => {
    const timeline = new Map<string, Record<string, string | number>>();

    experiments.forEach((experiment, experimentIndex) => {
      experiment.telemetry.forEach((point) => {
        const existing = timeline.get(point.time) ?? {
          time: point.time,
        };

        existing[`experiment_${experimentIndex}`] =
          point[metric];

        timeline.set(point.time, existing);
      });
    });

    return Array.from(timeline.values()).sort((a, b) =>
      String(a.time).localeCompare(String(b.time))
    );
  }, [experiments, metric]);

  const barData = useMemo(
    () =>
      experiments.map((experiment) => ({
        name: experiment.name,
        temperature: experiment.metrics.temperature,
        radiation: experiment.metrics.radiation,
        biomass: experiment.metrics.biomass,
      })),
    [experiments]
  );

  const hasEnoughExperiments = experiments.length >= 2;

  const hasChartData =
    mode === "line"
      ? lineData.length > 0
      : barData.length > 0;

  return (
    <section className="rounded-2xl border border-slate-800 bg-[#111827] p-5 sm:p-6">
      {/* HEADER */}
      <div className="mb-6 flex flex-col justify-between gap-4 xl:flex-row xl:items-center">
        <div>
          <h2 className="text-lg font-semibold text-white">
            {t.title}
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            {t.subtitle}
          </p>
        </div>

        {/* CONTROLS */}
        <div className="flex flex-col gap-3 sm:flex-row">
          <div>
            <label
              htmlFor="chart-mode"
              className="mb-1.5 block text-xs text-slate-400"
            >
              {t.chartType}
            </label>

            <select
              id="chart-mode"
              value={mode}
              onChange={(event) =>
                setMode(event.target.value as ChartMode)
              }
              className="w-full rounded-lg border border-slate-700 bg-[#0B0F19] px-3 py-2 text-sm text-white outline-none focus:border-cyan-500"
            >
              <option value="line">{t.line}</option>
              <option value="bar">{t.bar}</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="chart-metric"
              className="mb-1.5 block text-xs text-slate-400"
            >
              {t.metric}
            </label>

            <select
              id="chart-metric"
              value={metric}
              onChange={(event) =>
                setMetric(
                  event.target.value as ComparisonMetric
                )
              }
              className="w-full rounded-lg border border-slate-700 bg-[#0B0F19] px-3 py-2 text-sm text-white outline-none focus:border-cyan-500"
            >
              <option value="temperature">
                {metricLabels.temperature}
              </option>
              <option value="radiation">
                {metricLabels.radiation}
              </option>
              <option value="biomass">
                {metricLabels.biomass}
              </option>
            </select>
          </div>
        </div>
      </div>

      {/* CHART DESCRIPTION */}
      <p className="mb-4 text-xs text-slate-500">
        {mode === "line"
          ? t.lineDescription
          : t.barDescription}
      </p>

      {/* CHART */}
      {!hasEnoughExperiments ? (
        <div className="flex h-[320px] items-center justify-center rounded-xl border border-dashed border-slate-700 text-center text-sm text-slate-500">
          {experiments.length === 0 ? t.noData : t.needTwo}
        </div>
      ) : !hasChartData ? (
        <div className="flex h-[320px] items-center justify-center rounded-xl border border-dashed border-slate-700 text-center text-sm text-slate-500">
          {t.noData}
        </div>
      ) : (
        <div className="h-[320px] w-full sm:h-[380px]">
          <ResponsiveContainer width="100%" height="100%">
            {mode === "line" ? (
              <LineChart
                data={lineData}
                margin={{
                  top: 10,
                  right: 20,
                  left: 0,
                  bottom: 10,
                }}
              >
                <CartesianGrid
                  stroke="#263244"
                  strokeDasharray="3 3"
                />

                <XAxis
                  dataKey="time"
                  stroke="#64748B"
                  tick={{ fill: "#94A3B8", fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />

                <YAxis
                  stroke="#64748B"
                  tick={{ fill: "#94A3B8", fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                  label={{
                    value: `${metricLabels[metric]} (${experiments[0]?.units[metric] ?? ""})`,
                    angle: -90,
                    position: "insideLeft",
                    fill: "#94A3B8",
                    fontSize: 11,
                  }}
                />

                <Tooltip
                  content={
                    <CustomTooltip
                      mode="line"
                      metric={metric}
                      experiments={experiments}
                      language={language}
                    />
                  }
                />

                <Legend
                  wrapperStyle={{
                    color: "#94A3B8",
                    fontSize: "12px",
                  }}
                />

                {experiments.map((experiment, index) => (
                  <Line
                    key={experiment.id}
                    type="monotone"
                    dataKey={`experiment_${index}`}
                    name={experiment.name}
                    stroke={
                      Object.values(METRIC_COLORS)[
                        index % Object.values(METRIC_COLORS).length
                      ]
                    }
                    strokeWidth={2.5}
                    dot={false}
                    activeDot={{ r: 5 }}
                    connectNulls
                  />
                ))}
              </LineChart>
            ) : (
              <BarChart
                data={barData}
                margin={{
                  top: 10,
                  right: 20,
                  left: 0,
                  bottom: 10,
                }}
              >
                <CartesianGrid
                  stroke="#263244"
                  strokeDasharray="3 3"
                />

                <XAxis
                  dataKey="name"
                  stroke="#64748B"
                  tick={{ fill: "#94A3B8", fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />

                <YAxis
                  stroke="#64748B"
                  tick={{ fill: "#94A3B8", fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />

                <Tooltip
                  content={
                    <CustomTooltip
                      mode="bar"
                      metric={metric}
                      experiments={experiments}
                      language={language}
                    />
                  }
                />

                <Legend
                  wrapperStyle={{
                    color: "#94A3B8",
                    fontSize: "12px",
                  }}
                />

                <Bar
                  dataKey="temperature"
                  name={metricLabels.temperature}
                  fill={METRIC_COLORS.temperature}
                  radius={[5, 5, 0, 0]}
                />

                <Bar
                  dataKey="radiation"
                  name={metricLabels.radiation}
                  fill={METRIC_COLORS.radiation}
                  radius={[5, 5, 0, 0]}
                />

                <Bar
                  dataKey="biomass"
                  name={metricLabels.biomass}
                  fill={METRIC_COLORS.biomass}
                  radius={[5, 5, 0, 0]}
                />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      )}

      {/* FOOTER */}
      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-4">
        <span className="text-xs text-slate-500">
          {experiments.length}{" "}
          {language === "pt"
            ? "experiências selecionadas"
            : "experiments selected"}
        </span>

        <span className="text-xs text-slate-600">
          {t.value}: {metricLabels[metric]}
        </span>
      </div>
    </section>
  );
}
