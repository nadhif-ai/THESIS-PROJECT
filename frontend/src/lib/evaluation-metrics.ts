import type { EvaluationResult } from "./api";

export const QA_METRICS = [
  "Faithfulness",
  "Answer Relevancy",
  "Contextual Recall",
  "Contextual Precision",
] as const;

export const QA_RECIPE = "rag-four-metrics-v1";

export const percentage = (value?: number | null) =>
  value == null ? "Not scored" : `${(value * 100).toFixed(2)}%`;

export function metricEvidence(result: EvaluationResult, name: string) {
  const metrics = result.cases.map((row) => row.metrics.find((metric) => metric.name === name));
  const values = metrics.flatMap((metric) => metric && !metric.error && metric.status !== "unavailable" &&
    typeof metric.score === "number" && Number.isFinite(metric.score) && metric.score >= 0 && metric.score <= 1 ? [metric.score] : []);
  const mean = values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
  const standardError = values.length > 1 && mean !== null
    ? Math.sqrt(values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / (values.length - 1) / values.length)
    : null;
  // Large, complete samples only; this interval does not measure judge correctness.
  const interval = values.length >= 30 && values.length === metrics.length && standardError && mean !== null
    ? [Math.max(0, mean - 1.96 * standardError), Math.min(1, mean + 1.96 * standardError)] as const
    : null;
  const verdicts = metrics.flatMap((metric) => metric?.calculation?.items || []);
  const borderline = verdicts.filter((item) => item.verdict === "borderline" && item.counted).length;
  return { scored: values.length, total: metrics.length, errors: metrics.filter((metric) => metric?.error).length,
    missing: metrics.length - values.length, mean, standardError, interval, borderline };
}

// The export retains the complete historical record; this is the research view.
export function evaluationView(result: EvaluationResult): EvaluationResult {
  const names: readonly string[] = ["legacy", "audited"].includes(result.dataset)
    ? QA_METRICS
    : Object.keys(result.averages || {}).filter((name) => !name.startsWith("Business correctness"));
  return {
    ...result,
    averages: Object.fromEntries(names.map((name) => [name, result.averages?.[name] ?? null])),
    cases: result.cases.map((row) => ({
      ...row,
      metrics: names.flatMap((name) => {
        const metric = row.metrics.find((item) => item.name === name);
        return metric ? [metric] : [];
      }),
    })),
  };
}
