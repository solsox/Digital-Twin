import PatientStatus from "./components/PatientStatus";
import { useState } from "react";
import RiskChart from "./components/RiskChart";

function App() {
  const [age, setAge] = useState(30);
  const [weight, setWeight] = useState(70);
  const [systolic, setSystolic] = useState(120);
  const [diastolic, setDiastolic] = useState(80);
  const [cholesterol, setCholesterol] = useState(180);

  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<{ name: string; risk: number }[]>([]);

  const sendData = async () => {
    const response = await fetch("http://127.0.0.1:8000/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        age: age,
        gender: "male",
        weight: weight,
        systolic_bp: systolic,
        diastolic_bp: diastolic,
        cholesterol: cholesterol,
      }),
    });

    const data = await response.json();

    setResult(data);

    setHistory((prev) => [
      ...prev,
      {
        name: `P${prev.length + 1}`,
        risk: data.score,
      },
    ]);
  };

  return (
    <div style={{ 
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      alignItems: "center",
      
      }}>
      <h1>Digital Twin Health</h1>

      <div style={{ marginBottom: "20px", display: "flex", flexDirection: "column", gap: "10px", maxWidth: "300px" }}>

          <label>Edad</label>
          <input
            type="number"
            value={age}
            onChange={(e) => setAge(Number(e.target.value))}
          />

          <label>Peso (kg)</label>
          <input
            type="number"
            value={weight}
            onChange={(e) => setWeight(Number(e.target.value))}
          />

          <label>Presión sistólica</label>
          <input
            type="number"
            value={systolic}
            onChange={(e) => setSystolic(Number(e.target.value))}
          />

          <label>Presión diastólica</label>
          <input
            type="number"
            value={diastolic}
            onChange={(e) => setDiastolic(Number(e.target.value))}
          />

          <label>Colesterol</label>
          <input
            type="number"
            value={cholesterol}
            onChange={(e) => setCholesterol(Number(e.target.value))}
          />

        </div>

      <button onClick={sendData}>
        Enviar datos paciente
      </button>

      {result && (
        <div>
          <h2>Resultado:</h2>
          <p>Score: {result.score}</p>
          <p>Nivel: {result.level}</p>
        </div>
      )}

      {result && <PatientStatus level={result.level} />}

      {history.length > 0 && (
        <div>
          <h2>Historial de riesgo</h2>
          <RiskChart data={history} />
        </div>
      )}
    </div>
  );
}

export default App;