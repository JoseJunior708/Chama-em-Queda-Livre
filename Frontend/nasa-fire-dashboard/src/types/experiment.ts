
export type ExperimentStatus =
  | "completed"
  | "processing"
  | "pending";

export interface Experiment {
  id: string;
  title: string;
  mission: string;
  material: string;
  fuel: string;
  environment: string;
  temperature: number;
  oxygenConcentration: number;
  flameDuration: number;
  status: ExperimentStatus;
  date: string;
  source: string;
}
