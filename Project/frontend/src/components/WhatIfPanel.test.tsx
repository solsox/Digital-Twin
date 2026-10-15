import { fireEvent, render, screen } from "@testing-library/react";
import WhatIfPanel from "./WhatIfPanel";
import { api } from "../api";
import type { Simulation } from "../types";

const pred = (score: number, level: "bajo" | "medio" | "alto") => ({ score, level, factors: {} });

describe("WhatIfPanel", () => {
  afterEach(() => vi.restoreAllMocks());

  it("muestra la mejora cuando el escenario reduce el riesgo", async () => {
    const sim: Simulation = { baseline: pred(0.4, "alto"), scenario: pred(0.2, "medio"), score_change: -0.2 };
    const spy = vi.spyOn(api, "simulate").mockResolvedValue(sim);
    render(<WhatIfPanel patientId={7} />);

    expect(await screen.findByText("-20.0 pts")).toBeInTheDocument();
    expect(spy).toHaveBeenCalledWith(7, expect.objectContaining({ cholesterol_delta: 0 }), expect.anything());
  });

  it("envía el cambio al mover un deslizador", async () => {
    const sim: Simulation = { baseline: pred(0.3, "medio"), scenario: pred(0.3, "medio"), score_change: 0 };
    const spy = vi.spyOn(api, "simulate").mockResolvedValue(sim);
    render(<WhatIfPanel patientId={1} />);
    await screen.findByText("Sin cambio");

    fireEvent.change(screen.getByLabelText(/colesterol/i), { target: { value: "-50" } });
    await vi.waitFor(() =>
      expect(spy).toHaveBeenLastCalledWith(1, expect.objectContaining({ cholesterol_delta: -50 }), expect.anything()),
    );
  });

  it("muestra el error del servidor si el escenario no es válido", async () => {
    vi.spyOn(api, "simulate").mockRejectedValue(new Error("Escenario no válido"));
    render(<WhatIfPanel patientId={1} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Escenario no válido");
  });
});
