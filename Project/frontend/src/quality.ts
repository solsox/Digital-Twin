/** Calidad del modelo en palabras, a partir del AUC de validación (0.5 = azar). */
export function qualityLabel(auc: number): string {
  if (auc < 0.6) return "prácticamente azar";
  if (auc < 0.7) return "débil";
  if (auc < 0.8) return "aceptable";
  return "buena";
}
