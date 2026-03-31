type Props = {
  level: string;
};

const PatientStatus = ({ level }: Props) => {
  let color = "green";
  let text = "Saludable";

  if (level === "medio") {
    color = "orange";
    text = "Riesgo medio";
  }

  if (level === "alto") {
    color = "red";
    text = "Riesgo alto";
  }

  return (
    <div
      style={{
        marginTop: "30px",
        padding: "20px",
        borderRadius: "10px",
        backgroundColor: color,
        color: "white",
        fontWeight: "bold",
        textAlign: "center",
      }}
    >
      Estado del paciente: {text}
    </div>
  );
};

export default PatientStatus;