import type {
  AnalysisCatalog,
  EcgAnalysis,
  ImageAnalysis,
  Patient,
  PatientInput,
  Prediction,
  PredictionRecord,
  Simulation,
  SimulationInput,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

/** Convierte la respuesta de error de FastAPI (string o lista de errores 422) en un mensaje legible. */
function errorMessage(body: unknown, fallback: string): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: { loc?: (string | number)[]; msg?: string }) => {
        const field = d.loc?.filter((p) => p !== "body").join(".");
        return field ? `${field}: ${d.msg}` : (d.msg ?? "");
      })
      .join("; ");
  }
  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      // Con FormData el navegador pone solo el Content-Type (con el boundary).
      headers: init?.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError("No se pudo conectar con el servidor. ¿Está encendido el backend?", 0);
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(errorMessage(body, `Error ${response.status}`), response.status);
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}

const json = (data: unknown): RequestInit => ({ body: JSON.stringify(data) });

export const api = {
  /** Predicción rápida, sin guardar nada. */
  predict: (data: PatientInput) =>
    request<Prediction>("/predict", { method: "POST", ...json(data) }),

  createPatient: (data: PatientInput) =>
    request<Patient>("/patients", { method: "POST", ...json(data) }),

  updatePatient: (id: number, data: PatientInput) =>
    request<Patient>(`/patients/${id}`, { method: "PUT", ...json(data) }),

  createPrediction: (patientId: number) =>
    request<Prediction>(`/patients/${patientId}/predictions`, { method: "POST" }),

  listPredictions: (patientId: number) =>
    request<PredictionRecord[]>(`/patients/${patientId}/predictions`),

  /** Escenario what-if sobre un paciente guardado; no persiste nada. */
  simulate: (patientId: number, scenario: SimulationInput, signal?: AbortSignal) =>
    request<Simulation>(`/patients/${patientId}/simulate`, {
      method: "POST",
      signal,
      ...json(scenario),
    }),

  analysisCatalog: () => request<AnalysisCatalog>("/analysis"),

  analyzeEcg: (file: File, fs: number) => {
    const body = new FormData();
    body.append("file", file);
    body.append("fs", String(fs));
    return request<EcgAnalysis>("/analysis/ecg", { method: "POST", body });
  },

  analyzeImage: (kind: "retina" | "xray", file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<ImageAnalysis>(`/analysis/${kind}`, { method: "POST", body });
  },
};
