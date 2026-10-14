type Props = {
  factors: Record<string, number>;
};

const LABELS: Record<string, string> = {
  edad: "Edad",
  presion_sistolica: "Presión sistólica",
  presion_diastolica: "Presión diastólica",
  colesterol: "Colesterol",
  sexo: "Sexo",
  imc: "IMC",
};

/** Muestra cuánto aporta cada factor al riesgo (barras proporcionales al mayor aporte). */
const FactorBreakdown = ({ factors }: Props) => {
  const entries = Object.entries(factors).sort((a, b) => b[1] - a[1]);
  const max = Math.max(...entries.map(([, v]) => Math.abs(v)), 0.0001);

  return (
    <ul className="factors" aria-label="Aporte de cada factor al riesgo">
      {entries.map(([key, value]) => (
        <li key={key}>
          <span className="factor-name">{LABELS[key] ?? key}</span>
          <span className="factor-bar">
            <span
              className={value < 0 ? "bar neg" : "bar"}
              style={{ width: `${(Math.abs(value) / max) * 100}%` }}
            />
          </span>
          <span className="factor-value">{value > 0 ? "+" : ""}{value.toFixed(2)}</span>
        </li>
      ))}
    </ul>
  );
};

export default FactorBreakdown;
