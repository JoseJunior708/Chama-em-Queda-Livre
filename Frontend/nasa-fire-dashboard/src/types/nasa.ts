export type ExperimentStatus =
  | "completed"
  | "processing"
  | "pending";

export type InsightSeverity =
  | "low"
  | "medium"
  | "high"
  | "critical";

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

export interface ScientificMetric {
  id: string;
  label: string;
  value: number;
  unit: string;
  description: string;
  trend: number;
}

export interface AIInsight {
  id: string;
  title: string;
  description: string;
  severity: InsightSeverity;
  category: string;
  confidence: number;
  experimentId: string;
  source: string;
  createdAt: string;
}

export interface DashboardData {
  experiments: Experiment[];
  metrics: ScientificMetric[];
  insights: AIInsight[];
}