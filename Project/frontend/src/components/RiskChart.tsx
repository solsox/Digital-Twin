import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

type Props = {
  data: { name: string; risk: number }[];
};

const RiskChart = ({ data }: Props) => {
  return (
    <LineChart width={500} height={300} data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="name" />
      <YAxis />
      <Tooltip />
      <Line type="monotone" dataKey="risk" stroke="#8884d8" />
    </LineChart>
  );
};

export default RiskChart;