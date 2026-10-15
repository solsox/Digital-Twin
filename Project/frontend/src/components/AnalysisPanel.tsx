import { useEffect, useState } from "react";
import { api } from "../api";
import { qualityLabel } from "../quality";
import type { AnalysisCatalog, AnalysisKind, EcgAnalysis, ImageAnalysis } from "../types";

const TABS: { kind: AnalysisKind; label: string; accept: string; hint: string }[] = [
  { kind: "ecg", label: "ECG", accept: ".csv,.txt", hint: "Archivo CSV/TXT con una muestra por línea (un canal)." },
  { kind: "retina", label: "Retina", accept: "image/jpeg,image/png", hint: "Foto de fondo de ojo en JPG o PNG." },
  { kind: "xray", label: "Rayos X", accept: "image/jpeg,image/png", hint: "Radiografía de tórax en JPG o PNG." },
];

type Result = { kind: "ecg"; data: EcgAnalysis } | { kind: "image"; data: ImageAnalysis };

const AnalysisPanel = () => {
  const [tab, setTab] = useState<AnalysisKind>("ecg");
  const [catalog, setCatalog] = useState<AnalysisCatalog | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [fs, setFs] = useState(360);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Result | null>(null);

  useEffect(() => {
    api.analysisCatalog().then(setCatalog).catch(() => setCatalog(null));
  }, []);

  const current = TABS.find((t) => t.kind === tab)!;
  const card = catalog?.[tab];
  const available = card ? card.available : true; // sin catálogo, deja que el servidor responda

  const switchTab = (kind: AnalysisKind) => {
    setTab(kind);
    setFile(null);
    setResult(null);
    setError(null);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      if (tab === "ecg") setResult({ kind: "ecg", data: await api.analyzeEcg(file, fs) });
      else setResult({ kind: "image", data: await api.analyzeImage(tab, file) });
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo analizar el archivo.");
    } finally {
      setBusy(false);
    }
  };

  const metrics = card?.metrics as Record<string, number> | null | undefined;
  const auc = metrics?.cv_auc;

  return (
    <section className="card">
      <h2>Análisis de señales e imágenes</h2>

      <div className="tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.kind}
            type="button"
            role="tab"
            aria-selected={tab === t.kind}
            className={tab === t.kind ? "tab active" : "tab"}
            onClick={() => switchTab(t.kind)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {!available ? (
        <p className="notice" role="note">
          Aún no hay un modelo entrenado para {card?.title.toLowerCase()}. La interfaz está lista: al
          entrenarlo con ml/train_images.py (ver README) este análisis se activa solo.
        </p>
      ) : (
        <>
          {auc !== undefined && (
            <p className="notice" role="note">
              Modelo experimental: calidad {qualityLabel(auc)} (AUC {auc.toFixed(2)}; 0.5 = azar).
            </p>
          )}
          {tab === "ecg" && metrics?.cv_accuracy !== undefined && (
            <p className="notice" role="note">
              Modelo experimental: {(metrics.cv_accuracy * 100).toFixed(0)} % de exactitud en validación
              cruzada, probablemente optimista.
            </p>
          )}

          <form className="analysis-form" onSubmit={submit}>
            <div className="field">
              <label htmlFor="analysis-file">Archivo</label>
              <input
                id="analysis-file"
                key={tab}
                type="file"
                accept={current.accept}
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              <span className="hint">{current.hint} No se guarda en el servidor.</span>
            </div>

            {tab === "ecg" && (
              <div className="field">
                <label htmlFor="fs">
                  Frecuencia de muestreo <span className="unit">(Hz)</span>
                </label>
                <input
                  id="fs"
                  type="number"
                  min={50}
                  max={2000}
                  value={fs}
                  onChange={(e) => setFs(Number(e.target.value))}
                />
              </div>
            )}

            <button type="submit" disabled={!file || busy}>
              {busy ? "Analizando…" : "Analizar"}
            </button>
          </form>
        </>
      )}

      {error && <p className="error" role="alert">{error}</p>}

      {result?.kind === "ecg" && (
        <div className="analysis-result" aria-live="polite">
          <strong>{result.data.description}</strong>
          <span>
            Confianza {(result.data.confidence * 100).toFixed(0)} %
            {result.data.heart_rate_bpm !== null && ` · ${Math.round(result.data.heart_rate_bpm)} lpm`}
            {` · ${result.data.segments_analyzed} segmento(s)`}
          </span>
          <p className="hint">{result.data.disclaimer}</p>
        </div>
      )}

      {result?.kind === "image" && (
        <div className="analysis-result" aria-live="polite">
          <strong>{result.data.finding}</strong>
          <span>Probabilidad estimada {(result.data.probability * 100).toFixed(0)} %</span>
          <p className="hint">{result.data.disclaimer}</p>
        </div>
      )}
    </section>
  );
};

export default AnalysisPanel;
