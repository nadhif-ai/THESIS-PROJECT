import type { EvaluationResult } from "./api";

export const QA_METRICS = [
  "Faithfulness",
  "Answer Relevancy",
  "Contextual Recall",
  "Contextual Precision",
] as const;

export const QA_RECIPE = "rag-four-metrics-v1";

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
