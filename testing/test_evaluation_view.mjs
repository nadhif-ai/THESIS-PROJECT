import assert from "node:assert/strict";
import test from "node:test";
import { evaluationView, metricEvidence, percentage, QA_METRICS } from "../frontend/src/lib/evaluation-metrics.ts";

test("percentage display preserves two decimals and separates missing scores from actual perfect scores", () => {
  assert.equal(percentage(0.7644444444444444), "76.44%");
  assert.equal(percentage(0.8666666666666666), "86.67%");
  assert.equal(percentage(0.9999), "99.99%");
  assert.equal(percentage(0.99994), "99.99%");
  assert.equal(percentage(0.99996), "100.00%");
  assert.equal(percentage(1), "100.00%");
  assert.equal(percentage(0), "0.00%");
  assert.equal(percentage(null), "Not scored");
  assert.equal(percentage(), "Not scored");
});

test("percentage formatting does not cap or rewrite recorded values", () => {
  assert.equal(percentage(1.002), "100.20%");
  assert.equal(percentage(-0.002), "-0.20%");
});

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

test("metric evidence separates scoring failures from quality and exposes sample uncertainty", () => {
  const result = {cases: [
    {metrics: [{name:"Faithfulness",score:0.5}]},
    {metrics: [{name:"Faithfulness",score:1}]},
    {metrics: [{name:"Faithfulness",score:null,error:"BadRequestError"}]},
  ]};
  const evidence = metricEvidence(result,"Faithfulness");
  assert.equal(evidence.scored,2);
  assert.equal(evidence.errors,1);
  assert.equal(evidence.missing,1);
  assert.equal(evidence.mean,0.75);
  assert.equal(evidence.standardError,0.25);
  assert.equal(evidence.interval,null);
});

test("confidence intervals require a complete varied sample and never certify judge accuracy", () => {
  const result = {cases:Array.from({length:30},(_,i)=>({metrics:[{name:"Faithfulness",score:i%2}]}))};
  const evidence=metricEvidence(result,"Faithfulness");
  assert.ok(evidence.interval[0]>0.31 && evidence.interval[0]<0.32);
  assert.ok(evidence.interval[1]>0.68 && evidence.interval[1]<0.69);
  result.cases[0].metrics[0].error="Failure";
  assert.equal(metricEvidence(result,"Faithfulness").interval,null);
});

test('accepted borderline verdicts remain visible without altering the official mean', () => {
  const result={cases:[{metrics:[{name:'Faithfulness',score:1,calculation:{items:[
    {verdict:'yes',counted:true},{verdict:'borderline',counted:true},{verdict:'borderline',counted:false}
  ]}}]}]};
  const evidence=metricEvidence(result,'Faithfulness');
  assert.equal(evidence.mean,1);
  assert.equal(evidence.borderline,1);
});
