import type { EvaluationResult, Metric } from "@/lib/api";

const number = (value: number) => Number(value.toFixed(4)).toString();
const definitions = [
  {
    name: "Precision@k",
    formula: "P@k = Σ rᵢ / k",
    explanation: "rᵢ is 1 for an annotated relevant passage, otherwise 0. k is the requested retrieval limit. Unfilled positions contribute zero. Relevance is labelled offline for this passage snapshot, not inferred from its filename.",
  },
  {
    name: "Fact Coverage@k",
    formula: "FC@k = |covered reference facts| / |all reference facts|",
    explanation: "Count each reference fact once when a retrieved passage is annotated as containing it. Keep the same facts across chunking configurations and re-label their supporting passages. This is fact coverage, not standard passage Recall@k.",
  },
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
];

export function EvaluationMethodGuide() {
  return (
    <details className="evaluation-method">
      <summary>Evaluation methods and formulas</summary>
      <p className="help-copy">
        New single-question runs report two annotated retrieval measures and two LLM-judged answer measures. Internal staff assessment and SUS remain separate.
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
        Precision and fact coverage need offline annotations bound to the question and passage snapshot. Missing or stale labels produce an unavailable score, not zero. For chunking comparisons, keep the question set, reference facts, embedding, prompt, answer model and k fixed.
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
      {result.evaluation_recipe !== "chunking-fact-coverage-v1" && (
        <p className="help-copy">Historical run: original metric names and scores are preserved. Its contextual metrics must not be relabelled as annotated Precision@k or Fact Coverage@k.</p>
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
        <p>{metric.status === "unavailable"
          ? "No calculation is made until matching offline annotations are supplied."
          : metric.name.startsWith("Business correctness")
            ? "Historical G-Eval rubric score. This is not a count of correct answers; staff business assessment is separate in the new protocol."
            : "This saved score has no compatible calculation trace. Counts cannot be reconstructed from a percentage alone."}</p>
        {metric.name === "Contextual Precision" && <p className="calculation-equation">CP = Σ [P@i × rᵢ] / Σ rᵢ (LLM-judged ranking)</p>}
        {metric.name === "Contextual Recall" && <p className="calculation-equation">CR = attributable reference statements / all reference statements (LLM-judged)</p>}
      </div>
    );
  }
  return (
    <div className="metric-calculation">
      <p className="calculation-equation">{calculation.formula}</p>
      <p className="calculation-equation">
        {calculation.denominator === 0
          ? `No items to divide. DeepEval's empty-item convention returns ${calculation.empty_score}; this is not evidence of factual correctness.`
          : `${number(calculation.numerator)} / ${calculation.denominator} = ${number(calculation.numerator / calculation.denominator)}; × 100 = ${number(calculation.numerator / calculation.denominator * 100)}%`}
      </p>
      {calculation.strict_mode && <p>DeepEval strict mode applies its configured threshold after this ratio.</p>}
      {calculation.k !== undefined && <p>Requested k: {calculation.k}. Returned passages: {calculation.returned}. Each reference fact is counted at most once.</p>}
      {calculation.accepted_verdicts && <p>Accepted judge verdicts: {calculation.accepted_verdicts.join(", ")}. These decisions come from the LLM judge.</p>}
      <ul className="calculation-items">
        {calculation.items.map((item, index) => (
          <li key={index}>
            <div><span>{item.label}</span>{item.detail && <p>{item.detail}</p>}</div>
            <span>{item.verdict || (metric.name === "Fact Coverage@k"
              ? item.counted ? "Covered" : "Not covered"
              : item.counted ? "Relevant" : "Irrelevant")} · {item.counted ? "Counted" : "Not counted"}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
