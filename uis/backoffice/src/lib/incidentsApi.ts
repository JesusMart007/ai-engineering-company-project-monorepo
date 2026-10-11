import { apiFetch, apiJson } from "@/lib/apiClient";

export type ProblemKind = "missing" | "invalid";

export type AnalysisResult = {
  total_records: number;
  valid_records: number;
  invalid_records: number;
  invalid_breakdown: Record<string, number>;
  invalid_by_field: Record<string, Partial<Record<ProblemKind, number>>>;
  by_category: Record<string, number>;
  by_status: Record<string, number>;
  scored_tickets: number;
  closed_tickets: number;
  average_score: number | null;
  score_breakdown: Record<string, number>;
  labels: { rules: Record<string, string>; problems: Record<string, string>; scores: Record<string, string> };
};

export async function analyzeIncidents(file: File): Promise<AnalysisResult> {
  const body = new FormData();
  body.append("file", file);
  return apiJson<AnalysisResult>("/api/incidents/analyze", {
    method: "POST",
    body,
    fallback: "No se pudo analizar el archivo",
  });
}

export async function downloadResultsCsv(): Promise<void> {
  const response = await apiFetch("/api/incidents/results/export", { fallback: "No se pudo descargar el CSV" });
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = "results.csv";
  link.click();
  URL.revokeObjectURL(url);
}
