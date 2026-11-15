
import type { ExperimentStatus } from "../types/experiment";

interface FilterBarProps {
  language: "pt" | "en";

  search: string;
  setSearch: (value: string) => void;

  category: string;
  setCategory: (value: string) => void;

  status: string;
  setStatus: (value: string) => void;

  year: string;
  setYear: (value: string) => void;

  mission: string;
  setMission: (value: string) => void;

  categories: string[];
  years: string[];
  missions: string[];
  statuses: ExperimentStatus[];

  hasActiveFilters: boolean;
  clearFilters: () => void;
}

const statusLabels: Record<ExperimentStatus, { pt: string; en: string }> = {
  completed: { pt: "Concluído", en: "Completed" },
  processing: { pt: "Em análise", en: "Processing" },
  pending: { pt: "Pendente", en: "Pending" },
};

export default function FilterBar({
  language,
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
  hasActiveFilters,
  clearFilters,
}: FilterBarProps) {
  const pt = language === "pt";

  const selectStyle =
    "w-full rounded-xl border border-slate-700 bg-[#0B0F19] px-3 py-3 text-sm text-slate-200 outline-none transition focus:border-cyan-500";

  const labelStyle =
    "mb-2 block text-xs font-medium text-slate-400";

  return (
    <section className="rounded-2xl border border-slate-800 bg-[#111827] p-5">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold text-white">
            {pt ? "Filtros de experiências" : "Experiment Filters"}
          </h2>

          <p className="mt-1 text-xs text-slate-500">
            {pt
              ? "Pesquisa e combina diferentes critérios."
              : "Search and combine different criteria."}
          </p>
        </div>

        {hasActiveFilters && (
          <button
            type="button"
            onClick={clearFilters}
            className="rounded-lg border border-cyan-500/30 px-3 py-2 text-xs font-medium text-cyan-400 transition hover:bg-cyan-500/10"
          >
            {pt ? "Limpar Filtros" : "Clear Filters"}
          </button>
        )}
      </div>

      <div className="mb-4">
        <label htmlFor="experiment-search" className={labelStyle}>
          {pt ? "Pesquisar experiências" : "Search experiments"}
        </label>

        <input
          id="experiment-search"
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder={
            pt
              ? "Nome, código da missão ou palavra-chave..."
              : "Name, mission code or keyword..."
          }
          className={selectStyle}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div>
          <label htmlFor="category-filter" className={labelStyle}>
            {pt ? "Categoria / Material" : "Category / Material"}
          </label>

          <select
            id="category-filter"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            className={selectStyle}
          >
            <option value="">
              {pt ? "Todas as categorias" : "All categories"}
            </option>

            {categories.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="status-filter" className={labelStyle}>
            {pt ? "Estado" : "Status"}
          </label>

          <select
            id="status-filter"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
            className={selectStyle}
          >
            <option value="">
              {pt ? "Todos os estados" : "All statuses"}
            </option>

            {statuses.map((item) => (
              <option key={item} value={item}>
                {statusLabels[item][language]}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="year-filter" className={labelStyle}>
            {pt ? "Ano" : "Year"}
          </label>

          <select
            id="year-filter"
            value={year}
            onChange={(event) => setYear(event.target.value)}
            className={selectStyle}
          >
            <option value="">
              {pt ? "Todos os anos" : "All years"}
            </option>

            {years.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="mission-filter" className={labelStyle}>
            {pt ? "Missão" : "Mission"}
          </label>

          <select
            id="mission-filter"
            value={mission}
            onChange={(event) => setMission(event.target.value)}
            className={selectStyle}
          >
            <option value="">
              {pt ? "Todas as missões" : "All missions"}
            </option>

            {missions.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
      </div>
    </section>
  );
}
