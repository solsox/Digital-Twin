import type { RiskLevel } from "../types";

type Props = {
  level: RiskLevel;
  score: number;
};

const STATUS: Record<RiskLevel, { color: string; text: string }> = {
  bajo: { color: "#15803d", text: "Riesgo bajo" },
  medio: { color: "#b45309", text: "Riesgo medio" },
  alto: { color: "#b91c1c", text: "Riesgo alto" },
};

const PatientStatus = ({ level, score }: Props) => {
  const { color, text } = STATUS[level];

  return (
    <div className="status" style={{ backgroundColor: color }} role="status">
      <span className="status-label">{text}</span>
      <span className="status-score">{(score * 100).toFixed(1)}%</span>
    </div>
  );
};

export default PatientStatus;
