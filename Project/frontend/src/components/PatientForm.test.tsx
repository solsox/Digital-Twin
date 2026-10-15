import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PatientForm from "./PatientForm";
import type { PatientInput } from "../types";

const initial: PatientInput = {
  age: 40, gender: "male", weight: 80, height_cm: 175,
  systolic_bp: 120, diastolic_bp: 80, cholesterol: 190,
};

describe("PatientForm", () => {
  it("envía los datos cuando son válidos", async () => {
    const onSubmit = vi.fn();
    render(<PatientForm initial={initial} loading={false} onSubmit={onSubmit} />);
    await userEvent.click(screen.getByRole("button", { name: /calcular riesgo/i }));
    expect(onSubmit).toHaveBeenCalledWith(initial);
  });

  it("bloquea el envío si la sistólica no supera la diastólica", async () => {
    const onSubmit = vi.fn();
    render(<PatientForm initial={{ ...initial, systolic_bp: 70, diastolic_bp: 80 }} loading={false} onSubmit={onSubmit} />);
    await userEvent.click(screen.getByRole("button", { name: /calcular riesgo/i }));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/sistólica debe ser mayor/i);
  });

  it("avisa cuando un campo está vacío o fuera de rango", async () => {
    const onSubmit = vi.fn();
    render(<PatientForm initial={initial} loading={false} onSubmit={onSubmit} />);
    await userEvent.clear(screen.getByLabelText(/edad/i));
    await userEvent.click(screen.getByRole("button", { name: /calcular riesgo/i }));
    expect(screen.getByRole("alert")).toHaveTextContent(/completa el campo "edad"/i);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("deshabilita el botón mientras calcula", () => {
    render(<PatientForm initial={initial} loading onSubmit={vi.fn()} />);
    expect(screen.getByRole("button", { name: /calculando/i })).toBeDisabled();
  });
});
