import assert from "node:assert/strict";
import test from "node:test";
import { evaluationView, QA_METRICS } from "../frontend/src/lib/evaluation-metrics.ts";

test("QA research view keeps four named metrics in order without rewriting saved evidence", () => {
  const metrics = [...QA_METRICS].reverse().map((name) => ({ name, score: 0.8, reason: "fixture", passed: true }));
  metrics.push({ name: "Business correctness", score: 0.9, reason: "old rubric", passed: true });
  const saved = { dataset: "legacy", averages: Object.fromEntries(metrics.map((m) => [m.name, m.score])), cases: [{ id: "1", metrics }] };
  const copy = structuredClone(saved);
  const view = evaluationView(saved);
  assert.deepEqual(Object.keys(view.averages), QA_METRICS);
  assert.deepEqual(view.cases[0].metrics.map((m) => m.name), QA_METRICS);
  assert.deepEqual(saved, copy);
});

test("historical annotated scores cannot become contextual scores", () => {
  const view = evaluationView({ dataset: "audited", averages: { Faithfulness: 0.8, "Precision@k": 1, "Fact Coverage@k": 1 }, cases: [{ id: "1", metrics: [{ name: "Precision@k", score: 1 }] }] });
  assert.equal(view.averages["Contextual Recall"], null);
  assert.equal(view.averages["Contextual Precision"], null);
  assert.deepEqual(view.cases[0].metrics, []);
});

test("conversation diagnostics retain turn-level names", () => {
  const view = evaluationView({ dataset: "conversations", averages: { "Turn Faithfulness": 0.7 }, cases: [] });
  assert.deepEqual(view.averages, { "Turn Faithfulness": 0.7 });
});
