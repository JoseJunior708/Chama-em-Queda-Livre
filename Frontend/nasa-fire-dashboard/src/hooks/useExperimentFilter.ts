
import { useMemo, useState } from "react";
import type { Experiment } from "../types/experiment";

export function useExperimentFilter(experiments: Experiment[]) {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [year, setYear] = useState("");
  const [mission, setMission] = useState("");

  const normalize = (value: string) =>
    value
      .toLocaleLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();

  // Material é usado como categoria científica nesta versão dos dados.
  const categories = useMemo(
    () =>
      [...new Set(experiments.map((item) => item.material))]
        .filter(Boolean)
        .sort(),
    [experiments]
  );

  const years = useMemo(
    () =>
      [
        ...new Set(
          experiments
            .map((item) => item.date?.slice(0, 4))
            .filter((item): item is string => Boolean(item))
        ),
      ].sort((a, b) => Number(b) - Number(a)),
    [experiments]
  );

  const missions = useMemo(
    () =>
      [...new Set(experiments.map((item) => item.mission))]
        .filter(Boolean)
        .sort(),
    [experiments]
  );

  const statuses = useMemo(
    () => [...new Set(experiments.map((item) => item.status))],
    [experiments]
  );

  const filteredExperiments = useMemo(() => {
    const term = normalize(search);

    return experiments.filter((experiment) => {
      const searchableText = normalize(
        [
          experiment.id,
          experiment.title,
          experiment.mission,
          experiment.material,
          experiment.fuel,
          experiment.environment,
          experiment.source,
        ].join(" ")
      );

      const matchesSearch =
        !term || searchableText.includes(term);

      const matchesCategory =
        !category || experiment.material === category;

      const matchesStatus =
        !status || experiment.status === status;

      const experimentYear = experiment.date?.slice(0, 4);

      const matchesYear =
        !year || experimentYear === year;

      const matchesMission =
        !mission || experiment.mission === mission;

      return (
        matchesSearch &&
        matchesCategory &&
        matchesStatus &&
        matchesYear &&
        matchesMission
      );
    });
  }, [
    experiments,
    search,
    category,
    status,
    year,
    mission,
  ]);

  const hasActiveFilters = Boolean(
    search.trim() || category || status || year || mission
  );

  function clearFilters() {
    setSearch("");
    setCategory("");
    setStatus("");
    setYear("");
    setMission("");
  }

  return {
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
  };
}
