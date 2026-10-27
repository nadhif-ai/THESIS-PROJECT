# Vercel function storage audit

## Approved local implementation follow-up

The user approved bundle optimization, main-only automatic deployments, local checks before release, and retaining two prior production versions.

### Main-only policy applied

- Live project `previewDeploymentsDisabled` is now `true`.
- Live ignored-build guard is `case "$VERCEL_GIT_COMMIT_REF" in main) exit 1;; *) exit 0;; esac`, read back through the Vercel API. This also covers older dev commits whose repository config still enables previews.
- Local `vercel.json` now allows only main via `git.deploymentEnabled = {"**": false, "main": true}`. This source change is not committed or pushed; the live project controls are already effective.
- Seven-day retention remains unchanged for all deployment categories. The existing minimum `deploymentsToKeep: 10` remains: Vercel's dashboard offers durations but no count control, and its deployment-expiration PATCH endpoint rejected `deploymentsToKeep: 3` as an additional property. No deletion or unsupported settings workaround was performed. The request to reduce the protected minimum to current plus two prior versions is therefore **not implemented**; existing retention preserves more history.
- Hobby Instant Rollback supports only the immediately previous production deployment. Keeping two previous artifacts does not guarantee Instant Rollback to both, nor does Ready alone prove application correctness.
- Four focused loader/configuration tests passed after the policy source edit. No new production deployment was created.

- Added deployment exclusions for `dataset/image-product`, selected screenshot/comparison directories, and top-level testing PNG files. Runtime evaluation code, datasets and baselines remain included.
- Replaced pandas CSV parsing with standard-library csv and PyPDFLoader with shared direct pypdf parsing. PDF page numbers, labels and document metadata are retained; CSV missing-field string conversion is preserved for compatibility.
- Removed pandas and langchain-community runtime requirements. Refreshed the local-project metadata while regenerating uv.lock, removing 11 packages including NumPy and SQLAlchemy. Legacy reproduction requirements remain unchanged.
- Installed the locked runtime in an isolated temporary Python 3.12 environment without the removed packages. Six focused loader, deployment-configuration and chunking checks passed. The broader DB-backed run returned one failure and 19 setup errors at the existing maintenance-mode guard. Representative failures reproduce on unchanged HEAD in an isolated worktree, using the same local PostgreSQL 15 setup. Docker/PostgreSQL 17 was unavailable; the disposable loopback PostgreSQL 15 server was stopped afterward.
- No deployment, deletion, commit, or paid evaluation was performed. Remote policy updates are recorded above. Actual Vercel bundle reduction remains unmeasured until a controlled build/deployment. A main-only policy still retains history for each successive production deployment; disabling previews does not delete old ones.

Read-only platform audit on 2026-10-25. No deployment, deletion, retention change, or application change was performed during this audit. This supplements the earlier deployment-storage configuration verification.

## Live evidence

- Team `nadhif-s1`, Hobby; project `thesis-project`.
- Usage > Functions Storage > Projects shows **9.19 GB**, attributed to this project, for the last 30 days.
- Current production deployment `dpl_H9jLGP4gNgGajxwCjSddJb6sfGTW`, commit `e521d69d0f047924ab0b16ce4b16d450c5505ce3`.
- Resources lists three Python 3.12 functions in BOM1: `/fastapi`, `/_py_subscribers/app-integrations-waha__queue`, and `/_py_subscribers/app-integrations-admin__queue`. Each displays **137 MB**, approximately **411 MB summed function size per deployment**. This is resource-size arithmetic, not a reconstruction of the Usage accounting.
- Deployment API returned 37 records with no next page: 35 Ready (18 production, 17 preview) and two canceled. Historical sizes were not individually measured.
- Build and Deployment settings show one-week retention for canceled, errored, pre-production, and production deployments.
- Security > Recently Deleted lists two deployments, each with 29 days left for recovery. Retention cleanup has begun.
- Current `vercel.json` already restricts automatic Git deployments to main/dev and configures only BOM1. Earlier verification records a custom ignored-build guard and `deploymentsToKeep: 10`; those two fields were not independently returned by the simplified project MCP response in this audit.

Dashboard evidence:

- https://vercel.com/nadhif-s1/~/usage/deployments-functions?view=Projects
- https://vercel.com/nadhif-s1/thesis-project/H9jLGP4gNgGajxwCjSddJb6sfGTW/resources
- https://vercel.com/nadhif-s1/thesis-project/settings/build-and-deployment#deployment-retention-policy

## Interpretation

Functions Storage concerns stored deployment bundles, not chatbot documents, database rows, function RAM, or invocation volume. Both retained deployment count and bundle size matter. Vercel documents GB-month accounting using each project's daily maximum stored amount. Deleting output does not erase historical usage or guarantee an immediate dashboard decrease.

At today's displayed sizes, one preview plus one production deployment adds approximately 822 MB of function resources before any platform accounting or deduplication. The 9.19 GB Usage value cannot be reconciled exactly by multiplying all 35 Ready records by today's sizes: historical output sizes, time aggregation, recovery, and internal accounting have not been measured.

