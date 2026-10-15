import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { api, ApiError } from "./api";
import AnalysisPanel from "./components/AnalysisPanel";
import FactorBreakdown from "./components/FactorBreakdown";
import PatientForm from "./components/PatientForm";
import PatientStatus from "./components/PatientStatus";
import WhatIfPanel from "./components/WhatIfPanel";
import type { PatientInput, Prediction, PredictionRecord } from "./types";
import "./App.css";

// Recharts es pesado: se carga solo cuando hay historial que mostrar.
const RiskChart = lazy(() => import("./components/RiskChart"));

const STORAGE_KEY = "digital-twin:patientId";

const DEFAULTS: PatientInput = {
  age: 30,
  gender: "male",
  weight: 70,
  height_cm: 175,
  systolic_bp: 120,
  diastolic_bp: 80,
  cholesterol: 180,
};

function readStoredId(): number | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? Number(raw) : null;
  } catch {
    return null;
  }
}

function storeId(id: number | null) {
  try {
    if (id === null) localStorage.removeItem(STORAGE_KEY);
    else localStorage.setItem(STORAGE_KEY, String(id));
  } catch {
    /* el almacenamiento puede no estar disponible; no es crítico */
  }
}

function App() {
  const [patientId, setPatientId] = useState<number | null>(readStoredId);
  const [result, setResult] = useState<Prediction | null>(null);
  const [history, setHistory] = useState<PredictionRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Al abrir la app, recupera el historial del paciente guardado (si existe).
  useEffect(() => {
    if (patientId === null) return;
    api
      .listPredictions(patientId)
      .then(setHistory)
      .catch((e) => {
        if (e instanceof ApiError && e.status === 404) {
          setPatientId(null);
          storeId(null);
        }
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = useCallback(
    async (data: PatientInput) => {
      setLoading(true);
      setError(null);
      try {
        // Un solo paciente evoluciona en el tiempo: se crea la primera vez y luego se actualiza.
        let id = patientId;
        if (id === null) {
          id = (await api.createPatient(data)).id;
          setPatientId(id);
          storeId(id);
        } else {
          await api.updatePatient(id, data);
        }
        const prediction = await api.createPrediction(id);
        setResult(prediction);
        setHistory(await api.listPredictions(id));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Ocurrió un error inesperado.");
      } finally {
        setLoading(false);
      }
    },
    [patientId],
  );

  const startNewPatient = () => {
    setPatientId(null);
    storeId(null);
    setHistory([]);
    setResult(null);
    setError(null);
  };

  const chartData = history.map((h, i) => ({ name: `#${i + 1}`, risk: h.risk_score }));

  return (
    <main className="app">
      <h1>Digital Twin Health</h1>
      <p className="subtitle">
        Prototipo educativo de estimación de riesgo cardiovascular. No sustituye una evaluación médica.
      </p>

      <PatientForm initial={DEFAULTS} loading={loading} onSubmit={handleSubmit} />

      {error && <p className="error" role="alert">{error}</p>}

      {result && (
        <section className="card">
          <h2>Resultado</h2>
          <PatientStatus level={result.level} score={result.score} />
          <h3>¿Qué aporta a este resultado?</h3>
          <FactorBreakdown factors={result.factors} />
        </section>
      )}

      {result && patientId !== null && (
        // key: al recalcular el paciente el panel se reinicia con el escenario en cero
        <WhatIfPanel key={history.length} patientId={patientId} />
      )}

      <AnalysisPanel />

      {history.length > 0 && (
        <section className="card">
          <h2>Historial de riesgo</h2>
          <Suspense fallback={<p>Cargando gráfico…</p>}>
            <RiskChart data={chartData} />
          </Suspense>
          <button type="button" className="secondary" onClick={startNewPatient}>
            Empezar con un paciente nuevo
          </button>
        </section>
      )}
    </main>
  );
}

export default App;
