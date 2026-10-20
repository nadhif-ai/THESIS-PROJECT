import type { EvaluationResult, Metric } from "@/lib/api";
import { QA_RECIPE } from "@/lib/evaluation-metrics";

const number = (value: number) => Number(value.toFixed(4)).toString();
const definitions = [
  {
    name: "Faithfulness",
    formula: "F = accepted claim verdicts / all claim verdicts",
    explanation: "An LLM extracts claims and judges them against the retrieved context. The current DeepEval configuration accepts yes and borderline verdicts. Borderline does not establish factual correctness. Staff assess business correctness separately.",
  },
  {
    name: "Answer Relevancy",
    formula: "AR = accepted statement verdicts / all statement verdicts",
    explanation: "An LLM judges whether statements address the question. The current DeepEval configuration accepts yes and borderline verdicts. A relevant statement can still contain an incorrect price or calculation.",
  },
  {
    name: "Contextual Recall",
    formula: "CRᵢ = Aᵢ / Nᵢ",
    explanation: "Aᵢ counts reference-answer statements the judge can attribute to the retrieved context; Nᵢ counts all reference statements judged. This measures information coverage across the returned contexts, not the number of matching source files.",
  },
  {
    name: "Contextual Precision",
    formula: "CP = Σ [P@j × rⱼ] / Σ rⱼ; P@j = Σₗ≤ⱼ rₗ / j",
    explanation: "The judge marks each returned context relevant (rⱼ = 1) or irrelevant (0) using the question and reference answer. Cumulative precision at each relevant rank is averaged, rewarding relevant contexts near the top. This differs from unweighted Precision@k.",
  },
];

export function EvaluationMethodGuide() {
  return (
    <details className="evaluation-method">
      <summary>Evaluation methods and formulas</summary>
      <p className="help-copy">
        Single-question runs report Faithfulness, Answer Relevancy, Contextual Recall and Contextual Precision. All four use an LLM judge; staff assessment and SUS remain separate.
      </p>
      <dl className="evaluation-definitions">
        {definitions.map((definition) => (
          <div key={definition.name}>
            <dt>{definition.name}</dt>
            <dd>
              <p className="calculation-equation">{definition.formula}</p>
              <p>{definition.explanation}</p>
            </dd>
          </div>
        ))}
      </dl>
      <p className="help-copy">
        The judge extracts claims or statements and supplies verdicts; the application calculates the ratios and ranking weights. A mathematical score still depends on those semantic decisions. Compare chunking with the same questions, reference answers, corpus, embedding, prompt, models and k. Conversation scenarios use their separate turn-level measures.
      </p>
    </details>
  );
}

export function EvaluationMath({ result }: { result: EvaluationResult }) {
  return (
    <details className="evaluation-method">
      <summary>How the run averages are calculated</summary>
      <p className="help-copy">
        Each percentage is 100 × the arithmetic mean of available case scores, not the percentage of cases that passed. Missing scores are excluded and counted below. Each metric can have a different denominator.
      </p>
      <p className="calculation-equation">Mean(m) = Σ sᵢ,m / nₘ</p>
      {["legacy", "audited"].includes(result.dataset) && result.evaluation_recipe !== QA_RECIPE && (
        <p className="help-copy">Historical run: this view shows the four research metrics where recorded. Missing contextual scores are not inferred from other metrics. The JSON export preserves all original measurements.</p>
      )}
      {Object.entries(result.averages || {}).map(([name, saved]) => {
        const values = result.cases.map((row) => ({
          id: row.id,
          score: row.metrics.find((metric) => metric.name === name)?.score,
        }));
        const available = values.filter((value): value is { id: string; score: number } =>
          typeof value.score === "number" && Number.isFinite(value.score),
        );
        const sum = available.reduce((total, value) => total + value.score, 0);
        const mean = available.length ? sum / available.length : null;
        const mismatch = mean !== null && typeof saved === "number" && Math.abs(mean - saved) > 0.000001;
        return (
          <details className="metric-detail" key={name}>
            <summary><strong>{name}</strong><span>{available.length}/{values.length} case scores available</span></summary>
            <p className="calculation-equation">
              {mean === null ? "Mean unavailable: no case scores were recorded." :
                `${number(sum)} / ${available.length} = ${number(mean)}; × 100 = ${number(mean * 100)}%`}
            </p>
            <p>{values.length - available.length} missing. Values below are rounded for display; the mean uses unrounded scores.</p>
            {mismatch && <p>The saved average differs from the case arithmetic above. The saved result has not been changed.</p>}
            <ul className="calculation-items">
              {values.map((value, index) => (
                <li key={`${value.id}-${index}`}><span>Case {value.id}</span><span>{typeof value.score === "number" ? number(value.score) : "Unavailable"}</span></li>
              ))}
            </ul>
          </details>
        );
      })}
    </details>
  );
}

export function MetricMath({ metric }: { metric: Metric }) {
  const calculation = metric.calculation;
  const definition = definitions.find((item) => item.name === metric.name);
  if (!calculation) {
    return (
      <div className="metric-calculation">
        {definition && <p className="calculation-equation">{definition.formula}</p>}
        <p>This saved score has no compatible calculation trace. Counts cannot be reconstructed from a percentage alone.</p>
      </div>
    );
  }
  return (
    <div className="metric-calculation">
      <p className="calculation-equation">{calculation.formula}</p>
      <p className="calculation-equation">
        {calculation.denominator === 0
          ? `The denominator is zero. DeepEval returns ${calculation.empty_score} by convention; no 0/0 ratio is evaluated.`
          : `${number(calculation.numerator)} / ${calculation.denominator} = ${number(calculation.numerator / calculation.denominator)}; × 100 = ${number(calculation.numerator / calculation.denominator * 100)}%`}
      </p>
      {calculation.strict_mode && <p>DeepEval strict mode applies its configured threshold after this ratio.</p>}
      {calculation.k !== undefined && <p>Requested k: {calculation.k}. Returned passages: {calculation.returned}. Each reference fact is counted at most once.</p>}
      {calculation.accepted_verdicts && <p>Accepted judge verdicts: {calculation.accepted_verdicts.join(", ")}. These decisions come from the LLM judge.</p>}
      <ul className="calculation-items">
        {calculation.items.map((item, index) => (
          <li key={index}>
            <div>
              <span>{item.rank !== undefined ? `Rank ${item.rank}: ` : ""}{item.label}</span>
              {item.detail && <p>{item.detail}</p>}
              {item.rank !== undefined && item.relevant_so_far !== undefined && item.precision_at_rank !== undefined && item.contribution !== undefined && (
                <p>P@{item.rank} = {item.relevant_so_far}/{item.rank} = {number(item.precision_at_rank)}; weighted contribution = {number(item.contribution)}</p>
              )}
            </div>
            <span>{item.verdict || (item.counted ? "Accepted" : "Not accepted")} · {item.counted ? "Counted" : "Not counted"}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
