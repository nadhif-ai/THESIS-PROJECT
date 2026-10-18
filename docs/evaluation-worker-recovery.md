# Evaluation worker recovery — 19 October 2026

## Incident and evidence

Evaluation `2c5e19b457884742ad4160e4a1364411` was submitted at
2026-10-18 16:34:21 UTC. PostgreSQL recorded executor environment `local`,
sequence 59, nine completed cases, and three saved metrics for case 10.
Its last lease expired at 16:53:20 UTC; the local process no longer existed.
The dashboard still displayed `running` at 18:40 UTC because the read API
returned the persisted status without checking the execution lease.

This job was never submitted to production Queues: dispatch selects a local
thread-pool executor outside Vercel. Sharing PostgreSQL made it visible in the
production dashboard, but deploying code did not move its execution ownership.
Resume also rejected a local job from a production environment. A stopped local
worker therefore left a recoverable checkpoint with no worker to continue it.
This explains the two-hour apparent run; the original worker had made progress
for approximately fifteen minutes, then stopped. No evidence establishes a
provider timeout as the cause of this incident.

Vercel Hobby rejected the three-hour historical log query because retention is
one hour. Recent logs had no original execution event. After transferring only
this expired job under a database transaction and explicitly invoking production
Resume, Vercel logged `Administration execution=vercel_queue`, sequence 61,
phase scoring, in `bom1`. The job reached completed with 10 cases, 50 scored
metrics, and 50 reported LangSmith feedback records. Reporting error was null.
The original nine cases, last answer, first three metrics of case 10, and prompt
hash were compared before/after and remained exactly equal. No answers were
regenerated and no earlier scores were fabricated or replaced.

## Permanent behavior

- Job list, overview and detail derive `interrupted` for unfinished durable jobs
  with expired leases, or no lease and no checkpoint activity for five minutes.
  A live lease remains running. Database execution status is unchanged by reads.
- Responses include execution environment and lease state, plus a recovery notice
  consumed by the existing Resume UI. Detail responses also include resumability.
- Explicit authenticated Resume may transfer an expired local **evaluation** to
  production. Active leases, preview environments, and cross-environment source
  synchronization remain protected. Completed jobs cannot be resumed.
- Resume increments the sequence, clears the old token/lease and updates the
  environment atomically. An old worker cannot commit after takeover.
- Each successful worker checkpoint logs job, sequence, phase, saved progress,
  metric count, duration and completion, without customer text or credentials.

This is recovery, not a promise of a particular evaluation latency. Legacy ten-
case jobs retain their original five metrics and model/prompt configuration.
No judge, thresholds, datasets, retrieval recipe, or scores are changed by this fix.
New production evaluations use the existing durable Vercel Queue subscribers.

Verification: 190 offline backend tests passed in an isolated release worktree,
including seven recovery regressions. Two third-party deprecation warnings.
