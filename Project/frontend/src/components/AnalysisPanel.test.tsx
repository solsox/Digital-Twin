import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AnalysisPanel from "./AnalysisPanel";
import { api } from "../api";
import { qualityLabel } from "../quality";
import type { AnalysisCatalog } from "../types";

const card = (title: string, available: boolean, metrics: Record<string, number> | null = null) => ({
  title, available, metrics, source: null,
});

const catalog: AnalysisCatalog = {
  ecg: card("Electrocardiograma (señal)", true, { cv_accuracy: 0.87 }),
  retina: card("Retina (fondo de ojo)", true, { cv_auc: 0.66 }),
  xray: card("Radiografía de tórax", false),
};

describe("AnalysisPanel", () => {
  afterEach(() => vi.restoreAllMocks());

  it("describe la calidad del modelo en palabras", () => {
    expect(qualityLabel(0.55)).toBe("prácticamente azar");
    expect(qualityLabel(0.66)).toBe("débil");
    expect(qualityLabel(0.75)).toBe("aceptable");
    expect(qualityLabel(0.9)).toBe("buena");
  });

  it("avisa cuando no hay modelo para rayos X y no ofrece subir archivos", async () => {
    vi.spyOn(api, "analysisCatalog").mockResolvedValue(catalog);
    render(<AnalysisPanel />);
    await userEvent.click(await screen.findByRole("tab", { name: "Rayos X" }));
    expect(await screen.findByRole("note")).toHaveTextContent(/aún no hay un modelo entrenado/i);
    expect(screen.queryByRole("button", { name: /analizar/i })).not.toBeInTheDocument();
  });

  it("analiza un ECG y muestra resultado con el aviso", async () => {
    vi.spyOn(api, "analysisCatalog").mockResolvedValue(catalog);
    const spy = vi.spyOn(api, "analyzeEcg").mockResolvedValue({
      label: "N", description: "Ritmo normal (o bloqueo de rama)", confidence: 0.96,
      probabilities: { N: 0.96 }, heart_rate_bpm: 73.2, segments_analyzed: 1,
      disclaimer: "No es un diagnóstico",
    });
    render(<AnalysisPanel />);
    const file = new File(["0.1\n0.2\n"], "ecg.csv", { type: "text/csv" });
    await userEvent.upload(await screen.findByLabelText("Archivo"), file);
    await userEvent.click(screen.getByRole("button", { name: "Analizar" }));

    expect(await screen.findByText(/ritmo normal/i)).toBeInTheDocument();
    expect(screen.getByText(/73 lpm/)).toBeInTheDocument();
    expect(screen.getByText("No es un diagnóstico")).toBeInTheDocument();
    expect(spy).toHaveBeenCalledWith(file, 360);
  });

  it("muestra el error del servidor al fallar el análisis de retina", async () => {
    vi.spyOn(api, "analysisCatalog").mockResolvedValue(catalog);
    vi.spyOn(api, "analyzeImage").mockRejectedValue(new Error("El archivo no es una imagen válida"));
    render(<AnalysisPanel />);
    await userEvent.click(await screen.findByRole("tab", { name: "Retina" }));
    expect(await screen.findByText(/calidad débil/i)).toBeInTheDocument();
    await userEvent.upload(screen.getByLabelText("Archivo"), new File(["x"], "a.png", { type: "image/png" }));
    await userEvent.click(screen.getByRole("button", { name: "Analizar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("no es una imagen válida");
  });
});
