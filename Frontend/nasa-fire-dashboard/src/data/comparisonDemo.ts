
import type { ExperimentComparison } from "../components/ExperimentComparisonChart";

// Dados fictícios apenas para testar a interface.
// Não representam resultados oficiais da NASA.

export const comparisonDemo: ExperimentComparison[] = [
  {
    id: "DEMO-01",
    name: "DEMO — Experiment A",
    units: {
      temperature: "K",
      radiation: "W/m²",
      biomass: "g",
    },
    metrics: {
      temperature: 820,
      radiation: 145,
      biomass: 12.5,
    },
    telemetry: [
      { time: "00:00", temperature: 700, radiation: 110, biomass: 10 },
      { time: "00:05", temperature: 740, radiation: 120, biomass: 10.8 },
      { time: "00:10", temperature: 790, radiation: 135, biomass: 11.6 },
      { time: "00:15", temperature: 820, radiation: 145, biomass: 12.5 },
    ],
  },
  {
    id: "DEMO-02",
    name: "DEMO — Experiment B",
    units: {
      temperature: "K",
      radiation: "W/m²",
      biomass: "g",
    },
    metrics: {
      temperature: 760,
      radiation: 130,
      biomass: 11.2,
    },
    telemetry: [
      { time: "00:00", temperature: 680, radiation: 100, biomass: 9.5 },
      { time: "00:05", temperature: 710, radiation: 112, biomass: 10.1 },
      { time: "00:10", temperature: 735, radiation: 122, biomass: 10.7 },
      { time: "00:15", temperature: 760, radiation: 130, biomass: 11.2 },
    ],
  },
];
