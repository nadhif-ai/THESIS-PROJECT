import assert from "node:assert/strict";
import test from "node:test";
import { replyProcessing } from "../frontend/src/lib/whatsapp-status.ts";

test("Vercel mode does not report a stopped polling thread as a failure", () => {
  const check = replyProcessing({ execution_mode: "vercel_queue", worker_running: false });
  assert.equal(check.ready, undefined);
  assert.match(check.detail, /Vercel Queues/);
  assert.doesNotMatch(check.detail, /stopped|Keep the backend running/);
});

test("local mode reports the actual worker state, including older API responses", () => {
  assert.equal(replyProcessing({ execution_mode: "local_worker", worker_running: true }).ready, true);
  const stopped = replyProcessing({ worker_running: false });
  assert.equal(stopped.ready, false);
  assert.match(stopped.detail, /stopped/);
});
