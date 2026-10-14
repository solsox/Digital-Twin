import { useState } from "react";
import type { Gender, PatientInput } from "../types";

type Props = {
  initial: PatientInput;
  loading: boolean;
  onSubmit: (data: PatientInput) => void;
};

type NumericField = Exclude<keyof PatientInput, "gender" | "height_cm"> | "height_cm";

const FIELDS: { key: NumericField; label: string; unit: string; min: number; max: number }[] = [
  { key: "age", label: "Edad", unit: "años", min: 0, max: 120 },
  { key: "weight", label: "Peso", unit: "kg", min: 1, max: 400 },
  { key: "height_cm", label: "Estatura", unit: "cm", min: 51, max: 260 },
  { key: "systolic_bp", label: "Presión sistólica", unit: "mmHg", min: 50, max: 300 },
  { key: "diastolic_bp", label: "Presión diastólica", unit: "mmHg", min: 30, max: 200 },
  { key: "cholesterol", label: "Colesterol total", unit: "mg/dL", min: 50, max: 600 },
];

/** Validación local para dar respuesta inmediata; el backend vuelve a validar todo. */
function validate(values: PatientInput): string | null {
  for (const f of FIELDS) {
    const v = values[f.key];
    if (v === null || Number.isNaN(v)) return `Completa el campo "${f.label}".`;
    if (v < f.min || v > f.max) return `${f.label} debe estar entre ${f.min} y ${f.max} ${f.unit}.`;
  }
  if (values.systolic_bp <= values.diastolic_bp) {
    return "La presión sistólica debe ser mayor que la diastólica.";
  }
  return null;
}

const PatientForm = ({ initial, loading, onSubmit }: Props) => {
  const [values, setValues] = useState<PatientInput>(initial);
  const [error, setError] = useState<string | null>(null);

  const setNumber = (key: NumericField, raw: string) =>
    setValues((prev) => ({ ...prev, [key]: raw === "" ? NaN : Number(raw) }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const problem = validate(values);
    setError(problem);
    if (!problem) onSubmit(values);
  };

  return (
    <form className="card form" onSubmit={handleSubmit} noValidate>
      <div className="field">
        <label htmlFor="gender">Sexo</label>
        <select
          id="gender"
          value={values.gender}
          onChange={(e) => setValues((p) => ({ ...p, gender: e.target.value as Gender }))}
        >
          <option value="male">Masculino</option>
          <option value="female">Femenino</option>
        </select>
      </div>

      {FIELDS.map((f) => (
        <div className="field" key={f.key}>
          <label htmlFor={f.key}>
            {f.label} <span className="unit">({f.unit})</span>
          </label>
          <input
            id={f.key}
            type="number"
            inputMode="decimal"
            min={f.min}
            max={f.max}
            value={Number.isNaN(values[f.key]) || values[f.key] === null ? "" : (values[f.key] as number)}
            onChange={(e) => setNumber(f.key, e.target.value)}
          />
        </div>
      ))}

      {error && <p className="error" role="alert">{error}</p>}

      <button type="submit" disabled={loading}>
        {loading ? "Calculando…" : "Calcular riesgo"}
      </button>
    </form>
  );
};

export default PatientForm;