Seven-day retention and main/dev-only automatic builds are already implemented. Vercel documents background marking within approximately 48 hours, up to 30 days to re-evaluate former exceptions, and a 30-day recovery period for successful deployments. Active aliases and active-branch previews can protect output beyond the configured duration.

## Ranked next actions

**First, verify and exclude packaged source assets.** `dataset/image-product/` contains approximately **61.71 MB of tracked image originals**. Its application reference is the default path of the operator CLI in `app/admin/catalog_import.py:64`; runtime catalog delivery uses object-storage URLs in `app/admin/catalog_storage.py:52`. The folder is not covered by the existing `data` exclusion. Check actual bundle inclusion, then exclude it from deployment while retaining local import tooling. Non-evaluation/non-baseline files under `testing/` total approximately **12.99 MB**, also candidates for selective exclusion. These source sizes are not measured deployed savings; retain evaluation datasets, `testing/test_dataset.csv`, package initializers, and baseline results/snapshots used by runtime APIs and bootstrap paths. This packaging pass is lower-impact than changing parsing dependencies.

1. **Trim pandas and langchain-community from the production dependency closure.** `app/backend/loader.py:147` uses pandas for CSV parsing; replace it with standard-library CSV parsing while preserving BOM handling, strings, blanks, malformed-row behavior, and document metadata. `app/backend/loader.py:105` and `app/admin/knowledge.py:147` use PyPDFLoader; use direct pypdf with equivalent per-page documents and metadata. `app/admin/global_knowledge.py` already uses pypdf. Keep legacy Chroma reproduction isolated. Update requirements and uv.lock together.
2. **Exclude genuine development artifacts from Python output.** Existing `.vercelignore` already excludes virtualenvs, docs, graph output, data, node_modules, and frontend/dist. Inspect backend-specific exclusions for frontend source, scripts and ordinary tests. With Services, configure function options inside the backend service and verify all generated subscriber bundles. Do not exclude the frontend globally, because it must still build.
3. **Preserve runtime evaluations.** Despite its name, `testing/evals` is production code: admin routes, jobs and durable jobs import it. Do not exclude all `testing/**`, remove its package discovery, or classify DeepEval as development-only without first moving and preserving the runtime evaluation implementation.
4. **Review retained history after cleanup.** Identify unneeded custom aliases and merged/closed branch previews, preserve current production and dev, then agree the rollback history needed before manually deleting old deployments or reducing protected counts. The API's rollback flag alone is not enough to choose a deletion list.
5. **Consider hosting changes only if needed after measurement.** Moving the Python API and workers to an external host could leave only static Vite output on Vercel, but requires a supported replacement for Vercel Queue delivery, worker leases/checkpoints, retry behavior, authentication, routing and observability. Moving evaluation alone may produce smaller chat bundles but adds another deployable service. Neither migration is needed merely because three 137 MB functions exist.

## Size estimates and validation limits

A read-only dependency-closure analysis of uv.lock and locally installed macOS distribution RECORD files estimated:

| Removal after equivalent refactor | Local uncompressed dependency bytes avoided |
| --- | ---: |
| pandas and newly unneeded pytz | about 40.5 MB |
| langchain-community and dependencies no longer reachable from other roots | about 22.1 MB |
| Both together, also releasing NumPy | about 83.3 MB |

These are **not deployed Linux measurements** and cannot be subtracted from the dashboard's 137 MB figure or multiplied into guaranteed quota savings. Python has no automatic tree-shaking: lazy imports alone do not remove installed dependencies from the bundle. The local virtualenv also contains stale heavyweight packages excluded from deployment; its total size is not a Vercel bundle measurement.

For implementation, run focused CSV/PDF, knowledge-ingestion and evaluation-import tests, keep the active knowledge snapshot unchanged, and compare all three Resources sizes in one controlled preview. Verify chat, authenticated dashboard, uploads, sync, evaluation execution and both queue handlers before production release. No tests were run for this read-only audit; no paid evaluations were invoked.

## Pending decisions

- Recommended first scope: dependency and packaging optimization while keeping the full dashboard, evaluations and Vercel deployment architecture.
- Recommended retention requirement: current production, current dev, and two known-good production rollback releases, with other history treated as eligible only after reviewing aliases and investigation needs. This is a proposal, not an applied deletion policy.
- No ADR is created yet because no architecture trade-off has been selected. Business glossary terms are unchanged; deployment accounting terminology belongs in this operational report.

## Research and graph provenance

Graphify queried the existing graph using its vocabulary: vercel, services, entrypoint, dependencies, requirements, queue, pandas, deepeval, langchain. It surfaced the deployment configuration, requirements and ingestion helpers. The graph has stale source line locations, so recommendations above were checked against current files and live Resources. No graph rebuild was needed.

Current official documentation was retrieved through Exa and Context7:

- https://vercel.com/docs/deployment-storage
- https://vercel.com/docs/deployment-storage/optimize
- https://vercel.com/docs/deployment-retention
- https://vercel.com/docs/functions/runtimes/python
- https://vercel.com/changelog/hobby-projects-now-retain-fewer-deployments-to-free-up-storage
