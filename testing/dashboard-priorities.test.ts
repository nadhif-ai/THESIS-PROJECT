import assert from "node:assert/strict";
import test from "node:test";
import { dashboardPriorities } from "../frontend/src/lib/dashboard-priorities.ts";
import type { Job, Version, WhatsAppStatus } from "../frontend/src/lib/api.ts";
import type { KnowledgeCatalog } from "../frontend/src/components/knowledge-page.tsx";

const published = { chunk_count: 95, compatible: true } as Version;
const knowledge = { pending: false, sync_job: null } as KnowledgeCatalog;
const ready = { provider: "waha", session_status: "WORKING", worker_running: false, execution_mode: "vercel_queue", bot_replies_enabled: true } as WhatsAppStatus;
const state = { published, jobs: [] as Job[], knowledge, whatsapp: ready };

test("a Vercel queue session does not require a local worker", () => {
  assert.deepEqual(dashboardPriorities(state), []);
});
test("uncertain delivery takes priority and never invites an automatic retry", () => {
  const items = dashboardPriorities({ ...state, published: null, whatsapp: { ...ready, queue: { failed: 1, uncertain: 2 } } });
  assert.equal(items[0].title, "3 WhatsApp messages need review");
  assert.match(items[0].detail, /Inspect WhatsApp before retrying/);
  assert.equal(items[0].page, "Providers");
  assert.ok(items.some(item => item.title === "Customer knowledge is empty"));
});
test("ignored attention items are not reconstructed from historical queue failures", () => {
  assert.deepEqual(dashboardPriorities({ ...state, whatsapp: { ...ready, queue: { failed: 10 }, attention: { failed: 0, uncertain: 0, items: [] } } }), []);
});
test("pending changes prompt review while an active sync suppresses duplicate sync advice", () => {
  assert.equal(dashboardPriorities({ ...state, knowledge: { ...knowledge, pending: true } })[0].page, "Knowledge");
  assert.deepEqual(dashboardPriorities({ ...state, knowledge: { ...knowledge, pending: true, sync_job: "sync1" } }), []);
});
test("interrupted synchronization leads to knowledge and incompatible snapshots need review", () => {
  const items = dashboardPriorities({ ...state, published: { ...published, compatible: false }, jobs: [{ kind: "sync", status: "interrupted" } as Job] });
  assert.equal(items[0].page, "Knowledge");
  assert.ok(items.some(item => item.title === "Active knowledge needs reindexing"));
});
test("unknown auxiliary data does not create a healthy status claim or pause warning", () => {
  assert.deepEqual(dashboardPriorities({ ...state, knowledge: null, whatsapp: null }), []);
});

test("an active WAHA session still needs its webhook and credentials", () => {
  const items = dashboardPriorities({ ...state, whatsapp: { ...ready, webhook_configured: false } });
  assert.equal(items[0].title, "WhatsApp configuration is incomplete");
  assert.equal(items[0].page, "Providers");
});
test("legacy indexing failures lead to Knowledge", () => {
  const items = dashboardPriorities({ ...state, jobs: [{ kind: "index", status: "failed" } as Job] });
  assert.equal(items[0].page, "Knowledge");
});

test("first sync offers progress review without claiming a previous snapshot", () => {
  const items = dashboardPriorities({ ...state, published: null, knowledge: { ...knowledge, sync_job: "first-sync" } });
  assert.equal(items[0].title, "Initial knowledge sync is in progress");
  assert.equal(items[0].action, "View sync progress");
  assert.doesNotMatch(items[0].detail, /previous/);
});
