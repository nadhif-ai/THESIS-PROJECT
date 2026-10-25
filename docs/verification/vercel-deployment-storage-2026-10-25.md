# Deployment storage configuration verification

Verified 2026-10-25 for Vercel `nadhif-s1/thesis-project` (Hobby).

## Applied configuration

- Production branch: `main` (unchanged).
- Git automatic deployments: `git.deploymentEnabled = {"**": false, "main": true, "dev": true}` on all 11 existing remote branches. Only `vercel.json` changed in each commit; every other configuration key was compared with its original value.
- No GitHub Actions, GitLab, CircleCI, or Bitbucket deployment workflows were found in the inspected branch trees. GitHub Actions API reports zero workflows. No deploy hooks were configured.
- Project ignored-build guard: `case "$VERCEL_GIT_COMMIT_REF" in main|dev) exit 1;; *) exit 0;; esac`. This protects branches based on old commits lacking the Git configuration. Such attempts may leave canceled deployment records and count against deployment limits, but do not build application output. Repository `ignoreCommand` overrides must not bypass this policy.
- Project retention: preview, production, canceled, and errored deployments all set to **7 days**, read back from the Vercel API after saving in the Hobby dashboard.
- Existing `deploymentsToKeep: 10` preserved. No team-wide settings changed.

## Verification

- All 11 branch configs reread through GitHub API; commit file lists contain only `vercel.json`.
- Configuration-only main/dev commits were intentionally canceled using a temporary exact-message ignore rule. That temporary rule has been removed; normal main/dev builds are allowed.
- Feature-branch configuration commits produced no new deployments in the inspected recent deployment list.
- Both production aliases still point to `dpl_HnyVMwa7Mx7nVpvymd7uW9iujToc`: `chatbotta-nadhif.vercel.app` and `thesis-project-nadhif-s1.vercel.app`.
- Public homepage HTTP 200; `/health` returns `{"status":"ready","backend":"pinecone"}`.
- Project services, resource settings/regions, protection, Git connection and automatic domain assignment unchanged. Repository services, rewrites, `bom1` region and queue subscriber configuration preserved.
- `LANGSMITH_TRACING=false venv/bin/python -m pytest testing/test_vercel_configuration.py -q`: **2 passed**.
- Guard exit-code checks: main/dev build (1); feature, codex, release and empty ref skip (0).
- Local main fast-forwarded to the configuration commit. Existing unrelated WhatsApp edits preserved.
- No manual deployment deletions, application refactors, promotions, or rollbacks performed.

## Limits and expected savings

All four requested one-week retention choices were accepted on Hobby. The standard Preview environment's branch matcher is read-only, so Git configuration and the project ignore guard enforce the branch policy. Manual CLI/API deployments remain outside the automatic Git policy.

At constant deployment frequency and average artifact size, reducing an eligible retention window from 30 to 7 days represents approximately **76.7% less retained eligible history at steady state**, before protected deployments and recovery storage. This is a model, not measured byte savings. Removing other-branch automatic builds avoids their future artifacts; actual savings depend on their frequency and size.

Vercel preserves aliased deployments, recent deployments, and the latest preview of active branches. Existing feature-branch previews can therefore remain protected even after automatic builds are disabled. The configured rollback count was not lowered. Vercel's published Hobby defaults protect the last 3 deployments and last 3 ready production deployments; those defaults do not justify changing this project's existing count of 10.

Cleanup is asynchronous: eligible deployments are typically marked within 48 hours, former exceptions can take up to 30 days to be reevaluated, and successful deployments have a 30-day recovery period. Storage usage need not fall immediately or by the modeled percentage.

## Sources

- https://vercel.com/docs/project-configuration/git-configuration
- https://vercel.com/docs/deployment-retention
- https://vercel.com/docs/monorepos#ignoring-the-build-step
- https://vercel.com/changelog/hobby-projects-now-retain-fewer-deployments-to-free-up-storage

## Configuration commits

- `codex/catalog-runtime-dependency`: https://github.com/nadhif-ai/THESIS-PROJECT/commit/0892daec1a185e90e7cdc7919825ceab4b650d0b
- `codex/conversational-prompt-release`: https://github.com/nadhif-ai/THESIS-PROJECT/commit/b00a28ffb38860027a475d698878dd23214dc624
- `codex/evaluation-methodology-and-formulas`: https://github.com/nadhif-ai/THESIS-PROJECT/commit/ab8abb287a3d6fe2cfb7ef095ef2584b7e5a1c0f
- `codex/evaluation-terminal-state`: https://github.com/nadhif-ai/THESIS-PROJECT/commit/57008b6c13482dbae5ffbbd5da3f1744752f6a5e
- `codex/evaluation-worker-recovery`: https://github.com/nadhif-ai/THESIS-PROJECT/commit/60dc793694977ca5bf02ccfe014409c42474904b
- `codex/product-image-release`: https://github.com/nadhif-ai/THESIS-PROJECT/commit/304925972295643658e5b60e47a342c607c98703
- `codex/single-knowledge-base`: https://github.com/nadhif-ai/THESIS-PROJECT/commit/8d1ffec83e85a7c6f348ba094ed302cbfb91b8ec
- `codex/whatsapp-reliability`: https://github.com/nadhif-ai/THESIS-PROJECT/commit/aa792b06066c49f15259b894e47bc36b60f294de
- `dev`: https://github.com/nadhif-ai/THESIS-PROJECT/commit/3d85b063ecc0d8ef461b565e4da051b992cca829
- `improve-evaluation-workflow-rag-quality`: https://github.com/nadhif-ai/THESIS-PROJECT/commit/b1683ce7d1a36bb7638351e8d616bf4c7f41b395
- `main`: https://github.com/nadhif-ai/THESIS-PROJECT/commit/b9fd1ed6636dfdf7b5a79e74b481d45a6750ba98
