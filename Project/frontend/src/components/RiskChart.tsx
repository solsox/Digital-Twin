import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Props = {
  data: { name: string; risk: number }[];
};

// Mismos umbrales que usa el backend (ml/model.py).
const THRESHOLD_MEDIUM = 15;
const THRESHOLD_HIGH = 35;

const RiskChart = ({ data }: Props) => {
  const percent = data.map((d) => ({ ...d, risk: Number((d.risk * 100).toFixed(1)) }));

  return (
    <div style={{ width: "100%", height: 300 }}>
      <ResponsiveContainer>
        <LineChart data={percent} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis domain={[0, 100]} unit="%" />
          <Tooltip formatter={(v) => [`${v}%`, "Riesgo"]} />
          <ReferenceLine y={THRESHOLD_MEDIUM} stroke="#b45309" strokeDasharray="4 4" />
          <ReferenceLine y={THRESHOLD_HIGH} stroke="#b91c1c" strokeDasharray="4 4" />
          <Line type="monotone" dataKey="risk" stroke="#8884d8" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RiskChart;
