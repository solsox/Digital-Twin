export type Gender = "male" | "female";
export type RiskLevel = "bajo" | "medio" | "alto";

export interface PatientInput {
  age: number;
  gender: Gender;
  weight: number;
  height_cm: number | null;
  systolic_bp: number;
  diastolic_bp: number;
  cholesterol: number;
}

export interface Patient extends PatientInput {
  id: number;
}

export interface Prediction {
  id?: number | null;
  patient_id?: number | null;
  score: number;
  level: RiskLevel;
  factors: Record<string, number>;
  created_at?: string | null;
}

/** Fila del historial tal como la devuelve el backend. */
export interface PredictionRecord {
  id: number;
  patient_id: number;
  risk_score: number;
  risk_level: RiskLevel;
  factors: Record<string, number>;
  created_at: string;
}

export interface SimulationInput {
  systolic_bp_delta: number;
  diastolic_bp_delta: number;
  cholesterol_delta: number;
  weight_delta: number;
}

export interface Simulation {
  baseline: Prediction;
  scenario: Prediction;
  score_change: number;
}

export type AnalysisKind = "ecg" | "retina" | "xray";

export interface ModelCard {
  title: string;
  available: boolean;
  metrics: Record<string, unknown> | null;
  source: string | null;
}

export type AnalysisCatalog = Record<AnalysisKind, ModelCard>;

export interface EcgAnalysis {
  label: string;
  description: string;
  confidence: number;
  probabilities: Record<string, number>;
  heart_rate_bpm: number | null;
  segments_analyzed: number;
  disclaimer: string;
}

export interface ImageAnalysis {
  kind: string;
  finding: string;
  probability: number;
  image_size: number[];
  model_auc: number;
  disclaimer: string;
}
