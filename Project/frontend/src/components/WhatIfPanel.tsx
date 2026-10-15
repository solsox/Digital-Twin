import { useEffect, useState } from "react";
import { api } from "../api";
import type { Simulation, SimulationInput } from "../types";

type Props = {
  patientId: number;
};

const ZERO: SimulationInput = {
  systolic_bp_delta: 0,
  diastolic_bp_delta: 0,
  cholesterol_delta: 0,
  weight_delta: 0,
};

const SLIDERS: { key: keyof SimulationInput; label: string; unit: string; min: number; max: number }[] = [
  { key: "systolic_bp_delta", label: "Presión sistólica", unit: "mmHg", min: -40, max: 40 },
  { key: "diastolic_bp_delta", label: "Presión diastólica", unit: "mmHg", min: -30, max: 30 },
  { key: "cholesterol_delta", label: "Colesterol", unit: "mg/dL", min: -100, max: 100 },
  { key: "weight_delta", label: "Peso", unit: "kg", min: -20, max: 20 },
];

const pct = (n: number) => `${(n * 100).toFixed(1)}%`;

/** Gemelo digital: mueve los controles y compara el riesgo actual con el del escenario. */
const WhatIfPanel = ({ patientId }: Props) => {
  const [scenario, setScenario] = useState<SimulationInput>(ZERO);
  const [sim, setSim] = useState<Simulation | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Espera 250 ms tras el último movimiento y cancela la petición anterior si sigue en curso.
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      api
        .simulate(patientId, scenario, controller.signal)
        .then((s) => {
          setSim(s);
          setError(null);
        })
        .catch((e) => {
          if (e instanceof DOMException && e.name === "AbortError") return;
          setSim(null);
          setError(e instanceof Error ? e.message : "No se pudo simular el escenario.");
        });
    }, 250);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [patientId, scenario]);

  const change = sim?.score_change ?? 0;
  const tone = change < 0 ? "better" : change > 0 ? "worse" : "same";

  return (
    <section className="card">
      <h2>¿Y si cambiara…?</h2>
      <p className="hint">Mueve los controles para ver cómo cambiaría el riesgo. No se guarda nada.</p>

      <div className="whatif-sliders">
        {SLIDERS.map((s) => {
          const value = scenario[s.key];
          return (
            <div className="slider" key={s.key}>
              <label htmlFor={s.key}>
                {s.label}{" "}
                <span className="unit">
                  {value > 0 ? "+" : ""}
                  {value} {s.unit}
                </span>
              </label>
              <input
                id={s.key}
                type="range"
                min={s.min}
                max={s.max}
                value={value}
                onChange={(e) => setScenario((p) => ({ ...p, [s.key]: Number(e.target.value) }))}
              />
            </div>
          );
        })}
      </div>

      {error && <p className="error" role="alert">{error}</p>}

      {sim && !error && (
        <div className={`whatif-result ${tone}`} aria-live="polite">
          <div>
            <span className="label">Actual</span>
            <strong>{pct(sim.baseline.score)}</strong>
            <span className="level">{sim.baseline.level}</span>
          </div>
          <span aria-hidden="true">→</span>
          <div>
            <span className="label">Escenario</span>
            <strong>{pct(sim.scenario.score)}</strong>
            <span className="level">{sim.scenario.level}</span>
          </div>
          <div className="delta">
            {change === 0 ? "Sin cambio" : `${change > 0 ? "+" : ""}${(change * 100).toFixed(1)} pts`}
          </div>
        </div>
      )}

      <button type="button" className="secondary" onClick={() => setScenario(ZERO)}>
        Reiniciar escenario
      </button>
    </section>
  );
};

export default WhatIfPanel;
